"""
Seed script for local development.

Creates a superuser + realistic medical data so the full UI can be explored
without real Auth0 credentials or uploaded PDFs.

Usage (from the backend/ directory with .venv active):
    python scripts/seed_dev.py

Run it again safely — it is idempotent (skips if data already exists).
"""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Make sure `app` is importable when running from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.allergy import Allergy
from app.models.diagnosis import Diagnosis
from app.models.doctor import Doctor
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medication import Medication
from app.models.user import User
from app.models.vital import Vital

# Import all models so SQLAlchemy's mapper registry is populated
import app.models  # noqa: F401

DEV_SUB = "dev|superuser"

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with SessionLocal() as db:
        # ── 1. User ────────────────────────────────────────────────────────
        result = await db.execute(select(User).where(User.auth0_sub == DEV_SUB))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                auth0_sub=DEV_SUB,
                email="dev@medivault.local",
                email_verified=True,
                is_active=True,
            )
            db.add(user)
            await db.flush()
            print(f"✓ Created user  {user.user_id}")
        else:
            print(f"· User already exists  {user.user_id}")

        # ── 2. Self family member ──────────────────────────────────────────
        result = await db.execute(
            select(FamilyMember).where(
                FamilyMember.user_id == user.user_id,
                FamilyMember.relationship == "SELF",
            )
        )
        self_member = result.scalar_one_or_none()

        if self_member is None:
            self_member = FamilyMember(
                user_id=user.user_id,
                full_name="Arjun Mehta",
                relationship="SELF",
                date_of_birth=date(1988, 5, 12),
                blood_group="B+",
                is_self=True,
            )
            db.add(self_member)
            await db.flush()
            print(f"✓ Created self member  {self_member.member_id}")
        else:
            print(f"· Self member already exists  {self_member.member_id}")

        # ── 3. Second family member ────────────────────────────────────────
        result = await db.execute(
            select(FamilyMember).where(
                FamilyMember.user_id == user.user_id,
                FamilyMember.relationship == "SPOUSE",
            )
        )
        spouse = result.scalar_one_or_none()

        if spouse is None:
            spouse = FamilyMember(
                user_id=user.user_id,
                full_name="Priya Mehta",
                relationship="SPOUSE",
                date_of_birth=date(1991, 9, 3),
                blood_group="O+",
                is_self=False,
            )
            db.add(spouse)
            await db.flush()
            print(f"✓ Created spouse member  {spouse.member_id}")
        else:
            print(f"· Spouse member already exists  {spouse.member_id}")

        # ── 4. Medications ─────────────────────────────────────────────────
        result = await db.execute(
            select(Medication).where(Medication.member_id == self_member.member_id)
        )
        if not result.scalars().all():
            medications = [
                Medication(
                    member_id=self_member.member_id,
                    drug_name="Metformin",
                    drug_name_normalized="metformin",
                    dosage="500 mg",
                    frequency="Twice daily",
                    route="Oral",
                    start_date=date(2023, 1, 15),
                    is_active=True,
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                Medication(
                    member_id=self_member.member_id,
                    drug_name="Atorvastatin",
                    drug_name_normalized="atorvastatin",
                    dosage="10 mg",
                    frequency="Once daily at bedtime",
                    route="Oral",
                    start_date=date(2022, 6, 1),
                    is_active=True,
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                Medication(
                    member_id=self_member.member_id,
                    drug_name="Amlodipine",
                    drug_name_normalized="amlodipine",
                    dosage="5 mg",
                    frequency="Once daily",
                    route="Oral",
                    start_date=date(2023, 3, 10),
                    is_active=True,
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                Medication(
                    member_id=self_member.member_id,
                    drug_name="Pantoprazole",
                    drug_name_normalized="pantoprazole",
                    dosage="40 mg",
                    frequency="Once daily before breakfast",
                    route="Oral",
                    start_date=date(2024, 2, 1),
                    end_date=date(2024, 3, 1),
                    is_active=False,
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
            ]
            db.add_all(medications)
            print(f"✓ Created {len(medications)} medications")
        else:
            print("· Medications already seeded")

        # ── 5. Lab results (multiple dates for trend charts) ───────────────
        result = await db.execute(
            select(LabResult).where(LabResult.member_id == self_member.member_id)
        )
        if not result.scalars().all():
            today = date.today()
            lab_results = [
                # HbA1c — 3 readings (trending down, good)
                LabResult(
                    member_id=self_member.member_id,
                    test_name="HbA1c",
                    test_name_normalized="hba1c",
                    value=8.2,
                    unit="%",
                    reference_low=4.0,
                    reference_high=6.5,
                    flag="HIGH",
                    test_date=today - timedelta(days=180),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                LabResult(
                    member_id=self_member.member_id,
                    test_name="HbA1c",
                    test_name_normalized="hba1c",
                    value=7.4,
                    unit="%",
                    reference_low=4.0,
                    reference_high=6.5,
                    flag="HIGH",
                    test_date=today - timedelta(days=90),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                LabResult(
                    member_id=self_member.member_id,
                    test_name="HbA1c",
                    test_name_normalized="hba1c",
                    value=6.8,
                    unit="%",
                    reference_low=4.0,
                    reference_high=6.5,
                    flag="HIGH",
                    test_date=today - timedelta(days=7),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                # Total Cholesterol — 2 readings
                LabResult(
                    member_id=self_member.member_id,
                    test_name="Total Cholesterol",
                    test_name_normalized="total_cholesterol",
                    value=218.0,
                    unit="mg/dL",
                    reference_low=0,
                    reference_high=200.0,
                    flag="HIGH",
                    test_date=today - timedelta(days=180),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                LabResult(
                    member_id=self_member.member_id,
                    test_name="Total Cholesterol",
                    test_name_normalized="total_cholesterol",
                    value=188.0,
                    unit="mg/dL",
                    reference_low=0,
                    reference_high=200.0,
                    flag="NORMAL",
                    test_date=today - timedelta(days=30),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                # Haemoglobin
                LabResult(
                    member_id=self_member.member_id,
                    test_name="Haemoglobin",
                    test_name_normalized="haemoglobin",
                    value=13.8,
                    unit="g/dL",
                    reference_low=13.5,
                    reference_high=17.5,
                    flag="NORMAL",
                    test_date=today - timedelta(days=30),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                # Serum Creatinine
                LabResult(
                    member_id=self_member.member_id,
                    test_name="Serum Creatinine",
                    test_name_normalized="serum_creatinine",
                    value=1.1,
                    unit="mg/dL",
                    reference_low=0.7,
                    reference_high=1.2,
                    flag="NORMAL",
                    test_date=today - timedelta(days=30),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                # Fasting Blood Sugar — 3 readings
                LabResult(
                    member_id=self_member.member_id,
                    test_name="Fasting Blood Sugar",
                    test_name_normalized="fasting_blood_sugar",
                    value=162.0,
                    unit="mg/dL",
                    reference_low=70.0,
                    reference_high=100.0,
                    flag="HIGH",
                    test_date=today - timedelta(days=180),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                LabResult(
                    member_id=self_member.member_id,
                    test_name="Fasting Blood Sugar",
                    test_name_normalized="fasting_blood_sugar",
                    value=138.0,
                    unit="mg/dL",
                    reference_low=70.0,
                    reference_high=100.0,
                    flag="HIGH",
                    test_date=today - timedelta(days=90),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                LabResult(
                    member_id=self_member.member_id,
                    test_name="Fasting Blood Sugar",
                    test_name_normalized="fasting_blood_sugar",
                    value=112.0,
                    unit="mg/dL",
                    reference_low=70.0,
                    reference_high=100.0,
                    flag="HIGH",
                    test_date=today - timedelta(days=14),
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
            ]
            db.add_all(lab_results)
            print(f"✓ Created {len(lab_results)} lab results")
        else:
            print("· Lab results already seeded")

        # ── 6. Diagnoses ───────────────────────────────────────────────────
        result = await db.execute(
            select(Diagnosis).where(Diagnosis.member_id == self_member.member_id)
        )
        if not result.scalars().all():
            diagnoses = [
                Diagnosis(
                    member_id=self_member.member_id,
                    condition_name="Type 2 Diabetes Mellitus",
                    condition_normalized="type_2_diabetes_mellitus",
                    icd10_code="E11",
                    diagnosed_date=date(2022, 11, 5),
                    status="ACTIVE",
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                Diagnosis(
                    member_id=self_member.member_id,
                    condition_name="Essential Hypertension",
                    condition_normalized="essential_hypertension",
                    icd10_code="I10",
                    diagnosed_date=date(2021, 4, 20),
                    status="ACTIVE",
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                Diagnosis(
                    member_id=self_member.member_id,
                    condition_name="Hyperlipidaemia",
                    condition_normalized="hyperlipidaemia",
                    icd10_code="E78.5",
                    diagnosed_date=date(2022, 6, 1),
                    status="ACTIVE",
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                Diagnosis(
                    member_id=self_member.member_id,
                    condition_name="Viral Fever",
                    condition_normalized="viral_fever",
                    icd10_code="A99",
                    diagnosed_date=date(2023, 8, 14),
                    status="RESOLVED",
                    confidence_score="MEDIUM",
                    is_manual_entry=True,
                ),
            ]
            db.add_all(diagnoses)
            print(f"✓ Created {len(diagnoses)} diagnoses")
        else:
            print("· Diagnoses already seeded")

        # ── 7. Allergies ───────────────────────────────────────────────────
        result = await db.execute(
            select(Allergy).where(Allergy.member_id == self_member.member_id)
        )
        if not result.scalars().all():
            allergies = [
                Allergy(
                    member_id=self_member.member_id,
                    allergen_name="Penicillin",
                    reaction_type="Anaphylaxis",
                    severity="SEVERE",
                    confidence_score="HIGH",
                    is_manual_entry=True,
                ),
                Allergy(
                    member_id=self_member.member_id,
                    allergen_name="Dust mites",
                    reaction_type="Allergic rhinitis",
                    severity="MILD",
                    confidence_score="MEDIUM",
                    is_manual_entry=True,
                ),
            ]
            db.add_all(allergies)
            print(f"✓ Created {len(allergies)} allergies")
        else:
            print("· Allergies already seeded")

        # ── 8. Vitals ──────────────────────────────────────────────────────
        result = await db.execute(
            select(Vital).where(Vital.member_id == self_member.member_id)
        )
        if not result.scalars().all():
            today = date.today()
            vitals = [
                # Blood pressure — systolic, 3 readings
                Vital(member_id=self_member.member_id, vital_type="BP_SYSTOLIC",  value=148, unit="mmHg", recorded_date=today - timedelta(days=180), confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="BP_DIASTOLIC", value=95,  unit="mmHg", recorded_date=today - timedelta(days=180), confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="BP_SYSTOLIC",  value=138, unit="mmHg", recorded_date=today - timedelta(days=90),  confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="BP_DIASTOLIC", value=88,  unit="mmHg", recorded_date=today - timedelta(days=90),  confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="BP_SYSTOLIC",  value=128, unit="mmHg", recorded_date=today - timedelta(days=7),   confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="BP_DIASTOLIC", value=82,  unit="mmHg", recorded_date=today - timedelta(days=7),   confidence_score="HIGH"),
                # Weight
                Vital(member_id=self_member.member_id, vital_type="WEIGHT", value=88.5, unit="kg",  recorded_date=today - timedelta(days=180), confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="WEIGHT", value=86.0, unit="kg",  recorded_date=today - timedelta(days=90),  confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="WEIGHT", value=84.2, unit="kg",  recorded_date=today - timedelta(days=7),   confidence_score="HIGH"),
                # Height & BMI (static)
                Vital(member_id=self_member.member_id, vital_type="HEIGHT", value=174,  unit="cm",       recorded_date=today - timedelta(days=180), confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="BMI",    value=29.2, unit="kg/m²",    recorded_date=today - timedelta(days=7),   confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="SPO2",   value=98,   unit="%",        recorded_date=today - timedelta(days=7),   confidence_score="HIGH"),
                Vital(member_id=self_member.member_id, vital_type="PULSE",  value=76,   unit="bpm",      recorded_date=today - timedelta(days=7),   confidence_score="HIGH"),
            ]
            db.add_all(vitals)
            print(f"✓ Created {len(vitals)} vitals")
        else:
            print("· Vitals already seeded")

        # ── 9. Doctors ─────────────────────────────────────────────────────
        result = await db.execute(
            select(Doctor).where(Doctor.member_id == self_member.member_id)
        )
        if not result.scalars().all():
            today = date.today()
            doctors = [
                Doctor(
                    member_id=self_member.member_id,
                    doctor_name="Dr. Suresh Nair",
                    specialization="Diabetology & Endocrinology",
                    facility_name="Apollo Hospitals, Chennai",
                    visit_date=today - timedelta(days=7),
                    confidence_score="HIGH",
                ),
                Doctor(
                    member_id=self_member.member_id,
                    doctor_name="Dr. Kavitha Rajan",
                    specialization="Cardiology",
                    facility_name="Fortis Malar Hospital, Chennai",
                    visit_date=today - timedelta(days=90),
                    confidence_score="HIGH",
                ),
                Doctor(
                    member_id=self_member.member_id,
                    doctor_name="Dr. Ramesh Iyer",
                    specialization="General Medicine",
                    facility_name="MIOT International, Chennai",
                    visit_date=today - timedelta(days=180),
                    confidence_score="HIGH",
                ),
            ]
            db.add_all(doctors)
            print(f"✓ Created {len(doctors)} doctors")
        else:
            print("· Doctors already seeded")

        await db.commit()
        print("\n✅ Seed complete. Log in with dev token: dev-superuser-token-medivault-2026")


if __name__ == "__main__":
    asyncio.run(seed())
