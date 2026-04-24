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
│                    │  pdfminer.six → spaCy+scispaCy  │       │
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
| **Celery Worker** | Python, Celery 5, Redis broker | Async document processing: pdfminer.six extraction + spaCy+scispaCy NLP. |
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
│   │   │   ├── family.py            # Family member endpoints
│   │   │   ├── onboarding.py        # Onboarding endpoints
│   │   │   ├── provider.py          # Provider workflow endpoints
│   │   │   ├── family_circle.py     # Family Circle endpoints
│   │   │   ├── notifications.py     # Notification endpoints
│   │   │   ├── entity_crud.py       # Generic entity CRUD endpoints
│   │   │   ├── corrections.py       # Entity correction endpoints
│   │   │   └── export.py            # Data export endpoints
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
│   │   │   ├── passport.py
│   │   │   ├── family_circle.py     # Family, FamilyInvitation, FamilyMembership, VaultAccessGrant
│   │   │   ├── notification.py
│   │   │   ├── provider_profile.py
│   │   │   ├── provider_access_request.py
│   │   │   ├── medical_encounter.py
│   │   │   ├── auth_audit.py
│   │   │   └── correction_audit.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── document_service.py
│   │   │   ├── extraction_service.py
│   │   │   ├── nlp_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── passport_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── storage_service.py   # MinIO interface
│   │   │   ├── audit_service.py
│   │   │   ├── deduplication_service.py
│   │   │   └── pubsub.py
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   ├── extraction_tasks.py
│   │   │   ├── nlp_tasks.py
│   │   │   ├── export_tasks.py
│   │   │   ├── health_tasks.py
│   │   │   └── onboarding_tasks.py
│   │   ├── extractors/
│   │   │   ├── base.py
│   │   │   ├── pdfminer_extractor.py
│   │   │   └── pypdf_extractor.py   # Fallback
│   │   └── nlp/
│   │       ├── pipeline.py          # spaCy + scispaCy (en_ner_bc5cdr_md) pipeline setup
│   │       ├── medication_extractor.py
│   │       ├── lab_extractor.py
│   │       ├── diagnosis_extractor.py
│   │       ├── allergy_extractor.py
│   │       ├── vitals_extractor.py
│   │       ├── doctor_extractor.py
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
│   │   │   ├── passport/           # Passport overview — default route / + public view
│   │   │   ├── records/            # Timeline-only view (route: /records, per DECISION-012)
│   │   │   ├── dashboard/          # Health profile deep-view (route: /health)
│   │   │   ├── settings/           # Account settings (route: /settings)
│   │   │   ├── family/             # FamilyCirclePage, InviteAcceptancePage, VaultAccessPanel
│   │   │   ├── onboarding/         # OnboardingPage
│   │   │   └── provider/           # ProviderDashboardPage, ProviderPatientPage
│   │   │   {Note: / → PassportPage, /health → DashboardPage, /insights redirects to /health}
│   │   ├── components/
│   │   │   ├── layout/             # AppShell, NavBar, BottomNav
│   │   │   ├── profile/            # Profile cards, sections
│   │   │   ├── timeline/           # Timeline components
│   │   │   ├── charts/             # Chart components (Recharts)
│   │   │   ├── documents/          # Document cards, upload flow
│   │   │   ├── passport/           # Passport view, QR code
│   │   │   └── common/             # Buttons, badges, modals, toasts, NotificationCentre.tsx
│   │   ├── hooks/                  # React Query hooks, custom hooks
│   │   │   ├── useFamilyCircle.ts
│   │   │   └── useNotifications.ts
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
    role                VARCHAR(20) DEFAULT 'PATIENT',   -- PATIENT|PROVIDER
    onboarding_completed BOOLEAN DEFAULT FALSE,
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
    height_cm       FLOAT,
    weight_kg       FLOAT,
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
    encounter_id        UUID REFERENCES medical_encounters(encounter_id),
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
    encounter_id        UUID REFERENCES medical_encounters(encounter_id),
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

