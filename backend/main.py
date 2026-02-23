import asyncpg
import logging

from typing import Annotated

from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager

from app.models import User
from app.dependencies import get_current_user
from app.routers import auth, dashboard, stories
from app.config import POSTGRES_URI

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, POSTGRES_URI):
        self.URL = POSTGRES_URI

    async def get_db_pool(self):
        return await asyncpg.create_pool(
            dsn=self.URL,
        )

    async def initialize_connection(self):
        try: 
            self.pool = await self.get_db_pool()
            logger.info("Successfully connect to database")
        except Exception as e:
            logger.info("Failed to connect to database connection pool.")
            return None

    async def close_connection(self):
        if self.pool:
            await self.pool.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the connection pool once"""
    global db 
    db = DatabaseManager(POSTGRES_URI=POSTGRES_URI)
    await db.initialize_connection()
    app.state.db_manager = db # store in app state
    yield
    await app.state.db_manager.close_connection()

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(stories.router)

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
