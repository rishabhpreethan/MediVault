from celery import Celery
from kombu import Exchange, Queue

from app.config import settings

# ── Queue / Exchange definitions ───────────────────────────────────────────────
default_exchange = Exchange("default", type="direct")
extraction_exchange = Exchange("extraction", type="direct")
nlp_exchange = Exchange("nlp", type="direct")

TASK_QUEUES = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("extraction", extraction_exchange, routing_key="extraction"),
    Queue("nlp", nlp_exchange, routing_key="nlp"),
)

TASK_ROUTES = {
    "app.workers.extraction_tasks.extract_document": {
        "queue": "extraction",
        "routing_key": "extraction",
    },
    "app.workers.export_tasks.generate_user_export": {
        "queue": "default",
        "routing_key": "default",
    },
    "app.workers.nlp_tasks.process_nlp": {
        "queue": "nlp",
        "routing_key": "nlp",
    },
}

# ── Celery application ─────────────────────────────────────────────────────────
celery_app = Celery(
    "medivault",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.extraction_tasks",
        "app.workers.export_tasks",
        "app.workers.nlp_tasks",
        "app.workers.health_tasks",
    ],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Queues and routing
    task_queues=TASK_QUEUES,
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    task_routes=TASK_ROUTES,
    # Result expiry — keep results for 24 hours
    result_expires=86400,
    # Retry defaults (tasks override individually)
    task_max_retries=3,
    # Beat schedule placeholder (populated in MV-031+)
    beat_schedule={},
)
