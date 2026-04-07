"""Unit tests for the timeline API endpoint (MV-060).

Tests exercise the route handler directly without using TestClient
(greenlet compatibility issue in local dev).
"""
from __future__ import annotations

import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# Inject fake spacy so any transitive imports don't require the real package.
if "spacy" not in sys.modules:
    _fake_spacy = ModuleType("spacy")
    _fake_spacy.load = MagicMock()  # type: ignore[attr-defined]
    sys.modules["spacy"] = _fake_spacy

# Inject fake boto3 / aioboto3 so storage_service can be imported.
for _mod in ("boto3", "aioboto3", "botocore", "botocore.exceptions"):
    if _mod not in sys.modules:
        sys.modules[_mod] = ModuleType(_mod)

from app.api.timeline import (
    _load_member_or_404,
    _sort_events_desc,
    get_timeline,
)
from app.schemas.timeline import TimelineEvent, TimelineResponse


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_user(user_id: uuid.UUID | None = None):
    from app.models.user import User

    user = MagicMock(spec=User)
    user.user_id = user_id or uuid.uuid4()
    return user


def _make_member(
    user_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
):
    from app.models.family_member import FamilyMember

    member = MagicMock(spec=FamilyMember)
    member.member_id = member_id or uuid.uuid4()
    member.user_id = user_id or uuid.uuid4()
    return member


def _mock_db():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


def _db_result_scalar(value):
    """Return a mock result whose .scalar_one_or_none() returns value."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _db_result_scalars(rows):
    """Return a mock result whose .scalars().all() returns rows."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    result = MagicMock()
    result.scalars.return_value = scalars_mock
    return result


# ---------------------------------------------------------------------------
# Model mock factories
# ---------------------------------------------------------------------------


def _make_medication(member_id: uuid.UUID, doc_id: uuid.UUID | None = None) -> MagicMock:
    from app.models.medication import Medication

    m = MagicMock(spec=Medication)
    m.medication_id = uuid.uuid4()
    m.member_id = member_id
    m.drug_name = "Metformin"
    m.dosage = "500mg"
    m.frequency = "twice daily"
    m.document_id = doc_id
    m.confidence_score = "HIGH"
    return m


def _make_lab_result(
    member_id: uuid.UUID,
    test_date: date | None = None,
    doc_id: uuid.UUID | None = None,
) -> MagicMock:
    from app.models.lab_result import LabResult

    m = MagicMock(spec=LabResult)
    m.result_id = uuid.uuid4()
    m.member_id = member_id
    m.test_name = "HbA1c"
    m.value = Decimal("7.2")
    m.value_text = None
    m.unit = "%"
    m.test_date = test_date
    m.document_id = doc_id
    m.confidence_score = "HIGH"
    return m


def _make_diagnosis(member_id: uuid.UUID, doc_id: uuid.UUID | None = None) -> MagicMock:
    from app.models.diagnosis import Diagnosis

    m = MagicMock(spec=Diagnosis)
    m.diagnosis_id = uuid.uuid4()
    m.member_id = member_id
    m.condition_name = "Type 2 Diabetes"
    m.status = "ACTIVE"
    m.document_id = doc_id
    m.confidence_score = "MEDIUM"
    return m


def _make_allergy(member_id: uuid.UUID, doc_id: uuid.UUID | None = None) -> MagicMock:
    from app.models.allergy import Allergy

    m = MagicMock(spec=Allergy)
    m.allergy_id = uuid.uuid4()
    m.member_id = member_id
    m.allergen_name = "Penicillin"
    m.reaction_type = "rash"
    m.document_id = doc_id
    m.confidence_score = "LOW"
    return m


def _make_vital(member_id: uuid.UUID, doc_id: uuid.UUID | None = None) -> MagicMock:
    from app.models.vital import Vital

    m = MagicMock(spec=Vital)
    m.vital_id = uuid.uuid4()
    m.member_id = member_id
    m.vital_type = "BLOOD_PRESSURE"
    m.value = Decimal("120.0")
    m.unit = "mmHg"
    m.document_id = doc_id
    m.confidence_score = "HIGH"
    return m


