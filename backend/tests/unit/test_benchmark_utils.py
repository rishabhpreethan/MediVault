"""Unit tests for benchmark utility functions.

Tests cover calculate_fidelity and run_benchmark helper logic only —
no real PDF extraction is performed (all extractor calls are mocked).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Import the functions under test
# The benchmark script lives in backend/scripts/; add its parent to sys.path
# so it is importable without installing it as a package.
# ---------------------------------------------------------------------------
import importlib
import os
import sys

_BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
_BACKEND_DIR = os.path.normpath(_BACKEND_DIR)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Lazy-import: the module does a sys.path manipulation on load which is safe.
import scripts.benchmark_extraction as bm  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal valid PDF bytes reused across tests (same as used by the script)
# ---------------------------------------------------------------------------
MINIMAL_PDF = bm.MINIMAL_PDF


# ===========================================================================
# calculate_fidelity
# ===========================================================================

class TestCalculateFidelity:
    def test_perfect_match(self):
        """Identical text should yield 1.0 fidelity."""
        score = bm.calculate_fidelity("Hello World", "Hello World")
        assert score == pytest.approx(1.0)

    def test_partial_match(self):
        """Half the words present should yield ~0.5 fidelity."""
        score = bm.calculate_fidelity("Hello there", "Hello World")
        # ground_truth tokens: {hello, world} — extracted has {hello, there}
        # intersection = {hello} → 1/2 = 0.5
        assert score == pytest.approx(0.5)

    def test_no_match(self):
        """No overlapping words should yield 0.0."""
        score = bm.calculate_fidelity("foo bar baz", "Hello World")
        assert score == pytest.approx(0.0)

    def test_empty_ground_truth(self):
        """Empty ground truth should return 0.0 (not division-by-zero)."""
        score = bm.calculate_fidelity("some extracted text", "")
        assert score == pytest.approx(0.0)

    def test_case_insensitive(self):
        """Comparison must be case-insensitive: 'Hello' matches 'hello'."""
        score = bm.calculate_fidelity("hello world", "Hello World")
        assert score == pytest.approx(1.0)

    def test_punctuation_stripped(self):
        """Punctuation in either string should not affect fidelity."""
        score = bm.calculate_fidelity("Hello, World!", "Hello World")
        assert score == pytest.approx(1.0)

    def test_extra_words_in_extracted_do_not_penalise(self):
        """Extra words in extracted text are irrelevant — only GT coverage matters."""
        score = bm.calculate_fidelity("Hello World extra words here", "Hello World")
        assert score == pytest.approx(1.0)

    def test_duplicate_tokens_in_ground_truth(self):
        """Duplicate tokens in GT are collapsed into a set before scoring."""
        # GT set = {hello, world} — size 2
        score = bm.calculate_fidelity("Hello World", "Hello Hello World")
        assert score == pytest.approx(1.0)


# ===========================================================================
# run_benchmark
# ===========================================================================

class TestRunBenchmark:
    """Tests for run_benchmark using mocked extract_with_fallback."""

    def _make_sample(self, name: str, ground_truth: str, keywords: list) -> bm.BenchmarkSample:
        return bm.BenchmarkSample(
            name=name,
            pdf_path="",
            ground_truth=ground_truth,
            expected_keywords=keywords,
            pdf_bytes=MINIMAL_PDF,
        )

    def test_all_pass_when_extraction_returns_perfect_text(self):
        """When extractor returns the exact ground truth, all samples pass."""
        from app.extractors.base import ExtractionResult

        samples = [
            self._make_sample("s1", "Hello World", ["Hello", "World"]),
            self._make_sample("s2", "Glucose 95", ["Glucose", "95"]),
        ]

        perfect_result = ExtractionResult(
            text="Hello World Glucose 95",
            page_count=1,
            has_text_layer=True,
            library_used="pdfminer",
        )

        with patch(
            "app.extractors.orchestrator.extract_with_fallback",
            return_value=perfect_result,
        ):
            summary = bm.run_benchmark(samples)

        assert summary["total"] == 2
        assert summary["passed"] == 2
        assert summary["failed"] == 0
        assert summary["average_fidelity"] == pytest.approx(1.0)

    def test_fails_below_threshold_when_extraction_returns_partial_text(self):
        """When extractor returns text missing most ground-truth words, sample fails."""
        from app.extractors.base import ExtractionResult

        samples = [
            self._make_sample(
                "partial",
                "Patient Name John Doe Date 2024 01 15 Diagnosis Hypertension",
                ["Patient", "John", "Doe", "Hypertension"],
            ),
        ]

        # Return only one word — fidelity will be well below 95%
        partial_result = ExtractionResult(
            text="Patient",
            page_count=1,
            has_text_layer=True,
            library_used="pdfminer",
        )

        with patch(
            "app.extractors.orchestrator.extract_with_fallback",
            return_value=partial_result,
        ):
            summary = bm.run_benchmark(samples)

        assert summary["failed"] >= 1
        assert summary["results"][0]["fidelity"] < bm.FIDELITY_THRESHOLD

    def test_summary_structure(self):
        """run_benchmark result must have the expected top-level keys."""
        from app.extractors.base import ExtractionResult

        samples = [self._make_sample("s1", "Hello World", ["Hello"])]
        mock_result = ExtractionResult(
            text="Hello World",
            page_count=1,
            has_text_layer=True,
            library_used="pdfminer",
        )

        with patch(
            "app.extractors.orchestrator.extract_with_fallback",
            return_value=mock_result,
        ):
            summary = bm.run_benchmark(samples)

        assert "total" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "average_fidelity" in summary
        assert "results" in summary
        assert isinstance(summary["results"], list)

    def test_result_entry_structure(self):
        """Each result entry must contain the expected keys."""
        from app.extractors.base import ExtractionResult

        samples = [self._make_sample("s1", "Hello World", ["Hello", "World"])]
        mock_result = ExtractionResult(
            text="Hello World",
            page_count=1,
            has_text_layer=True,
            library_used="pdfminer",
        )

        with patch(
            "app.extractors.orchestrator.extract_with_fallback",
            return_value=mock_result,
        ):
            summary = bm.run_benchmark(samples)

        entry = summary["results"][0]
        assert "name" in entry
        assert "passed" in entry
        assert "fidelity" in entry
        assert "keywords_found" in entry
        assert "keywords_missing" in entry

    def test_missing_keywords_reported(self):
        """Keywords not in extracted text appear in keywords_missing list."""
        from app.extractors.base import ExtractionResult

        samples = [
            self._make_sample("kw_test", "Hello World", ["Hello", "World", "Missing"]),
        ]
        mock_result = ExtractionResult(
            text="Hello World",
            page_count=1,
            has_text_layer=True,
            library_used="pdfminer",
        )

        with patch(
            "app.extractors.orchestrator.extract_with_fallback",
            return_value=mock_result,
        ):
            summary = bm.run_benchmark(samples)

        entry = summary["results"][0]
        assert "Missing" in entry["keywords_missing"]
        assert "Hello" in entry["keywords_found"]
        assert "World" in entry["keywords_found"]
