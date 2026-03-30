# Import all models here so Alembic can detect them for migrations
from app.models.user import User
from app.models.family_member import FamilyMember
from app.models.document import Document
from app.models.medication import Medication
from app.models.lab_result import LabResult
from app.models.diagnosis import Diagnosis
from app.models.allergy import Allergy
from app.models.vital import Vital
from app.models.doctor import Doctor
from app.models.procedure import Procedure
from app.models.passport import SharedPassport, PassportAccessLog, CorrectionAudit

__all__ = [
    "User",
    "FamilyMember",
    "Document",
    "Medication",
    "LabResult",
    "Diagnosis",
    "Allergy",
    "Vital",
    "Doctor",
    "Procedure",
    "SharedPassport",
    "PassportAccessLog",
    "CorrectionAudit",
]
