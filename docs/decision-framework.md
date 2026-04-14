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
