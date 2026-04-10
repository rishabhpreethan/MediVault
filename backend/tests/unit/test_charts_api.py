"""Unit tests for the charts API endpoints (MV-070).

Tests exercise the route handlers directly without using TestClient.
"""
from __future__ import annotations

import sys
import uuid
from datetime import date
from decimal import Decimal
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

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

from app.api.charts import get_available_tests, get_lab_trends, get_medication_timeline
from app.schemas.charts import AvailableTestsResponse, LabTrendResponse, MedicationTimelineResponse


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


def _make_lab_result(
    member_id: uuid.UUID,
    test_name: str = "HbA1c",
    test_date: date | None = date(2025, 1, 1),
    value: Decimal | None = Decimal("7.2"),
    unit: str | None = "%",
    flag: str = "NORMAL",
    reference_low: Decimal | None = None,
    reference_high: Decimal | None = None,
    document_id: uuid.UUID | None = None,
) -> MagicMock:
    from app.models.lab_result import LabResult

    m = MagicMock(spec=LabResult)
    m.result_id = uuid.uuid4()
    m.member_id = member_id
    m.test_name = test_name
    m.test_date = test_date
    m.value = value
    m.unit = unit
    m.flag = flag
    m.reference_low = reference_low
    m.reference_high = reference_high
    m.document_id = document_id
    return m


# ---------------------------------------------------------------------------
# Tests: get_lab_trends
# ---------------------------------------------------------------------------


class TestLabTrendsReturnsSeries:
    """test_lab_trends_returns_series_per_test — 2 rows with same test_name → 1 series, 2 points."""

    @pytest.mark.asyncio
    async def test_lab_trends_returns_series_per_test(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        lab1 = _make_lab_result(mid, test_name="HbA1c", test_date=date(2025, 1, 1), value=Decimal("7.2"))
        lab2 = _make_lab_result(mid, test_name="HbA1c", test_date=date(2025, 6, 1), value=Decimal("6.9"))

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),   # _load_member_or_404
                _db_result_scalars([lab1, lab2]),  # lab results query
            ]
        )

        response = await get_lab_trends(
            member_id=mid,
            current_user=user,
            db=db,
        )

        assert isinstance(response, LabTrendResponse)
        assert response.member_id == str(mid)
        assert len(response.series) == 1
        assert response.series[0].test_name == "HbA1c"
        assert len(response.series[0].data_points) == 2


class TestLabTrendsHasEnoughDataTrue:
    """test_lab_trends_has_enough_data_true_when_two_or_more."""

    @pytest.mark.asyncio
    async def test_lab_trends_has_enough_data_true_when_two_or_more(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        lab1 = _make_lab_result(mid, test_name="Glucose", test_date=date(2025, 1, 1), value=Decimal("95"))
        lab2 = _make_lab_result(mid, test_name="Glucose", test_date=date(2025, 4, 1), value=Decimal("102"))

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),
                _db_result_scalars([lab1, lab2]),
            ]
        )

        response = await get_lab_trends(member_id=mid, current_user=user, db=db)

        assert response.series[0].has_enough_data is True


class TestLabTrendsHasEnoughDataFalse:
    """test_lab_trends_has_enough_data_false_when_one."""

    @pytest.mark.asyncio
    async def test_lab_trends_has_enough_data_false_when_one(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        lab1 = _make_lab_result(mid, test_name="Cholesterol", test_date=date(2025, 3, 1), value=Decimal("190"))

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),
                _db_result_scalars([lab1]),
            ]
        )

        response = await get_lab_trends(member_id=mid, current_user=user, db=db)

        assert len(response.series) == 1
        assert response.series[0].has_enough_data is False


class TestLabTrendsTestNamesFilter:
    """test_lab_trends_test_names_filter — comma-separated filter returns only matching series."""

    @pytest.mark.asyncio
    async def test_lab_trends_test_names_filter(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        lab_hba1c_1 = _make_lab_result(mid, test_name="HbA1c", test_date=date(2025, 1, 1), value=Decimal("7.2"))
        lab_hba1c_2 = _make_lab_result(mid, test_name="HbA1c", test_date=date(2025, 6, 1), value=Decimal("6.8"))
        # Cholesterol row will be excluded by the filter
        lab_chol = _make_lab_result(mid, test_name="Cholesterol", test_date=date(2025, 2, 1), value=Decimal("195"))

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),
                _db_result_scalars([lab_hba1c_1, lab_hba1c_2, lab_chol]),
            ]
        )

        response = await get_lab_trends(
            member_id=mid,
            current_user=user,
            db=db,
            test_names="hba1c",
        )

        assert len(response.series) == 1
        assert response.series[0].test_name == "HbA1c"


class TestLabTrendsSkipsResultsWithoutDate:
    """test_lab_trends_skips_results_without_date — null test_date excluded at DB level."""

    @pytest.mark.asyncio
    async def test_lab_trends_skips_results_without_date(self):
        """Rows with null test_date are excluded by the WHERE clause in the query.

        We verify this by confirming only the in-date rows appear (simulating DB filtering).
        """
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        # Simulate DB having already excluded the null-date row (query filter)
        lab_with_date = _make_lab_result(mid, test_name="HbA1c", test_date=date(2025, 1, 1), value=Decimal("7.2"))
        # lab_no_date would not be returned by DB because of IS NOT NULL filter
        # We only return the one with a date from the mock.

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),
                _db_result_scalars([lab_with_date]),
            ]
        )

        response = await get_lab_trends(member_id=mid, current_user=user, db=db)

        assert len(response.series) == 1
        assert len(response.series[0].data_points) == 1
        assert response.series[0].data_points[0].date == date(2025, 1, 1)


