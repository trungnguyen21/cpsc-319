from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..dependencies import get_current_user
from ..service.ai_service import generate_impact_story

TOKEN_TTL = 60

class StoryGenerationRequest(BaseModel):
    orgID: str
    user_prompt: str

class Story(BaseModel):
    storyID: str
    content: str
    organizationID: str
    status: str

router = APIRouter(
    tags=["stories"],
    prefix="/stories",
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]
)

@router.get("/")
async def get_stories():
    """Get only the story title and the org ID"""
    return "list of stories here"

@router.post("/generation")
async def generate_story(request: StoryGenerationRequest):
    """
    Triggers the full Multi-Agent-System pipeline via generate_impact_story():

    Input (StoryGenerationRequest):
        orgID       → passed as org_id       (nonprofit/organization name)
        user_prompt → passed as user_prompt  (additional donor/context info)

    Pipeline:
      1. Internal Data Agent  (RAG over annual report PDFs)
      2. Research Agent       (Google Search, last 12 months only)
      3. Synthesis Agent      (writes the 2-paragraph donor story)
      4. Validation Agent     (fact-checks + writing audit → APPROVED/REJECTED)
         ↑ Orchestrator retries Synthesis up to 2 times on REJECTED.

    Response:
      {
        "status"        : "APPROVED" | "REJECTED",
        "story"         : "<2-paragraph impact story>",
        "factual_errors": [],
        "writing_issues": [],
        "facts_summary" : "<verified metrics used>",
        "org_id"        : "<echoed back>"
      }
    """
    try:
        result = await generate_impact_story(
            org_id=request.orgID,
            user_prompt=request.user_prompt,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return result

@router.get("/{storyID}")
async def get_story_detail(storyID: str):
    return f"Full content of {storyID} here"

@router.patch("/{storyID}")
async def edit_story(updated_story: Story):
    return f"Update the content of story {updated_story.storyID}"

@router.post("/{storyID}/send")
async def story_dispatch(storyID: str):
    return f"Send to all the donors for story {storyID}"
