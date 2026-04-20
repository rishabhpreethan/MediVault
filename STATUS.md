# MediVault — Project Status

**Last Updated:** 2026-04-14
**SRS Version:** 1.2
**Active Phase:** V1 MVP

> **Design Source:** Google Stitch export at `/Users/rishabh/Downloads/stitch_health_passport/`
> Design system: Manrope font, teal primary `#006b5f`, no-border separation, glass nav, 4-tab nav (Dashboard/Records/Insights/Passport).
> See `.claude/commands/frontend-design.md` for the full design system and Stitch→task mapping.

---

## Active Workers

> Claim a task here before starting. This prevents two people from picking the same task.
> Clear your entry once your PR is merged.

| Person | Agent Role | Currently Working On | Task ID | Branch | Last Updated |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

## Legend

| Status | Meaning |
|---|---|
| `Not Started` | Available to pick up |
| `In Progress` | Being built by Developer Agent |
| `In Review` | With Reviewer Agent |
| `In QA` | With QA Agent |
| `Done (Pending Merge)` | PR open, waiting for human to merge |
| `Done` | Merged to main |
| `Blocked` | Cannot start — depends on another task |

| Priority | Meaning |
|---|---|
| P0 | Critical blocker — nothing else can proceed without this |
| P1 | High — needed for core V1 MVP value loop |
| P2 | Medium — important but not blocking the critical path |
| P3 | Low — nice to have for V1 |

---

## Task Board

### EPIC: Infrastructure Setup

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-001 | Repo structure, Docker Compose scaffold, .env.example | P0 | Done | Rishabh / Developer Agent | — | feature/MV-001-repo-init |
| MV-002 | PostgreSQL + Redis + MinIO Docker Compose services | P0 | Done | Rishabh / Developer Agent | MV-001 | feature/MV-001-repo-init |
| MV-003 | FastAPI project scaffolding (app factory, config, router) | P0 | Done | Rishabh / Developer Agent | MV-001 | feature/MV-003-fastapi-scaffold |
| MV-004 | React PWA scaffolding (Vite, TypeScript, Tailwind, Auth0 SDK) | P0 | Done | Rishabh / Developer Agent | MV-001 | feature/MV-004-react-scaffold |
| MV-005 | Alembic setup + initial DB migration (all core tables) | P0 | Done | Rishabh / Developer Agent | MV-002, MV-003 | feature/MV-005-db-migrations |
| MV-006 | GitHub Actions CI pipeline (lint, typecheck, unit tests) | P1 | Done | Rishabh / Developer Agent | MV-003, MV-004 | feature/MV-001-repo-init |

### EPIC: Authentication

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-010 | Auth0 tenant + application configuration, JWKS setup | P0 | Done | Rishabh | — | — |
| MV-011 | Backend JWT middleware | P0 | Done | Developer Agent | MV-010 | feature/MV-011-jwt-middleware |
| MV-012 | User model, family_members model, DB migration (covered by MV-005) | P0 | Done | Rishabh / Developer Agent | MV-005 | feature/MV-005-db-migrations |
| MV-013 | /auth/provision endpoint — user provisioning on first login | P0 | Done | Developer Agent | MV-011, MV-012 | feature/MV-013-auth-provision |
| MV-014 | Frontend Auth0 SDK integration, protected route wrapper | P0 | Done | Developer Agent | MV-004, MV-010 | feature/MV-014-auth0-frontend |
| MV-015 | Login / Signup UI screens — ref: `stitch_health_passport/user_login/` | P0 | Done | Developer Agent | MV-014 | feature/MV-015-login-signup-ui |
| MV-016 | Frontend app shell, bottom nav, member selector | P0 | Done | Developer Agent | MV-014 | feature/MV-016-app-shell |
| MV-016b | Redesign app shell to Stitch layout (responsive top nav + left sidebar desktop; 4-tab bottom nav mobile; Manrope + teal design system) | P0 | Done | Developer Agent | MV-016 | feature/MV-016b-app-shell-redesign |
| MV-017 | Session inactivity (30-day), token refresh, logout | P1 | Done | Developer Agent | MV-013 | feature/MV-017-session-inactivity |

### EPIC: Document Management

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-020 | Document DB model + Alembic migration | P0 | Done | Developer Agent | MV-005 | feature/MV-005-db-migrations |
| MV-021 | File upload API (validation, MinIO storage, queue job) | P0 | Done | Developer Agent | MV-011, MV-020 | feature/MV-021-file-upload-api |
| MV-022 | Scanned PDF detection (embedded text layer check) | P0 | Done | Developer Agent | MV-021 | feature/MV-022-scanned-pdf-detection |
| MV-023 | Document library API (list, get, delete, retry) | P0 | Done | Developer Agent | MV-021 | feature/MV-023-document-retry-status |
| MV-024 | Document library UI ("Clinical Archive") — ref: `stitch_health_passport/document_vault/` | P0 | Done | Developer Agent | MV-016b, MV-023 | feature/MV-024-document-library-ui |
| MV-025 | Upload flow UI (file picker, type selection, date, progress, rejection) | P0 | Done | Developer Agent | MV-021, MV-024 | feature/MV-025-upload-flow-ui |
| MV-026 | Document detail page (PDF viewer + extracted data panel, inline edit) | P1 | Done | Developer Agent | MV-024 | feature/MV-026-document-detail |
| MV-027 | Manual field correction API + audit trail | P1 | Done | Developer Agent | MV-023 | feature/MV-027-manual-correction-api |

### EPIC: PDF Extraction Pipeline

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-030 | Celery app setup + Redis broker + worker Dockerfile | P0 | Done | Rishabh / Developer Agent | MV-002, MV-003 | feature/MV-030-celery-worker |
| MV-031 | pdfminer.six extraction worker (primary extractor) | P0 | Done | Developer Agent | MV-030 | feature/MV-031-pdfminer-worker |
| MV-032 | pypdf fallback extractor + extraction orchestration logic | P0 | Done | Developer Agent | MV-031 | feature/MV-032-pypdf-fallback |
| MV-033 | Extraction job retry logic (3 attempts, exponential backoff) | P0 | Done | Developer Agent | MV-032 | feature/MV-031-pdfminer-worker |
| MV-034 | Raw text storage to Document record + status state machine | P0 | Done | Developer Agent | MV-031, MV-020 | feature/MV-032-pypdf-fallback |

