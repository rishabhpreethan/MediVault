# Architecture.md Quick Navigation

`docs/architecture.md` is the single source of truth for system design. Use this index to jump to the right section without reading the whole file.

---

## When you need to...

| Task | Section to read |
|---|---|
| Design or review a new API endpoint | API Catalog + Service Contracts |
| Check DB schema for a table | Data Model → DB Schema |
| Understand the auth/JWT flow | Authentication Flow |
| Build or modify the NLP pipeline | NLP Pipeline Detail |
| Add a Celery task | Task Queue Design |
| Work with MinIO file storage | Object Storage |
| Check indexing requirements | DB Schema (indexes subsection) |
| Understand HLD service boundaries | High-Level Design |
| Understand LLD component contracts | Low-Level Design |
| Add a new service/module | LLD → Service Contracts |

---

## Key Constraints Enforced by Architecture

These are the most commonly missed architectural rules — check them before coding:

**API design**
- All private endpoints must use `get_current_user` as a FastAPI dependency
- All responses must use Pydantic v2 schemas — no raw dicts
- Error shape is always: `{"error": "ERROR_CODE", "message": "Human readable"}`
- Rate limits: auth (10/min/IP), upload (20/min/user), public passport (60/min/IP)

**Database**
- All UUIDs use `gen_random_uuid()` as default
- Every query must scope to `user_id` from JWT — never from client body
- PHI fields (`full_name`, `date_of_birth`) must use `encrypt_field()` / `decrypt_field()`
- Column drops require: add new → backfill → drop old (never single-step)

**Storage**
- File path convention: `{user_id}/{member_id}/{doc_id}.pdf`
- ClamAV scan must complete before writing to MinIO
- Never store files on local filesystem

**Family vault access**
- `member_id` ownership must be verified via `vault_access_grants` on every request
- `member_id` always comes from URL path — never request body
- `is_self` FamilyMember cannot be deleted (guard required)

---

## Checklist for New Endpoints

Before submitting a new endpoint for review, verify:

- [ ] Route is documented in architecture.md API Catalog
- [ ] Uses `get_current_user` dependency (or explicitly noted as public)
- [ ] Request body is a Pydantic v2 model
- [ ] Response body is a Pydantic v2 model
- [ ] Scopes DB query to authenticated user
- [ ] Rate limiting applied if applicable
- [ ] Error responses follow standard shape
