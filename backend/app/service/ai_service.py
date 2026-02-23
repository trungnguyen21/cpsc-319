"""
Benevity — Intelligent Nonprofit Matching: Multi-Agent System
==============================================================
Agents
------
    internal_data_agent  Gemini 2.0 Flash + GCP Agent Builder (RAG over annual report PDFs)
    research_agent       Gemini 2.0 Flash + Google Search grounding
    synthesis_agent      Gemini 2.0 Flash  (NO tools — can only use research data)
    validation_agent     Gemini 2.0 Flash  (fact-check + grammar/readability audit)
    orchestrator         Gemini 2.0 Flash  (uses AgentTool which allows to re-run agents in a loop in the case of validation failures)

    ***FOR THE MVP***: All agents use gemini-2.0-flash-001 as they are the cheapest model

Loop logic (inside the Orchestrator)
---------
    1. internal_data_agent → internal report (RAG over annual report PDFs)
    2. research_agent      → raw research report (Google Search)
    3. synthesis_agent     → story draft  (attempt 1)
    4. validation_agent    → APPROVED or REJECTED + errors
    if REJECTED and rewrites_so_far < 2:
        5. synthesis_agent → revised story  (attempt 2 or 3)
        6. validation_agent → APPROVED or REJECTED + errors
    Orchestrator emits the final JSON regardless of outcome.

Why no output_schema on synthesis_agent / orchestrator?
    ADK constrains: an agent cannot have BOTH tools and output_schema.
    validation_agent has output_schema (no tools needed) — controlled generation
    enforces valid JSON.  The Orchestrator simply echoes that JSON as its last
    message, which we parse in generate_impact_story().
"""

from __future__ import annotations

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

from .prompts import (
    INTERNAL_DATA_INSTRUCTION,
    RESEARCH_INSTRUCTION,
    SYNTHESIS_INSTRUCTION,
    VALIDATION_INSTRUCTION,
    build_orchestrator_instruction,
    _TODAY,
)

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
_MAX_REWRITES = 2   # Synthesis can be asked to rewrite at most 2 times (also passed to build_orchestrator_instruction)


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

internal_data_agent = Agent(
    name="internal_data_agent",
    model="gemini-2.0-flash-001",
    description="Searches the internal Agent Builder database for official Annual Reports and financial metrics.",
    instruction=INTERNAL_DATA_INSTRUCTION,
    tools=[search_annual_reports],
)

# =========================================================================== #
#  Agent 1 — Research Agent                                                    #
#  Model  : Gemini 2.0 Flash                                                   #
#  Tools  : google_search (grounded retrieval)                                 #
# =========================================================================== #

research_agent = Agent(
    name="research_agent",
    model="gemini-2.0-flash-001",
    description=(
        "Researches a nonprofit's verified impact data from the last 12 months "
        "using grounded Google Search. Returns a structured research report."
    ),
    instruction=RESEARCH_INSTRUCTION,
    tools=[google_search],
)


# =========================================================================== #
#  Agent 2 — Synthesis Agent                                                   #
#  Model  : Gemini 2.0 flash                                                    #
#  Tools  : NONE — intentionally sandboxed to research data only               #
# =========================================================================== #

synthesis_agent = Agent(
    name="synthesis_agent",
    model="gemini-2.0-flash-001",
    description=(
        "Converts the research report into a 2-paragraph donor-facing Impact "
        "Story using ONLY verified facts from the research. No internet access."
    ),
    instruction=SYNTHESIS_INSTRUCTION,
)


# =========================================================================== #
#  Agent 3 — Validation Agent                                                  #
#  Model  : Gemini 2.0 Flash                                                    #
#  Tools  : NONE — performs analytical reasoning only                          #
#  output_schema enforces structured JSON output (controlled generation)       #
# =========================================================================== #

validation_agent = Agent(
    name="validation_agent",
    model="gemini-2.0-flash-001",
    description=(
        "Fact-checks the story draft against the research report AND audits "
        "grammar/readability. Returns structured JSON: APPROVED or REJECTED."
    ),
    instruction=VALIDATION_INSTRUCTION,
    output_schema=ValidationOutput,   # controlled generation — guarantees JSON
    # tools intentionally omitted (output_schema + tools cannot coexist in ADK)
)


# =========================================================================== #
#  Agent 4 — Orchestrator                                                      #
#  Model  : Gemini 2.0 Flash                                                   #
#  Tools  : AgentTool wrappers for all four sub-agents above                   #
# =========================================================================== #

orchestrator = Agent(
    name="orchestrator",
    model="gemini-2.0-flash-001",
    description="Orchestrates Research → Synthesis → Validation with retry loop.",
    instruction=build_orchestrator_instruction(_MAX_REWRITES),
    tools=[
        AgentTool(agent=internal_data_agent),
        AgentTool(agent=research_agent),
        AgentTool(agent=synthesis_agent),
        AgentTool(agent=validation_agent),
    ],
)


# =========================================================================== #
#  Private helpers                                                             #
# =========================================================================== #

def _extract_json(text: str) -> str:
    """
    Cleans up the Orchestrator's raw text output so it can be parsed as JSON.
    Called by generate_impact_story() after the pipeline run completes.

    Even when instructed to return only JSON, LLMs sometimes wrap it in
    markdown code fences, add prose before/after, use invalid escape sequences,
    or nest it inside an extra wrapper key. This function strips all of that.
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


# =========================================================================== #
#  Public API — entry point for the FastAPI router                             #
# =========================================================================== #

async def generate_impact_story(org_id: str, user_prompt: str) -> dict[str, Any]:
    """
    Run the full Multi-Agent-System pipeline and return a structured result dict.

    Called by POST /stories/generation (stories router).
    
    Input:
    Params come from StoryGenerationRequest:
        org_id      ← request.orgID       (the nonprofit/organization name)
        user_prompt ← request.user_prompt (additional context from the user)

    Output:
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
