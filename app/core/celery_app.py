from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "v11pos_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.modules.data_copy.tasks", "app.modules.billing.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "expire-trials-daily": {
            "task": "billing.expire_trials",
            "schedule": 86400.0,
        },
        "reset-monthly-orders": {
            "task": "billing.reset_monthly_orders",
            "schedule": 86400.0,
        },
    },
)
