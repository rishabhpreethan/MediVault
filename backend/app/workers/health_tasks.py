"""Worker health-check task.

Used by the /api/v1/health endpoint and the docker-compose healthcheck
to verify the Celery worker is alive and connected to the broker.
"""
from app.workers.celery_app import celery_app


@celery_app.task(name="worker.ping", queue="default")
def ping() -> str:
    """Lightweight liveness check. Returns 'pong'."""
    return "pong"
