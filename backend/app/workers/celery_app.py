"""
Celery Configuration and Task Queue Setup
"""

from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "cerebro",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.audio_worker",
        "app.workers.document_worker",
        "app.workers.web_worker",
        "app.workers.image_worker",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
)
