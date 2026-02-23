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
from google.cloud import discoveryengine_v1alpha as discoveryengine

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


def search_annual_reports(nonprofit_name: str, query: str) -> str:
    """
    USE THIS TOOL FIRST
    Searches official nonprofit Annual Reports (PDFs)
    Use this to find verified financial metrics, cost-per-unit, and historical beneficiary
    counts before general web search for recent momentum.
    """

    print(f"\n[RAG TOOL] Searching Agent Builder: '{nonprofit_name} {query}'")

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("DATA_STORE_LOCATION", "global")
    data_store_id = os.environ.get("DATA_STORE_ID")

    # debug
    print(f"\n[DIAGNOSTICS] ----------------------------------")
    print(f"Project ID    : {project_id}")
    print(f"Location      : {location}")
    print(f"Data Store ID : {data_store_id}")
    print(f"Query         : {nonprofit_name} {query}")

    if not data_store_id:
        print("ERROR: DATA_STORE_ID is missing from environment variables!")
        print(f"------------------------------------------------\n")
        return "ERROR: DATA_STORE_ID is missing from environment variables."

    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = client.serving_config_path(
            project=project_id,
            location=location,
            data_store=data_store_id,
            serving_config="default_search"
        )
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=f"{nonprofit_name} {query}",
            page_size=3,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                search_result_mode=discoveryengine.SearchRequest.ContentSearchSpec.SearchResultMode.CHUNKS,
                chunk_spec=discoveryengine.SearchRequest.ContentSearchSpec.ChunkSpec(
                    num_previous_chunks=1,
                    num_next_chunks=1,
                ),
            ),
        )
        response = client.search(request)  # GCP call

        context = ""
        for i, result in enumerate(response.results):
            if result.chunk and result.chunk.content:
                context += f"[Annual Report]: {result.chunk.content}\n"

        if context:
            print(f"[RAG SUCCESS] Retrieved {len(response.results)} chunks from the database!")
            print(f"[RAG PREVIEW] {context[:150]}...\n")
        else:
            print("[RAG WARNING] Database returned 0 results. Check if PDFs are indexed properly.\n")
        return context if context else "No annual report data found."
    except Exception as e:
        print(f"\n[RAG ERROR] Google Cloud failed: {e}\n")
        return f"Database error: {e}"



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
#  Agent 1A — Internal Data Agent (RAG)                                        #
#  Model  : Gemini 2.0 Flash                                                   #
#  Tools  : search_annual_reports (Custom GCP Agent Builder Tool)              #
# =========================================================================== #
_INTERNAL_DATA_INSTRUCTION = """\
You are an internal financial analyst for Benevity.
YOUR MISSION: Use the `search_annual_reports` tool to extract verified financial 
metrics, cost-per-unit impact (e.g., "$10 provides a meal"), and historical 
beneficiary counts for the requested nonprofit.

Return a structured INTERNAL REPORT containing:
- Specific dollar-to-impact ratios (if found)
- Verified historical metrics
- If no data is found, state: "No internal annual report data available."
"""

internal_data_agent = Agent(
    name="internal_data_agent",
    model="gemini-2.0-flash-001",
    description="Searches the internal Agent Builder database for official Annual Reports and financial metrics.",
    instruction=_INTERNAL_DATA_INSTRUCTION,
    tools=[search_annual_reports],
)

# =========================================================================== #
#  Agent 1 — Research Agent                                                    #
#  Model  : Gemini 2.0 Flash                                                   #
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
#  Model  : Gemini 2.0 flash                                                    #
#  Tools  : NONE — intentionally sandboxed to research data only               #
# =========================================================================== #

