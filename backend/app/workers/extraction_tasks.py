from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def extract_document(self, document_id: str) -> None:
    """Extract text from a PDF document. Implemented in MV-031."""
    raise NotImplementedError("Implemented in MV-031")
