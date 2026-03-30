"""Unit tests for Celery worker configuration and task registration."""
import pytest

from app.workers.celery_app import celery_app, TASK_QUEUES, TASK_ROUTES
from app.workers.extraction_tasks import extract_document
from app.workers.nlp_tasks import process_nlp
from app.workers.health_tasks import ping


class TestCeleryAppConfig:
    def test_app_name(self):
        assert celery_app.main == "medivault"

    def test_serialization(self):
        conf = celery_app.conf
        assert conf.task_serializer == "json"
        assert conf.result_serializer == "json"
        assert "json" in conf.accept_content

    def test_reliability_settings(self):
        conf = celery_app.conf
        assert conf.task_acks_late is True
        assert conf.task_reject_on_worker_lost is True
        assert conf.worker_prefetch_multiplier == 1

    def test_timezone(self):
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True

    def test_result_expires(self):
        assert celery_app.conf.result_expires == 86400

    def test_default_queue(self):
        assert celery_app.conf.task_default_queue == "default"


class TestTaskQueues:
    def _queue_names(self):
        return {q.name for q in TASK_QUEUES}

    def test_three_queues_defined(self):
        assert len(TASK_QUEUES) == 3

    def test_queue_names(self):
        names = self._queue_names()
        assert {"default", "extraction", "nlp"} == names


class TestTaskRoutes:
    def test_extraction_task_routed(self):
        assert "app.workers.extraction_tasks.extract_document" in TASK_ROUTES
        route = TASK_ROUTES["app.workers.extraction_tasks.extract_document"]
        assert route["queue"] == "extraction"

    def test_nlp_task_routed(self):
        assert "app.workers.nlp_tasks.process_nlp" in TASK_ROUTES
        route = TASK_ROUTES["app.workers.nlp_tasks.process_nlp"]
        assert route["queue"] == "nlp"


class TestExtractionTask:
    def test_task_registered(self):
        assert "extraction.extract_document" in celery_app.tasks

    def test_max_retries(self):
        assert extract_document.max_retries == 3

    def test_retry_delay(self):
        assert extract_document.default_retry_delay == 30

    def test_queue(self):
        assert extract_document.queue == "extraction"

    def test_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            extract_document.run("test-doc-id")


class TestNlpTask:
    def test_task_registered(self):
        assert "nlp.process_nlp" in celery_app.tasks

    def test_max_retries(self):
        assert process_nlp.max_retries == 3

    def test_retry_delay(self):
        assert process_nlp.default_retry_delay == 60

    def test_queue(self):
        assert process_nlp.queue == "nlp"

    def test_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            process_nlp.run("test-doc-id")


class TestPingTask:
    def test_task_registered(self):
        assert "worker.ping" in celery_app.tasks

    def test_returns_pong(self):
        result = ping.run()
        assert result == "pong"

    def test_queue(self):
        assert ping.queue == "default"
