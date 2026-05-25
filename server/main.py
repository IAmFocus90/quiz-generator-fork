import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from slowapi.errors import RateLimitExceeded

from server.app.api.router import router as app_router
from server.app.core.rate_limiter import limiter, rate_limit_handler
from server.app.db.core.connection import (
    database,
    get_auth_events_collection,
    get_quizzes_collection,
    get_user_sessions_collection,
    get_users_collection,
    startUp,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
raw_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
origins = [origin.strip() for origin in raw_origins if origin.strip() and origin.strip() != "*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startUp()
    redis_client = Redis.from_url(redis_url, decode_responses=True)
    app.state.redis = redis_client
    app.state.users_collection = get_users_collection()
    app.state.user_sessions_collection = get_user_sessions_collection()
    app.state.auth_events_collection = get_auth_events_collection()
    app.state.quizzes_collection = get_quizzes_collection()

    yield

    get_users_collection().database.client.close()
    await redis_client.close()


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.database = database
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(app_router)
