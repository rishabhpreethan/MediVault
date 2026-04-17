# PR Completion Checklist

Run through the relevant section before moving a task to the next status. All three roles must complete their section before a PR is merged.

---

## Developer — before moving status → In Review

- [ ] All unit tests pass locally: `pytest backend/tests/unit -v` and `npm run test`
- [ ] All integration tests pass: `pytest backend/tests/integration -v`
- [ ] Lint passes: `ruff check .` and `eslint .`
- [ ] Type check passes: `mypy backend/` and `tsc --noEmit`
- [ ] `.env.example` updated if any new environment variables were added
- [ ] No PHI in any log statement — only IDs, statuses, event names
- [ ] No secrets or hardcoded credentials in any file
- [ ] If DB schema changed: Alembic migration file present and tested
- [ ] PR description includes a Summary section and links to MV-XXX task IDs
- [ ] STATUS.md updated: status → `In Review`, Activity Log entry added

---

## Reviewer — before moving status → In QA

- [ ] Reviewed all sections of `docs/alignment-spec.md` applicable to this PR
- [ ] §1 Security & Privacy: PASS (any failure here is a hard blocker — do not proceed)
- [ ] §2 Architecture Alignment: PASS or N/A
- [ ] §3 SRS Functional Requirements: verified relevant FRs
- [ ] §4 Non-Functional Requirements: verified applicable NFRs
- [ ] §5 Code Quality: PASS
- [ ] PHI/authorization deep-dive completed (see `reviewer.md` Security Deep-Dive section)
- [ ] Decision framework classification verified for any non-trivial choices
- [ ] Reviewer sign-off block added to PR description
- [ ] STATUS.md updated: status → `In QA`, Activity Log entry added

---

## QA — before moving status → Done (Pending Merge)

- [ ] Unit and integration tests pass on the branch
- [ ] E2E tests pass for all user flows touched by this PR
- [ ] Mobile tested at 375px and 414px (including Family tab if applicable)
- [ ] Cross-vault isolation matrix run (if PR touches family or vault access)
- [ ] Notification content checked for PHI leakage (if PR touches notifications or invitations)
- [ ] All authorization bypass tests passed
- [ ] All input validation tests passed
- [ ] Extraction accuracy benchmarks run and results logged (if PR touches NLP)
- [ ] Error state tests run for new async operations
- [ ] QA sign-off block added to PR description
- [ ] STATUS.md updated: status → `Done (Pending Merge)`, Activity Log entry added

---

## Human — final check before merge

- [ ] Reviewer sign-off block present in PR description
- [ ] QA sign-off block present in PR description
- [ ] STATUS.md shows `Done (Pending Merge)`
- [ ] CI is passing
- [ ] Feature branch name matches the task ID (e.g. `feature/MV-XXX-slug`)
- [ ] No `.env` files, credentials, or real PHI in the diff
