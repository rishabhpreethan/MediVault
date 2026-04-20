"""Onboarding Celery tasks — MV-152.

NMC (National Medical Commission) licence verification stub.
Real integration with NMC registry is deferred; this task logs the request
and leaves verification_status as PENDING for manual/future resolution.
"""
from __future__ import annotations

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=1, name="onboarding_tasks.verify_licence_task")
def verify_licence_task(
    self,
    user_id: str,
    licence_number: str,
    registration_council: str,
) -> None:
    """Stub: log licence verification request.

    Future implementation will query the NMC public registry at
    https://www.nmc.org.in/ and update provider_profiles.verification_status
    to VERIFIED or FAILED accordingly.
    """
    logger.info(
        "Licence verification queued — user_id=%s council=%s (NMC integration pending)",
        user_id,
        registration_council,
    )
    # No DB write here — status remains PENDING until NMC integration is built.