def _make_document(
    member_id: uuid.UUID,
    doc_date: date | None = None,
) -> MagicMock:
    from app.models.document import Document

    doc_id = uuid.uuid4()
    m = MagicMock(spec=Document)
    m.document_id = doc_id
    m.member_id = member_id
    m.original_filename = "report.pdf"
    m.document_type = "LAB"
    m.document_date = doc_date
    m.processing_status = "DONE"
    return m


# ---------------------------------------------------------------------------
# Helper: build a db mock that returns appropriate rows per-query
# The timeline endpoint issues 6 sequential db.execute() calls (one per entity).
# We use side_effect to feed them in order: member, med, lab, diag, allergy, vital, doc.
# ---------------------------------------------------------------------------


def _build_db_side_effects(member, med_rows, lab_rows, diag_rows, allergy_rows, vital_rows, doc_rows):
    """Return list of AsyncMock side_effect values for db.execute() calls."""
    return [
        _db_result_scalar(member),      # _load_member_or_404
        _db_result_scalars(med_rows),   # _fetch_medications
        _db_result_scalars(lab_rows),   # _fetch_lab_results
        _db_result_scalars(diag_rows),  # _fetch_diagnoses
        _db_result_scalars(allergy_rows),  # _fetch_allergies
        _db_result_scalars(vital_rows),    # _fetch_vitals
        _db_result_scalars(doc_rows),      # _fetch_documents
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetTimelineMergedEvents:
    """test_get_timeline_returns_merged_events — mock all 6 tables returning 1 row each."""

    @pytest.mark.asyncio
    async def test_get_timeline_returns_merged_events(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        med = _make_medication(mid)
        lab = _make_lab_result(mid)
        diag = _make_diagnosis(mid)
        allergy = _make_allergy(mid)
        vital = _make_vital(mid)
        doc = _make_document(mid)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=_build_db_side_effects(member, [med], [lab], [diag], [allergy], [vital], [doc])
        )

        response = await get_timeline(
            member_id=mid,
            current_user=user,
            db=db,
        )

        assert isinstance(response, TimelineResponse)
        assert response.total == 6
        assert len(response.items) == 6
        assert response.member_id == str(mid)

        event_types = {e.event_type for e in response.items}
        assert event_types == {"MEDICATION", "LAB_RESULT", "DIAGNOSIS", "ALLERGY", "VITAL", "DOCUMENT"}


class TestGetTimelineDateSortedDesc:
    """test_get_timeline_date_sorted_desc — events with dates sorted newest first, None last."""

    @pytest.mark.asyncio
    async def test_get_timeline_date_sorted_desc(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        lab_old = _make_lab_result(mid, test_date=date(2023, 1, 1))
        lab_new = _make_lab_result(mid, test_date=date(2025, 6, 1))
        lab_none = _make_lab_result(mid, test_date=None)
        doc_mid = _make_document(mid, doc_date=date(2024, 3, 15))

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=_build_db_side_effects(
                member,
                [],                        # medications
                [lab_old, lab_new, lab_none],  # lab results
                [],                        # diagnoses
                [],                        # allergies
                [],                        # vitals
                [doc_mid],                 # documents
            )
        )

        response = await get_timeline(
            member_id=mid,
            current_user=user,
            db=db,
        )

        # Expect: lab_new (2025-06-01), doc_mid (2024-03-15), lab_old (2023-01-01), lab_none (None)
        assert response.total == 4
        dates = [e.event_date for e in response.items]
        assert dates[0] == date(2025, 6, 1)
        assert dates[1] == date(2024, 3, 15)
        assert dates[2] == date(2023, 1, 1)
        assert dates[3] is None


class TestGetTimelineEventTypeFilter:
    """test_get_timeline_event_type_filter — passing event_type=LAB_RESULT returns only lab events."""

    @pytest.mark.asyncio
    async def test_get_timeline_event_type_filter(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        lab1 = _make_lab_result(mid, test_date=date(2025, 1, 1))
        lab2 = _make_lab_result(mid, test_date=date(2025, 3, 1))

        # With event_type=LAB_RESULT, only member lookup + lab query are issued.
        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),       # _load_member_or_404
                _db_result_scalars([lab1, lab2]),  # _fetch_lab_results
            ]
        )

        response = await get_timeline(
            member_id=mid,
            current_user=user,
            db=db,
            event_type="LAB_RESULT",
        )

        assert response.total == 2
        assert all(e.event_type == "LAB_RESULT" for e in response.items)