### EPIC: NLP Medical Data Extraction

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-040 | spaCy + Med7 pipeline setup, model loading, base extractor | P0 | Done | Developer Agent | MV-034 | feature/MV-040-nlp-pipeline |
| MV-041 | Medication extraction (drug name, dosage, frequency, duration, route) | P0 | Done | Developer Agent | MV-040 | feature/MV-041-042-043-nlp-extractors |
| MV-042 | Lab result extraction (test name, value, unit, reference range, H/L flag) | P0 | Done | Developer Agent | MV-040 | feature/MV-041-042-043-nlp-extractors |
| MV-043 | Diagnosis extraction (condition name, date, status) | P0 | Done | Developer Agent | MV-040 | feature/MV-041-042-043-nlp-extractors |
| MV-044 | Allergy extraction | P1 | Done | Developer Agent | MV-040 | feature/MV-044-045-046-extractors |
| MV-045 | Vitals extraction (BP, weight, height, BMI, SpO2) | P1 | Done | Developer Agent | MV-040 | feature/MV-044-045-046-extractors |
| MV-046 | Doctor/facility/visit date extraction | P1 | Done | Developer Agent | MV-040 | feature/MV-044-045-046-extractors |
| MV-047 | Confidence scoring system (HIGH/MEDIUM/LOW) + low-confidence flagging | P0 | Done | Developer Agent | MV-041, MV-042, MV-043 | feature/MV-047-050-confidence-profile |
| MV-048 | Entity deduplication across documents (chronic conditions, medications) | P1 | Done | Developer Agent | MV-043 | feature/MV-048-entity-deduplication |
| MV-049 | Drug synonym normalization dictionary | P2 | Done | Developer Agent | MV-041 | feature/MV-049-drug-synonym-normalization |

### EPIC: Health Profile

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-050 | Profile aggregation service (builds HealthProfileRM from all entities) | P0 | Done | Developer Agent | MV-041, MV-042, MV-043 | feature/MV-047-050-confidence-profile |
| MV-051 | Profile API endpoints (GET full profile, GET summary) | P0 | Done | Developer Agent | MV-050 | feature/MV-051-profile-api |
| MV-052 | Health profile dashboard UI — ref: `stitch_health_passport/health_profile_dashboard/` | P0 | Done | Developer Agent | MV-051, MV-016b | feature/MV-052-health-profile-ui |
| MV-053 | Manual add/edit/delete API for all entity types | P1 | Done | Developer Agent | MV-051 | feature/MV-053-entity-crud-api |
| MV-054 | Discontinue medication toggle (API + UI) | P2 | Done | Developer Agent | MV-052 | feature/MV-054-discontinue-medication-ui |
| MV-055 | Production bugfixes — Auth0 redirect flow, Celery event loop isolation, scispaCy NLP pipeline (replaces Med7), entity UUID serialization, document entity joins | P0 | Done | Developer Agent | — | feature/MV-055-056-057-fixes-and-polish |
| MV-056 | Dashboard UI polish — remove Pulse Rate card + Sparkline, fix BP empty state, fix Blood Type badges, replace Upcoming Consult with Known Conditions (live diagnoses) | P1 | Done | Developer Agent | MV-052 | feature/MV-055-056-057-fixes-and-polish |
| MV-057 | Records UI corrections — DISCHARGE→DISCHARGE_SUMMARY enum fix, add doctor_name to document cards | P1 | Done | Developer Agent | MV-024 | feature/MV-055-056-057-fixes-and-polish |
| MV-058 | Make Health Passport the default landing page — route `/` → PassportPage, move Health Profile to `/health`, update nav order and labels | P1 | In Progress | Developer Agent | MV-084 | feature/MV-058-passport-as-home |

### EPIC: Health Timeline

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-060 | Timeline data API (paginated, filterable by type/date) | P0 | Done | Developer Agent | MV-050 | feature/MV-060-timeline-api |
| MV-061 | Timeline UI (under Records tab) — ref: `stitch_health_passport/health_timeline/` | P0 | Done | Developer Agent | MV-060, MV-016b | feature/MV-061-timeline-ui |

### EPIC: Trend Visualizations

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-070 | Lab trend chart data API (time-series per parameter, ≥2 data points check) | P0 | Done | Developer Agent | MV-050 | feature/MV-070-lab-trend-api |
| MV-071 | Lab trend chart UI (Recharts, reference range band, out-of-range markers) | P0 | Done | Developer Agent | MV-070, MV-016 | feature/MV-071-lab-trend-chart-ui |
| MV-072 | Medication Gantt chart (API + UI) | P1 | Done | Developer Agent | MV-050 | feature/MV-072-medication-gantt |
| MV-073 | Vitals trend chart (BP, weight over time) | P1 | Done | Developer Agent | MV-050 | feature/MV-073-vitals-trend-chart |

### EPIC: Health Passport

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-080 | Passport generation API (UUID, expiry, section visibility settings) | P0 | Done | Developer Agent | MV-050 | feature/MV-080-passport-api |
| MV-081 | Passport revoke/expiry API + access log | P0 | Done | Developer Agent (covered by MV-080) | MV-080 | feature/MV-080-passport-api |
| MV-082 | Public passport view endpoint (no auth, rate limited) | P0 | Done | Developer Agent (covered by MV-080) | MV-080 | feature/MV-080-passport-api |
| MV-083 | QR code generation (frontend, links to passport URL) | P0 | Done | Developer Agent | MV-080 | feature/MV-083-084-passport-ui |
| MV-084 | Passport management UI — ref: `stitch_health_passport/health_passport/` | P0 | Done | Developer Agent | MV-080, MV-016b | feature/MV-083-084-passport-ui |
| MV-085 | Public passport page UI (read-only) — ref: `stitch_health_passport/health_passport/` | P0 | Done | Developer Agent | MV-082 | feature/MV-085-public-passport-ui |

### EPIC: Family Accounts

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-090 | Family member DB model + migration (included in MV-012 if done together) | P1 | Done | Developer Agent | MV-005 | feature/MV-005-db-migrations |
| MV-091 | Family member CRUD API (add, list, update, delete with data purge) | P1 | Done | Developer Agent | MV-090, MV-011 | feature/MV-091-family-crud |
| MV-092 | Family management UI ("Family Circle") — ref: `stitch_health_passport/family_health_ecosystem/` + `add_family_member/` | P1 | Done | Developer Agent | MV-091, MV-016b | feature/MV-092-family-ui |
| MV-093 | Per-member data isolation verification (all queries scoped to member_id) | P0 | Done | Developer Agent | MV-091 | feature/MV-093-data-isolation-tests |

