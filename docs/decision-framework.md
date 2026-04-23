# MediVault — Decision Framework

Every technical and product decision in MediVault is classified by how reversible it is. Before making a decision, identify its door type and apply the appropriate process.

---

## Door Types

### 1-Way Door — Change within a day
Low risk. Can be undone in a single sitting. No architectural impact. No migration required.

**Process:** Decide and do. No approval needed. Log in STATUS.md activity log.

**Examples:**
- Variable names, function names, file names within a module
- UI copy, labels, placeholder text, error messages
- Color palette tweaks within the design system
- Log levels or log message formatting
- Config values that have a safe default (e.g., timeout durations, page sizes)
- Removing a feature flag after full rollout
- Adding a new NLP entity extraction rule
- Adding a new drug synonym to the synonym dictionary
- README or documentation updates

---

### 1.5-Way Door — Change takes ~1 week
Moderate risk. Reversible but requires coordinated changes across multiple files or components. May require a migration script or API version bump.

**Process:** Leave a comment or note in the relevant PR description explaining the decision and its rationale. Flag in STATUS.md if it affects another active task. One team member reviews before merge.

**Examples:**
- API response shape changes (adding/removing fields)
- New DB column additions (non-breaking migration)
- Frontend component restructuring that affects multiple pages
- Switching a single NLP extraction strategy for one entity type
- Adding a new Celery task type
- Changing PDF processing pipeline step order
- Adding a new document type category (ENUM extension)
- Changing confidence scoring thresholds
- Modifying the shareable passport URL structure (requires notifying existing URLs)
- Updating Auth0 rules or hooks
- Adding a new user-facing feature behind a flag
- Splitting or merging two API endpoints

---

### 2-Way Door — Change takes 2–3 weeks
High risk. Requires coordinated effort, likely involves data migration, breaking API changes, or replacing a core dependency. Must be treated like a small project.

**Process:** Create a dedicated decision record in this file under **Recorded Decisions** below. Document: what is changing, why, alternatives considered, migration plan, and who approved it. Requires both collaborators to align before work begins.

**Examples:**
- Replacing pdfminer.six with a different extraction library (Tika, PDFBox)
- Replacing spaCy + Med7 with another NLP system
- Switching from Auth0 to a different auth provider
- Replacing MinIO with a different object storage solution
- Switching from PostgreSQL to a different database
- Replacing Celery + Redis with a different task queue
- Changing the primary key strategy (UUID → auto-increment or vice versa)
- Removing a DB column with existing data (destructive migration)
- Changing the data isolation model for family accounts
- Replacing the frontend framework (React)
- Changing the encryption scheme for stored PHI
- Moving from fully local hosting to cloud infrastructure
- Switching from REST to GraphQL

---

## Quick Reference

| Door | Reversibility | Process | Approval |
|---|---|---|---|
| 1-Way | Same day | Just do it | None |
| 1.5-Way | ~1 week | Note in PR + flag in STATUS | 1 team member |
| 2-Way | 2–3 weeks | Decision record below + alignment | Both collaborators |

---

## Recorded Decisions

> Each 2-Way Door decision made during development is logged here.

### Template

```
### [DECISION-XXX] — [Title]
- **Date:** YYYY-MM-DD
- **Decided by:** [name]
- **What changed:** ...
- **Why:** ...
- **Alternatives considered:** ...
- **Migration plan:** ...
- **Approved by:** [both names]
```

---

### [DECISION-001] — Python + FastAPI as backend framework
- **Date:** 2026-03-29
- **Decided by:** Rishabh
- **What changed:** Backend language/framework selected
- **Why:** spaCy and pdfminer.six are Python-native. FastAPI gives async support, automatic OpenAPI docs, and strong type hints via Pydantic. No Java sidecar needed.
- **Alternatives considered:** Node.js (Express/NestJS) — would require Tika REST server for PDF extraction and a separate Python service for NLP; Go — excellent performance but poor ML/NLP ecosystem
- **Migration plan:** N/A — greenfield decision
- **Approved by:** Rishabh

### [DECISION-002] — pdfminer.six as primary PDF extraction library
- **Date:** 2026-03-29
- **Decided by:** Rishabh
- **What changed:** PDF extraction library selected from the three candidates in SRS
- **Why:** Python-native (no sidecar), superior layout-aware and positional text extraction for tabular lab reports. Apache Tika and pypdf serve as fallback libraries.
- **Alternatives considered:** Apache Tika REST server (adds Java dependency); Apache PDFBox (Java, not Python-native); pypdf (lightweight but weaker on complex tabular layouts)
- **Migration plan:** N/A — greenfield decision
- **Approved by:** Rishabh

