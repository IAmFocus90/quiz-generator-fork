import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import ssl
from redis.asyncio import Redis


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


redis_kwargs = {
    "decode_responses": True,  # strings instead of bytes
}

parsed = urlparse(REDIS_URL)
if parsed.scheme == "rediss":
    # create SSL context instead of passing ssl=True directly
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    redis_kwargs.update({
        "ssl": ssl_ctx,  # <--- pass SSLContext object
    })


# One shared async Redis client for reuse across the app.
redis: Redis = Redis.from_url(REDIS_URL, **redis_kwargs)


async def get_redis_client() -> Redis:
    """
    Return the shared Redis client. Import and call this from other modules (or import `redis` directly).
    """
    return redis


async def close_redis_client() -> None:
    """Gracefully close the client (call on app shutdown)."""
    try:
        await redis.close()
        await redis.connection_pool.disconnect()
    except Exception:
        # intentionally silent here, function not called anywhere yet; swap for logging when called and if needed
        pass

