# NLP Extraction Patterns & Edge Cases

This is a living document. Update it when you find a new extraction bug, edge case, or pattern worth remembering. Do NOT remove existing entries — append to each section.

---

## Known Extraction Challenges

### Medications
- **Dosage parsing:** "2 tablets BID" must capture unit (tablet) + frequency (BID) as separate fields
- **Duration:** Often missing from documents — do not infer; leave null and set confidence LOW
- **Route of administration:** Sometimes implicit (Insulin → SQ, Aspirin → PO) — capture only when explicitly stated
- **Deduplication:** Match on INN (generic name), not brand name. Use `drug_synonyms.py` for mapping.

### Lab Results
- **Reference ranges:** Lab-specific — parse from the document, never hardcode
- **Units:** Same test can appear in different units across labs (e.g. Hemoglobin: g/dL vs mmol/L) — store unit with value
- **Out-of-range detection:** Derive from the parsed reference range, not hardcoded thresholds

### Diagnoses
- **Implicit dates:** "Chronic HTN" has no date — set confidence LOW, do not guess or fill with document date
- **Status field:** "Resolved", "controlled", "active" are meaningful — extract as a separate field when present
- **ICD code matching:** Not always present in documents; only include when explicitly stated

### Vitals
- **Inconsistent labeling:** "BP", "Blood Pressure", "B.P." are all the same — normalize on extraction
- **Pulse vs Heart Rate:** Treat as equivalent — normalize to a single field

---

## Confidence Scoring Rules

| Score | Label | Meaning |
|---|---|---|
| > 0.85 | HIGH | Clear entity boundaries, explicit values |
| 0.60–0.85 | MEDIUM | Reasonable extraction, some ambiguity |
| < 0.60 | LOW | Flag for user review — do not trust automatically |

All extracted entities must have a `confidence_score`. Missing confidence is a reviewer blocker.

---

## Deduplication Rules

- **Deduplicate:** medications, diagnoses, allergies
- **Do NOT deduplicate:** lab results, vitals (these are time-series data)
- **Skip:** manual entries (`is_manual_entry=True`) — user-entered data is authoritative
- **Service:** use `deduplication_service.py` (built in MV-048)

---

## Test Fixture Matrix

| Fixture | Type | Test Complexity | Notes |
|---|---|---|---|
| `lab_report_v1.pdf` | Digital PDF | Low | Good baseline for unit tests |
| `discharge_summary_v1.pdf` | Scanned PDF | High | Tests OCR path — use for benchmark |
| `prescription_handwritten.pdf` | Mixed format | High | Hardest case; known low accuracy |

Run benchmarks: `pytest tests/benchmarks/extraction_accuracy.py -v`
Targets: ≥ 95% raw text fidelity (TEST-003), ≥ 90% NLP field extraction (TEST-004)

---

## Bug History (extraction-related)

| Task | Bug | Fix |
|---|---|---|
| MV-145 | `provision_user` wasn't creating `is_self=True` FamilyMember → family tree broken | Added `is_self` creation in provisioning flow |
| MV-146 | No guard on deleting `is_self` member → tree left in broken state | Added 409 guard on delete |
| MV-142 | Notification dispatch embedded inviter email in title → PHI leak | Sanitize notification title/body — no PII allowed |

Add new entries here when extraction or provisioning bugs are found and fixed.
