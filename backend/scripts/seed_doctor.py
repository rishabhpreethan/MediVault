"""Seed / promote a user to PROVIDER role for local testing.

Usage (from backend/ with .venv active):

    # Promote an existing user by email:
    python scripts/seed_doctor.py --email doctor@example.com

    # Create a brand-new dev provider (no Auth0 needed — uses a fake sub):
    python scripts/seed_doctor.py --create-dev

The --create-dev flag creates a user with sub "dev|doctor" that you can use
with the dev seed login (same pattern as seed_dev.py).

Run safely multiple times — idempotent.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401 — populate SQLAlchemy mapper registry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.family_member import FamilyMember
from app.models.provider_profile import ProviderProfile
from app.models.user import User

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

DEV_DOCTOR_SUB = "dev|doctor"
DEV_DOCTOR_EMAIL = "doctor@medivault.dev"


async def promote_by_email(email: str) -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            print(f"[ERROR] No user found with email: {email}")
            print("  Make sure the user has logged in at least once via Auth0 first.")
            sys.exit(1)

        user.role = "PROVIDER"
        user.onboarding_completed = True

        pp_result = await db.execute(
            select(ProviderProfile).where(ProviderProfile.user_id == user.user_id)
        )
        pp = pp_result.scalar_one_or_none()
        if pp is None:
            pp = ProviderProfile(
                user_id=user.user_id,
                licence_number="TEST-LIC-001",
                registration_council="Medical Council of India",
                licence_verified=True,
                verification_status="VERIFIED",
            )
            db.add(pp)
        else:
            pp.licence_verified = True
            pp.verification_status = "VERIFIED"

        await db.commit()
        print(f"[OK] user_id={user.user_id} ({email}) is now PROVIDER / onboarding complete.")


async def create_dev_doctor() -> None:
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.auth0_sub == DEV_DOCTOR_SUB))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                user_id=uuid.uuid4(),
                auth0_sub=DEV_DOCTOR_SUB,
                email=DEV_DOCTOR_EMAIL,
                email_verified=True,
                is_active=True,
                role="PROVIDER",
                onboarding_completed=True,
            )
            db.add(user)
            await db.flush()

            self_member = FamilyMember(
                member_id=uuid.uuid4(),
                user_id=user.user_id,
                full_name="Dr. Test Doctor",
                relationship="SELF",
                is_self=True,
            )
            db.add(self_member)
            await db.flush()

            pp = ProviderProfile(
                user_id=user.user_id,
                licence_number="TEST-LIC-001",
                registration_council="Medical Council of India",
                licence_verified=True,
                verification_status="VERIFIED",
            )
            db.add(pp)
            await db.commit()
            print(f"[CREATED] dev doctor user_id={user.user_id}")
        else:
            user.role = "PROVIDER"
            user.onboarding_completed = True
            pp_result = await db.execute(
                select(ProviderProfile).where(ProviderProfile.user_id == user.user_id)
            )
            pp = pp_result.scalar_one_or_none()
            if pp is None:
                pp = ProviderProfile(
                    user_id=user.user_id,
                    licence_number="TEST-LIC-001",
                    registration_council="Medical Council of India",
                    licence_verified=True,
                    verification_status="VERIFIED",
                )
                db.add(pp)
            else:
                pp.licence_verified = True
                pp.verification_status = "VERIFIED"
            await db.commit()
            print(f"[UPDATED] dev doctor user_id={user.user_id} — already existed, role refreshed.")

        print(f"  auth0_sub : {DEV_DOCTOR_SUB}")
        print(f"  email     : {DEV_DOCTOR_EMAIL}")
        print(f"  role      : PROVIDER")
        print(f"  onboarding: complete")
        print()
        print("To use in tests: log in with auth0_sub='dev|doctor' or hit the")
        print("  /auth/provision endpoint with a JWT that has sub='dev|doctor'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a doctor/provider user")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--email", help="Email of an existing Auth0 user to promote")
    group.add_argument(
        "--create-dev",
        action="store_true",
        help="Create a local dev doctor (no real Auth0 needed)",
    )
    args = parser.parse_args()

    if args.create_dev:
        asyncio.run(create_dev_doctor())
    else:
        asyncio.run(promote_by_email(args.email))


if __name__ == "__main__":
    main()
