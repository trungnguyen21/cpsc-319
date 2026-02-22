"""
Benevity — Intelligent Nonprofit Matching: Multi-Agent System
==============================================================
Agents
------
    research_agent    Gemini 2.0 Flash + Google Search grounding
    synthesis_agent   Gemini 2.0 Flash  (NO tools — can only use research data)
    validation_agent  Gemini 2.0 Flash  (fact-check + grammar/readability audit)
    orchestrator      Gemini 2.0 Flash  (drives the loop via AgentTool calls)

    All agents use gemini-2.0-flash-001 for the MVP — cheapest viable model
    that still handles complex instruction-following well.

Loop logic (inside the Orchestrator)
---------
    1. research_agent  → raw research report
    2. synthesis_agent → story draft  (attempt 1)
    3. validation_agent → APPROVED or REJECTED + errors
    if REJECTED and rewrites_so_far < 2:
        4. synthesis_agent → revised story  (attempt 2 or 3)
        5. validation_agent → APPROVED or REJECTED + errors
    Orchestrator emits the final JSON regardless of outcome.

Why AgentTool and not SequentialAgent?
    SequentialAgent is linear — it cannot branch back to Synthesis on rejection.
    AgentTool wraps each sub-agent so the Orchestrator LLM controls the flow.

Why no output_schema on synthesis_agent / orchestrator?
    ADK constrains: an agent cannot have BOTH tools and output_schema.
    validation_agent has output_schema (no tools needed) — controlled generation
    enforces valid JSON.  The Orchestrator simply echoes that JSON as its last
    message, which we parse in generate_impact_story().
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load .env before anything reads os.environ
load_dotenv()

# --------------------------------------------------------------------------- #
# Google ADK                                                                    #
# --------------------------------------------------------------------------- #
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Vertex AI backend — ADK reads these env-vars automatically                   #
# Set GCP_PROJECT_ID and GCP_LOCATION in your .env                             #
# --------------------------------------------------------------------------- #
# Switch between backends:
#   Option A — Google AI Studio (free API key, simplest for MVP):
#              Set GOOGLE_GENAI_USE_VERTEXAI=FALSE and GOOGLE_API_KEY in .env
#   Option B — Vertex AI (full GCP project, production path):
#              Set GOOGLE_GENAI_USE_VERTEXAI=TRUE, GCP_PROJECT_ID, GCP_LOCATION in .env
#              and run: gcloud auth application-default login
_use_vertexai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper()
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", _use_vertexai)
if _use_vertexai == "TRUE":
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT_ID", ""))
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.getenv("GCP_LOCATION", "us-central1"))

_APP_NAME = "benevity_mas"
_MAX_REWRITES = 2   # Synthesis can be asked to rewrite at most 2 times


# =========================================================================== #
#  Pydantic schema — Validation Agent's structured output                      #
# =========================================================================== #

class ValidationOutput(BaseModel):
    """
    Structured verdict produced by the Validation Agent.

    status          : "APPROVED" — all checks passed.
                      "REJECTED" — one or more issues found.
    story           : The story draft being evaluated (verbatim).
    factual_errors  : Claims in the story not supported by the research report
                      (hallucinations, extrapolations, contradictions).
    writing_issues  : Grammar mistakes or overly complex language flagged for
                      the Synthesis agent to fix on a rewrite.
    facts_summary   : One sentence listing the key verified metrics used.
    """
    status: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    story: str
    factual_errors: list[str] = Field(default_factory=list)
    writing_issues: list[str] = Field(default_factory=list)
    facts_summary: str = Field(default="")


# =========================================================================== #
#  Agent 1 — Research Agent                                                    #
#  Model  : Gemini 1.5 Flash (fast, cost-efficient for search-heavy work)      #
#  Tools  : google_search (grounded retrieval)                                 #
# =========================================================================== #

_TODAY = datetime.now().strftime("%B %d, %Y")
_CUTOFF = datetime.now().replace(year=datetime.now().year - 1).strftime("%B %d, %Y")

_RESEARCH_INSTRUCTION = f"""\
You are an expert nonprofit research analyst for Benevity, a corporate giving platform.

