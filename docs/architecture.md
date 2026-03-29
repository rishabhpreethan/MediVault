# MediVault — Architecture

Reference document for the Developer Agent. Contains HLD, LLD, API catalog, DB schema, and service contracts.

---

## High-Level Design (HLD)

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                        MediVault System                      │
│                                                              │
│  ┌──────────┐    HTTPS    ┌─────────────┐                   │
│  │ React PWA│◄───────────►│  API Gateway│                   │
│  │(Browser) │             │  (FastAPI)  │                   │
│  └──────────┘             └──────┬──────┘                   │
│                                  │                           │
│         ┌────────────────────────┼────────────────────┐     │
│         │                        │                    │     │
│  ┌──────▼──────┐  ┌─────────────▼──────┐  ┌─────────▼───┐ │
│  │Auth Service │  │  Document Service   │  │Profile Svc  │ │
│  │(Auth0 JWT)  │  │  (upload/validate)  │  │(aggregation)│ │
│  └─────────────┘  └─────────────┬──────┘  └─────────────┘ │
│                                  │                           │
│                    ┌─────────────▼──────────────────┐       │
│                    │     Processing Pipeline          │       │
│                    │  Redis Queue → Celery Worker     │       │
│                    │  pdfminer.six → spaCy+Med7 NLP  │       │
│                    └─────────────────────────────────┘       │
│                                                              │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐    │
│  │  PostgreSQL  │  │   MinIO    │  │      Redis        │    │
│  │  (primary DB)│  │(PDF store) │  │ (queue + cache)   │    │
│  └──────────────┘  └────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘

External:
  Auth0 (identity provider, token issuer)
  SendGrid (transactional email)
```

### Container Diagram

| Container | Technology | Responsibility |
|---|---|---|
| **React PWA** | React 18, Vite, TypeScript, Tailwind CSS | All patient-facing UI. Communicates via REST to API Gateway. Installable as PWA. |
| **API Gateway / Backend** | Python 3.12, FastAPI, Pydantic v2, Uvicorn | Single backend entry point. JWT validation, routing, rate limiting, business logic. |
| **Celery Worker** | Python, Celery 5, Redis broker | Async document processing: pdfminer.six extraction + spaCy+Med7 NLP. |
| **PostgreSQL 16** | PostgreSQL | Primary relational store. All structured data, entities, metadata. |
| **MinIO** | MinIO (S3-compatible) | Encrypted storage for uploaded PDF files. Per-user bucket prefixes. |
| **Redis 7** | Redis | Celery task queue, session cache, rate limit counters. |
| **Auth0** | Auth0 (external) | Identity provider. Issues RS256-signed JWTs. |

### Deployment (Local — V1)

All services run via Docker Compose on the local machine:

```yaml
services:
  api:        # FastAPI + Uvicorn
  worker:     # Celery worker (same image as api)
  postgres:   # PostgreSQL 16
  redis:      # Redis 7
  minio:      # MinIO
  frontend:   # Nginx serving built React app (or Vite dev server)
