# Benevity — Multi-Agent Impact Story Generator

Generates a 2-paragraph donor-facing "Impact Story" for a given nonprofit using a pipeline of 5 Gemini 2.0 Flash agents coordinated by Google ADK.

---

## Relevant Files

| File                              | Purpose                                                                     |
| --------------------------------- | --------------------------------------------------------------------------- |
| `ai_service.py`                   | Agent definitions, ADK wiring, pipeline runner (`generate_impact_story`)    |
| `prompts.py`                      | All agent instruction prompts — edit here to tune agent behaviour           |
| `../routers/stories.py`           | FastAPI endpoint `POST /stories/generation` — calls `generate_impact_story` |
| `../../tests/test_ai_pipeline.py` | CLI test - runs the full pipeline end to end                                |
| `../../.env`                      | GCP credentials and config (see Quick Start below)                          |

---

## Agents & Responsibilities

```
internal_data_agent   Searches internal annual report PDFs (RAG via GCP Agent Builder)
                      → outputs: INTERNAL REPORT (verified dollar-to-impact ratios)

research_agent        Google Search grounded to last 12 months only
                      → outputs: RESEARCH REPORT (verified metrics + recent news)

synthesis_agent       Writes the 2-paragraph donor story from both reports (no internet)
                      → outputs: STORY DRAFT

validation_agent      Fact-checks every claim + audits grammar/length
                      → outputs: JSON verdict { status, story, factual_errors, writing_issues }

orchestrator          Coordinates the 4 agents above in order and manages the retry loop
```

### Pipeline Loop

```
orchestrator
  ├─ 1. internal_data_agent  →  INTERNAL REPORT
  ├─ 2. research_agent       →  RESEARCH REPORT
  ├─ 3. synthesis_agent      →  STORY DRAFT
  ├─ 4. validation_agent     →  APPROVED ✓  (done)
  │                          →  REJECTED ✗
  │       ├─ 5. synthesis_agent  (rewrite with error feedback)
  │       └─ 6. validation_agent (re-check)
  │              ... up to 2 rewrites total
  └─ emits final JSON regardless of outcome
```

---

## Quick Start

### 1. GCP Setup

- Make sure you have access to the GCP project
- Enable **Vertex AI** and **Discovery Engine (Agent Builder)** APIs
- Run: `gcloud auth application-default login`

### 2. Required `.env` values for Multi-Agent-System

```env
# --- Vertex AI ---
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GCP_PROJECT_ID=your-gcp-project-id          # GCP Console → project selector
GCP_LOCATION=us-central1

# --- Agent Builder (RAG data store) ---
DATA_STORE_ID=your-data-store-id            # Agent Builder → Data Stores → your store
DATA_STORE_LOCATION=global

```

### 3. Run the test

```bash
cd backend
uv sync
uv run python -m tests.test_ai_pipeline
```
