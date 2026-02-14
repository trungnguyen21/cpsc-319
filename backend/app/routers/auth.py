from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..dependencies import authenticate_user, create_access_token, get_password_hash, fake_users_db
from ..models import Token, UserSignUp

import asyncpg

TOKEN_TTL = 60
POSTGRES_URI = "postgresql://benevity:alpine@localhost:5432/AdminUsers"

router = APIRouter(
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    ## Login endpoint
    
    * :param form_data: Reads `username` and `password`
    * :type form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
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
async def signup(form_data: Annotated[dict, UserSignUp]):
    user = UserSignUp(**form_data)
    passwd_hased = get_password_hash(user.password)

    try:
        conn = await asyncpg.connect(POSTGRES_URI)
        await conn.execute('''
            INSERT INTO AdminUsers (username, full_name, email, hashed_password)
            VALUES  (:username, :full_name, :email, :hashed_password)
            ON CONFLICT (username) DO NOTHING;
            ''', user.username, user.full_name, user.email, passwd_hased)
        return {
            "statusCode": 200,
            "detail": f"Sign up {user.username} successfully."
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to sign up user"
        )