TODAY'S DATE: {_TODAY}
DATA CUTOFF : {_CUTOFF}  ← Discard any information published before this date.

═══ YOUR MISSION ═══════════════════════════════════════════════════════════════
Research the specified nonprofit and extract concrete, quantitative impact data
published within the LAST 12 MONTHS ONLY.

WHAT TO LOOK FOR (use as many as search results support)
  • Funds raised or disbursed (dollar amounts)
  • Number of beneficiaries reached / lives impacted
  • Specific programs, campaigns, or initiatives launched or completed
  • Volunteer hours or employee-giving participation data
  • Measurable environmental or social outcomes
  • Credible third-party recognition, partnerships, or awards

SEARCH STRATEGY — run multiple targeted queries, for example:
  "[nonprofit name] 2024 2025 annual report impact results"
  "[nonprofit name] funds raised beneficiaries 2024"
  "[nonprofit name] new programs initiatives recent"

STRICT RULES
  1. Every metric MUST include a source URL and publication date.
  2. If a source is older than {_CUTOFF}, omit it entirely.
  3. Do NOT invent, estimate, or extrapolate figures under any circumstances.
  4. If no data within 12 months is found for a category, say so explicitly.

═══ OUTPUT FORMAT ════════════════════════════════════════════════════════════
Return a structured RESEARCH REPORT with these sections:

## Organization
[Name] — [one-sentence mission statement]

## Verified Metrics (last 12 months)
- [Metric]: [value]  |  Source: [URL]  |  Date: [publication date]
- ...

## Recent News & Achievements
[Short paragraph of notable activities in the last 12 months]

## Unverified / Insufficient Data
[List any categories where data could not be found within the 12-month window]
"""

research_agent = Agent(
    name="research_agent",
    model="gemini-2.0-flash-001",
    description=(
        "Researches a nonprofit's verified impact data from the last 12 months "
        "using grounded Google Search. Returns a structured research report."
    ),
    instruction=_RESEARCH_INSTRUCTION,
    tools=[google_search],
)


# =========================================================================== #
#  Agent 2 — Synthesis Agent                                                   #
#  Model  : Gemini 1.5 Pro (quality narrative writing)                         #
#  Tools  : NONE — intentionally sandboxed to research data only               #
# =========================================================================== #

_SYNTHESIS_INSTRUCTION = """\
You are an award-winning nonprofit copywriter for Benevity whose work inspires
corporate donors to give.

═══ YOUR MISSION ═══════════════════════════════════════════════════════════════
Transform the Research Report you have been given into a donor-facing
"Impact Story" — a compelling 2-paragraph narrative.

CRITICALLY IMPORTANT: You must use ONLY information that appears in the
Research Report. You have no access to the internet. Do not introduce any
statistic, program name, dollar amount, or claim that cannot be found verbatim
in the Research Report.  If a data point you need is missing, write
[DATA NOT AVAILABLE] in its place — do not guess or make it up.

PARAGRAPH 1 — Human Impact
Open with the people or communities served. Weave in 2–3 specific, verified
statistics from the Research Report to anchor the emotion in real outcomes.

PARAGRAPH 2 — Forward Momentum
Connect the organization's demonstrated momentum to what the donor's
contribution makes possible next. End with one clear, memorable call-to-action.

STYLE RULES
  • Warm, second-person voice ("your support…"), active voice.
  • No jargon, acronyms, or passive constructions.
  • Plain language — avoid complex or technical vocabulary.
  • Maximum 150 words total.

If you receive a rewrite request, you will also be given a list of errors from
the reviewer. Address every error explicitly in your revised story.

OUTPUT: Return the story text ONLY — no headers, labels, or commentary.
"""

synthesis_agent = Agent(
    name="synthesis_agent",
    model="gemini-2.0-flash-001",
    description=(
        "Converts the research report into a 2-paragraph donor-facing Impact "
        "Story using ONLY verified facts from the research. No internet access."
    ),
    instruction=_SYNTHESIS_INSTRUCTION,
    # tools intentionally omitted — synthesis_agent is fully sandboxed
)


# =========================================================================== #
#  Agent 3 — Validation Agent                                                  #
#  Model  : Gemini 1.5 Pro                                                     #
#  Tools  : NONE — performs analytical reasoning only                          #
#  output_schema enforces structured JSON output (controlled generation)       #
# =========================================================================== #

_VALIDATION_INSTRUCTION = """\
You are an elite fact-checker and senior editor for Benevity's content pipeline.
You are the final gatekeeper before any story reaches a donor.

