"""SMTP email service.

No PHI must appear in email templates or log messages — only document type,
processing status, and app URL are included.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_body: str) -> bool:
    """Send a transactional email via SMTP (TLS).

    Returns True on success, False on any failure (disabled, missing config,
    or SMTP error).  Never raises — callers should treat False as a
    non-critical, best-effort notification.
    """
    if not settings.notifications_enabled:
        logger.warning("Notifications disabled; skipping email to user (ID only in production)")
        return False

    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP_USER or SMTP_PASSWORD not set; skipping email notification")
        return False

    from_addr = settings.from_email or settings.smtp_user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(from_addr, [to], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Failed to send email via SMTP", extra={"error": str(exc)})
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


def send_family_invite_email(
    to: str,
    inviter_name: str,
    relationship: str,
    accept_url: str,
    app_url: str,
) -> bool:
    """Send a family invitation email to a prospective family member.

    No PHI in the email — only the inviter's display name, relationship label,
    and a tokenised accept URL.
    """
    rel_label = relationship.capitalize()
    subject = f"{inviter_name} has invited you to join their family circle — MediVault"
    html_body = f"""
    <html>
      <body style="font-family: sans-serif; color: #1a1a1a; max-width: 520px; margin: auto;">
        <h2 style="color: #006b5f;">You've been invited to MediVault</h2>
        <p><strong>{inviter_name}</strong> has invited you to join their family
        circle as a <strong>{rel_label}</strong>.</p>
        <p>MediVault lets families securely share and manage health records
        together.</p>
        <p style="margin: 24px 0;">
          <a href="{accept_url}"
             style="background:#006b5f;color:#fff;padding:12px 24px;border-radius:8px;
                    text-decoration:none;font-weight:600;display:inline-block;">
            Accept Invitation
          </a>
        </p>
        <p style="color:#666;font-size:13px;">
          This invitation expires in 7 days. If you did not expect this email
          you can safely ignore it.
        </p>
        <p style="color:#666;font-size:13px;">
          Or copy this link into your browser:<br/>
          <a href="{accept_url}" style="color:#006b5f;">{accept_url}</a>
        </p>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;"/>
        <p style="color:#999;font-size:12px;">
          MediVault &mdash; Your personal health record vault.
          <a href="{app_url}" style="color:#006b5f;">Visit app</a>
        </p>
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
