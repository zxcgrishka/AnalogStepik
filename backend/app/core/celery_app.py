import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend="rpc://" # Для получения результатов, если нужно
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Включаем авто-обнаружение тасок в модулях
    imports=["app.worker.tasks"]
)
