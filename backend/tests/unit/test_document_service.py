"""Unit tests for DocumentService state machine — no DB required."""
import pytest

from app.services.document_service import (
    QUEUED, PROCESSING, COMPLETE, FAILED, MANUAL_REVIEW,
    MAX_AUTO_ATTEMPTS,
    InvalidStatusTransition,
    assert_valid_transition,
)


class TestAllowedTransitions:
    def test_queued_to_processing(self):
        assert_valid_transition(QUEUED, PROCESSING)  # no raise

    def test_processing_to_complete(self):
        assert_valid_transition(PROCESSING, COMPLETE)

    def test_processing_to_failed(self):
        assert_valid_transition(PROCESSING, FAILED)

    def test_failed_to_processing(self):
        assert_valid_transition(FAILED, PROCESSING)

    def test_failed_to_manual_review(self):
        assert_valid_transition(FAILED, MANUAL_REVIEW)

    def test_manual_review_to_processing(self):
        assert_valid_transition(MANUAL_REVIEW, PROCESSING)

    def test_complete_to_processing(self):
        assert_valid_transition(COMPLETE, PROCESSING)


class TestInvalidTransitions:
    def test_queued_to_complete_invalid(self):
        with pytest.raises(InvalidStatusTransition):
            assert_valid_transition(QUEUED, COMPLETE)

    def test_queued_to_failed_invalid(self):
        with pytest.raises(InvalidStatusTransition):
            assert_valid_transition(QUEUED, FAILED)

    def test_complete_to_queued_invalid(self):
        with pytest.raises(InvalidStatusTransition):
            assert_valid_transition(COMPLETE, QUEUED)

    def test_complete_to_failed_invalid(self):
        with pytest.raises(InvalidStatusTransition):
            assert_valid_transition(COMPLETE, FAILED)

    def test_processing_to_queued_invalid(self):
        with pytest.raises(InvalidStatusTransition):
            assert_valid_transition(PROCESSING, QUEUED)

    def test_manual_review_to_complete_invalid(self):
        with pytest.raises(InvalidStatusTransition):
            assert_valid_transition(MANUAL_REVIEW, COMPLETE)

    def test_unknown_status_invalid(self):
        with pytest.raises(InvalidStatusTransition):
            assert_valid_transition("UNKNOWN_STATUS", PROCESSING)

    def test_error_message_includes_both_statuses(self):
        with pytest.raises(InvalidStatusTransition) as exc_info:
            assert_valid_transition(QUEUED, COMPLETE)
        assert QUEUED in str(exc_info.value)
        assert COMPLETE in str(exc_info.value)

    def test_error_message_includes_allowed_transitions(self):
        with pytest.raises(InvalidStatusTransition) as exc_info:
            assert_valid_transition(QUEUED, COMPLETE)
        assert PROCESSING in str(exc_info.value)


class TestStatusConstants:
    def test_status_values(self):
        assert QUEUED == "QUEUED"
        assert PROCESSING == "PROCESSING"
        assert COMPLETE == "COMPLETE"
        assert FAILED == "FAILED"
        assert MANUAL_REVIEW == "MANUAL_REVIEW"

    def test_max_attempts(self):
        assert MAX_AUTO_ATTEMPTS == 3


class TestInvalidStatusTransitionError:
    def test_is_exception(self):
        err = InvalidStatusTransition("test")
        assert isinstance(err, Exception)