class TestLabTrends404MemberNotFound:
    """test_lab_trends_404_member_not_found."""

    @pytest.mark.asyncio
    async def test_lab_trends_404_member_not_found(self):
        user = _make_user()
        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result_scalar(None))

        with pytest.raises(HTTPException) as exc_info:
            await get_lab_trends(
                member_id=uuid.uuid4(),
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 404


class TestLabTrends403WrongUser:
    """test_lab_trends_403_wrong_user."""

    @pytest.mark.asyncio
    async def test_lab_trends_403_wrong_user(self):
        user = _make_user()
        other_user_id = uuid.uuid4()
        member = _make_member(user_id=other_user_id)  # belongs to a different user

        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result_scalar(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_lab_trends(
                member_id=member.member_id,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: get_available_tests
# ---------------------------------------------------------------------------


class TestAvailableTestsReturnsDistinctNames:
    """test_available_tests_returns_distinct_names."""

    @pytest.mark.asyncio
    async def test_available_tests_returns_distinct_names(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        lab1 = _make_lab_result(mid, test_name="HbA1c", test_date=date(2025, 1, 1))
        lab2 = _make_lab_result(mid, test_name="HbA1c", test_date=date(2025, 6, 1))
        lab3 = _make_lab_result(mid, test_name="Cholesterol", test_date=date(2025, 2, 1))
        lab4 = _make_lab_result(mid, test_name="Glucose", test_date=date(2025, 3, 1))

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),
                _db_result_scalars([lab1, lab2, lab3, lab4]),
            ]
        )

        response = await get_available_tests(
            member_id=mid,
            current_user=user,
            db=db,
        )

        assert isinstance(response, AvailableTestsResponse)
        assert response.member_id == str(mid)
        # HbA1c appears twice in DB rows but should be de-duped to once
        assert len(response.test_names) == 3
        assert set(response.test_names) == {"HbA1c", "Cholesterol", "Glucose"}


# ---------------------------------------------------------------------------
# Tests: get_medication_timeline (MV-072)
# ---------------------------------------------------------------------------


def _make_medication(
    member_id: uuid.UUID,
    drug_name: str = "Metformin",
    dosage: Optional[str] = "500 mg",
    is_active: bool = True,
    start_date: date | None = date(2025, 1, 1),
    end_date: date | None = None,
) -> MagicMock:
    from app.models.medication import Medication

    m = MagicMock(spec=Medication)
    m.medication_id = uuid.uuid4()
    m.member_id = member_id
    m.drug_name = drug_name
    m.dosage = dosage
    m.is_active = is_active
    m.start_date = start_date
    m.end_date = end_date
    return m


class TestMedicationTimelineReturnsBars:
    """test_medication_timeline_returns_bars — two meds → two bars with correct offsets."""

    @pytest.mark.asyncio
    async def test_medication_timeline_returns_bars(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        med1 = _make_medication(mid, drug_name="Metformin", start_date=date(2025, 1, 1), end_date=date(2025, 6, 1))
        med2 = _make_medication(mid, drug_name="Atorvastatin", start_date=date(2025, 3, 1), end_date=None, is_active=True)

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),
                _db_result_scalars([med1, med2]),
            ]
        )

        response = await get_medication_timeline(
            member_id=mid,
            current_user=user,
            db=db,
        )

        assert isinstance(response, MedicationTimelineResponse)
        assert response.member_id == str(mid)
        assert len(response.bars) == 2

        # Bars are sorted by start_day asc then drug_name asc
        # Metformin starts on earliest date → start_day == 0
        metformin_bar = next(b for b in response.bars if b.drug_name == "Metformin")
        atorva_bar = next(b for b in response.bars if b.drug_name == "Atorvastatin")

        assert metformin_bar.start_day == 0
        assert metformin_bar.duration_days == (date(2025, 6, 1) - date(2025, 1, 1)).days
        assert metformin_bar.end_date == "2025-06-01"

        # Atorvastatin starts 59 days after Metformin (Jan 1 → Mar 1 = 59 days)
        assert atorva_bar.start_day == (date(2025, 3, 1) - date(2025, 1, 1)).days
        assert atorva_bar.duration_days is None  # ongoing

        assert response.earliest_date == "2025-01-01"


class TestMedicationTimelineEmptyReturnsEmptyBars:
    """test_medication_timeline_empty_returns_empty_bars — no medications → bars=[]."""

    @pytest.mark.asyncio
    async def test_medication_timeline_empty_returns_empty_bars(self):
        user = _make_user()
        member = _make_member(user_id=user.user_id)
        mid = member.member_id

        db = _mock_db()
        db.execute = AsyncMock(
            side_effect=[
                _db_result_scalar(member),
                _db_result_scalars([]),
            ]
        )

        response = await get_medication_timeline(
            member_id=mid,
            current_user=user,
            db=db,
        )

        assert isinstance(response, MedicationTimelineResponse)
        assert response.bars == []
        assert response.earliest_date is None
        assert response.member_id == str(mid)


class TestMedicationTimeline403WrongUser:
    """test_medication_timeline_403_wrong_user — member belongs to another user."""

    @pytest.mark.asyncio
    async def test_medication_timeline_403_wrong_user(self):
        user = _make_user()
        other_user_id = uuid.uuid4()
        member = _make_member(user_id=other_user_id)  # belongs to a different user

        db = _mock_db()
        db.execute = AsyncMock(return_value=_db_result_scalar(member))

        with pytest.raises(HTTPException) as exc_info:
            await get_medication_timeline(
                member_id=member.member_id,
                current_user=user,
                db=db,
            )

        assert exc_info.value.status_code == 403
