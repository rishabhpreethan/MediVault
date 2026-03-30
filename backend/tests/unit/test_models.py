"""Unit tests for SQLAlchemy model definitions (no DB required)."""
import uuid

import pytest

from app.models import (
    Allergy,
    CorrectionAudit,
    Diagnosis,
    Doctor,
    Document,
    FamilyMember,
    LabResult,
    Medication,
    PassportAccessLog,
    Procedure,
    SharedPassport,
    User,
    Vital,
)


def _col_names(model) -> set:
    return {c.key for c in model.__table__.columns}


class TestUserModel:
    def test_tablename(self):
        assert User.__tablename__ == "users"

    def test_columns_present(self):
        cols = _col_names(User)
        assert {"user_id", "auth0_sub", "email", "phone_number",
                "email_verified", "is_active", "created_at", "last_login_at"} <= cols

    def test_auth0_sub_unique_constraint(self):
        # auth0_sub column has unique=True set directly
        col = User.__table__.c["auth0_sub"]
        assert col.unique is True

    def test_email_unique_constraint(self):
        col = User.__table__.c["email"]
        assert col.unique is True

    def test_instantiation_sets_provided_fields(self):
        uid = uuid.uuid4()
        user = User(user_id=uid, auth0_sub="auth0|abc", email="a@b.com")
        assert user.user_id == uid
        assert user.auth0_sub == "auth0|abc"
        assert user.email == "a@b.com"

    def test_optional_fields_default_to_none(self):
        user = User(user_id=uuid.uuid4(), auth0_sub="auth0|xyz")
        assert user.phone_number is None
        assert user.last_login_at is None


class TestFamilyMemberModel:
    def test_tablename(self):
        assert FamilyMember.__tablename__ == "family_members"

    def test_columns_present(self):
        cols = _col_names(FamilyMember)
        assert {"member_id", "user_id", "full_name", "relationship",
                "date_of_birth", "blood_group", "is_self"} <= cols

    def test_instantiation(self):
        uid = uuid.uuid4()
        member = FamilyMember(
            member_id=uuid.uuid4(),
            user_id=uid,
            full_name="Jane Doe",
            relationship="SELF",
        )
        assert member.full_name == "Jane Doe"
        assert member.date_of_birth is None
        assert member.blood_group is None


class TestDocumentModel:
    def test_tablename(self):
        assert Document.__tablename__ == "documents"

    def test_columns_present(self):
        cols = _col_names(Document)
        assert {"document_id", "member_id", "user_id", "document_type",
                "storage_path", "processing_status", "uploaded_at"} <= cols

    def test_instantiation_required_fields(self):
        doc = Document(
            document_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            document_type="LAB_REPORT",
            storage_path="user/abc/doc.pdf",
        )
        assert doc.document_type == "LAB_REPORT"
        assert doc.storage_path == "user/abc/doc.pdf"
        assert doc.facility_name is None
        assert doc.extracted_raw_text is None

    def test_processing_status_column_default(self):
        col = Document.__table__.c["processing_status"]
        assert col.default is not None


class TestMedicationModel:
    def test_tablename(self):
        assert Medication.__tablename__ == "medications"

    def test_columns_present(self):
        cols = _col_names(Medication)
        assert {"medication_id", "member_id", "drug_name", "dosage",
                "frequency", "is_active", "confidence_score"} <= cols

    def test_instantiation(self):
        med = Medication(
            medication_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            drug_name="Metformin",
            dosage="500mg",
        )
        assert med.drug_name == "Metformin"
        assert med.dosage == "500mg"
        assert med.drug_name_normalized is None


class TestLabResultModel:
    def test_tablename(self):
        assert LabResult.__tablename__ == "lab_results"

    def test_columns_present(self):
        cols = _col_names(LabResult)
        assert {"result_id", "member_id", "test_name", "value",
                "unit", "reference_low", "reference_high", "flag"} <= cols

    def test_instantiation(self):
        lr = LabResult(
            result_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            test_name="HbA1c",
        )
        assert lr.test_name == "HbA1c"
        assert lr.value is None
        assert lr.test_name_normalized is None


