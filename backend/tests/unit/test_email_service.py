"""Unit tests for the SendGrid email service wrapper."""
from __future__ import annotations

from typing import Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers to override settings inside tests
# ---------------------------------------------------------------------------

def _patch_settings(notifications_enabled: bool = True, api_key: Optional[str] = "test-sg-key"):
    """Return a mock that replaces app.services.email_service.settings."""
    mock_settings = MagicMock()
    mock_settings.notifications_enabled = notifications_enabled
    mock_settings.sendgrid_api_key = api_key
    mock_settings.from_email = "noreply@medivault.health"
    return mock_settings


# ---------------------------------------------------------------------------
# send_email behaviour tests
# ---------------------------------------------------------------------------

class TestSendEmail:
    def test_send_email_skipped_when_disabled(self):
        """Returns False without making an HTTP call when notifications_enabled=False."""
        mock_settings = _patch_settings(notifications_enabled=False)

        with patch("app.services.email_service.settings", mock_settings), \
             patch("app.services.email_service.requests.post") as mock_post:
            from app.services.email_service import send_email
            result = send_email("user@example.com", "Subject", "<p>body</p>")

        assert result is False
        mock_post.assert_not_called()

    def test_send_email_skipped_when_no_api_key(self):
        """Returns False without making an HTTP call when sendgrid_api_key is None."""
        mock_settings = _patch_settings(notifications_enabled=True, api_key=None)

        with patch("app.services.email_service.settings", mock_settings), \
             patch("app.services.email_service.requests.post") as mock_post:
            from app.services.email_service import send_email
            result = send_email("user@example.com", "Subject", "<p>body</p>")

        assert result is False
        mock_post.assert_not_called()

    def test_send_email_calls_sendgrid_api(self):
        """Calls SendGrid v3 /mail/send with the correct URL and Bearer auth header."""
        mock_settings = _patch_settings()

        mock_response = MagicMock()
        mock_response.status_code = 202

        with patch("app.services.email_service.settings", mock_settings), \
             patch("app.services.email_service.requests.post", return_value=mock_response) as mock_post:
            from app.services.email_service import send_email
            result = send_email("user@example.com", "Hello", "<p>hi</p>")

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args

        # Verify URL
        positional_args = call_kwargs[0] if call_kwargs[0] else []
        url = positional_args[0] if positional_args else call_kwargs[1].get("url") or call_kwargs.args[0]
        assert url == "https://api.sendgrid.com/v3/mail/send"

        # Verify auth header
        headers = call_kwargs[1].get("headers") or call_kwargs.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer test-sg-key"

    def test_send_email_returns_false_on_http_error(self):
        """Returns False (no exception propagated) when requests.post raises."""
        mock_settings = _patch_settings()

        with patch("app.services.email_service.settings", mock_settings), \
             patch("app.services.email_service.requests.post", side_effect=ConnectionError("timeout")):
            from app.services.email_service import send_email
            result = send_email("user@example.com", "Subject", "<p>body</p>")

        assert result is False


# ---------------------------------------------------------------------------
# Template function tests (HTML body content)
# ---------------------------------------------------------------------------

class TestEmailTemplates:
    def test_processing_complete_email_template(self):
        """html_body for processing-complete contains app_url and 'complete' (case-insensitive)."""
        mock_settings = _patch_settings()
        mock_response = MagicMock()
        mock_response.status_code = 202

        captured_body: list[str] = []

        def capture_post(url, json=None, headers=None, timeout=None):
            if json:
                for content_block in json.get("content", []):
                    captured_body.append(content_block.get("value", ""))
            return mock_response

        with patch("app.services.email_service.settings", mock_settings), \
             patch("app.services.email_service.requests.post", side_effect=capture_post):
            from app.services.email_service import send_processing_complete_email
            send_processing_complete_email(
                to="user@example.com",
                document_type="Lab Report",
                app_url="https://app.medivault.health",
            )

        assert captured_body, "No email body was captured"
        body = captured_body[0].lower()
        assert "complete" in body
        assert "https://app.medivault.health" in captured_body[0]

    def test_extraction_failed_email_template(self):
        """html_body for extraction-failed contains 'failed' (case-insensitive)."""
        mock_settings = _patch_settings()
        mock_response = MagicMock()
        mock_response.status_code = 202

        captured_body: list[str] = []

        def capture_post(url, json=None, headers=None, timeout=None):
            if json:
                for content_block in json.get("content", []):
                    captured_body.append(content_block.get("value", ""))
            return mock_response

        with patch("app.services.email_service.settings", mock_settings), \
             patch("app.services.email_service.requests.post", side_effect=capture_post):
            from app.services.email_service import send_extraction_failed_email
            send_extraction_failed_email(
                to="user@example.com",
                document_type="Prescription",
                app_url="https://app.medivault.health",
            )

        assert captured_body, "No email body was captured"
        body = captured_body[0].lower()
        assert "failed" in body