### [DECISION-003] — spaCy + Med7 for medical NLP
- **Date:** 2026-03-29
- **Decided by:** Rishabh
- **What changed:** NLP/NER engine selected
- **Why:** Self-hosted — PHI never leaves the infrastructure, satisfying CON-006. Rules can be added iteratively. Med7 is specifically trained on clinical text for 7 medication-related entity types.
- **Alternatives considered:** Amazon Comprehend Medical — transmits PHI to AWS, violates CON-006 without a DPA; building from scratch with spaCy only — Med7 gives a better clinical NER baseline
- **Migration plan:** N/A — greenfield decision
- **Approved by:** Rishabh

### [DECISION-004] — Auth0 as authentication provider
- **Date:** 2026-03-29
- **Decided by:** Rishabh
- **What changed:** Auth provider selected
- **Why:** Supports email/password, Google OAuth, and phone OTP out of the box. RS256 JWT validation is straightforward. Good free tier for early-stage projects.
- **Alternatives considered:** Firebase Auth — comparable features but less flexibility on custom rules; custom JWT — too much maintenance overhead
- **Migration plan:** N/A — greenfield decision
- **Approved by:** Rishabh

### [DECISION-005] — MinIO as local object storage
- **Date:** 2026-03-29
- **Decided by:** Rishabh
- **What changed:** Object storage selected
- **Why:** S3-compatible API — switching to AWS S3 later requires only a config change (endpoint URL + credentials). Runs locally in Docker for V1. Satisfies the "fully local" hosting requirement.
- **Alternatives considered:** Local filesystem — not S3-compatible, makes cloud migration harder; AWS S3 directly — cloud dependency, V1 is fully local
- **Migration plan:** N/A — greenfield decision
- **Approved by:** Rishabh