class TestDiagnosisModel:
    def test_tablename(self):
        assert Diagnosis.__tablename__ == "diagnoses"

    def test_columns_present(self):
        cols = _col_names(Diagnosis)
        assert {"diagnosis_id", "member_id", "condition_name",
                "icd10_code", "status", "confidence_score"} <= cols

    def test_instantiation(self):
        diag = Diagnosis(
            diagnosis_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            condition_name="Type 2 Diabetes",
        )
        assert diag.condition_name == "Type 2 Diabetes"
        assert diag.icd10_code is None
        assert diag.condition_normalized is None


class TestAllergyModel:
    def test_tablename(self):
        assert Allergy.__tablename__ == "allergies"

    def test_columns_present(self):
        cols = _col_names(Allergy)
        assert {"allergy_id", "member_id", "allergen_name",
                "reaction_type", "severity", "confidence_score"} <= cols

    def test_instantiation(self):
        allergy = Allergy(
            allergy_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            allergen_name="Penicillin",
        )
        assert allergy.allergen_name == "Penicillin"
        assert allergy.severity is None
        assert allergy.reaction_type is None


class TestVitalModel:
    def test_tablename(self):
        assert Vital.__tablename__ == "vitals"

    def test_columns_present(self):
        cols = _col_names(Vital)
        assert {"vital_id", "member_id", "vital_type", "value",
                "unit", "recorded_date"} <= cols

    def test_instantiation(self):
        vital = Vital(
            vital_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            vital_type="BP_SYSTOLIC",
            value=120,
            unit="mmHg",
        )
        assert vital.vital_type == "BP_SYSTOLIC"
        assert vital.value == 120
        assert vital.unit == "mmHg"


class TestDoctorModel:
    def test_tablename(self):
        assert Doctor.__tablename__ == "doctors"

    def test_instantiation(self):
        doctor = Doctor(
            doctor_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            doctor_name="Dr. Smith",
            specialization="Endocrinologist",
        )
        assert doctor.doctor_name == "Dr. Smith"
        assert doctor.facility_name is None


class TestProcedureModel:
    def test_tablename(self):
        assert Procedure.__tablename__ == "procedures"

    def test_instantiation(self):
        proc = Procedure(
            procedure_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            procedure_name="Appendectomy",
        )
        assert proc.procedure_name == "Appendectomy"
        assert proc.outcome is None
        assert proc.procedure_date is None


class TestPassportModels:
    def test_shared_passport_tablename(self):
        assert SharedPassport.__tablename__ == "shared_passports"

    def test_shared_passport_columns(self):
        cols = _col_names(SharedPassport)
        assert {"passport_id", "member_id", "user_id", "is_active",
                "expires_at", "visible_sections", "access_count"} <= cols

    def test_shared_passport_instantiation(self):
        passport = SharedPassport(
            passport_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
        )
        assert passport.expires_at is None
        assert passport.last_accessed_at is None

    def test_passport_access_log_tablename(self):
        assert PassportAccessLog.__tablename__ == "passport_access_log"

    def test_passport_access_log_instantiation(self):
        log = PassportAccessLog(
            log_id=uuid.uuid4(),
            passport_id=uuid.uuid4(),
            ip_hash="a" * 64,
        )
        assert log.ip_hash == "a" * 64

    def test_correction_audit_tablename(self):
        assert CorrectionAudit.__tablename__ == "correction_audit"

    def test_correction_audit_instantiation(self):
        audit = CorrectionAudit(
            audit_id=uuid.uuid4(),
            entity_type="medication",
            entity_id=uuid.uuid4(),
            field_name="dosage",
            old_value="500mg",
            new_value="1000mg",
        )
        assert audit.entity_type == "medication"
        assert audit.old_value == "500mg"