```

---

## Low-Level Design (LLD)

### Project Directory Structure

```
medivault/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory
│   │   ├── config.py                # Settings (Pydantic BaseSettings)
│   │   ├── dependencies.py          # Shared DI (db session, current user)
│   │   ├── api/
│   │   │   ├── router.py            # Aggregates all routers
│   │   │   ├── auth.py              # Auth endpoints
│   │   │   ├── documents.py         # Document management endpoints
│   │   │   ├── profile.py           # Health profile endpoints
│   │   │   ├── timeline.py          # Timeline endpoints
│   │   │   ├── charts.py            # Chart data endpoints
│   │   │   ├── passport.py          # Passport endpoints
│   │   │   └── family.py            # Family member endpoints
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── family_member.py
│   │   │   ├── document.py
│   │   │   ├── medication.py
│   │   │   ├── lab_result.py
│   │   │   ├── diagnosis.py
│   │   │   ├── allergy.py
│   │   │   ├── vital.py
│   │   │   ├── doctor.py
│   │   │   ├── procedure.py
│   │   │   └── passport.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── document_service.py
│   │   │   ├── extraction_service.py
│   │   │   ├── nlp_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── passport_service.py
│   │   │   ├── notification_service.py
│   │   │   └── storage_service.py   # MinIO interface
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   ├── extraction_tasks.py
│   │   │   └── nlp_tasks.py
│   │   ├── extractors/
│   │   │   ├── base.py
│   │   │   ├── pdfminer_extractor.py
│   │   │   └── pypdf_extractor.py   # Fallback
│   │   └── nlp/
│   │       ├── pipeline.py          # spaCy + Med7 pipeline setup
│   │       ├── extractors/
│   │       │   ├── medication.py
│   │       │   ├── lab_result.py
│   │       │   ├── diagnosis.py
│   │       │   ├── allergy.py
│   │       │   ├── vitals.py
│   │       │   └── doctor.py
│   │       ├── confidence.py        # Confidence scoring
│   │       └── deduplication.py     # Cross-document entity dedup
│   ├── alembic/                     # DB migrations
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/                # Sample PDFs for testing
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── auth/               # Login, signup, OTP
│   │   │   ├── profile/            # Health profile dashboard
│   │   │   ├── timeline/           # Timeline view
│   │   │   ├── charts/             # Trends + charts
│   │   │   ├── documents/          # Document library + detail
│   │   │   └── passport/           # Passport management + public view
│   │   ├── components/
│   │   │   ├── layout/             # AppShell, NavBar, BottomNav
│   │   │   ├── profile/            # Profile cards, sections
│   │   │   ├── timeline/           # Timeline components
│   │   │   ├── charts/             # Chart components (Recharts)
│   │   │   ├── documents/          # Document cards, upload flow
│   │   │   ├── passport/           # Passport view, QR code
│   │   │   └── common/             # Buttons, badges, modals, toasts
│   │   ├── hooks/                  # React Query hooks, custom hooks
│   │   ├── lib/
│   │   │   ├── api.ts              # Axios instance + API calls
│   │   │   ├── auth.ts             # Auth0 React SDK setup
│   │   │   └── utils.ts
│   │   └── types/                  # TypeScript interfaces
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── docker-compose.yml
├── docker-compose.test.yml
├── .env.example
├── CLAUDE.md
├── STATUS.md
├── srs.md
└── docs/
```

---

### Database Schema (PostgreSQL)

All tables use UUID primary keys. PHI fields are stored encrypted at the application layer (AES-256) where noted.

#### `users`
```sql
CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth0_sub       VARCHAR(128) UNIQUE NOT NULL,  -- Auth0 subject identifier
    email           VARCHAR(255) UNIQUE,
    phone_number    VARCHAR(20),
    email_verified  BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);