### [DECISION-006] — Family accounts included in V1
- **Date:** 2026-03-29
- **Decided by:** Rishabh
- **What changed:** Family accounts moved from V2 to V1 scope (SRS §11 Open Issue #7 resolved)
- **Why:** The data model supports it without significant added complexity. A parent managing elderly parents' or children's records is a primary use case for the Indian context.
- **Data model impact:** `family_members` table linked to `users`. All medical records (documents, medications, diagnoses, etc.) are scoped to `family_member_id`, not `user_id` directly. The account owner is also represented as a family member (self).
- **Approved by:** Rishabh

### [DECISION-007] — Family Circle: invitation-based model + explicit vault access grants
- **Date:** 2026-04-11
- **Decided by:** Rishabh
- **What changed:** The family model is redesigned from direct member creation (owner creates profiles for everyone) to a hybrid model:
  1. **Managed Profiles** (no account required) remain for true dependents — young children, elderly parents who will never use the app themselves.
  2. **Linked Accounts** — other MediVault users join via email invitation. Accepting the invitation does NOT automatically share vault data; vault access requires an explicit grant by the family admin.
  3. **Family Circle UI** becomes a dedicated 5th nav tab with a visual family tree (parents above, spouse same level, children below). Settings moves out of the bottom nav into the avatar/profile menu.
  4. **Notification system** added: in-app notification inbox (bell icon) + email, covering family invite events and processing events.
- **Why:** The original model let the owner unilaterally create accounts/profiles for adults (spouse, adult children) — a privacy violation. Adults must consent to being part of a family and must explicitly grant access to their own health records. The visual tree provides a much clearer mental model for multi-generational families.
- **Alternatives considered:**
  - Auto-share vault on invitation accept — rejected (privacy: accepting ≠ consenting to share records)
  - Single-admin-only model — accepted for V1; `can_invite` flag added to allow delegation without full admin rights
  - Bidirectional automatic vault link — rejected; read-only explicit grants in V1 is simpler and safer
- **Migration plan:**
  - New Alembic migration: `families`, `family_invitations`, `family_memberships`, `vault_access_grants`, `notifications` tables
  - Existing `family_members` rows with `is_self=FALSE` are Managed Profiles — no migration needed; they remain as-is
  - No existing linked-account data to migrate (feature is new)
  - Backend: new Family Circle API, Invite API, Access Grants API, Notifications API
  - Frontend: new Family tab + tree UI, notification bell + centre, updated nav (5 tabs, Settings removed from bottom nav)
  - Cross-vault access middleware: before serving any profile/document/chart data, check `vault_access_grants` if the requesting user is not the record owner
- **Approved by:** Rishabh

### [DECISION-008] — User Onboarding + Role System (Patient vs Provider)
- **Date:** 2026-04-20
- **Decided by:** neerajmenon4
- **What changed:** A mandatory post-login onboarding flow is introduced. The system gains a `role` field on users (PATIENT | PROVIDER). Providers must supply an Indian medical licence number which is verified against the NMC (National Medical Commission) public registry. New DB: `role` + `onboarding_completed` on `users`; `height_cm` + `weight_kg` on `family_members`; new `provider_profiles` table.
- **Why:** V1 has two meaningfully different user types with different data needs and different feature access. Collecting a health baseline at onboarding (DOB already captured, add height/weight/blood group/allergies) allows the Health Passport to show useful summary data immediately without requiring a document upload. Provider verification is required before giving a provider access to the patient-lookup flow — unverified accounts must not be able to look up patient data.
- **Alternatives considered:**
  - Defer provider role to V2 — rejected: the doctor-facing passport lookup (DECISION-009) is in-scope for this release; the role system is a prerequisite.
  - Store height/weight as vitals entities (existing table) — rejected for onboarding baseline: vitals table is extraction-sourced and NLP-gated; we need a lightweight user-provided baseline not tied to document uploads.
  - Skip licence verification and use self-declaration — rejected: unverified providers could abuse the patient-lookup API to access health data without consent.
- **Migration plan:**
  - Alembic migration 0007: add `role VARCHAR(20) DEFAULT 'PATIENT'`, `onboarding_completed BOOLEAN DEFAULT FALSE` to `users`; add `height_cm FLOAT`, `weight_kg FLOAT` to `family_members`; create `provider_profiles(profile_id UUID PK, user_id UUID FK, licence_number VARCHAR(50), registration_council VARCHAR(100), licence_verified BOOLEAN DEFAULT FALSE, verification_status VARCHAR(20) DEFAULT 'PENDING', verified_at TIMESTAMPTZ, created_at TIMESTAMPTZ)`.
  - Backfill: existing users set `role='PATIENT'`, `onboarding_completed=FALSE` (prompted on next login).
  - NMC verification: best-effort async; providers can use the app with `PENDING` status but cannot access patient-lookup until `VERIFIED`.
- **Approved by:** neerajmenon4

### [DECISION-009] — Provider / Doctor Workflow with Passport-Based Patient Lookup
- **Date:** 2026-04-20
- **Decided by:** neerajmenon4
- **What changed:** Authenticated PROVIDER-role users can enter a patient's Health Passport UUID on their MediVault instance to look up that patient's data (gated by a valid, non-expired, non-revoked passport). The provider gets a read-only clinical view (health profile, timeline, lab trend chart, treatment pathway graph) plus a medical encounter logging form. Encounters are persisted to a new `medical_encounters` table and are visible to both the provider (their own encounters) and to the patient on their own profile. This decision moves "doctor-facing workflows" (previously out-of-scope in SRS v1.2 §1.2) into scope for this release.
- **Why:** The core value proposition of the Health Passport is enabling the patient to share their history at a doctor's visit without carrying paper. The current public passport view (no auth required) is too lightweight for clinical use. A structured encounter log closes the loop: the patient gets a record of what the doctor noted. Requiring an active passport (patient-controlled) preserves patient consent.
- **Alternatives considered:**
  - Public (unauthenticated) doctor view — rejected: no audit trail, no encounter logging, no provider verification.
  - QR-code scan flow only — retained as secondary path; provider can scan QR or type the UUID manually.
  - Provider writes directly to patient's medications/diagnoses tables — rejected for V1: encounters stored in a separate `medical_encounters` table and surfaced to the patient as read-only encounter feed.
  - Immediate access on valid passport + provider auth — rejected: patient must explicitly consent to each provider access session; the passport UUID alone is not sufficient consent (it could be leaked or guessed).
- **Access consent model:** Passport lookup is a **two-step consent flow**:
  1. Provider enters passport UUID → system validates passport is active/non-expired → creates a `provider_access_requests` record with status `PENDING` and TTL of 15 minutes.
  2. Patient receives an in-app notification: *"Dr. [provider display name] is requesting to view your health profile. Accept or Decline?"* The notification contains deep-link action buttons.
  3. Patient accepts → request status → `ACCEPTED`; provider's polling/waiting screen transitions to the clinical view; access session is valid for the duration of the encounter (same day, or until provider logs out of the lookup).
  4. Patient declines → request status → `DECLINED`; provider sees "Patient declined the request" screen.
  5. If the patient does not respond within 15 minutes → request expires (`EXPIRED`); provider must re-initiate.
  6. The patient can see all past provider access requests (accepted/declined/expired) in their notification history, giving full auditability.
- **Migration plan:**
  - Alembic migration 0008: create `provider_access_requests(request_id UUID PK, provider_user_id UUID FK users, patient_member_id UUID FK family_members, passport_id_used UUID FK health_passports, status VARCHAR(20) DEFAULT 'PENDING', requested_at TIMESTAMPTZ, responded_at TIMESTAMPTZ, expires_at TIMESTAMPTZ, notification_id UUID FK notifications)`.
  - Alembic migration 0009: create `medical_encounters(encounter_id UUID PK, provider_user_id UUID FK users, patient_member_id UUID FK family_members, access_request_id UUID FK provider_access_requests, encounter_date DATE NOT NULL, chief_complaint TEXT, diagnosis_notes TEXT, prescriptions_note TEXT, follow_up_date DATE, created_at TIMESTAMPTZ)`.
  - New API prefix `/provider/` — all routes gated by `require_provider_role` dependency (checks `users.role = 'PROVIDER'` AND `provider_profiles.licence_verified = TRUE`).
  - Notification dispatch: reuse existing `NotificationDispatchService`; add `PROVIDER_ACCESS_REQUEST` and `PROVIDER_ACCESS_ACCEPTED/DECLINED` notification types.
  - Treatment pathway graph component: based on stitch design at `stitch_health_passport/treatment_pathway/DESIGN.md`. Renders a chronological narrative of diagnoses + encounters + medications with the "Clinical Curator" aesthetic.
- **Approved by:** neerajmenon4

### [DECISION-011] — Insights page → Health Summary
- **Date:** 2026-04-23
- **Decided by:** neerajmenon4
- **Door type:** 1.5-Way Door (full page component replacement; frontend-only; no DB or API changes needed)
- **What changed:** InsightsPage (`/insights`) replaces trend charts (lab trend, medication Gantt, vitals) with a Health Summary view: active medications list, recent diagnoses list, latest lab result per test with H/L flag. Nav label "Insights" renamed to "Summary".
- **Why:** Trend charts require months of data across multiple documents to be useful. Most users — especially early on — have 1–2 documents at most. Showing empty charts is a dead end. The profile API already powers a useful, data-rich summary the moment a single document is processed.
- **Alternatives considered:** Keep charts alongside a summary — rejected (adds clutter; users who lack data still land on empty chart UI). Add data-sufficiency check to show charts when enough data exists — rejected for now (premature; redesign this once >50% of users have sufficient data).
- **Migration plan:** InsightsPage.tsx rewritten in-place. No backend changes. Chart components (InsightsPage was self-contained) can be re-added to a `/insights/trends` route later if needed.
- **Approved by:** neerajmenon4

### [DECISION-012] — Page clarity restructuring: Records → timeline-only; Passport → health snapshot; Health → read-only
- **Date:** 2026-04-23
- **Decided by:** neerajmenon4
- **Door type:** 1.5-Way Door (multi-file frontend changes; reversible in ~1 week; no backend or DB changes)
- **What changed:**
  1. **Records** (`/records`): Remove archive tab and Import Record button. Page becomes timeline-only. Title changes to "Health Timeline". Document detail pages remain reachable via direct URL `/records/:documentId`.
  2. **Health Profile** (`/health`, DashboardPage): Remove non-functional "Share Vault" and "New Entry" header buttons. Page becomes a read-only health data view; entries come from document uploads (upload pipeline) and provider encounters (provider workflow).
  3. **Passport** (`/`): Add "Health Snapshot" section below the QR/passport-ID card. Shows blood group, active allergies, active medications — pulled from the existing profile API. Titled "Health Snapshot — What a Doctor Sees".
- **Why:** The previous layout had overlapping purposes: Records mixed a document archive with a timeline; the Health page had action buttons for features not yet wired up (New Entry) and a share shortcut that duplicates the Passport page. The Passport page is the primary identity surface and benefits from showing the health summary that providers will see when granted access.
- **Alternatives considered:** Keep archive tab behind a toggle — rejected (adds decision burden; document detail is still reachable via deep link); wire up New Entry to entity-crud API — deferred to a future sprint (manual entry UX needs its own flow design).
- **Migration plan:** Three frontend files edited (RecordsPage.tsx, DashboardPage.tsx, PassportManagePage.tsx). No backend changes.
- **Approved by:** neerajmenon4
