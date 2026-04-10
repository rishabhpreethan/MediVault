"""Unit tests for scanned PDF detection heuristic.

Tests cover is_likely_scanned() from app.extractors.orchestrator.
No database or external dependencies are required.
"""
from __future__ import annotations

from app.extractors.orchestrator import is_likely_scanned


class TestIsLikelyScanned:
    def test_is_likely_scanned_empty_text(self):
        """Empty string → True (nothing extracted at all)."""
        assert is_likely_scanned("", page_count=1) is True

    def test_is_likely_scanned_sparse_text(self):
        """40 chars across 2 pages → 20 chars/page → True (< 50 threshold)."""
        text = "a" * 40
        assert is_likely_scanned(text, page_count=2) is True

    def test_is_likely_scanned_sufficient_text(self):
        """200 chars on 1 page → 200 chars/page → False (well above threshold)."""
        text = "a" * 200
        assert is_likely_scanned(text, page_count=1) is False

    def test_is_likely_scanned_zero_pages(self):
        """page_count=0 with 50 chars: absolute threshold passes (>=100 chars needed),
        but per-page heuristic is skipped when page_count == 0.
        50 chars < 100 absolute min → True."""
        text = "a" * 50
        # 50 chars < MIN_ABSOLUTE_CHARS (100) → True regardless of page_count
        assert is_likely_scanned(text, page_count=0) is True

    def test_is_likely_scanned_zero_pages_sufficient_text(self):
        """page_count=0 with 150 chars: per-page check skipped, absolute check passes → False."""
        text = "a" * 150
        assert is_likely_scanned(text, page_count=0) is False

    def test_is_likely_scanned_threshold_edge(self):
        """Exactly 50 chars/page → False (boundary: strictly < 50 is True, == 50 is False)."""
        # 100 chars / 2 pages = exactly 50 chars/page → not scanned
        text = "a" * 100
        assert is_likely_scanned(text, page_count=2) is False

    def test_is_likely_scanned_just_below_threshold(self):
        """99 chars / 2 pages = 49.5 chars/page → True (< 50)."""
        text = "a" * 99
        assert is_likely_scanned(text, page_count=2) is True

    def test_is_likely_scanned_whitespace_only(self):
        """Whitespace-only text strips to empty → True."""
        text = "   \n\t  "
        assert is_likely_scanned(text, page_count=5) is True

    def test_is_likely_scanned_large_pdf_with_enough_text(self):
        """Large PDF (50 pages) with 100 chars/page = 5000 chars → False."""
        text = "a" * 5000
        assert is_likely_scanned(text, page_count=50) is False

    def test_is_likely_scanned_large_pdf_sparse(self):
        """Large PDF (50 pages) with only 200 chars = 4 chars/page → True."""
        text = "a" * 200
        assert is_likely_scanned(text, page_count=50) is True
