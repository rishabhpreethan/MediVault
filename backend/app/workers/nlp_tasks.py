from app.workers.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_nlp(self, document_id: str) -> None:
    """Run NLP extraction on raw document text. Implemented in MV-040."""
    raise NotImplementedError("Implemented in MV-040")