CREATE INDEX idx_users_auth0_sub ON users(auth0_sub);
```

#### `family_members`
```sql
CREATE TABLE family_members (
    member_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    full_name       VARCHAR(255) NOT NULL,           -- encrypted
    relationship    VARCHAR(50) NOT NULL,             -- SELF | SPOUSE | PARENT | CHILD | OTHER
    date_of_birth   DATE,                            -- encrypted
    blood_group     VARCHAR(10),                     -- A+|A-|B+|B-|O+|O-|AB+|AB-|Unknown
    is_self         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_family_members_user_id ON family_members(user_id);
```

#### `documents`
```sql
CREATE TABLE documents (
    document_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    document_type       VARCHAR(50) NOT NULL,   -- LAB_REPORT|PRESCRIPTION|DISCHARGE|SCAN|OTHER
    document_date       DATE,
    facility_name       VARCHAR(255),
    doctor_name         VARCHAR(255),
    storage_path        VARCHAR(512) NOT NULL,  -- MinIO object key
    file_size_bytes     BIGINT,
    has_text_layer      BOOLEAN,
    processing_status   VARCHAR(30) DEFAULT 'QUEUED',  -- QUEUED|PROCESSING|COMPLETE|FAILED|MANUAL_REVIEW
    extraction_library  VARCHAR(50),            -- pdfminer|pypdf
    extracted_raw_text  TEXT,
    extraction_attempts INTEGER DEFAULT 0,
    uploaded_at         TIMESTAMPTZ DEFAULT NOW(),
    processed_at        TIMESTAMPTZ
);
CREATE INDEX idx_documents_member_id ON documents(member_id);
CREATE INDEX idx_documents_processing_status ON documents(processing_status);
```

#### `medications`
```sql
CREATE TABLE medications (
    medication_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    drug_name           VARCHAR(255) NOT NULL,
    drug_name_normalized VARCHAR(255),          -- after synonym normalization
    dosage              VARCHAR(100),
    frequency           VARCHAR(100),
    route               VARCHAR(50),
    start_date          DATE,
    end_date            DATE,
    is_active           BOOLEAN DEFAULT TRUE,
    confidence_score    VARCHAR(10) DEFAULT 'MEDIUM',  -- HIGH|MEDIUM|LOW
    is_manual_entry     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_medications_member_id ON medications(member_id);
CREATE INDEX idx_medications_is_active ON medications(is_active);
```

#### `lab_results`
```sql
CREATE TABLE lab_results (
    result_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    test_name           VARCHAR(255) NOT NULL,
    test_name_normalized VARCHAR(255),
    value               NUMERIC(12, 4),
    value_text          VARCHAR(100),           -- for non-numeric values like "Positive"
    unit                VARCHAR(50),
    reference_low       NUMERIC(12, 4),
    reference_high      NUMERIC(12, 4),
    flag                VARCHAR(20) DEFAULT 'NORMAL',  -- NORMAL|HIGH|LOW|CRITICAL
    test_date           DATE,
    confidence_score    VARCHAR(10) DEFAULT 'MEDIUM',
    is_manual_entry     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_lab_results_member_id ON lab_results(member_id);
CREATE INDEX idx_lab_results_test_name_normalized ON lab_results(test_name_normalized);
CREATE INDEX idx_lab_results_test_date ON lab_results(test_date);
```

#### `diagnoses`
```sql
CREATE TABLE diagnoses (
    diagnosis_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    condition_name      VARCHAR(255) NOT NULL,
    condition_normalized VARCHAR(255),
    icd10_code          VARCHAR(20),
    diagnosed_date      DATE,
    status              VARCHAR(20) DEFAULT 'UNKNOWN',  -- ACTIVE|RESOLVED|CHRONIC|UNKNOWN
    confidence_score    VARCHAR(10) DEFAULT 'MEDIUM',
    is_manual_entry     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_diagnoses_member_id ON diagnoses(member_id);
CREATE INDEX idx_diagnoses_status ON diagnoses(status);
```

#### `allergies`
```sql
CREATE TABLE allergies (
    allergy_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    allergen_name       VARCHAR(255) NOT NULL,
    reaction_type       VARCHAR(255),
    severity            VARCHAR(20),   -- MILD|MODERATE|SEVERE|UNKNOWN
    confidence_score    VARCHAR(10) DEFAULT 'MEDIUM',
    is_manual_entry     BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_allergies_member_id ON allergies(member_id);
```

#### `vitals`
```sql
CREATE TABLE vitals (
    vital_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    vital_type          VARCHAR(50) NOT NULL,  -- BP_SYSTOLIC|BP_DIASTOLIC|PULSE|WEIGHT|HEIGHT|BMI|SPO2|TEMPERATURE|BLOOD_SUGAR
    value               NUMERIC(8, 2) NOT NULL,
    unit                VARCHAR(30),
    recorded_date       DATE,
    confidence_score    VARCHAR(10) DEFAULT 'MEDIUM',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_vitals_member_id ON vitals(member_id);
CREATE INDEX idx_vitals_type_date ON vitals(vital_type, recorded_date);
```

#### `doctors`
```sql
CREATE TABLE doctors (
    doctor_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    doctor_name         VARCHAR(255),
    specialization      VARCHAR(255),
    facility_name       VARCHAR(255),
    visit_date          DATE,
    confidence_score    VARCHAR(10) DEFAULT 'MEDIUM',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_doctors_member_id ON doctors(member_id);
```

#### `procedures`
```sql
CREATE TABLE procedures (
    procedure_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    document_id         UUID REFERENCES documents(document_id) ON DELETE SET NULL,
    procedure_name      VARCHAR(255) NOT NULL,
    procedure_date      DATE,
    outcome             TEXT,
    confidence_score    VARCHAR(10) DEFAULT 'MEDIUM',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_procedures_member_id ON procedures(member_id);
```

#### `shared_passports`
```sql
CREATE TABLE shared_passports (
    passport_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id           UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    is_active           BOOLEAN DEFAULT TRUE,
    expires_at          TIMESTAMPTZ,
    visible_sections    JSONB DEFAULT '["conditions","medications","allergies","labs","vitals","last_visit"]'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at    TIMESTAMPTZ,
    access_count        INTEGER DEFAULT 0
);
CREATE INDEX idx_passports_member_id ON shared_passports(member_id);
CREATE INDEX idx_passports_is_active ON shared_passports(is_active);
```

#### `passport_access_log`
```sql
CREATE TABLE passport_access_log (
    log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    passport_id         UUID NOT NULL REFERENCES shared_passports(passport_id) ON DELETE CASCADE,
    accessed_at         TIMESTAMPTZ DEFAULT NOW(),
    ip_hash             VARCHAR(64)   -- SHA-256 of IP, never store raw IP
);
CREATE INDEX idx_passport_access_passport_id ON passport_access_log(passport_id);
```

#### `correction_audit`
```sql
CREATE TABLE correction_audit (
    audit_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type         VARCHAR(50) NOT NULL,   -- medication|lab_result|diagnosis|allergy|vital
    entity_id           UUID NOT NULL,
    field_name          VARCHAR(100) NOT NULL,
    old_value           TEXT,
    new_value           TEXT,
    corrected_by        UUID REFERENCES users(user_id),
    corrected_at        TIMESTAMPTZ DEFAULT NOW()
);
```

---

### API Endpoint Catalog

Base URL: `/api/v1`
All endpoints require `Authorization: Bearer <Auth0 JWT>` unless marked `[PUBLIC]`.

#### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/auth/provision` | Called after Auth0 login; creates user record if first login |
| GET | `/auth/me` | Returns current user and their family members |

#### Family Members
| Method | Path | Description |
|---|---|---|
| GET | `/family` | List all family members for authenticated user |
| POST | `/family` | Add a new family member |
| GET | `/family/{member_id}` | Get a single family member |
| PUT | `/family/{member_id}` | Update family member details |
| DELETE | `/family/{member_id}` | Remove member + all associated data |

#### Documents
| Method | Path | Description |
|---|---|---|
| POST | `/documents/upload` | Upload PDF (multipart/form-data); returns doc_id + processing status |
| GET | `/documents?member_id=&type=&status=` | List documents for a member |
| GET | `/documents/{doc_id}` | Get document metadata + extraction status |
| GET | `/documents/{doc_id}/download` | Download original PDF (signed MinIO URL) |
| PATCH | `/documents/{doc_id}` | Update document type or date |
| DELETE | `/documents/{doc_id}` | Delete document + all extracted data |
| POST | `/documents/{doc_id}/retry` | Re-queue failed extraction job |

#### Health Profile
| Method | Path | Description |
|---|---|---|
| GET | `/profile/{member_id}` | Full aggregated health profile |
| GET | `/profile/{member_id}/summary` | Summary card (name, age, blood group, conditions, allergies) |
| POST | `/profile/{member_id}/medications` | Manually add a medication |
| PUT | `/profile/{member_id}/medications/{med_id}` | Edit or correct a medication |
| DELETE | `/profile/{member_id}/medications/{med_id}` | Delete a medication entry |
| PATCH | `/profile/{member_id}/medications/{med_id}/discontinue` | Mark medication as discontinued |
| POST | `/profile/{member_id}/diagnoses` | Manually add a diagnosis |
| PUT | `/profile/{member_id}/diagnoses/{diag_id}` | Edit a diagnosis |
| DELETE | `/profile/{member_id}/diagnoses/{diag_id}` | Delete a diagnosis |
| POST | `/profile/{member_id}/allergies` | Manually add an allergy |
| PUT | `/profile/{member_id}/allergies/{allergy_id}` | Edit an allergy |
| DELETE | `/profile/{member_id}/allergies/{allergy_id}` | Delete an allergy |

#### Timeline
| Method | Path | Description |
|---|---|---|
| GET | `/timeline/{member_id}?type=&from=&to=&page=&limit=` | Paginated chronological events |

#### Charts
| Method | Path | Description |
|---|---|---|
| GET | `/charts/{member_id}/lab-trends?test_name=&from=&to=` | Time-series data for a lab parameter |
| GET | `/charts/{member_id}/lab-parameters` | List lab parameters with ≥2 data points |
| GET | `/charts/{member_id}/medications-gantt` | Medication active periods for Gantt |
| GET | `/charts/{member_id}/vitals?vital_type=&from=&to=` | Vitals time-series |

#### Health Passport
| Method | Path | Description |
|---|---|---|
| POST | `/passport` | Generate a new passport |
| GET | `/passport?member_id=` | List passports for a member |
| PUT | `/passport/{passport_id}` | Update passport settings (expiry, sections) |
| DELETE | `/passport/{passport_id}` | Revoke passport |
| GET | `/passport/public/{uuid}` | [PUBLIC] View health passport (no auth) |

#### Account
| Method | Path | Description |
|---|---|---|
| DELETE | `/account` | Initiate account deletion |
| POST | `/account/export` | Request data export |

---

### Service Contracts

#### Document Upload Flow
```
POST /documents/upload
Content-Type: multipart/form-data
Body: { file: <PDF binary>, member_id: UUID, document_type?: string, document_date?: date }

Response 202 Accepted:
{ document_id: UUID, processing_status: "QUEUED", message: "Document queued for processing" }

Response 400:
{ error: "INVALID_FORMAT", message: "MediVault accepts PDF files only." }
{ error: "SCANNED_DOCUMENT", message: "This appears to be a scanned document..." }
{ error: "FILE_TOO_LARGE", message: "File exceeds 20MB limit." }
{ error: "VIRUS_DETECTED", message: "File failed security scan." }
```

#### Public Passport View
```
GET /passport/public/{uuid}

Response 200:
{
  patient_name: string,
  age: number,
  blood_group: string,
  generated_at: ISO8601,
  disclaimer: "Patient-reported data — not clinically verified",
  sections: {
    conditions: [...],
    medications: [...],
    allergies: [...],
    recent_labs: [...],
    last_visit: {...}
  }
}

Response 404: { error: "NOT_FOUND" }
Response 410: { error: "EXPIRED", message: "This health passport has expired." }
Response 403: { error: "REVOKED", message: "This health passport is no longer active." }
```

---

### Async Processing Pipeline

```
1. Document upload accepted → document_id created, status=QUEUED
2. Celery task enqueued: extract_document.apply_async(args=[document_id], countdown=0)
3. Worker: fetch PDF from MinIO → run pdfminer.six
   - On success: store raw_text, enqueue NLP task
   - On failure: increment extraction_attempts
     - If attempts < 3: re-queue with exponential backoff (30s, 90s, 270s)
     - If attempts = 3: status=FAILED, send failure notification
4. Celery task: process_nlp.apply_async(args=[document_id])
5. NLP worker: run spaCy+Med7 pipeline → store entities → update profile
6. status=COMPLETE, send completion notification
```

---

### NLP Pipeline Detail

```python
# Pipeline stages (applied in order):
1. doc = nlp(raw_text)              # spaCy tokenization + Med7 NER
2. medication_extractor(doc)         # Med7 entities: DRUG, STRENGTH, FORM, FREQUENCY, ROUTE, DURATION, DOSAGE
3. lab_result_extractor(doc)         # Rule-based: "Test: Value Unit (Range)"
4. diagnosis_extractor(doc)          # Med7 + custom rules for condition names
5. allergy_extractor(doc)            # Pattern: "allergic to X", "allergy: X"
6. vitals_extractor(doc)             # Pattern: "BP: 120/80", "Weight: 70kg"
7. doctor_extractor(doc)             # Pattern: "Dr. [Name]", facility name NER
8. confidence_scorer(entities)       # HIGH: structured field in table; MEDIUM: clear sentence; LOW: ambiguous
9. deduplicator(entities, member_id) # Check existing diagnoses/medications for duplicates
```

**Med7 entity types:** `DRUG`, `STRENGTH`, `FORM`, `FREQUENCY`, `ROUTE`, `DURATION`, `DOSAGE`

**Confidence scoring rules:**
- `HIGH`: entity found in a structured table (lab report table rows, prescription table)
- `MEDIUM`: entity found in a clear declarative sentence with expected context
- `LOW`: entity extracted from free text with low surrounding context or ambiguous phrasing

---

### Authentication Flow

```
1. Frontend: Auth0 Universal Login → user logs in
2. Auth0 issues: access_token (JWT, RS256, 1hr TTL) + refresh_token (30 days)
3. Frontend sends: Authorization: Bearer <access_token> on every API request
4. API Gateway middleware: validates JWT signature using Auth0 JWKS endpoint
5. Extracts auth0_sub from token claims
6. Calls /auth/provision if first login (creates user row in users table)
7. Injects user_id into request context for downstream handlers
8. Token refresh: Auth0 React SDK handles silently in background
```

---

### Environment Variables

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/medivault
REDIS_URL=redis://redis:6379/0
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=medivault-documents
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.medivault.local
ENCRYPTION_KEY=...              # AES-256 key for PHI field encryption
SENDGRID_API_KEY=...
ENVIRONMENT=development

# Frontend
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=...
VITE_AUTH0_AUDIENCE=https://api.medivault.local
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

### Security Considerations for Developer

1. **PHI Encryption at rest:** `full_name`, `date_of_birth` in `family_members` must be encrypted at the application layer using the `ENCRYPTION_KEY` before storage. Use a field-level encryption utility, not database-level.
2. **Storage isolation:** All MinIO objects must use path prefix `{user_id}/{member_id}/` to enforce per-user isolation. Never use shared paths.
3. **Passport URL entropy:** `passport_id` uses PostgreSQL `gen_random_uuid()` (128-bit) — never use sequential IDs.
4. **IP logging:** In `passport_access_log`, store `SHA-256(ip_address)` — never store raw IP addresses.
5. **No PHI in logs:** Application logs must never contain medical data, names, or document content. Log only IDs and statuses.
6. **Rate limiting:** Auth endpoints: 10 req/min per IP. Upload endpoint: 20 req/min per user. Public passport: 60 req/min per IP.
7. **Virus scanning:** Use ClamAV (runs in Docker) for all uploaded files before any processing.
8. **CORS:** API Gateway allows requests only from the configured frontend origin. Never `*`.
