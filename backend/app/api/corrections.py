"""Corrections API — PATCH and GET endpoints for manual field corrections with audit trail."""
from __future__ import annotations

import logging
import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models.allergy import Allergy
from app.models.correction_audit import CorrectionAudit
from app.models.diagnosis import Diagnosis
from app.models.family_member import FamilyMember
from app.models.lab_result import LabResult
from app.models.medication import Medication
from app.models.vital import Vital
from app.schemas.corrections import CorrectionAuditResponse, FieldCorrectionRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# Allowed fields per entity type — reject anything outside this list with 400
ALLOWED_FIELDS = {
    "medication": {"drug_name", "dosage", "frequency", "duration", "route"},
    "lab_result": {"test_name", "value", "unit", "reference_range"},
    "diagnosis": {"condition_name", "icd10_code", "status"},
    "allergy": {"allergen_name", "reaction_type", "severity"},
    "vital": {"value"},
}

# Map entity_type string → (ORM model class, primary key attribute name)
_ENTITY_MAP = {
    "medication": (Medication, "medication_id"),
    "lab_result": (LabResult, "result_id"),
    "diagnosis": (Diagnosis, "diagnosis_id"),
    "allergy": (Allergy, "allergy_id"),
    "vital": (Vital, "vital_id"),
}


async def _load_entity_or_404(db: DbSession, entity_type: str, entity_id: uuid.UUID):
    """Load an entity by type and ID, or raise 404."""
    if entity_type not in _ENTITY_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_ENTITY_TYPE",
                "message": f"entity_type must be one of: {', '.join(sorted(_ENTITY_MAP))}",
            },
        )

    model_class, pk_attr = _ENTITY_MAP[entity_type]
    result = await db.execute(
        select(model_class).where(getattr(model_class, pk_attr) == entity_id)
    )
    entity = result.scalar_one_or_none()
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "ENTITY_NOT_FOUND",
                "message": f"{entity_type} with id {entity_id} not found",
            },
        )
    return entity


async def _verify_ownership(db: DbSession, entity, current_user) -> None:
    """Verify the entity's family member belongs to the current user."""
    member_result = await db.execute(
        select(FamilyMember).where(FamilyMember.member_id == entity.member_id)
    )
    member = member_result.scalar_one_or_none()
    if member is None or member.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ACCESS_DENIED", "message": "Access denied"},
        )


@router.patch("/{entity_type}/{entity_id}", response_model=CorrectionAuditResponse)
async def patch_entity_field(
    entity_type: str,
    entity_id: uuid.UUID,
    body: FieldCorrectionRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> CorrectionAuditResponse:
    """Correct a single field on an extracted entity and write an audit record."""
    # 1. Validate entity_type
    if entity_type not in _ENTITY_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_ENTITY_TYPE",
                "message": f"entity_type must be one of: {', '.join(sorted(_ENTITY_MAP))}",
            },
        )

    # 2. Validate field_name
    allowed = ALLOWED_FIELDS[entity_type]
    if body.field_name not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_FIELD",
                "message": f"field_name '{body.field_name}' is not allowed for {entity_type}. "
                           f"Allowed: {', '.join(sorted(allowed))}",
            },
        )

    # 3. Load entity
    entity = await _load_entity_or_404(db, entity_type, entity_id)

    # 4. Verify ownership via member
    await _verify_ownership(db, entity, current_user)

    # 5. Read old value
    old_value = getattr(entity, body.field_name, None)
    if old_value is not None:
        old_value = str(old_value)

    # 6. Apply update
    setattr(entity, body.field_name, body.new_value)

    # 7. Write audit record
    audit = CorrectionAudit(
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=body.field_name,
        old_value=old_value,
        new_value=body.new_value,
        corrected_by=current_user.user_id,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)

    # PHI rule: log only IDs and field name — never values
    logger.info(
        "Field correction applied",
        extra={
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "field_name": body.field_name,
            "user_id": str(current_user.user_id),
        },
    )

    return CorrectionAuditResponse(
        audit_id=str(audit.audit_id),
        entity_type=audit.entity_type,
        entity_id=str(audit.entity_id),
        field_name=audit.field_name,
        old_value=audit.old_value,
        new_value=audit.new_value,
        corrected_at=audit.corrected_at,
    )


@router.get("/{entity_type}/{entity_id}", response_model=List[CorrectionAuditResponse])
async def get_correction_history(
    entity_type: str,
    entity_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> List[CorrectionAuditResponse]:
    """Return all correction audit records for a given entity."""
    # Validate entity_type
    if entity_type not in _ENTITY_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_ENTITY_TYPE",
                "message": f"entity_type must be one of: {', '.join(sorted(_ENTITY_MAP))}",
            },
        )

    # Load and verify ownership
    entity = await _load_entity_or_404(db, entity_type, entity_id)
    await _verify_ownership(db, entity, current_user)

    # Fetch audit records
    rows = (
        await db.execute(
            select(CorrectionAudit)
            .where(
                CorrectionAudit.entity_type == entity_type,
                CorrectionAudit.entity_id == entity_id,
            )
            .order_by(CorrectionAudit.corrected_at.desc())
        )
    ).scalars().all()

    logger.info(
        "Correction history retrieved",
        extra={
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "user_id": str(current_user.user_id),
        },
    )

    return [
        CorrectionAuditResponse(
            audit_id=str(r.audit_id),
            entity_type=r.entity_type,
            entity_id=str(r.entity_id),
            field_name=r.field_name,
            old_value=r.old_value,
            new_value=r.new_value,
            corrected_at=r.corrected_at,
        )
        for r in rows
    ]
