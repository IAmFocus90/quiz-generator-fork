from celery import Celery
import os
from dotenv import load_dotenv
from urllib.parse import urlparse


load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
parsed = urlparse(redis_url)

# Check if using secure Redis (rediss://)
use_ssl = parsed.scheme == "rediss"



celery_app = Celery(
    "quiz_app",
    broker=redis_url,
    backend=redis_url,
)

if use_ssl:
    celery_app.conf.broker_use_ssl = {
        "ssl_cert_reqs": "CERT_NONE"
    }
    celery_app.conf.redis_backend_use_ssl = {
        "ssl_cert_reqs": "CERT_NONE"
    }


celery_app.conf.task_routes = {
    "server.tasks.send_quiz_email": {"queue": "email"}
}

import server.app.share.share_tasks
