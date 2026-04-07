from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.family import router as family_router
from app.api.profile import router as profile_router
from app.api.timeline import router as timeline_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(family_router, prefix="/family", tags=["family"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(timeline_router, prefix="/timeline", tags=["timeline"])

# Routers registered here as features are built out:
# from app.api import charts, passport