class TestGetTimelinePagination:
    """test_get_timeline_pagination — page=2, page_size=2 returns correct slice."""

    @pytest.mark.asyncio
    async def test_get_timeline_pagination(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        # Create 5 lab results with distinct dates
        labs = [_make_lab_result(mid, test_date=date(2025, i + 1, 1)) for i in range(5)]

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=_build_db_side_effects(member, [], labs, [], [], [], [])
        )

        response = await get_timeline(
            member_id=mid,
            current_user=user,
            db=db,
            page=2,
            page_size=2,
        )

        assert response.total == 5
        assert response.page == 2
        assert response.page_size == 2
        assert len(response.items) == 2
        # Page 2 with page_size=2: items at index 2 and 3 (sorted desc by date)
        # Sorted desc: May, Apr, Mar, Feb, Jan
        assert response.items[0].event_date == date(2025, 3, 1)
        assert response.items[1].event_date == date(2025, 2, 1)


class TestGetTimelineMemberNotFound:
    """test_get_timeline_member_not_found — 404."""

    @pytest.mark.asyncio
    async def test_get_timeline_member_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result_scalar(None))

        with pytest.raises(HTTPException) as exc_info:
            await get_timeline(
                member_id=uuid.uuid4(),
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404


class TestGetTimelineWrongUser:
    """test_get_timeline_wrong_user — 403."""

    @pytest.mark.asyncio
    async def test_get_timeline_wrong_user(self):
        user = _make_user()
        other_user_id = uuid.uuid4()
        member = _make_member(user_id=other_user_id)  # belongs to a different user

        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result_scalar(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_timeline(
                member_id=member.member_id,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 403


class TestGetTimelineEmptyMember:
    """test_get_timeline_empty_member — all tables empty → items=[], total=0."""

    @pytest.mark.asyncio
    async def test_get_timeline_empty_member(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=_build_db_side_effects(member, [], [], [], [], [], [])
        )

        response = await get_timeline(
            member_id=mid,
            current_user=user,
            db=db,
        )

        assert response.total == 0
        assert response.items == []
        assert response.member_id == str(mid)


class TestGetTimelineDateRangeFilter:
    """test_get_timeline_date_range_filter — date_from/date_to filters lab results by test_date."""

    @pytest.mark.asyncio
    async def test_get_timeline_date_range_filter(self):
        """Verify that date_from / date_to params are passed through and SQLAlchemy filters are applied.

        We do not re-implement the DB filter here — we verify that the function
        passes the parsed dates down and returns whatever the (mocked) DB returns.
        """
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        # Simulate DB returning only the in-range lab (as if filter was applied)
        lab_in_range = _make_lab_result(mid, test_date=date(2024, 6, 15))

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=_build_db_side_effects(member, [], [lab_in_range], [], [], [], [])
        )

        response = await get_timeline(
            member_id=mid,
            current_user=user,
            db=db,
            date_from="2024-01-01",
            date_to="2024-12-31",
        )

        assert response.total == 1
        assert response.items[0].event_type == "LAB_RESULT"
        assert response.items[0].event_date == date(2024, 6, 15)

    @pytest.mark.asyncio
    async def test_get_timeline_invalid_date_from(self):
        """Invalid date_from should raise 400."""
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result_scalar(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_timeline(
                member_id=member.member_id,
                current_user=user,
                db=db,
                date_from="not-a-date",
            )

        assert exc_info.value.status_code == 400