Your inputs (both available to you in this conversation):
  [RESEARCH REPORT] — the verified raw data from the Research Agent.
  [STORY DRAFT]     — the narrative written by the Synthesis Agent.

═══ YOUR 3-PASS VALIDATION PROTOCOL ════════════════════════════════════════

PASS 1 — FACTUAL ACCURACY (compare story against research report)
  Read every sentence of the story. Extract each factual claim:
  numbers, percentages, program names, geographic scope, beneficiary counts,
  dollar figures, dates, outcomes.

  For each claim, look it up in the Research Report:
    SUPPORTED     → The Research Report contains this exact figure with a source.
    UNSUPPORTED   → Not found in the Research Report, contradicted, or
                    extrapolated beyond what is stated.
    PLACEHOLDER   → The story contains a [DATA NOT AVAILABLE] marker.

  Any UNSUPPORTED claim → REJECTED.
  Any PLACEHOLDER remaining → REJECTED (means research data was insufficient
  for a full story — do not approve incomplete stories).

PASS 2 — WRITING QUALITY (read as the target audience: a corporate HR manager)
  Flag any of the following:
    • Grammatical errors or awkward sentence structure.
    • Jargon, acronyms, or technical language a general reader wouldn't know.
    • Overly complex vocabulary (if a simpler word exists, flag it).
    • Passive voice constructions.
    • Story exceeds 150 words.

  Writing issues alone → REJECTED.

PASS 3 — VERDICT
  APPROVED : ALL claims are SUPPORTED and NO writing issues found.
  REJECTED : Any UNSUPPORTED claim OR any writing issue.

═══ CRITICAL RULES ══════════════════════════════════════════════════════════
  • Return ONLY the JSON object — no text before or after it.
  • "factual_errors" lists every UNSUPPORTED claim (empty list if none).
  • "writing_issues" lists every writing problem found (empty list if none).
  • Do NOT alter the story text in the "story" field — copy it verbatim.
  • Be ruthlessly strict. A compelling story with even one unverified
    statistic or one grammar error must be REJECTED.
  • "facts_summary" is one sentence listing the key verified metrics you used.
"""

validation_agent = Agent(
    name="validation_agent",
    model="gemini-2.0-flash-001",
    description=(
        "Fact-checks the story draft against the research report AND audits "
        "grammar/readability. Returns structured JSON: APPROVED or REJECTED."
    ),
    instruction=_VALIDATION_INSTRUCTION,
    output_schema=ValidationOutput,   # controlled generation — guarantees JSON
    # tools intentionally omitted (output_schema + tools cannot coexist in ADK)
)


# =========================================================================== #
#  Agent 4 — Orchestrator                                                      #
#  Model  : Gemini 1.5 Pro                                                     #
#  Tools  : AgentTool wrappers for the three sub-agents above                  #
# =========================================================================== #

_ORCHESTRATOR_INSTRUCTION = f"""\
You are the Orchestrator of Benevity's Impact Story generation pipeline.
Your job is to coordinate three specialist agents in the correct order and
manage a validation-retry loop.

YOU HAVE ACCESS TO THREE TOOLS:
  research_agent    — searches for verified nonprofit impact data
  synthesis_agent   — writes the donor story from research data only
  validation_agent  — fact-checks and edits the story; returns JSON verdict

═══ WORKFLOW (follow this EXACTLY) ══════════════════════════════════════════

STEP 1 — RESEARCH
  Call research_agent with the nonprofit name, today's date ({_TODAY}),
  and the user's prompt.
  Save the full output as the RESEARCH REPORT.

STEP 2 — STORY DRAFT (attempt 1)
  Call synthesis_agent. Pass it the entire RESEARCH REPORT.
  Save the output as STORY DRAFT.

