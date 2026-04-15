import os
from celery import Celery
from celery.schedules import crontab

from core.config import settings

celery_app = Celery("diplom")

celery_app.conf.broker_url = settings.celery.broker_url
celery_app.conf.result_backend = settings.celery.result_backend

# Общие настройки
celery_app.conf.timezone = os.getenv("CELERY_TIMEZONE", "UTC")
celery_app.conf.enable_utc = True
celery_app.conf.task_track_started = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True

# Авто-импорт тасок
celery_app.conf.imports = ("tasks.sessions",)

# Расписание Celery Beat
celery_app.conf.beat_schedule = {
    "cleanup-user-sessions-daily": {
        "task": "tasks.sessions.cleanup_user_sessions",
        # Каждый день в 03:10 UTC
        "schedule": crontab(hour=3, minute=10),
        "args": (7,),  # retention_days = 7
    },
}