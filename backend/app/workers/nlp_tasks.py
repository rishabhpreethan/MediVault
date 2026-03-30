from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="nlp.process_nlp",
    queue="nlp",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_nlp(self, document_id: str) -> dict:
    """Run NLP extraction on raw document text.

    Args:
        document_id: UUID string of the Document record.

    Returns:
        dict with keys: document_id, entities_extracted

    Full implementation in MV-040.
    """
    logger.info("process_nlp called", extra={"document_id": document_id})
    raise NotImplementedError("Implemented in MV-040")