STEP 3 — VALIDATE
  Call validation_agent. Pass it BOTH the RESEARCH REPORT and the STORY DRAFT.
  Save the full JSON response.

STEP 4 — RETRY LOOP (if needed)
  If the JSON status is "REJECTED" AND you have made fewer than {_MAX_REWRITES}
  rewrite attempts so far:
    a. Call synthesis_agent again. Pass it:
         - The full RESEARCH REPORT
         - The rejected STORY DRAFT
         - The factual_errors list from the validation JSON
         - The writing_issues list from the validation JSON
       Instruct it to rewrite the story addressing every listed error.
    b. Call validation_agent again with the RESEARCH REPORT and the new draft.
    c. Update your saved JSON response.
    d. If still REJECTED and rewrites_so_far < {_MAX_REWRITES}, repeat from (a).

STEP 5 — FINAL OUTPUT
  When the loop ends (either APPROVED or max rewrites reached), output the
  validation JSON VERBATIM as your final message — copy it exactly, no extra
  text, no markdown code fences, no labels.  Just the raw JSON object.

IMPORTANT
  • Never skip steps or change their order.
  • Never call synthesis_agent without passing the full RESEARCH REPORT.
  • The synthesis_agent has no internet access — give it ALL the data it needs.
  • Count rewrites carefully: you may rewrite at most {_MAX_REWRITES} times.
  • Your final message must be ONLY the JSON — the downstream system parses it.