### EPIC: Notifications

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-100 | Email notification service (SendGrid integration) | P2 | Done | Developer Agent | MV-034 | feature/MV-100-sendgrid-email-service |
| MV-101 | Processing complete + extraction failed notifications | P2 | Done | Developer Agent | MV-100, MV-034 | feature/MV-100-sendgrid-email-service |

### EPIC: Account Management

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-110 | Account deletion API (initiates data purge, revokes all passports) | P1 | Done | Developer Agent | MV-011 | feature/MV-110-account-deletion-api |
| MV-111 | Data export API (JSON + zip of PDFs, async, email link) | P1 | Done | Developer Agent | MV-050 | feature/MV-111-data-export-api |
| MV-112 | Account settings UI (delete account, export data) | P1 | Done | Developer Agent | MV-016 | feature/MV-112-account-settings-ui |

### EPIC: Test Suite

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-120 | pytest setup + Vitest setup + test fixtures (sample PDFs) | P1 | Done | Developer Agent | MV-003, MV-004 | feature/MV-120-test-setup |
| MV-121 | Backend unit tests (NLP extractors, confidence scorer, deduplication) | P1 | Done | Developer Agent | MV-047 | feature/MV-121-nlp-unit-tests |
| MV-122 | Backend integration tests (upload → extract → NLP → profile pipeline) | P1 | Done | Developer Agent | MV-050 | feature/MV-122-pipeline-integration-tests |
| MV-123 | Playwright E2E tests (critical user journeys UF-001 through UF-009) | P1 | Done | Developer Agent | MV-052, MV-061, MV-084 | feature/MV-123-playwright-e2e-tests |
| MV-124 | PDF extraction accuracy benchmarking (≥95% text fidelity target) | P2 | Done | Developer Agent | MV-032 | feature/MV-124-pdf-benchmarking |

### EPIC: Family Circle Redesign (DECISION-007)

> **2-Way Door decision** made 2026-04-11. Full spec in srs.md §3.9–§3.10, architecture.md, user-flows.md UF-009 + UF-014–UF-019, decision-framework.md DECISION-007.

#### Sub-Epic: Backend — DB + Core APIs

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-125 | Alembic migration: families, family_invitations, family_memberships, vault_access_grants, notifications tables | P0 | Done (Pending Merge) | Developer Agent | — | feature/MV-125-140-family-circle-redesign |
| MV-126 | Family Circle API — GET /family/circle (returns memberships + managed profiles + pending invites) | P1 | Done (Pending Merge) | Developer Agent | MV-125 | feature/MV-125-140-family-circle-redesign |
| MV-127 | Family Invitations API — POST /family/invitations, GET /family/invitations, DELETE invitation, POST resend | P1 | Done (Pending Merge) | Developer Agent | MV-125 | feature/MV-125-140-family-circle-redesign |
| MV-128 | Invite acceptance flow — GET /invite/:token, POST accept, POST decline (handles new + existing users) | P1 | Done (Pending Merge) | Developer Agent | MV-127 | feature/MV-125-140-family-circle-redesign |
| MV-129 | Vault Access Grants API — GET /family/access, POST grant, DELETE revoke, PATCH can-invite | P1 | Done (Pending Merge) | Developer Agent | MV-125 | feature/MV-125-140-family-circle-redesign |
| MV-130 | Cross-vault access middleware — check vault_access_grants before serving profile/documents/charts for non-owner | P0 | Done (Pending Merge) | Developer Agent | MV-129 | feature/MV-125-140-family-circle-redesign |
| MV-131 | Notifications API — GET /notifications, GET unread-count, PATCH read, POST read-all, DELETE | P2 | Done (Pending Merge) | Developer Agent | MV-125 | feature/MV-125-140-family-circle-redesign |
| MV-132 | Notification dispatch service — emit in-app notifications for family invite events + processing events | P2 | Done (Pending Merge) | Developer Agent | MV-131, MV-127 | feature/MV-125-140-family-circle-redesign |

#### Sub-Epic: Frontend — Family Circle UI

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-133 | Update app shell nav: add Family tab (5-tab bottom nav), move Settings to avatar menu | P1 | Done (Pending Merge) | Developer Agent | — | feature/MV-125-140-family-circle-redesign |
| MV-134 | Family Circle page — visual family tree (parents / spouse / children layout), node cards, pending badges, Add button | P1 | Done (Pending Merge) | Developer Agent | MV-126, MV-133 | feature/MV-125-140-family-circle-redesign |
| MV-135 | Invite flow UI — email input, relationship selector, confirmation; handles existing user + new user paths | P1 | Done (Pending Merge) | Developer Agent | MV-127, MV-134 | feature/MV-125-140-family-circle-redesign |
| MV-136 | Invitation acceptance page — /invite/:token route, accept/decline UI, post-accept redirect | P1 | Done (Pending Merge) | Developer Agent | MV-128 | feature/MV-125-140-family-circle-redesign |
| MV-137 | Vault access permissions UI — per-member access toggle panel (grant/revoke READ access, toggle can-invite) | P2 | Done (Pending Merge) | Developer Agent | MV-129, MV-134 | feature/MV-125-140-family-circle-redesign |
| MV-138 | In-app notification bell + notification centre (unread badge, list, mark read, action deep-links) | P2 | Done (Pending Merge) | Developer Agent | MV-131, MV-133 | feature/MV-125-140-family-circle-redesign |

#### Sub-Epic: Backend Tests

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-139 | Unit + integration tests for invite flow, acceptance, family membership, access grants | P1 | Done (Pending Merge) | Developer Agent | MV-128, MV-129 | feature/MV-125-140-family-circle-redesign |
| MV-140 | Cross-vault isolation tests (grantee can read, non-grantee gets 403, revoke works) | P0 | Done (Pending Merge) | Developer Agent | MV-130 | feature/MV-125-140-family-circle-redesign |

