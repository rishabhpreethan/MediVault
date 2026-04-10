"""Thin SendGrid email service wrapper.

No PHI must appear in email templates or log messages — only document type,
processing status, and app URL are included.
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)

_SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send a transactional email via the SendGrid v3 API.

    Returns True on success, False on any failure (disabled, missing key,
    or HTTP error).  Never raises — callers should treat False as a
    non-critical, best-effort notification.
    """
    if not settings.notifications_enabled:
        logger.warning("Notifications disabled; skipping email to user (ID only in production)")
        return False

    if not settings.sendgrid_api_key:
        logger.warning("SENDGRID_API_KEY not set; skipping email notification")
        return False

    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": settings.from_email},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_body}],
    }

    headers = {
        "Authorization": f"Bearer {settings.sendgrid_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(_SENDGRID_SEND_URL, json=payload, headers=headers, timeout=10)
        if response.status_code >= 400:
            logger.error(
                "SendGrid returned error status",
                extra={"status_code": response.status_code},
            )
            return False
        return True
    except Exception as exc:
        logger.error("Failed to send email via SendGrid", extra={"error": str(exc)})
        return False


# ---------------------------------------------------------------------------
# Template helpers — no PHI; only document_type, status, and app_url
# ---------------------------------------------------------------------------

def send_processing_complete_email(
    to: str,
    document_type: str,
    app_url: str,
) -> bool:
    """Notify a user that their document has been processed successfully."""
    subject = "Your document is ready — MediVault"
    html_body = f"""
    <html>
      <body>
        <p>Good news! Your <strong>{document_type}</strong> document has been
        processed successfully.</p>
        <p>Processing status: <strong>Complete</strong></p>
        <p><a href="{app_url}">View your health profile</a></p>
        <hr/>
        <small>MediVault &mdash; Your personal health record vault.</small>
      </body>
    </html>
    """
    return send_email(to, subject, html_body)


def send_extraction_failed_email(
    to: str,
    document_type: str,
    app_url: str,
) -> bool:
    """Notify a user that document extraction failed."""
    subject = "Document processing issue — MediVault"
    html_body = f"""
    <html>
      <body>
        <p>We were unable to process your <strong>{document_type}</strong>
        document.</p>
        <p>Processing status: <strong>Failed</strong></p>
        <p>Please try uploading the document again or contact support.</p>
        <p><a href="{app_url}">Go to MediVault</a></p>
        <hr/>
        <small>MediVault &mdash; Your personal health record vault.</small>
      </body>
    </html>
    """
    return send_email(to, subject, html_body)
