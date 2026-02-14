from typing import Annotated
from datetime import datetime, timedelta, timezone

import jwt, asyncpg
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from jwt.exceptions import InvalidTokenError
from starlette.requests import Request

from .models import UserInDB, TokenData
from .config import TOKEN_TTL, SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)
password_hash = PasswordHash.recommended()
# the tokenUrl="login" refers to a relative URL /login
# does not create /login endpoint but client should use that endpoint to get the token
oauth_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_db(request: Request):
    db_manager = request.app.state.db_manager
    async with db_manager.pool.acquire() as conn:
        yield conn

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

async def get_user(db: asyncpg.Connection, username: str):
    row = await db.fetchrow('''
                        SELECT * FROM AdminUsers WHERE username=$1
                     ''', username)
    if row is None:
        return None
    user_dict = dict(row)
    return UserInDB(**user_dict)

async def authenticate_user(db, username: str, password: str):
    user = await get_user(db, username)

    if not user:
        return False

    if not verify_password(password, user.hashed_password):
        return False
    
    return user

async def signup_user(db: asyncpg.Connection, username: str, full_name: str, email: str, passwd_hashed: str):
    try:
        await db.execute('''
                INSERT INTO AdminUsers (username, full_name, email, hashed_password)
                VALUES  ($1, $2, $3, $4)
                ON CONFLICT (username) DO NOTHING;
                ''', username, full_name, email, passwd_hashed)
        return True
    except Exception as e:
        logger.info(f"Failed to signup user: {e}")
        return False
    

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL)

    to_encode.update({"exp": expire})

    # use jwt to encode the token with ALGORITHM, KEY and TTL
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth_scheme)], db: Annotated[asyncpg.Connection, Depends(get_db)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not verify credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