### EPIC: Passport & Family Enhancements (Phase 2)

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-141 | Fix passport landing page — route `/` renders PassportManagePage (Health Passport), retire redundant PassportPage (content now covered by FamilyCirclePage) | P1 | Done | Developer Agent | MV-084 | feature/MV-142-144-family-enhancements |
| MV-142 | Family invite email — SMTP via smtplib (replaced SendGrid); template with accept link; graceful no-op if SMTP not configured; .env.example updated | P1 | Done | Developer Agent | MV-127 | feature/MV-142-144-family-enhancements |
| MV-143 | Child-under-12 invite UX — date-of-birth field in InviteModal when CHILD selected; if age <12 hide email, skip invite flow, create managed FamilyMember directly | P2 | Done | Developer Agent | MV-135 | feature/MV-142-144-family-enhancements |
| MV-144 | SVG family tree graph — foreignObject+HTML NodeCard, bezier edges, hierarchical layout; self_member from dedicated backend field (fixed is_self exclusion bug) | P2 | Done | Developer Agent | MV-134 | feature/MV-142-144-family-enhancements |
| MV-145 | Bug fix — provision_user creates self FamilyMember on first login + backfills existing users; 4 unit tests added covering new/existing/idempotent/name-derivation paths | P0 | Done | Developer Agent | — | feature/MV-142-144-family-enhancements |
| MV-146 | FR-FAM-009 — Delete managed member (409 guard on is_self); cancel-invitation ✕ on pending nodes; unit test for 409 guard; useDeleteManagedMember + onCancelInvitation wired | P1 | Done | Developer Agent | — | feature/MV-142-144-family-enhancements |
| MV-147 | Tech debt — encrypt full_name in FamilyMember writes (pre-existing gap in POST /family/members and provision_user self-member creation; flagged by Reviewer §1.1) | P1 | Not Started | — | — | — |

---

## Activity Log

> Append-only. Never edit existing rows. Format: `YYYY-MM-DD HH:MM | Actor | Action | Task IDs`

