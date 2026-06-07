"""Celery application configuration."""

from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "chatbot_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "purge-old-conversations": {
            "task": "app.tasks.cleanup_tasks.purge_expired_conversations",
            "schedule": 86400,  # Run daily (every 24 hours)
        },
        "cleanup-expired-tokens": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_tokens",
            "schedule": 3600,  # Run hourly
        },
    },
)
