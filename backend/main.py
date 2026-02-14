from typing import Annotated

from fastapi import Depends, FastAPI

from app.models import User
from app.dependencies import get_current_user
from app.routers import auth


app = FastAPI()
app.include_router(auth.router)

@app.get("/")
async def helloworld():
    return "Hello World"

@app.get("/users/me")
async def user(current_user: Annotated[User, Depends(get_current_user)]):
    """
    ## User
    Get the current user
    """
    return current_user
