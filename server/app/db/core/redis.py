import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from redis.asyncio import Redis, ConnectionPool
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

parsed = urlparse(REDIS_URL)
redis_kwargs = {
    "decode_responses": True,
    "max_connections": 10,
}

if parsed.scheme == "rediss":
    redis_kwargs.update({
        "ssl_cert_reqs": "none",  # Match Celery's configuration
    })

redis_pool = ConnectionPool.from_url(REDIS_URL, **redis_kwargs)
redis = Redis(connection_pool=redis_pool)

async def get_redis_client() -> Redis:
    logger.debug(f"Returning Redis client for URL: {REDIS_URL}, pool size: {redis_pool.max_connections}")
    return redis

async def close_redis_client() -> None:
    try:
        logger.debug("Closing Redis client and connection pool")
        await redis.close()
        await redis.connection_pool.disconnect()
    except Exception as e:
        logger.error(f"Error closing Redis client: {str(e)}")
        