_SYNTHESIS_INSTRUCTION = """\
You are an award-winning nonprofit copywriter for Benevity whose work inspires corporate donors.

YOUR MISSION: Transform the Research Report and INTERNAL Report into a compelling, highly cohesive 2-paragraph "Impact Story".

CRITICALLY IMPORTANT RULES:
1. NO INTERNET: You must use ONLY information from the provided reports. 
2. DONOR MATH: You MUST explicitly mention the donor's specific contribution amount in the second paragraph.
 If the Internal Report provides a cost-per-unit, calculate their exact impact. If not, *explain generally what their specific amount helps fund* (VERY IMPORTANT))
3. HALLUCINATION CHECK: If a data point is missing, Do not guess.

PARAGRAPH 1 — The Human Impact
Focus on ONE specific community or event from the reports. Weave in 2 verified statistics about that specific event to show the scale of the need and the Red Cross's response.

PARAGRAPH 2 — Forward Momentum & The Donor
Explicitly mention their donation amount. Connect the organization's demonstrated momentum to what their contribution makes possible next. End with a clear call-to-action.

STYLE RULES
  • Warm, second-person voice, active voice.
  • No jargon or passive constructions.
  • Maximum 150 words total.

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
#  Model  : Gemini 2.0 Flash                                                    #
#  Tools  : NONE — performs analytical reasoning only                          #
#  output_schema enforces structured JSON output (controlled generation)       #
# =========================================================================== #

_VALIDATION_INSTRUCTION = """\
You are an elite fact-checker for Benevity. You evaluate the STORY DRAFT against the INTERNAL REPORT and Research REPORT.

PASS 1 — FACTUAL ACCURACY
  Extract each factual claim in the story.
  For each claim, look it up in either the Internal or Research Report.
  Any UNSUPPORTED claim → REJECTED.

PASS 2 — WRITING QUALITY
  Flag grammar errors, passive voice, or stories exceeding 150 words.
  Writing issues alone → REJECTED.

PASS 3 — VERDICT
  APPROVED : ALL claims are SUPPORTED and NO writing issues found.
  REJECTED : Any UNSUPPORTED claim OR any writing issue.

CRITICAL RULES:
  • Return ONLY the JSON object.
  • "factual_errors" lists every UNSUPPORTED claim.
  • "writing_issues" lists every writing problem.
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
#  Model  : Gemini 2.0 Flash                                                    #
#  Tools  : AgentTool wrappers for the three sub-agents above                  #
# =========================================================================== #

_ORCHESTRATOR_INSTRUCTION = f"""\
You are the Orchestrator of Benevity's Impact Story generation pipeline.
Your job is to coordinate three specialist agents in the correct order and
manage a validation-retry loop.

YOU HAVE ACCESS TO THREE TOOLS:
  internal_data_agent — searches the database for official Annual Reports and financial metrics
  research_agent    — searches for verified nonprofit impact data
  synthesis_agent   — writes the donor story from research data only
  validation_agent  — fact-checks and edits the story; returns JSON verdict

═══ WORKFLOW (follow this EXACTLY) ══════════════════════════════════════════

STEP 1 — RESEARCH
  a. Call internal_data_agent with the nonprofit name to get financial metrics. Save as INTERNAL REPORT.
  b. Call research_agent with the nonprofit name, today's date ({_TODAY}), and the user's prompt.
  Save the full output as the RESEARCH REPORT.

STEP 2 — STORY DRAFT (attempt 1)
  Call synthesis_agent. Pass it BOTH the INTERNAL REPORT (if available) and RESEARCH REPORT.
  Save the output as STORY DRAFT.

STEP 3 — VALIDATE
  Call validation_agent. Pass it BOTH the INTERNAL REPORT (if available) and the RESEARCH REPORT and the STORY DRAFT.
  Save the full JSON response.

STEP 4 — RETRY LOOP (if needed)
  If the JSON status is "REJECTED" AND you have made fewer than {_MAX_REWRITES}
  rewrite attempts so far:
    a. Call synthesis_agent again. Pass it:
         - The full RESEARCH REPORT and INTERNAL REPORT (if available)
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
        AgentTool(agent=internal_data_agent),
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

    test_org    = "Canadian Red Cross"
    test_prompt = (
        "A donor from Vancouver recently contributed $100 to the Canadian Red Cross. "
        "Focus specifically on recent efforts in Canada or "
        "British Columbia. Combine verified financial metrics "
        "from their annual reports with recent news to close the feedback loop for the donor."
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