"""

orchestrator = Agent(
    name="orchestrator",
    model="gemini-2.0-flash-001",
    description="Orchestrates Research → Synthesis → Validation with retry loop.",
    instruction=_ORCHESTRATOR_INSTRUCTION,
    tools=[
        AgentTool(agent=research_agent),
        AgentTool(agent=synthesis_agent),
        AgentTool(agent=validation_agent),
    ],
)


# =========================================================================== #
#  Public service function — called by the FastAPI router                      #
# =========================================================================== #

def _extract_json(text: str) -> str:
    """
    Robustly extract a JSON object from LLM output that may contain:
      - Prose before/after the JSON
      - Markdown code fences (```json ... ```)
      - Invalid \\' escape sequences (LLM sometimes escapes single quotes)
      - A nested wrapper key e.g. {"validation_agent_response": {...}}
    """
    # 1. Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()

    # 2. Extract the outermost {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return text
    json_str = match.group(0)

    # 3. Fix invalid \' escape sequences (not valid JSON — single quotes don't need escaping)

    json_str = re.sub(r"\\'", "'", json_str)

    # 4. Unwrap nested wrapper key if the orchestrator added one
    #    e.g. {"validation_agent_response": { ...actual payload... }}
    try:
        candidate = json.loads(json_str)
        if isinstance(candidate, dict) and len(candidate) == 1:
            inner = next(iter(candidate.values()))
            if isinstance(inner, dict) and "status" in inner:
                json_str = json.dumps(inner)
    except Exception:
        pass  # leave as-is and let the caller handle parse errors

    return json_str


async def generate_impact_story(org_id: str, user_prompt: str) -> dict[str, Any]:
    """
    Run the full MAS pipeline and return a structured result dict:

        {
            "status"        : "APPROVED" | "REJECTED",
            "story"         : "<2-paragraph impact story>",
            "factual_errors": [],
            "writing_issues": [],
            "facts_summary" : "<one-liner of verified metrics used>",
            "org_id"        : "<echoed back>",
        }

    Raises RuntimeError if the pipeline fails to produce any output.
    """
    session_service = InMemorySessionService()
    user_id = "system"
    session_id = f"{org_id.replace(' ', '_')}_{uuid.uuid4().hex[:8]}"

    await session_service.create_session(
        app_name=_APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    runner = Runner(
        agent=orchestrator,
        app_name=_APP_NAME,
        session_service=session_service,
    )

    # Seed message that starts the entire pipeline
    seed_message = types.Content(
        role="user",
        parts=[types.Part(text=(
            f"Nonprofit / Organization : {org_id}\n"
            f"Additional context       : {user_prompt}\n"
            f"Today's date             : {_TODAY}\n\n"
            "Please begin the pipeline."
        ))],
    )

    final_text: str | None = None
    _pipeline_start = datetime.now()

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=seed_message,
        ):
            if hasattr(event, "author"):
                logger.debug("Event from agent: %s", event.author)

            # Collect any text emitted by the orchestrator.
            # is_final_response() can fire on a function_call event (no text),
            # so we track the last text seen across all orchestrator events and
            # fall back to that if the final event has no text.
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        # Only capture text from the top-level orchestrator
                        if getattr(event, "author", None) == "orchestrator":
                            final_text = part.text
                        break

    except Exception as exc:
        logger.exception("MAS pipeline error for org '%s'.", org_id)
        raise RuntimeError(f"Impact story generation failed: {exc}") from exc

    total_elapsed = round((datetime.now() - _pipeline_start).total_seconds(), 1)

    if final_text is None:
        raise RuntimeError("Pipeline completed but produced no output.")

    # ---------------------------------------------------------------------- #
    # Parse the Orchestrator's final output (echoed validation JSON)          #
    # ---------------------------------------------------------------------- #
    try:
        json_str = _extract_json(final_text)
        payload = json.loads(json_str)
        result = ValidationOutput(**payload)
    except Exception as exc:
        logger.error(
            "Could not parse final JSON.\nRaw output:\n%s\nError: %s",
            final_text, exc,
        )
        # Graceful degradation — surface the raw text so the API isn't empty
        return {
            "status": "ERROR",
            "story": final_text,
            "factual_errors": [f"Output parse failure: {exc}"],
            "writing_issues": [],
            "facts_summary": "",
            "org_id": org_id,
            "total_elapsed": total_elapsed,
        }

    return {
        "status": result.status,
        "story": result.story,
        "factual_errors": result.factual_errors,
        "writing_issues": result.writing_issues,
        "facts_summary": result.facts_summary,
        "org_id": org_id,
        "total_elapsed": total_elapsed,
    }


# =========================================================================== #
#  CLI test harness                                                             #
#  Run with:  python -m app.service.ai_service                                 #
#                                                                               #
#  Prerequisites:                                                               #
#    1. GCP_PROJECT_ID and GCP_LOCATION set in backend/.env                    #
#    2. gcloud auth application-default login                                   #
#    3. Vertex AI API enabled on the project                                    #
# =========================================================================== #

async def _main() -> None:
    import textwrap

    test_org    = "American Red Cross"
    test_prompt = (
        "A donor recently contributed to the American Red Cross and wants to know "
        "the real-world impact of their generosity. Focus on the March 2025 Myanmar "
        "earthquake response — relief efforts, number of people helped, shelters "
        "provided, funds raised, and aid delivered. The story should close the "
        "feedback loop for the donor and inspire continued giving."
    )

    bar = "=" * 67
    print(f"\n{bar}")
    print("  Benevity — Impact Story Generator  (MVP Demo)")
    print(bar)
    print(f"  Org    : {test_org}")
    print(f"  Prompt : {test_prompt}")
    print(f"  Time   : {datetime.now().strftime('%H:%M:%S')}")
    print(f"{bar}\n")

    print("  Running pipeline (Research → Synthesis → Validation)...", end="", flush=True)
    result = await generate_impact_story(test_org, test_prompt)
    print(f" done ({result.get('total_elapsed', '?')}s)\n")

    print(f"\n{bar}")
    print(f"  FINAL STATUS : {result['status']}")
    print(f"  FACTS USED   : {result['facts_summary']}")
    print(bar)
    print("\n  ── IMPACT STORY ──────────────────────────────────────────────\n")
    for line in textwrap.wrap(result["story"], width=65):
        print(f"  {line}")

    if result["factual_errors"]:
        print("\n  ── FACTUAL ERRORS ────────────────────────────────────────────")
        for err in result["factual_errors"]:
            print(f"  ✗  {err}")

    if result["writing_issues"]:
        print("\n  ── WRITING ISSUES ────────────────────────────────────────────")
        for issue in result["writing_issues"]:
            print(f"  ✎  {issue}")

    print(f"\n{bar}\n")


if __name__ == "__main__":
    asyncio.run(_main())
