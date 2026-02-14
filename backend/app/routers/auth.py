import asyncpg

from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..dependencies import authenticate_user, create_access_token, get_password_hash, get_db, signup_user
from ..models import Token, UserSignUp

TOKEN_TTL = 60

router = APIRouter(
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                db: Annotated[asyncpg.Connection, Depends(get_db)]):
    """
    ## Login endpoint
    
    * :param form_data: Reads `username` and `password`
    * :type form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/ password"
        )
    access_token_expires = timedelta(minutes=TOKEN_TTL)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/signup")
async def signup(form_data: Annotated[dict, UserSignUp],
                 db: Annotated[asyncpg.Connection, Depends(get_db)]):
    passwd_hased = get_password_hash(form_data.password)
    result = await signup_user(
        db=db,
        username=form_data.username,
        full_name=form_data.full_name,
        email=form_data.email,
        passwd_hashed=passwd_hased
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to sign up user"
        )
        
    return {
        "status_code": 200,
        "detail": f"Sign up {form_data.username} successfully."
    }

