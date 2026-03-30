from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="extraction.extract_document",
    queue="extraction",
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def extract_document(self, document_id: str) -> dict:
    """Extract text from a PDF document.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, status, library_used

    Full implementation in MV-031.
    """
    logger.info("extract_document called", extra={"document_id": document_id})
    raise NotImplementedError("Implemented in MV-031")