#### `families`
```sql
-- One family per account owner. The owner is the sole admin by default.
CREATE TABLE families (
    family_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(200),                                -- optional display name, e.g. "The Mehta Family"
    created_by_user_id  UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `family_invitations`
```sql
-- Tracks every invitation sent by the owner. Supports both existing users and new users.
CREATE TABLE family_invitations (
    invitation_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id           UUID NOT NULL REFERENCES families(family_id) ON DELETE CASCADE,
    invited_by_user_id  UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    invited_email       VARCHAR(320) NOT NULL,
    invited_user_id     UUID REFERENCES users(user_id) ON DELETE SET NULL,  -- NULL if invitee has no account yet
    relationship        VARCHAR(50) NOT NULL,        -- PARENT|SPOUSE|CHILD|SIBLING|OTHER
    status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING|ACCEPTED|DECLINED|EXPIRED|REVOKED
    token               UUID NOT NULL DEFAULT gen_random_uuid(), -- used in /invite/:token deep link
    expires_at          TIMESTAMPTZ NOT NULL,                    -- 7 days from creation
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_family_invitations_token ON family_invitations(token);
CREATE INDEX idx_family_invitations_family_id ON family_invitations(family_id);
CREATE INDEX idx_family_invitations_invited_email ON family_invitations(invited_email);
```

#### `family_memberships`
```sql
-- Created when an invitee accepts an invitation. One row per (family, user) pair.
CREATE TABLE family_memberships (
    membership_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id           UUID NOT NULL REFERENCES families(family_id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role                VARCHAR(20) NOT NULL DEFAULT 'MEMBER',  -- ADMIN|MEMBER
    can_invite          BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at           TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (family_id, user_id)
);
CREATE INDEX idx_family_memberships_user_id ON family_memberships(user_id);
```

#### `vault_access_grants`
```sql
-- Explicit READ grants: grantee can view target's vault.
-- Accepting a family invitation does NOT auto-create a grant.
CREATE TABLE vault_access_grants (
    grant_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    family_id           UUID NOT NULL REFERENCES families(family_id) ON DELETE CASCADE,
    grantee_user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,  -- who can view
    target_user_id      UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,  -- whose vault
    access_type         VARCHAR(20) NOT NULL DEFAULT 'READ',    -- READ only in V1
    granted_by_user_id  UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    granted_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (family_id, grantee_user_id, target_user_id)
);
CREATE INDEX idx_vault_access_grants_grantee ON vault_access_grants(grantee_user_id);
CREATE INDEX idx_vault_access_grants_target ON vault_access_grants(target_user_id);
```

#### `notifications`
```sql
-- In-app notification inbox per user.
CREATE TABLE notifications (
    notification_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type                VARCHAR(50) NOT NULL,         -- FAMILY_INVITE|INVITE_ACCEPTED|INVITE_DECLINED|VAULT_ACCESS_GRANTED|VAULT_ACCESS_REVOKED|PROCESSING_COMPLETE|EXTRACTION_FAILED
    title               VARCHAR(200) NOT NULL,
    body                TEXT NOT NULL,
    is_read             BOOLEAN NOT NULL DEFAULT FALSE,
    action_url          VARCHAR(512),                 -- deep link e.g. /family, /invite/:token
    metadata            JSONB,                        -- e.g. { invitation_id, inviter_name }
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(user_id, is_read);
```

#### `provider_profiles`
```sql
CREATE TABLE provider_profiles (
    profile_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    licence_number      VARCHAR(100),
    registration_council VARCHAR(200),
    licence_verified    BOOLEAN DEFAULT FALSE,
    verification_status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING|VERIFIED|REJECTED
    verified_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `provider_access_requests`
```sql
CREATE TABLE provider_access_requests (
    request_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_user_id    UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    patient_member_id   UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    passport_id_used    UUID REFERENCES shared_passports(passport_id),
    notification_id     UUID REFERENCES notifications(notification_id),
    status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING|ACCEPTED|DECLINED|EXPIRED
    requested_at        TIMESTAMPTZ DEFAULT NOW(),
    responded_at        TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ NOT NULL      -- 15 minutes from creation
);
CREATE INDEX idx_provider_access_requests_provider ON provider_access_requests(provider_user_id);
CREATE INDEX idx_provider_access_requests_patient ON provider_access_requests(patient_member_id);
```

#### `medical_encounters`
```sql
CREATE TABLE medical_encounters (
    encounter_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_user_id    UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    patient_member_id   UUID NOT NULL REFERENCES family_members(member_id) ON DELETE CASCADE,
    access_request_id   UUID REFERENCES provider_access_requests(request_id),
    encounter_date      DATE NOT NULL,
    chief_complaint     TEXT,
    diagnosis_notes     TEXT,
    prescriptions_note  TEXT,
    follow_up_date      DATE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_encounters_provider ON medical_encounters(provider_user_id);
CREATE INDEX idx_encounters_patient ON medical_encounters(patient_member_id);
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
| GET | `/profile/{member_id}/encounters` | List medical encounters for a patient member |

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

#### Onboarding
| Method | Path | Description |
|---|---|---|
| GET | `/auth/onboarding/status` | Return onboarding_completed flag and role |
| POST | `/auth/onboarding` | Complete onboarding (DOB, blood group, height, weight, allergies, role; creates ProviderProfile if PROVIDER) |

#### Provider Workflow
| Method | Path | Description |
|---|---|---|
| POST | `/provider/patient-lookup` | Validate passport UUID, create PENDING access request, notify patient |
| GET | `/provider/access-requests/{request_id}/status` | Poll access request status (PENDING/ACCEPTED/DECLINED/EXPIRED) |
| POST | `/provider/access-requests/{request_id}/respond` | Patient accepts or declines provider access request |
| GET | `/provider/patient/{request_id}` | Get full patient clinical data (only if ACCEPTED) |
| POST | `/provider/encounters` | Log a medical encounter (diagnosis, prescriptions, follow-up) |
| GET | `/provider/patient/{request_id}/encounters` | List encounters for an access request |

#### Family Circle
| Method | Path | Description |
|---|---|---|
| GET | `/family/circle` | Get the caller's family: memberships + managed profiles + pending invitations |
| POST | `/family/invitations` | Send a family invitation (email + relationship) |
| GET | `/family/invitations` | List all invitations sent by the caller |
| DELETE | `/family/invitations/{invitation_id}` | Cancel / revoke a pending invitation |
| POST | `/family/invitations/{invitation_id}/resend` | Resend the invitation email |
| GET | `/invite/{token}` | [PUBLIC] Resolve an invitation token → returns invitation details |
| POST | `/invite/{token}/accept` | Accept an invitation (caller becomes a family member) |
| POST | `/invite/{token}/decline` | Decline an invitation |
| DELETE | `/family/memberships/{membership_id}` | Leave a family (member removes themselves) |
| DELETE | `/family/members/{user_id}` | Remove a member from the family (admin only) |

#### Vault Access Grants
| Method | Path | Description |
|---|---|---|
| GET | `/family/access` | List all vault access grants in the caller's family |
| POST | `/family/access` | Create a vault access grant (admin only) |
| DELETE | `/family/access/{grant_id}` | Revoke a vault access grant (admin only) |
| PATCH | `/family/memberships/{membership_id}/can-invite` | Toggle can_invite flag for a member (admin only) |

#### Notifications
| Method | Path | Description |
|---|---|---|
| GET | `/notifications` | List notifications for the caller (paginated, newest first) |
| GET | `/notifications/unread-count` | Return count of unread notifications |
| PATCH | `/notifications/{notification_id}/read` | Mark a single notification as read |
| POST | `/notifications/read-all` | Mark all notifications as read |
| DELETE | `/notifications/{notification_id}` | Delete a notification |

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
5. NLP worker: run spaCy+scispaCy pipeline → store entities → update profile
6. status=COMPLETE, send completion notification
```

---

### NLP Pipeline Detail

```python
# Pipeline stages (applied in order):
1. doc = nlp(raw_text)              # spaCy tokenization + scispaCy (en_ner_bc5cdr_md) NER
2. medication_extractor(doc)         # scispaCy CHEMICAL→DRUG label remap + rule-based STRENGTH, FORM, FREQUENCY, ROUTE, DURATION, DOSAGE
3. lab_result_extractor(doc)         # Rule-based: "Test: Value Unit (Range)"
4. diagnosis_extractor(doc)          # scispaCy DISEASE→DIAGNOSIS label remap + custom rules for condition names
5. allergy_extractor(doc)            # Pattern: "allergic to X", "allergy: X"
6. vitals_extractor(doc)             # Pattern: "BP: 120/80", "Weight: 70kg"
7. doctor_extractor(doc)             # Pattern: "Dr. [Name]", facility name NER
8. confidence_scorer(entities)       # HIGH: structured field in table; MEDIUM: clear sentence; LOW: ambiguous
9. deduplicator(entities, member_id) # Check existing diagnoses/medications for duplicates
```

**scispaCy (en_ner_bc5cdr_md) entity types (remapped):** `CHEMICAL`→`DRUG`, `DISEASE`→`DIAGNOSIS`
**Rule-based entity types:** `STRENGTH`, `FORM`, `FREQUENCY`, `ROUTE`, `DURATION`, `DOSAGE`

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
9. Role-based routing: after provision, if onboarding_completed=false, frontend redirects to /onboarding
10. After onboarding, PROVIDER role users see an additional "Provider" tab in the navigation
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
