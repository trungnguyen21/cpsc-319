from fastapi import APIRouter, Depends

from ..dependencies import get_current_user

TOKEN_TTL = 60

router = APIRouter(
    tags=["dashboard"],
    prefix="/organizations",
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]
)

@router.get("/search")
async def search_org():
    return "list of orgs here"

@router.get("/{orgID}")
async def search_org(orgID: str):
    return f"profile for {orgID}"