| DateTime | Actor | Action | Task IDs | Notes |
|---|---|---|---|---|
| 2026-03-29 | Rishabh | Project setup: SRS v1.2, CLAUDE.md, STATUS.md, all docs created | — | Initial project scaffolding |
| 2026-03-30 | Developer Agent | Started MV-001 — repo structure, Docker Compose scaffold, .env.example | MV-001 | — |
| 2026-03-30 | Developer Agent | Completed MV-001 + MV-002 implementation, moved to In Review | MV-001, MV-002 | MV-001 and MV-002 built on same branch (tightly coupled) |
| 2026-03-30 | Reviewer Agent | Reviewed MV-001 + MV-002 — APPROVED, moved to In QA | MV-001, MV-002 | Stack conformance ✅, no secrets ✅, healthchecks ✅ |
| 2026-03-30 | QA Agent | QA passed MV-001 + MV-002 — all 26 files present, no hardcoded secrets, .mcp.json gitignored | MV-001, MV-002 | Ready for merge |
| 2026-03-30 | Developer Agent | PR opened — rishabhpreethan/MediVault#1 | MV-001, MV-002 | Awaiting merge by Rishabh |
| 2026-03-30 | Rishabh | Merged PR #1 | MV-001, MV-002 | MV-001, MV-002, MV-006 marked Done |
| 2026-03-30 | Developer Agent | Started MV-003 + MV-004 — FastAPI scaffolding and React PWA scaffolding | MV-003, MV-004 | — |
| 2026-03-30 | Rishabh | Merged PR #2 (MV-003) and PR #3 (MV-004) | MV-003, MV-004 | — |
| 2026-03-30 | Developer Agent | Started MV-005 — all core SQLAlchemy models + Alembic initial migration | MV-005 | — |
| 2026-03-30 | Developer Agent | Started MV-030 — Celery worker setup | MV-030 | — |
| 2026-03-30 | Rishabh | Merged PR #4 (MV-005) and PR #5 (MV-030) | MV-005, MV-030 | MV-020, MV-090 marked Done (covered by MV-005) |
| 2026-03-30 | Developer Agent (A) | Started MV-031 — pdfminer.six extraction worker | MV-031 | — |
| 2026-03-30 | Developer Agent (B) | Started MV-120 — pytest + Vitest setup + test fixtures | MV-120 | — |
| 2026-03-30 | Rishabh | Merged PR #6 (MV-031) and PR #7 (MV-120) | MV-031, MV-120 | MV-033 marked Done (already in MV-031) |
| 2026-03-30 | Developer Agent | Started MV-032 + MV-034 — pypdf fallback, orchestrator, status state machine | MV-032, MV-034 | — |
| 2026-03-30 | Rishabh | Merged PR #8 (MV-032 + MV-034) | MV-032, MV-034 | — |
| 2026-03-30 | Developer Agent | Implemented MV-011 — Auth0 RS256 JWT middleware, get_current_user dependency | MV-011 | PR #9 |
| 2026-03-30 | Developer Agent | Implemented MV-014 — frontend Auth0 SDK, useAuthToken hook, .env.example | MV-014 | PR #10 |
| 2026-03-30 | Rishabh | Merged PR #9 (MV-011) and PR #10 (MV-014) | MV-011, MV-014 | — |
| 2026-03-30 | Developer Agent | Implemented MV-013 — POST /auth/provision upsert endpoint | MV-013 | PR #11 |
| 2026-03-30 | Developer Agent | Implemented MV-016 — app shell, bottom nav (5 tabs, SVG icons), MemberSelector hook | MV-016 | PR #12 |
| 2026-03-30 | Developer Agent | Implemented MV-040 — spaCy/Med7 lazy pipeline, BaseNlpExtractor ABC, nlp_tasks stub | MV-040 | PR #13 |
| 2026-03-30 | Rishabh | Merged PR #11 (MV-013), PR #12 (MV-016), PR #13 (MV-040) | MV-013, MV-016, MV-040 | — |
| 2026-03-30 | Developer Agent | Implemented MV-021 — file upload API, MinIO storage service, Alembic migration 0002 | MV-021 | PR #14 merged |
| 2026-03-30 | Developer Agent | Implemented MV-041/042/043 — medication, lab, diagnosis NLP extractors; updated nlp_tasks | MV-041, MV-042, MV-043 | PR #15 merged |
| 2026-03-30 | Rishabh | Merged PR #14 (MV-021) and PR #15 (MV-041/042/043) | MV-021, MV-041, MV-042, MV-043 | — |
| 2026-03-30 | Developer Agent | Implemented MV-023 — retry + status endpoints added to documents API | MV-023 | PR #16 open |
| 2026-03-30 | Developer Agent | Implemented MV-047 + MV-050 — confidence scoring and health profile aggregation service | MV-047, MV-050 | PR #17 open |
| 2026-03-30 | Developer Agent | Implemented MV-091 — family member CRUD API (POST/GET/PATCH/DELETE /family/members) | MV-091 | PR #18 open |
| 2026-03-30 | Developer Agent | Implemented MV-015 — polished LoginPage + CallbackPage + /callback route | MV-015 | PR #19 open |
| 2026-04-07 | Rishabh | Provided Google Stitch export as UI source of truth; teal design system adopted | — | Stitch dir: ~/Downloads/stitch_health_passport/ |
| 2026-04-07 | Developer Agent | Updated frontend-design skill + STATUS.md: Stitch→task mapping, teal design system, MV-016b added for app shell redesign | — | All future UI tasks reference Stitch screens |
| 2026-04-07 | Rishabh | Merged PRs #16 (MV-023), #17 (MV-047/050), #18 (MV-091), #19 (MV-015) | MV-015, MV-023, MV-047, MV-050, MV-091 | — |
| 2026-04-07 | Developer Agent | Started MV-016b (app shell redesign), MV-051 (profile API), MV-044/045/046 (allergy/vitals/doctor extractors) | MV-016b, MV-051, MV-044, MV-045, MV-046 | Running in parallel |
| 2026-04-07 | Rishabh | Merged PR #20 (MV-051) | MV-051 | — |
| 2026-04-07 | Developer Agent | Completed MV-016b — responsive app shell (teal design system, 4-tab nav) | MV-016b | PR #21 open |
| 2026-04-07 | Developer Agent | Completed MV-044/045/046 — allergy, vitals, doctor extractors | MV-044, MV-045, MV-046 | Pending tests/PR |
| 2026-04-07 | Developer Agent | Implemented MV-044/045/046 — allergy, vitals, doctor extractors; 50 tests pass | MV-044, MV-045, MV-046 | PR #22 open |
| 2026-04-07 | Developer Agent | Implemented MV-016b — responsive app shell, teal design system, 4-tab nav | MV-016b | PR #21 open |
| 2026-04-07 | Rishabh | Merged PR #21 (MV-016b) and PR #22 (MV-044/045/046) | MV-016b, MV-044, MV-045, MV-046 | — |
| 2026-04-07 | Developer Agent | Started MV-024, MV-052, MV-060, MV-092 in parallel | MV-024, MV-052, MV-060, MV-092 | Running in parallel |
| 2026-04-07 | Developer Agent | Completed MV-060 — timeline API with schemas, endpoint, router registration, 9 unit tests | MV-060 | Moved to In Review |
| 2026-04-07 | Developer Agent | Completed MV-024 — Clinical Archive UI (RecordsPage): header, extraction accuracy banner, active markers panel, document list with skeleton/empty/error states, import button, search filter | MV-024 | Moved to In Review |
| 2026-04-07 | Developer Agent | Completed MV-052 — Health profile dashboard UI: vitals strip (pulse/BP/blood type), biochemical metrics list with lab flag badges, active plan with medication list, upcoming consult card, skeleton loading, empty states, error state, two-column desktop layout | MV-052 | Moved to In Review |
| 2026-04-07 | Developer Agent | Completed MV-092 — Family Circle UI (PassportPage): primary member card, family member grid, add-member dashed card, recent activity section, skeleton/empty/error states; AddFamilyMemberPage: info panel, identity + clinical profile form, blood group pill selector, mutation with query invalidation; /passport/add-member route added to App.tsx | MV-092 | Moved to In Review |
| 2026-04-07 | Developer Agent | Completed MV-024 (document library UI), MV-052 (health profile dashboard), MV-060 (timeline API) | MV-024, MV-052, MV-060 | PRs #23 #24 #25 open |
| 2026-04-07 | Developer Agent | Completed MV-092 — Family Circle + Add Member form | MV-092 | PR #26 open |
| 2026-04-09 | Rishabh | Merged PRs #23 (MV-024), #24 (MV-052), #25 (MV-060), #26 (MV-092) | MV-024, MV-052, MV-060, MV-092 | — |
| 2026-04-09 | neerajmenon4 | Fix: startup errors, auth race conditions, blank pages, member vault switching | — | Runnable baseline commit |
| 2026-04-09 | Developer Agent | Started MV-061, MV-025, MV-070, MV-080 in parallel | MV-061, MV-025, MV-070, MV-080 | Running in parallel |
| 2026-04-09 | Developer Agent | Completed MV-070 — lab trend chart data API: GET /charts/lab-trends + GET /charts/available-tests, schemas, router registered, 8 unit tests | MV-070 | Moved to In Review |
| 2026-04-07 | Developer Agent | Completed MV-061 — Health Timeline UI: TimelineTab.tsx (event feed grouped by month, sidebar, skeleton/empty/error states, load more), Archive/Timeline tab switcher in RecordsPage.tsx | MV-061 | Moved to In Review |
| 2026-04-07 | Developer Agent | Completed MV-080 — Passport generation API: schemas/passport.py, api/passport.py (POST/GET/DELETE/public endpoints), router registration, 15 unit tests | MV-080, MV-081, MV-082 | Moved to In Review |
| 2026-04-07 | Developer Agent | Completed MV-025 — Upload flow UI: UploadModal.tsx (4-step modal: file selection with drag-and-drop, document type pills, date picker, uploading spinner, success/error states), RecordsPage updated to open modal on Import Record click | MV-025 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-085 — Public Passport Page UI | MV-085 | branch: feature/MV-085-public-passport-ui |
| 2026-04-10 | Developer Agent | Completed MV-085 — PublicPassportPage.tsx: standalone page (no AppShell/Auth0), hero card, allergies/medications/diagnoses section cards, 4 page states (loading/404/410/error), plain axios call to public endpoint | MV-085 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-026 — Document Detail Page | MV-026 | branch: feature/MV-026-document-detail |
| 2026-04-10 | Developer Agent | Completed MV-026 — DocumentDetailPage.tsx: two-column layout (doc header card + PDF placeholder left; extracted data panel right), lab results table, medications/diagnoses/allergies lists, PROCESSING spinner, FAILED error state with Retry button, Download Original link, React Query with useMutation for retry; RecordsPage cards made clickable via Link; /records/:documentId route added to App.tsx | MV-026 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-071 — Lab Trend Chart UI | MV-071 | branch: feature/MV-071-lab-trend-chart-ui |
| 2026-04-10 | Developer Agent | Completed MV-071 — InsightsPage.tsx: test pill selector, Recharts LineChart with ReferenceArea band, custom dots (red for out-of-range, teal for normal), custom tooltip, stats strip (latest/min/max/avg), skeleton/empty/error states; typed against actual backend schema (date, is_abnormal fields) | MV-071 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-083 + MV-084 — QR code component + Passport management UI | MV-083, MV-084 | branch: feature/MV-083-084-passport-ui |
| 2026-04-10 | Developer Agent | Completed MV-083 + MV-084 — PassportManagePage.tsx: bento-grid layout (QR module with qrcode.react QRCodeSVG, Medical Identity card, Active Passports table, Visibility Controls, Revoke/Share panel); inline GenerateModal (section checkboxes + 30/60/90 day expiry); PassportPage.tsx updated with Manage Passport button on SELF card; /passport/manage route added to App.tsx | MV-083, MV-084 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-022 — Scanned PDF detection | MV-022 | branch: feature/MV-022-scanned-pdf-detection |
| 2026-04-10 | Developer Agent | Completed implementation MV-022 — is_likely_scanned() heuristic in orchestrator.py, mark_manual_review() in document_service.py, page_count via pypdf in extraction_tasks.py, PROCESSING→MANUAL_REVIEW transition added, 10 unit tests in test_scanned_detection.py | MV-022 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-072 — Medication Gantt chart (API + UI) | MV-072 | branch: feature/MV-072-medication-gantt |
| 2026-04-10 | Developer Agent | Completed MV-072 — GET /charts/medication-timeline endpoint + MedicationBar/MedicationTimelineResponse schemas; MedicationGanttChart component in InsightsPage.tsx (Recharts vertical BarChart with offset+duration stacked bars, teal/grey active/discontinued coloring, custom tooltip, legend, skeleton/empty/error states); top-level Lab Trends / Medications tab switcher; 3 new backend unit tests | MV-072 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-027 — Manual field correction API + audit trail | MV-027 | branch: feature/MV-027-manual-correction-api |
| 2026-04-10 | Developer Agent | Completed implementation MV-027 — Alembic migration 0003 (correction_audit table), CorrectionAudit ORM model (correction_audit.py, moved out of passport.py), schemas/corrections.py (FieldCorrectionRequest + CorrectionAuditResponse), api/corrections.py (PATCH + GET endpoints with ALLOWED_FIELDS validation, ownership check, audit write), router.py updated, __init__.py updated, 6 unit tests in test_corrections_api.py | MV-027 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-053 — Manual add/edit/delete API for all entity types | MV-053 | branch: feature/MV-053-entity-crud-api |
| 2026-04-10 | Developer Agent | Completed implementation MV-053 — schemas/entity_crud.py (Create/Update/Response schemas for all 5 entity types), api/entity_crud.py (14 endpoints across medications/lab-results/diagnoses/allergies/vitals; is_manual_entry=True on all creates; PATCH /discontinue for meds; ownership check on all writes), router.py updated with entity_crud_router, 12 unit tests in test_entity_crud_api.py | MV-053 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-073 — Vitals trend chart (BP, weight over time) | MV-073 | branch: feature/MV-073-vitals-trend-chart |
| 2026-04-10 | Developer Agent | Started MV-093 — Per-member data isolation verification | MV-093 | branch: feature/MV-093-data-isolation-tests |
| 2026-04-10 | Developer Agent | Completed implementation MV-093 — 13 cross-user isolation tests in backend/tests/integration/test_data_isolation.py; covers profile, timeline, documents, charts (lab-trends + medication-timeline), entity-crud, corrections, passport, and family APIs; 9 negative-path 403 tests + 2 positive-path ownership tests + 2 additional scope tests | MV-093 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-054 — Discontinue medication toggle (UI) | MV-054 | branch: feature/MV-054-discontinue-medication-ui |
| 2026-04-10 | Developer Agent | Completed MV-054 — ActivePlan component in DashboardPage.tsx: Discontinue button per active med row (useMutation → PATCH /profile/{memberId}/medications/{medId}/discontinue, invalidates profile query); discontinued meds shown with opacity-50 + strikethrough + "Discontinued" badge; "Show N discontinued" toggle button; "No active medications" empty state when all meds are discontinued | MV-054 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started MV-048 — Entity deduplication across documents | MV-048 | branch: feature/MV-048-entity-deduplication |
| 2026-04-10 | Developer Agent | Completed implementation MV-048 — deduplication_service.py (deduplicate_medications/diagnoses/allergies + run_deduplication); extraction_tasks.py updated to capture member_id and call run_deduplication after save_extraction_result; 14 unit tests in test_deduplication_service.py; lab_results and vitals explicitly excluded; manual entries skipped | MV-048 | Moved to In Review |
| 2026-04-10 | Developer Agent | Started wave 5: MV-049, MV-110, MV-111, MV-121 in parallel | MV-049, MV-110, MV-111, MV-121 | Running in parallel |
| 2026-04-10 | Developer Agent | Completed MV-049 — drug_synonyms.py: 26 brand→INN mappings, normalize_drug_name(), integrated into medication_extractor drug_name_normalized; 15 unit tests | MV-049 | PR #44 open |
| 2026-04-10 | Developer Agent | Completed MV-110 — DELETE /auth/account: soft-delete + passport revocation + purge_user_data Celery task (MinIO cleanup + FamilyMember cascade delete); migration 0004; 8 unit tests | MV-110 | PR #45 open |
| 2026-04-10 | Developer Agent | Completed MV-111 — POST /export/request-all + POST /export/request + GET /export/status; generate_user_export task builds in-memory ZIP (health_data.json + PDFs), uploads to MinIO, returns presigned URL; 18 unit tests | MV-111 | PR #47 open |
| 2026-04-10 | Developer Agent | Completed MV-121 — test_nlp_comprehensive.py: 55 tests covering orchestrator scanned heuristics, confidence scorer all combos, flag_low_confidence, medication normalization, dedup manual-entry skip | MV-121 | PR #46 open |
| 2026-04-10 | Developer Agent | Started MV-112 — Account settings UI (delete account modal + export data button) | MV-112 | feature/MV-112-account-settings-ui |
| 2026-04-10 | Developer Agent | Started wave 6: MV-122, MV-123, MV-100/101, MV-124 in parallel | MV-122, MV-123, MV-100, MV-101, MV-124 | Running in parallel |
| 2026-04-10 | Developer Agent | Completed MV-122 — 11 pipeline integration tests: upload API, extraction state machine, NLP extraction, profile reflection, deduplication merge | MV-122 | PR #49 open |
| 2026-04-10 | Developer Agent | Completed MV-124 — benchmark_extraction.py: BenchmarkSample + calculate_fidelity + run_benchmark with ANSI output; 13 unit tests | MV-124 | PR #50 open |
| 2026-04-10 | Developer Agent | Completed MV-100 + MV-101 — email_service.py: requests-based SendGrid wrapper, processing_complete + extraction_failed templates (no PHI); extraction_tasks.py hooked with best-effort notify; 6 unit tests | MV-100, MV-101 | PR #51 open |
| 2026-04-10 | Developer Agent | Completed MV-123 — playwright.config.ts + 6 e2e spec files (auth, navigation, records, health-profile, passport, public-passport); all API calls mocked via page.route() | MV-123 | PR #52 open |
| 2026-04-11 | Developer Agent | Started wave 7: rate limiting middleware (NFR-SEC-007), auth audit logging, multi-file upload (MV-FR-DOC-004), test stub fixes | NFR-SEC-007, MV-FR-DOC-004 | feature/MV-SEC-rate-limit-audit |
| 2026-04-11 | Developer Agent | Completed NFR-SEC-007 — middleware-based rate limiting (limits library), app/limiter.py extracted to avoid circular imports; 3 paths rate-limited: upload 20/min, provision 10/min, delete-account 5/hr | NFR-SEC-007 | feature/MV-SEC-rate-limit-audit |
| 2026-04-11 | Developer Agent | Completed auth audit logging — AuthAuditLog model + migration 0005 + audit_service.py; provision/login/delete-account events logged with IP+user-agent; 5 unit tests | auth-audit | feature/MV-SEC-rate-limit-audit |
| 2026-04-11 | Developer Agent | Completed MV-FR-DOC-004 — multi-file upload (up to 10 files), individual per-file type/date/status in UploadModal.tsx; failures don't block other uploads | MV-FR-DOC-004 | feature/MV-SEC-rate-limit-audit |
| 2026-04-11 | Developer Agent | Fixed test stubs — added boto3/spacy stubs to 6 test files; fixed patch targets, request param, FamilyMemberResponse fields, dependency_overrides for health test; 563 unit tests passing at 86% coverage | test-fixes | feature/MV-SEC-rate-limit-audit |
| 2026-04-11 | Developer Agent | [1-Way Door] Dashboard polish: removed Pulse Rate card (no wearable data source), removed Sparkline decorative component, removed hardcoded BP fallback 118/76 → proper empty state, removed fake "Donor"/"Insured" badges from Blood Type card, expanded allergy badges to show actual allergen names (up to 3) | MV-052 polish | — |
| 2026-04-11 | Developer Agent | [1.5-Way Door] Dashboard: replaced static Upcoming Consult card with KnownConditions component (diagnoses from profile API, with ICD-10 codes and status badges); VitalsStrip grid changed from 3-col to 2-col | MV-052 polish | — |
| 2026-04-11 | Developer Agent | [1-Way Door] Records: fixed DISCHARGE → DISCHARGE_SUMMARY type label/icon/color to match backend enum; added doctor_name to document card subtitle row | MV-024 polish | — |
| 2026-04-13 | Rishabh | Decision: Health Passport replaces Dashboard as default landing page — Dashboard (Health Profile) moves to /health; Passport at / | MV-058 | [1.5-Way Door] |
| 2026-04-13 | Developer Agent | Updated specs for MV-058: srs.md §3.5 + §7.2 + §7.3, user-flows.md UF-001 + UF-002, architecture.md frontend routing; added MV-058 to task board | MV-058 | — |
| 2026-04-13 | Developer Agent | Started MV-058 — Passport as default landing page | MV-058 | feature/MV-058-passport-as-home |
| 2026-04-11 | Rishabh | [2-Way Door — DECISION-007] Family Circle redesigned: invitation-based linked accounts + managed profiles; visual family tree; explicit vault access grants; in-app notifications; 5-tab nav (Family added, Settings moved to avatar menu) | — | Full spec in srs.md §3.9-§3.10, architecture.md, user-flows.md UF-009/UF-014-UF-019, decision-framework.md DECISION-007 |
| 2026-04-11 | Developer Agent | Completed spec changes for DECISION-007 — updated srs.md §7.3; updated user-flows.md actors table + UF-009 (managed profiles) + UF-014–UF-019 (family tree, invite existing user, invite new user, accept invite, manage access grants, view delegated vault); added 5 new DB tables + 25 new API endpoints to architecture.md; added DECISION-007 to decision-framework.md; added MV-125–MV-140 to task board | MV-125 through MV-140 | No branch cut yet — spec-only changes |
| 2026-04-14 | Developer Agent | Started MV-125 through MV-140 — Family Circle redesign full implementation | MV-125–MV-140 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-125 — Alembic migration 0006: families, family_invitations, family_memberships, vault_access_grants, notifications tables with all indexes and constraints | MV-125 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-126–MV-129 — family_circle API: 12 endpoints (GET /family/circle, POST/GET/DELETE /family/invitations, resend, GET/POST/DELETE /family/access, PATCH can-invite, GET/POST /invite/:token accept/decline); ORM models Family/FamilyInvitation/FamilyMembership/VaultAccessGrant/Notification; schemas; notification dispatch service | MV-126, MV-127, MV-128, MV-129, MV-132 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-130 — require_vault_access dependency in dependencies.py; owner always allowed; grantee with vault_access_grants row allowed; all others 403 | MV-130 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-131 — notifications API: GET /notifications (paginated), GET /notifications/unread-count, PATCH read, POST read-all, DELETE; registered in router.py | MV-131 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-133 — AppShell: 5-tab nav (Passport/Records/Insights/Health/Family), Settings moved to gear icon in TopNav right section | MV-133 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-134/MV-135 — FamilyCirclePage: visual family tree (parents/owner+spouse/children rows, CSS flexbox), managed profile nodes, pending invitation dashed nodes, inline InviteModal (email + relationship pills), cancel invitation; useFamilyCircle hook; /family route added to App.tsx | MV-134, MV-135 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-136 — InviteAcceptancePage: public /invite/:token page, skeleton loading, status-aware states (invalid/expired/revoked/accepted), auth gate redirects to login, accept/decline mutations | MV-136 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-137 — VaultAccessPanel: slide-up modal with grant/revoke toggles per member, can-invite toggle, admin-only guard | MV-137 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-138 — NotificationCentre: dropdown panel from bell icon, 30s poll unread count, red badge, notification list with mark-read, mark-all-read, action URL navigation, outside-click dismiss | MV-138 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-139 — 31 unit tests (test_family_circle.py): notification dispatch, invite send, cancel, accept, decline, access grants, require_vault_access | MV-139 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Completed MV-140 — 16 cross-vault isolation tests (test_family_vault_isolation.py): owner access, grantee access, non-grantee 403, revoke works, expired/double-accept invite, non-member grant attempt | MV-140 | feature/MV-125-140-family-circle-redesign |
| 2026-04-14 | Developer Agent | Added MV-141–MV-144 to task board (Passport & Family Enhancements Phase 2): passport route fix, invite email, child-under-12 UX, SVG tree graph | MV-141, MV-142, MV-143, MV-144 | — |
| 2026-04-14 | Developer Agent | Started MV-141 — fix passport landing page (route / → PassportManagePage) | MV-141 | feature/MV-141-passport-page-fix |
| 2026-04-14 | Developer Agent | Started MV-142, MV-143, MV-144 — family enhancements: invite email, child-under-12 UX, SVG tree | MV-142, MV-143, MV-144 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Completed MV-141 — App.tsx: route `/` now renders PassportManagePage; removed redundant /passport/manage route and PassportPage import | MV-141 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Completed MV-142 — email_service.py: send_family_invite_email() with branded teal HTML template; hooked into POST /family/invitations and POST /family/invitations/{id}/resend; best-effort (no-op if SendGrid key unset) | MV-142 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Completed MV-143 — InviteModal: DOB field shown for CHILD; if age<12 email hidden, managed profile created via POST /family/members; useCreateManagedMember hook added; distinct success states for invite vs managed | MV-143 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Completed MV-144 — FamilyCirclePage: replaced CSS flexbox tree with SVG node-edge graph; computed hierarchical level positions; bezier curve edges; SvgNode renders initials circle + name + label; pending invites shown as dashed nodes; add-member button integrated into SVG canvas | MV-144 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Completed MV-142 update — switched email service from SendGrid to SMTP (smtplib stdlib); config updated with smtp_host/port/user/password fields; requirements.txt sendgrid removed | MV-142 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Started MV-145 (bug: self FamilyMember not created on provision) and MV-146 (FR-FAM-009: delete managed member) | MV-145, MV-146 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Completed MV-145 — auth.py provision_user now creates is_self FamilyMember on first login (display_name from email prefix); fixes NFR-USE-001 | MV-145 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Completed MV-146 — family.py DELETE /family/members/{id} guards against is_self deletion; useDeleteManagedMember hook; trash icon button on NodeCard in FamilyTree (confirm dialog warns about cascade) | MV-146 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Reviewer Agent | Started review of MV-141–MV-146 on feature/MV-142-144-family-enhancements | MV-141–MV-146 | — |
| 2026-04-14 | Reviewer Agent | CHANGES REQUESTED on MV-141–MV-146 — 5 issues found: (1) §1.1 full_name written unencrypted in auth.py provision_user self-member creation (same pre-existing gap in family.py, flagged for awareness); (2) §5 .env.example still references SENDGRID_API_KEY instead of new SMTP vars — stale after MV-142 SMTP migration; (3) §3 selfMember lookup bug in FamilyCirclePage.tsx line 768 — searches managed_profiles for is_self but backend filters is_self==False, so selfMember is always undefined and the SELF node always displays "Me" regardless of actual user name; (4) §1.1 notification title/body embeds inviter email address (current_user.email) in in-app notification store — email is PII/quasi-PHI; (5) §5 no unit tests added for MV-145 provision_user self-member creation or MV-146 delete guard (alignment-spec §5 requires tests for new backend service logic) | MV-141–MV-146 | feature/MV-142-144-family-enhancements |
| 2026-04-14 | Developer Agent | Resolved all reviewer blockers: (1) .env.example updated with SMTP vars; (2) selfMember bug fixed — added self_member field to FamilyCircleResponse schema+query, FamilyCircle TS type, and FamilyCirclePage now reads circle.self_member; (3) 4 unit tests added for MV-145 provision paths (test_auth_provision.py); (4) MV-146 is_self 409 guard test added (test_family_api.py); (5) full_name encryption logged as pre-existing gap, new task MV-147 created | MV-141–MV-146 | feature/MV-142-144-family-enhancements |
| 2026-04-20 | Developer Agent | Completed MV-150 — Alembic migration 0007: role+onboarding_completed on users; height_cm+weight_kg on family_members; provider_profiles table; User+FamilyMember models updated; ProviderProfile model created | MV-150 | feature/MV-150-154-onboarding |
| 2026-04-20 | Developer Agent | Completed MV-151 — GET /auth/onboarding/status + POST /auth/onboarding: updates self FamilyMember, creates allergy entities, sets role+onboarding_completed, upserts provider_profiles, queues verify_licence_task | MV-151 | feature/MV-150-154-onboarding |
| 2026-04-20 | Developer Agent | Completed MV-152 — verify_licence_task Celery stub: logs request, leaves status PENDING; NMC integration deferred | MV-152 | feature/MV-150-154-onboarding |
| 2026-04-20 | Developer Agent | Completed MV-153 — OnboardingPage: full-screen 6-step wizard (personal info / blood group / allergies / role / provider licence / complete); StepDots progress indicator; PROVIDER licence step conditional; POST /auth/onboarding on complete; TypeScript clean | MV-153 | feature/MV-150-154-onboarding |
| 2026-04-20 | Developer Agent | Completed MV-154 — RequireOnboarding guard in App.tsx: queries /auth/onboarding/status, redirects to /onboarding if incomplete; /onboarding route inside AuthGuard but outside AppShell | MV-154 | feature/MV-150-154-onboarding |
