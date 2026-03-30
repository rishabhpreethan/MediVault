from fastapi import APIRouter

from app.api.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])

# Routers registered here as features are built out:
# from app.api import auth, documents, profile, timeline, charts, passport, family
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
