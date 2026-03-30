# MediVault — Project Status

**Last Updated:** 2026-03-29
**SRS Version:** 1.2
**Active Phase:** V1 MVP

---

## Active Workers

> Claim a task here before starting. This prevents two people from picking the same task.
> Clear your entry once your PR is merged.

| Person | Agent Role | Currently Working On | Task ID | Branch | Last Updated |
|---|---|---|---|---|---|
| Rishabh | Developer Agent | Repo structure, Docker Compose scaffold, .env.example | MV-001 | feature/MV-001-repo-init | 2026-03-30 |

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
| MV-001 | Repo structure, Docker Compose scaffold, .env.example | P0 | Done (Pending Merge) | Rishabh / Developer Agent | — | feature/MV-001-repo-init |
| MV-002 | PostgreSQL + Redis + MinIO Docker Compose services | P0 | Done (Pending Merge) | Rishabh / Developer Agent | MV-001 | feature/MV-001-repo-init |
| MV-003 | FastAPI project scaffolding (app factory, config, router) | P0 | Not Started | — | MV-001 | — |
| MV-004 | React PWA scaffolding (Vite, TypeScript, Tailwind, Auth0 SDK) | P0 | Not Started | — | MV-001 | — |
| MV-005 | Alembic setup + initial DB migration (all core tables) | P0 | Not Started | — | MV-002, MV-003 | — |
| MV-006 | GitHub Actions CI pipeline (lint, typecheck, unit tests) | P1 | Not Started | — | MV-003, MV-004 | — |

### EPIC: Authentication

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-010 | Auth0 tenant + application configuration, JWKS setup | P0 | Not Started | — | — | — |
| MV-011 | Backend JWT middleware (Auth0 RS256 validation, get_current_user dep) | P0 | Not Started | — | MV-003, MV-010 | — |
| MV-012 | User model, family_members model, DB migration | P0 | Not Started | — | MV-005 | — |
| MV-013 | /auth/provision endpoint — user provisioning on first login | P0 | Not Started | — | MV-011, MV-012 | — |
| MV-014 | Frontend Auth0 SDK integration, protected route wrapper | P0 | Not Started | — | MV-004, MV-010 | — |
| MV-015 | Login / Signup UI screens (email, Google OAuth, phone OTP) | P0 | Not Started | — | MV-014 | — |
| MV-016 | Frontend app shell, bottom nav, member selector | P0 | Not Started | — | MV-014 | — |
| MV-017 | Session inactivity (30-day), token refresh, logout | P1 | Not Started | — | MV-013 | — |

### EPIC: Document Management

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-020 | Document DB model + Alembic migration | P0 | Not Started | — | MV-005 | — |
| MV-021 | File upload API (validation, virus scan, MinIO storage, queue job) | P0 | Not Started | — | MV-011, MV-020 | — |
| MV-022 | Scanned PDF detection (embedded text layer check) | P0 | Not Started | — | MV-021 | — |
| MV-023 | Document library API (list, get, delete, retry) | P0 | Not Started | — | MV-021 | — |
| MV-024 | Document library UI (grid/list, status badges, upload CTA) | P0 | Not Started | — | MV-016, MV-023 | — |
| MV-025 | Upload flow UI (file picker, type selection, date confirmation, progress, rejection messages) | P0 | Not Started | — | MV-021, MV-024 | — |
| MV-026 | Document detail page (PDF viewer + extracted data panel, inline edit) | P1 | Not Started | — | MV-024 | — |
| MV-027 | Manual field correction API + audit trail | P1 | Not Started | — | MV-023 | — |

### EPIC: PDF Extraction Pipeline

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-030 | Celery app setup + Redis broker + worker Dockerfile | P0 | Not Started | — | MV-002, MV-003 | — |
| MV-031 | pdfminer.six extraction worker (primary extractor) | P0 | Not Started | — | MV-030 | — |
| MV-032 | pypdf fallback extractor + extraction orchestration logic | P0 | Not Started | — | MV-031 | — |
| MV-033 | Extraction job retry logic (3 attempts, exponential backoff) | P0 | Not Started | — | MV-032 | — |
| MV-034 | Raw text storage to Document record + status state machine | P0 | Not Started | — | MV-031, MV-020 | — |

