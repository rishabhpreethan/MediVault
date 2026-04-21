from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.onboarding import router as onboarding_router
from app.api.provider import router as provider_router
from app.api.charts import router as charts_router
from app.api.corrections import router as corrections_router
from app.api.documents import router as documents_router
from app.api.entity_crud import router as entity_crud_router
from app.api.export import router as export_router
from app.api.family import router as family_router
from app.api.family_circle import router as family_circle_router
from app.api.notifications import router as notifications_router
from app.api.passport import router as passport_router
from app.api.profile import router as profile_router
from app.api.timeline import router as timeline_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(onboarding_router, prefix="/auth/onboarding", tags=["onboarding"])
api_router.include_router(charts_router, prefix="/charts", tags=["charts"])
api_router.include_router(corrections_router, prefix="/corrections", tags=["corrections"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(entity_crud_router, tags=["entity-crud"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(family_router, prefix="/family", tags=["family"])
api_router.include_router(family_circle_router, tags=["family-circle"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(passport_router, prefix="/passport", tags=["passport"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(provider_router, prefix="/provider", tags=["provider"])
api_router.include_router(timeline_router, prefix="/timeline", tags=["timeline"])
