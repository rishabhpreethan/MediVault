# MediVault — Branching & GitHub Strategy

## Principles
- One feature branch per task (or tightly related group of tasks, see below)
- A PR is raised **only** after: developer builds → reviewer approves → QA signs off
- Only the human (Rishabh or collaborator) merges PRs into `main`
- No direct commits to `main`
- STATUS.md is the coordination layer — always claim a task before starting

---

## Branch Structure

```
main                        ← production-ready, protected
└── feature/MV-XXX-slug     ← one per task / feature
```

There is no long-lived `develop` branch. Feature branches are cut from `main` and merged back into `main` via PR. This keeps the history linear and the branch list clean.

---

## Branch Naming

Format: `feature/{TASK-ID}-{short-slug}`

| Task ID | Branch Name |
|---|---|
| MV-001 | `feature/MV-001-repo-init` |
| MV-010 | `feature/MV-010-auth0-config` |
| MV-031 | `feature/MV-031-pdfminer-worker` |

**Rules:**
- All lowercase, hyphens only (no underscores, no spaces)
- Slug is 2–4 words max
- Use the exact Task ID from STATUS.md

**Grouping tasks on one branch:** If two tasks are tightly coupled (e.g., MV-020 DB model + MV-021 upload API), they may share a branch named after the primary task: `feature/MV-020-document-model`. Note the secondary task ID in the PR description and mark both tasks in STATUS.md.

---

## Workflow: Start a Task

1. Check STATUS.md — confirm the task is `Not Started` and not claimed
2. Update STATUS.md: set status to `In Progress`, set `Assigned To` to your name, log in Activity Log
3. Cut branch from latest `main`:
   ```bash
   git checkout main && git pull origin main
   git checkout -b feature/MV-XXX-slug
   ```
4. Build the feature

---

## Workflow: Complete a Task

1. **Developer Agent** finishes implementation, runs lint + unit tests locally
2. Developer updates STATUS.md: status → `In Review`
3. **Reviewer Agent** reviews the code against `docs/alignment-spec.md` and the SRS
   - If changes needed: leaves inline comments, status → `In Progress` (back to developer)
   - If approved: updates STATUS.md status → `In QA`, leaves approval note in PR description
4. **QA Agent** runs the test suite against this branch
   - If issues found: status → `In Progress` (back to developer)
   - If all tests pass: updates STATUS.md status → `Done (Pending Merge)`, leaves QA sign-off note
5. Developer opens PR:
   ```
   Title: [MV-XXX] Short description of what was built
   Body:  ## Summary
          - What was built
          - Key decisions made (note door type from decision-framework.md)
          ## Test Evidence
          - QA agent sign-off (paste summary)
          ## Reviewer Sign-Off
          - Reviewer agent approval note
          ## Checklist
          - [ ] STATUS.md updated
          - [ ] alignment-spec.md requirements met
          - [ ] No PHI logged or exposed
          - [ ] Tests passing
   ```
6. Human reviews and merges PR
7. After merge: delete the feature branch

---

## Handling Conflicts

Since both collaborators work on separate feature branches, conflicts only arise if two branches touch the same file. The most likely conflict-prone files are:

| File | Risk | Mitigation |
|---|---|---|
| `STATUS.md` | High | Always pull latest `main` before editing STATUS.md. The Activity Log is append-only — add rows, never edit existing ones. |
| `alembic/versions/*.py` | Medium | One DB migration per branch. Coordinate migration ordering via STATUS.md blocker field. |
| `backend/app/api/router.py` | Low | Router registrations — easy to merge manually |

**Conflict resolution rule:** If you hit a merge conflict in `STATUS.md`, keep all rows from both versions — never delete a log entry. For task rows, take the most recent status.

---

## PR Checklist (for the human reviewer)

Before merging any PR:
- [ ] Reviewer Agent approval is present in PR description
- [ ] QA Agent sign-off is present in PR description
- [ ] STATUS.md has been updated (task marked Done)
- [ ] Branch name matches the task ID
- [ ] No secrets, credentials, or PHI committed
- [ ] All CI checks pass (GitHub Actions)

---

## GitHub Actions CI

Every push to a feature branch triggers:
1. `backend`: `pytest` (unit + integration tests), `ruff` lint, `mypy` type check
2. `frontend`: `vitest` unit tests, `eslint` lint, `tsc` type check
3. On PR open: E2E tests (Playwright) against a local Docker Compose stack

PR cannot be merged if CI is red. Human can override only for genuine infrastructure-only changes (e.g., Dockerfile tweaks) with explicit note in PR.

---

## Tagging and Releases

Once V1 MVP is complete and all MVP tasks are `Done`:
```bash
git tag -a v1.0.0-mvp -m "MediVault V1 MVP"
git push origin v1.0.0-mvp
```

Tag naming: `v{major}.{minor}.{patch}[-label]`