### EPIC: NLP Medical Data Extraction

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-040 | spaCy + Med7 pipeline setup, model loading, base extractor | P0 | Not Started | — | MV-034 | — |
| MV-041 | Medication extraction (drug name, dosage, frequency, duration, route) | P0 | Not Started | — | MV-040 | — |
| MV-042 | Lab result extraction (test name, value, unit, reference range, H/L flag) | P0 | Not Started | — | MV-040 | — |
| MV-043 | Diagnosis extraction (condition name, date, status) | P0 | Not Started | — | MV-040 | — |
| MV-044 | Allergy extraction | P1 | Not Started | — | MV-040 | — |
| MV-045 | Vitals extraction (BP, weight, height, BMI, SpO2) | P1 | Not Started | — | MV-040 | — |
| MV-046 | Doctor/facility/visit date extraction | P1 | Not Started | — | MV-040 | — |
| MV-047 | Confidence scoring system (HIGH/MEDIUM/LOW) + low-confidence flagging | P0 | Not Started | — | MV-041, MV-042, MV-043 | — |
| MV-048 | Entity deduplication across documents (chronic conditions, medications) | P1 | Not Started | — | MV-043 | — |
| MV-049 | Drug synonym normalization dictionary | P2 | Not Started | — | MV-041 | — |

### EPIC: Health Profile

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-050 | Profile aggregation service (builds HealthProfileRM from all entities) | P0 | Not Started | — | MV-041, MV-042, MV-043 | — |
| MV-051 | Profile API endpoints (GET full profile, GET summary) | P0 | Not Started | — | MV-050 | — |
| MV-052 | Health profile dashboard UI (summary card, medications, conditions, allergies, labs) | P0 | Not Started | — | MV-051, MV-016 | — |
| MV-053 | Manual add/edit/delete API for all entity types | P1 | Not Started | — | MV-051 | — |
| MV-054 | Discontinue medication toggle (API + UI) | P2 | Not Started | — | MV-052 | — |

### EPIC: Health Timeline

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-060 | Timeline data API (paginated, filterable by type/date) | P0 | Not Started | — | MV-050 | — |
| MV-061 | Timeline UI (vertical scroll, event type icons, expand/collapse, filters) | P0 | Not Started | — | MV-060, MV-016 | — |

### EPIC: Trend Visualizations

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-070 | Lab trend chart data API (time-series per parameter, ≥2 data points check) | P0 | Not Started | — | MV-050 | — |
| MV-071 | Lab trend chart UI (Recharts, reference range band, out-of-range markers) | P0 | Not Started | — | MV-070, MV-016 | — |
| MV-072 | Medication Gantt chart (API + UI) | P1 | Not Started | — | MV-050 | — |
| MV-073 | Vitals trend chart (BP, weight over time) | P1 | Not Started | — | MV-050 | — |

### EPIC: Health Passport

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-080 | Passport generation API (UUID, expiry, section visibility settings) | P0 | Not Started | — | MV-050 | — |
| MV-081 | Passport revoke/expiry API + access log | P0 | Not Started | — | MV-080 | — |
| MV-082 | Public passport view endpoint (no auth, rate limited) | P0 | Not Started | — | MV-080 | — |
| MV-083 | QR code generation (frontend, links to passport URL) | P0 | Not Started | — | MV-080 | — |
| MV-084 | Passport management UI (generate, list, revoke, copy link, QR) | P0 | Not Started | — | MV-080, MV-016 | — |
| MV-085 | Public passport page UI (read-only, patient-reported disclaimer, print-friendly) | P0 | Not Started | — | MV-082 | — |

### EPIC: Family Accounts

| Task ID | Task Name | Priority | Status | Assigned To | Blocked By | Branch |
|---|---|---|---|---|---|---|
| MV-090 | Family member DB model + migration (included in MV-012 if done together) | P1 | Not Started | — | MV-005 | — |
| MV-091 | Family member CRUD API (add, list, update, delete with data purge) | P1 | Not Started | — | MV-090, MV-011 | — |
| MV-092 | Family management UI (add member, member selector across all tabs) | P1 | Not Started | — | MV-091, MV-016 | — |
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
| MV-120 | pytest setup + Vitest setup + test fixtures (sample PDFs) | P1 | Not Started | — | MV-003, MV-004 | — |
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
