from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..dependencies import get_current_user

TOKEN_TTL = 60

class StoryGeneraionRequest(BaseModel):
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
async def search_org(request: StoryGeneraionRequest):
    return f"Generate story for {request.orgID}"

@router.get("/{storyID}")
async def get_story_detail(storyID: str):
    return f"Full content of {storyID} here"

@router.patch("/{storyID}")
async def edit_story(updated_story: Story):
    return f"Update the content of story {updated_story.storyID}"

@router.post("/{storyID}/send")
async def story_dispatch(storyID: str):
    return f"Send to all the donors for story {storyID}"
