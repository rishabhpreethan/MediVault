# MediVault — Project Status

**Last Updated:** 2026-04-07 (PRs #16–#19 open; Stitch designs adopted as UI source of truth)
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
| Developer Agent | Developer | Public Passport Page UI | MV-085 | feature/MV-085-public-passport-ui | 2026-04-10 |
| Developer Agent | Developer | Document Detail Page — In Review | MV-026 | feature/MV-026-document-detail | 2026-04-10 |
| Developer Agent | Developer | QR code component + Passport management UI | MV-083, MV-084 | feature/MV-083-084-passport-ui | 2026-04-10 |

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
| MV-017 | Session inactivity (30-day), token refresh, logout | P1 | Not Started | — | MV-013 | — |

### EPIC: Document Management

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-020 | Document DB model + Alembic migration | P0 | Done | Developer Agent | MV-005 | feature/MV-005-db-migrations |
| MV-021 | File upload API (validation, MinIO storage, queue job) | P0 | Done | Developer Agent | MV-011, MV-020 | feature/MV-021-file-upload-api |
| MV-022 | Scanned PDF detection (embedded text layer check) | P0 | Not Started | — | MV-021 | — |
| MV-023 | Document library API (list, get, delete, retry) | P0 | Done | Developer Agent | MV-021 | feature/MV-023-document-retry-status |
| MV-024 | Document library UI ("Clinical Archive") — ref: `stitch_health_passport/document_vault/` | P0 | In Review | Developer Agent | MV-016b, MV-023 | feature/MV-024-document-library-ui |
| MV-025 | Upload flow UI (file picker, type selection, date, progress, rejection) | P0 | In Review | Developer Agent | MV-021, MV-024 | feature/MV-025-upload-flow-ui |
| MV-026 | Document detail page (PDF viewer + extracted data panel, inline edit) | P1 | In Review | Developer Agent | MV-024 | feature/MV-026-document-detail |
| MV-027 | Manual field correction API + audit trail | P1 | Not Started | — | MV-023 | — |

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
| MV-048 | Entity deduplication across documents (chronic conditions, medications) | P1 | Not Started | — | MV-043 | — |
| MV-049 | Drug synonym normalization dictionary | P2 | Not Started | — | MV-041 | — |

### EPIC: Health Profile

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-050 | Profile aggregation service (builds HealthProfileRM from all entities) | P0 | Done | Developer Agent | MV-041, MV-042, MV-043 | feature/MV-047-050-confidence-profile |
| MV-051 | Profile API endpoints (GET full profile, GET summary) | P0 | Done | Developer Agent | MV-050 | feature/MV-051-profile-api |
| MV-052 | Health profile dashboard UI — ref: `stitch_health_passport/health_profile_dashboard/` | P0 | In Review | Developer Agent | MV-051, MV-016b | feature/MV-052-health-profile-ui |
| MV-053 | Manual add/edit/delete API for all entity types | P1 | Not Started | — | MV-051 | — |
| MV-054 | Discontinue medication toggle (API + UI) | P2 | Not Started | — | MV-052 | — |

### EPIC: Health Timeline

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-060 | Timeline data API (paginated, filterable by type/date) | P0 | In Review | Developer Agent | MV-050 | feature/MV-060-timeline-api |
| MV-061 | Timeline UI (under Records tab) — ref: `stitch_health_passport/health_timeline/` | P0 | In Review | Developer Agent | MV-060, MV-016b | feature/MV-061-timeline-ui |

### EPIC: Trend Visualizations

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-070 | Lab trend chart data API (time-series per parameter, ≥2 data points check) | P0 | In Review | Developer Agent | MV-050 | feature/MV-070-lab-trend-api |
| MV-071 | Lab trend chart UI (Recharts, reference range band, out-of-range markers) | P0 | In Review | Developer Agent | MV-070, MV-016 | feature/MV-071-lab-trend-chart-ui |
| MV-072 | Medication Gantt chart (API + UI) | P1 | Not Started | — | MV-050 | — |
| MV-073 | Vitals trend chart (BP, weight over time) | P1 | Not Started | — | MV-050 | — |

### EPIC: Health Passport

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-080 | Passport generation API (UUID, expiry, section visibility settings) | P0 | In Review | Developer Agent | MV-050 | feature/MV-080-passport-api |
| MV-081 | Passport revoke/expiry API + access log | P0 | Done | Developer Agent (covered by MV-080) | MV-080 | feature/MV-080-passport-api |
| MV-082 | Public passport view endpoint (no auth, rate limited) | P0 | Done | Developer Agent (covered by MV-080) | MV-080 | feature/MV-080-passport-api |
| MV-083 | QR code generation (frontend, links to passport URL) | P0 | In Review | Developer Agent | MV-080 | feature/MV-083-084-passport-ui |
| MV-084 | Passport management UI — ref: `stitch_health_passport/health_passport/` | P0 | In Review | Developer Agent | MV-080, MV-016b | feature/MV-083-084-passport-ui |
| MV-085 | Public passport page UI (read-only) — ref: `stitch_health_passport/health_passport/` | P0 | In Review | Developer Agent | MV-082 | feature/MV-085-public-passport-ui |

### EPIC: Family Accounts

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-090 | Family member DB model + migration (included in MV-012 if done together) | P1 | Done | Developer Agent | MV-005 | feature/MV-005-db-migrations |
| MV-091 | Family member CRUD API (add, list, update, delete with data purge) | P1 | Done | Developer Agent | MV-090, MV-011 | feature/MV-091-family-crud |
| MV-092 | Family management UI ("Family Circle") — ref: `stitch_health_passport/family_health_ecosystem/` + `add_family_member/` | P1 | In Review | Developer Agent | MV-091, MV-016b | feature/MV-092-family-ui |
| MV-093 | Per-member data isolation verification (all queries scoped to member_id) | P0 | Not Started | — | MV-091 | — |

### EPIC: Notifications

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-100 | Email notification service (SendGrid integration) | P2 | Not Started | — | MV-034 | — |
| MV-101 | Processing complete + extraction failed notifications | P2 | Not Started | — | MV-100, MV-034 | — |

### EPIC: Account Management

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-110 | Account deletion API (initiates data purge, revokes all passports) | P1 | Not Started | — | MV-011 | — |
| MV-111 | Data export API (JSON + zip of PDFs, async, email link) | P1 | Not Started | — | MV-050 | — |
| MV-112 | Account settings UI (delete account, export data) | P1 | Not Started | — | MV-016 | — |

### EPIC: Test Suite

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-120 | pytest setup + Vitest setup + test fixtures (sample PDFs) | P1 | Done | Developer Agent | MV-003, MV-004 | feature/MV-120-test-setup |
| MV-121 | Backend unit tests (NLP extractors, confidence scorer, deduplication) | P1 | Not Started | — | MV-047 | — |
| MV-122 | Backend integration tests (upload → extract → NLP → profile pipeline) | P1 | Not Started | — | MV-050 | — |
| MV-123 | Playwright E2E tests (critical user journeys UF-001 through UF-009) | P1 | Not Started | — | MV-052, MV-061, MV-084 | — |
| MV-124 | PDF extraction accuracy benchmarking (≥95% text fidelity target) | P2 | Not Started | — | MV-032 | — |

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
