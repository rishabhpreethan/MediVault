from celery import Celery

from app.config import settings

celery_app = Celery(
    "medivault",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.extraction_tasks",
        "app.workers.nlp_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)
