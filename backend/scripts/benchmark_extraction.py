"""Benchmarking script for PDF text extraction fidelity.

Measures the text extraction accuracy of the extraction pipeline against
known ground-truth samples. Target: >=95% fidelity = PASS.

Usage:
    python3 backend/scripts/benchmark_extraction.py

Exit codes:
    0 — all samples passed (>=95% fidelity)
    1 — one or more samples failed (<95% fidelity)
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import List

# ---------------------------------------------------------------------------
# Path setup: allow running from repo root or from backend/
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# ---------------------------------------------------------------------------
# ANSI colour helpers
# ---------------------------------------------------------------------------
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

FIDELITY_THRESHOLD = 0.95  # 95%

# ---------------------------------------------------------------------------
# Minimal valid PDF bytes — contains the text "Hello World"
# ---------------------------------------------------------------------------
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 44>>stream\n"
    b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
    b"endstream\nendobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000274 00000 n \n"
    b"0000000370 00000 n \n"
    b"trailer<</Size 6/Root 1 0 R>>\n"
    b"startxref\n441\n%%EOF"
)


def _make_pdf_with_text(text_line: str) -> bytes:
    """Build a minimal PDF that renders a single line of ASCII text.

    Only printable ASCII characters that are safe inside a PDF content stream
    are supported (parentheses are escaped).  Non-ASCII characters are dropped.
    """
    safe = re.sub(r"[^\x20-\x7e]", "", text_line)
    safe = safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content = f"BT /F1 12 Tf 100 700 Td ({safe}) Tj ET\n".encode()
    length = len(content)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        + f"4 0 obj<</Length {length}>>stream\n".encode()
        + content
        + b"endstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000274 00000 n \n"
        b"0000000370 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n441\n%%EOF"
    )
    return pdf


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkSample:
    """Represents one PDF extraction benchmark test case."""

    name: str
    pdf_path: str           # path to PDF file, or "" when pdf_bytes is supplied
    ground_truth: str       # expected extracted text (key phrases that MUST appear)
    expected_keywords: List[str]  # specific words/numbers that must be in output
    pdf_bytes: bytes = field(default=b"", repr=False)  # inline bytes (overrides pdf_path)


# ---------------------------------------------------------------------------
# Fidelity calculation
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Lowercase and strip punctuation, return list of word tokens."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return [t for t in text.split() if t]


def calculate_fidelity(extracted: str, ground_truth: str) -> float:
    """Return proportion of ground-truth tokens found in extracted text.

    Args:
        extracted: Text returned by the extraction pipeline.
        ground_truth: Reference text with all expected words.

    Returns:
        Float in [0.0, 1.0]. Returns 0.0 if ground_truth is empty.
    """
    gt_tokens = _tokenize(ground_truth)
    if not gt_tokens:
        return 0.0

    gt_set = set(gt_tokens)
    ext_set = set(_tokenize(extracted))
    return len(gt_set & ext_set) / len(gt_set)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_benchmark(samples: List[BenchmarkSample]) -> dict:
    """Run the extraction pipeline against all samples and report results.

    Args:
        samples: List of BenchmarkSample instances to evaluate.

    Returns:
        Summary dict with keys: total, passed, failed, average_fidelity, results.
    """
    from app.extractors.orchestrator import extract_with_fallback  # noqa: PLC0415

    results = []
    total_fidelity = 0.0

    for sample in samples:
        # Resolve PDF bytes
        if sample.pdf_bytes:
            pdf_bytes = sample.pdf_bytes
        elif sample.pdf_path:
            with open(sample.pdf_path, "rb") as fh:
                pdf_bytes = fh.read()
        else:
            print(f"{_YELLOW}[SKIP]{_RESET} {sample.name} — no pdf_bytes or pdf_path")
            continue

        try:
            result = extract_with_fallback(pdf_bytes)
            extracted_text = result.text
        except Exception as exc:  # noqa: BLE001
            extracted_text = ""
            print(f"{_RED}[ERROR]{_RESET} {sample.name}: extraction raised {exc}")

        fidelity = calculate_fidelity(extracted_text, sample.ground_truth)
        total_fidelity += fidelity

        ext_lower = extracted_text.lower()
        found_keywords = [kw for kw in sample.expected_keywords if kw.lower() in ext_lower]
        missing_keywords = [kw for kw in sample.expected_keywords if kw.lower() not in ext_lower]

        passed = fidelity >= FIDELITY_THRESHOLD

        if passed:
            status_str = f"{_GREEN}{_BOLD}PASS{_RESET}"
        else:
            status_str = f"{_RED}{_BOLD}FAIL{_RESET}"

        print(
            f"  [{status_str}] {sample.name:40s} "
            f"fidelity={fidelity:.2%}  "
            f"keywords_found={len(found_keywords)}/{len(sample.expected_keywords)}"
        )
        if missing_keywords:
            print(f"         {_RED}missing keywords:{_RESET} {', '.join(missing_keywords)}")

        results.append(
            {
                "name": sample.name,
                "passed": passed,
                "fidelity": round(fidelity, 4),
                "keywords_found": found_keywords,
                "keywords_missing": missing_keywords,
                "library_used": getattr(
                    result if "result" in dir() else None, "library_used", "unknown"
                ),
            }
        )

    n = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = n - passed_count
    avg_fidelity = total_fidelity / n if n > 0 else 0.0

    return {
        "total": n,
        "passed": passed_count,
        "failed": failed_count,
        "average_fidelity": round(avg_fidelity, 4),
        "results": results,
    }


# ---------------------------------------------------------------------------
# Synthetic benchmark samples
# ---------------------------------------------------------------------------

def build_synthetic_samples() -> List[BenchmarkSample]:
    """Return 3 synthetic BenchmarkSample instances with in-memory PDF bytes."""

    # Sample 1: basic "Hello World"
    sample1 = BenchmarkSample(
        name="Synthetic — Hello World",
        pdf_path="",
        ground_truth="Hello World",
        expected_keywords=["Hello", "World"],
        pdf_bytes=MINIMAL_PDF,
    )

    # Sample 2: lab report style — numeric values
    lab_text = "Glucose 95 mg/dL Reference 70 to 100"
    sample2 = BenchmarkSample(
        name="Synthetic — Lab Report Values",
        pdf_path="",
        ground_truth=lab_text,
        expected_keywords=["Glucose", "95", "70", "100"],
        pdf_bytes=_make_pdf_with_text(lab_text),
    )

    # Sample 3: medication prescription style
    rx_text = "Metformin 500mg twice daily for 30 days"
    sample3 = BenchmarkSample(
        name="Synthetic — Prescription Text",
        pdf_path="",
        ground_truth=rx_text,
        expected_keywords=["Metformin", "500mg", "30"],
        pdf_bytes=_make_pdf_with_text(rx_text),
    )

    return [sample1, sample2, sample3]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    """Run benchmark and return exit code (0 = all pass, 1 = any fail)."""
    print(f"\n{_BOLD}MediVault — PDF Extraction Fidelity Benchmark{_RESET}")
    print(f"Target threshold: {FIDELITY_THRESHOLD:.0%}\n")

    samples = build_synthetic_samples()

    print(f"Running {len(samples)} sample(s)…\n")
    summary = run_benchmark(samples)

    print(f"\n{'─' * 60}")
    print(
        f"  Total:   {summary['total']}\n"
        f"  Passed:  {_GREEN}{summary['passed']}{_RESET}\n"
        f"  Failed:  {_RED}{summary['failed']}{_RESET}\n"
        f"  Avg fidelity: {summary['average_fidelity']:.2%}"
    )
    print("─" * 60)

    if summary["failed"] == 0:
        print(f"\n{_GREEN}{_BOLD}All samples passed.{_RESET} Extraction fidelity meets the >=95% target.\n")
        return 0
    else:
        print(
            f"\n{_RED}{_BOLD}{summary['failed']} sample(s) failed.{_RESET} "
            "Extraction fidelity is below the 95% target.\n"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
