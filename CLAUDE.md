# MediVault — Project Instructions

This file is read by every Claude agent working on this project. Read it fully before doing anything.

---

## Project Overview

**MediVault** is a patient-centric Progressive Web App that lets individuals upload medical PDFs (lab reports, prescriptions, discharge summaries), automatically extracts structured health data via NLP, and visualizes it as a unified health profile, timeline, and shareable Health Passport.

- **SRS:** `srs.md` (v1.2)
- **Architecture:** `docs/architecture.md`
- **User Flows:** `docs/user-flows.md`

---

## Your Role

Every agent working on this project has a specific role. Identify yours before starting:

| Role | Instructions File | When to Use |
|---|---|---|
| **Developer Agent** | `.claude/agents/developer.md` | Building features, writing code |
| **Reviewer Agent** | `.claude/agents/reviewer.md` | Reviewing code for correctness and alignment |
| **QA Agent** | `.claude/agents/qa.md` | Testing features before PR is opened |

Read your role's instruction file immediately after reading this file.

---

## Tech Stack (decided — 2-Way Door to change)

| Component | Choice |
|---|---|
| Backend | Python 3.12 + FastAPI + Pydantic v2 |
| Database | PostgreSQL 16 + SQLAlchemy (async) + Alembic |
| Task Queue | Celery 5 + Redis |
| Object Storage | MinIO (local, S3-compatible) |
| PDF Extraction | pdfminer.six (primary), pypdf (fallback) |
| NLP | spaCy 3 + Med7 |
| Auth | Auth0 (RS256 JWT) |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + Recharts |
| Testing | pytest + Vitest + Playwright |

Changing any item in this table is a **2-Way Door decision** — add a record to `docs/decision-framework.md` and align with both collaborators before proceeding.

---

## Non-Negotiable Rules (apply to all agents)

1. **No PHI in logs.** Never log patient names, medical values, or document content — only IDs and statuses.
2. **No PHI to external APIs.** Document processing stays entirely on-infrastructure (CON-006 in SRS).
3. **No direct commits to `main`.** All work happens on feature branches.
4. **STATUS.md is always up to date.** Update it when you start, finish, or block on a task.
5. **One task at a time per person.** Check STATUS.md before claiming a task to avoid conflicts.
6. **No PR without Reviewer + QA sign-off.** See `docs/branching-strategy.md`.

---

## STATUS.md — How to Use It

`STATUS.md` is the coordination layer between collaborators. Every agent must update it:

- **Before starting a task:** claim it (In Progress + Assigned To)
- **After completing work:** update status and add a line to the Activity Log
- **When blocked:** update status to Blocked and note the blocker task ID

The Activity Log is **append-only** — never edit existing log entries.

---

## Key Documents

| Document | Purpose |
|---|---|
| `srs.md` | What the product does; functional + non-functional requirements |
| `docs/architecture.md` | HLD, LLD, DB schema, API catalog, service contracts |
| `docs/alignment-spec.md` | Reviewer checklist — code must satisfy this |
| `docs/user-flows.md` | Actor journeys — drives implementation logic and test cases |
| `docs/event-model.md` | Commands → Events → Read Models |
| `docs/decision-framework.md` | 1-way / 1.5-way / 2-way door decisions |
| `docs/branching-strategy.md` | Git workflow, PR process, conflict resolution |
| `STATUS.md` | Task board + activity log |

---

## Collaboration Notes

Two people (Rishabh + collaborator) work on this repo simultaneously, each using Claude agents. To avoid conflicts:

- Always `git pull origin main` before cutting a new branch
- Claim tasks in STATUS.md before starting (prevents two people picking the same task)
- The most conflict-prone file is `STATUS.md` — see `docs/branching-strategy.md` for conflict resolution
- DB migrations must be coordinated — check STATUS.md blocker field before creating a migration
- When in doubt about what to work on: check STATUS.md for `Not Started` tasks with no blockers and no owner
