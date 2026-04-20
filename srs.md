# MediVault
## Personal Medical Records Platform
### Software Requirements Specification (SRS)
**Version 1.2 | March 2026**
*Classification: Internal / Confidential*

| Document Type | Version | Date | Status |
|---|---|---|---|
| SRS | 1.2 | March 2026 | **Draft** |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Features and Functional Requirements](#3-system-features-and-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [System Architecture Overview](#5-system-architecture-overview)
6. [Data Model](#6-data-model)
7. [UI/UX Requirements](#7-uiux-requirements)
8. [External Interface Requirements](#8-external-interface-requirements)
9. [Testing Requirements](#9-testing-requirements)
10. [MVP Definition and Phased Roadmap](#10-mvp-definition-and-phased-roadmap)
11. [Open Issues and Decisions Pending](#11-open-issues-and-decisions-pending)
12. [Revision History](#12-revision-history)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the complete functional and non-functional requirements for MediVault — a patient-centric, web-based Personal Medical Records Platform. The document serves as the authoritative reference for design, development, testing, and stakeholder alignment throughout the software development lifecycle.

MediVault enables individuals to upload, parse, and visualize their complete medical history — prescriptions, lab reports, diagnostic scans, discharge summaries — in a single unified profile accessible from any device via a browser.

### 1.2 Scope

MediVault is a Progressive Web Application (PWA) accessible via modern desktop and mobile browsers. It is not a hospital information system, an EMR, or a clinical workflow tool. It is exclusively patient-owned infrastructure — no hospital or clinic integration is required.

**In scope for Version 1.0:**

- Document upload and management (digital-origin PDFs only)
- Server-side PDF text extraction pipeline (Apache Tika / PDFBox / pdfminer)
- Automated medical data parsing and structuring via NLP
- Patient health profile dashboard
- Visual health timeline (chronological)
- Diagnostic and medication trend charts
- Shareable read-only health summary
- User onboarding flow (health baseline, role selection, provider licence verification)
- Provider / doctor workflow: passport-based patient lookup with patient consent gate, clinical view, encounter logging, treatment pathway graph

> **V1 Feature Gate — Document Extraction UI:** The PDF upload + NLP extraction pipeline code is complete and tested. For the V1.0 launch the upload UI entry point shows a "Coming Soon" state; the backend pipeline remains in place and will be enabled in a subsequent release without code changes.

**Out of scope for Version 1.0:**

- Image-based document upload (JPEG, PNG, HEIC) — deferred to V2
- Handwritten prescription parsing — deferred to V2
- Cloud OCR for scanned or image-based PDFs — deferred to V2
- Real-time wearable or IoT data ingestion
- Integration with hospital EMR/EHR systems
- Insurance claim processing
- Backend hosted on cloud infrastructure (AWS / GCP)

> **V1 Assumption:** All uploaded documents are digital-origin PDFs with embedded, machine-readable text. This covers the vast majority of documents issued by organized clinics, labs, and hospitals in India (Apollo, Fortis, SRL, Metropolis, etc.).

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|---|---|
| **PDF Extraction** | Server-side parsing of machine-readable text embedded in digital-origin PDF files — no OCR required |
| **Apache Tika** | Open-source content detection and text extraction library supporting PDF and other document formats |
| **PDFBox** | Apache library for working with PDF documents; used for text extraction from digital PDFs |
| **pdfminer** | Python library for extracting text and metadata from PDF files |
| **PWA** | Progressive Web Application — web app installable on mobile with native-like experience |
| **Health Profile** | The structured, patient-owned record assembled from all uploaded documents |
| **Health Passport** | A shareable, read-only snapshot of critical health information for clinician use |
| **Parser** | Automated module that extracts structured fields (medications, values, dates) from raw extracted text |
| **PHI** | Protected Health Information — any data that can identify a patient's health status |
| **NER** | Named Entity Recognition — NLP technique to identify medical terms in unstructured text |
| **NLP** | Natural Language Processing — used to extract structured medical entities from raw text |
| **V1** | Version 1 — the initial product release as scoped in this document |
| **MVP** | Minimum Viable Product — smallest feature set that delivers meaningful user value |
| **OCR** | Optical Character Recognition — NOT used in V1; deferred to V2 for scanned/image documents |

### 1.4 Document Conventions

Requirements are identified using the format `[MODULE-TYPE-NUMBER]`:

- `FR` = Functional Requirement
- `NFR` = Non-Functional Requirement
- `CON` = Constraint
- Priority levels: **High** / **Medium** / **Low**
- Phases: `V1-MVP` / `V1` / `V2`

### 1.5 References

- IEEE Std 830-1998: Recommended Practice for Software Requirements Specifications
- OWASP Web Application Security Guidelines
- India Personal Data Protection Bill (2023) — health data obligations
- ABDM (Ayushman Bharat Digital Mission) Health Data Management Policy
- Apache Tika Documentation — https://tika.apache.org
- Apache PDFBox Documentation — https://pdfbox.apache.org
- HL7 FHIR R4 — standard for health data interoperability (future reference)

---

## 2. Overall Description

### 2.1 Product Perspective

MediVault is a standalone, patient-facing web application. It operates independently of any healthcare provider infrastructure. The system interfaces with:

- The patient's device (browser file picker for PDF uploads)
- A backend PDF text extraction pipeline (Apache Tika or PDFBox — no external API calls)
- A backend NLP processing pipeline for medical data parsing and storage
- The patient's browser for rendering the health dashboard

MediVault does not interface with cloud OCR APIs, hospital software, payment systems, insurance networks, or government health registries in Version 1.

### 2.2 Product Functions — High Level

| # | Function | Description |
|---|---|---|
| **1** | **Ingest** | Accept digital-origin PDF documents uploaded by the patient |
| **2** | **Extract** | Parse embedded PDF text using server-side extraction libraries + NLP to identify structured medical data |
| **3** | **Profile** | Assemble extracted data into a unified, searchable patient health profile |
| **4** | **Visualize** | Display the health profile as timeline, charts, and a shareable health passport |

### 2.3 User Classes and Characteristics

#### 2.3.1 Primary User — Patient / Individual

| Attribute | Detail |
|---|---|
| **Tech Literacy** | Moderate — comfortable with smartphones, WhatsApp, basic apps |
| **Age Range** | 0–100 years (primary); family account management for elderly |
| **Motivation** | Avoid carrying paper files; have history ready at any doctor visit |
| **Device** | Android/iOS smartphone (primary); laptop/desktop (secondary) |
| **Upload Frequency** | Episodic — after each doctor visit or lab test (not daily) |
| **Pain Point** | Cannot recall medications, past diagnoses, or test values under pressure |

#### 2.3.2 Secondary User — Healthcare Provider (Doctor / Clinician)

| Attribute | Detail |
|---|---|
| **Interaction Type** | Active — registers a MediVault account with PROVIDER role; verifies medical licence at onboarding |
| **Action** | Enters patient's Health Passport UUID to request a consent-gated clinical view; logs medical encounters |
| **Motivation** | Access structured patient history instantly at the point of care; create a digital record of the visit |
| **Constraint** | Must have a verified Indian medical licence (NMC registry) before using patient-lookup features |
| **Device** | Desktop primary (clinic setting); mobile secondary |

#### 2.3.2b Legacy Secondary User — Attending Clinician (Public Passport, Read-Only)

| Attribute | Detail |
|---|---|
| **Interaction Type** | Passive — receives a shared link or QR from the patient |
| **Action** | Views read-only public health passport; no account or login required |
| **Motivation** | Quick glance at patient history without needing a MediVault account |
| **Constraint** | Zero onboarding required; sees limited summary only (no timeline, no encounter logging) |

#### 2.3.3 System Administrator

| Attribute | Detail |
|---|---|
| **Role** | Internal operations team managing infrastructure, compliance, abuse |
| **Access** | Admin console (not part of V1 patient-facing SRS) |
| **Responsibility** | Data integrity, uptime monitoring, extraction pipeline health |

### 2.4 Operating Environment

- Web application — runs in modern browsers (Chrome 90+, Safari 14+, Firefox 88+, Edge 90+)
- Responsive design — fully functional on mobile viewports (320px and above)
- PDF text extraction runs entirely server-side — no external API dependencies for V1
- No native app required — browser-only for V1

### 2.5 Assumptions and Dependencies

#### 2.5.1 Assumptions

- All uploaded documents are **digital-origin PDFs** with embedded machine-readable text (not scanned or photographed)
- Digital-origin PDFs cover the large majority of documents from organized Indian clinics, hospitals, and diagnostic labs
- Users have a stable internet connection during upload and initial processing
- Documents are primarily in English; Hindi support considered for V2
- Users are responsible for the accuracy of documents they upload

#### 2.5.2 Dependencies

| Dependency | Purpose |
|---|---|
| Apache Tika or PDFBox (Java) / pdfminer (Python) | Server-side PDF text extraction — no external API |
| PDF.js | Client-side PDF preview rendering in browser |
| spaCy + Med7 | NLP/NER for medical entity extraction from raw text (self-hosted; PHI stays on-infrastructure) |
| pdfminer.six | Primary PDF text extraction library (Python-native; superior layout/tabular extraction for Indian medical PDFs) |
| Auth0 | Authentication provider — OAuth 2.0, OIDC, JWT; supports email/password, Google OAuth, phone OTP |
| MinIO | Local S3-compatible object storage for encrypted PDF files |

### 2.6 Constraints

- `[CON-001]` The system must not share or sell patient data to any third party
- `[CON-002]` All PHI must be encrypted at rest (AES-256) and in transit (TLS 1.3)
- `[CON-003]` Raw uploaded documents must be stored in the patient's isolated storage partition
- `[CON-004]` System must comply with India's Digital Personal Data Protection Act (DPDPA) 2023
- `[CON-005]` V1 accepts **only digital-origin PDFs** — no image uploads, no cloud OCR dependencies
- `[CON-006]` PDF text extraction must run entirely on the system's own backend infrastructure — no PHI transmitted to external extraction APIs in V1
- `[CON-007]` No hospital or third-party system integration in V1

---

## 3. System Features and Functional Requirements

### 3.1 User Authentication and Account Management

#### 3.1.1 Description

All patient data is private and requires authenticated access. The system supports secure sign-up, login, session management, and account deletion.

#### 3.1.2 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-AUTH-001 | System shall support sign-up via email and password | **High** | V1-MVP |
| FR-AUTH-002 | System shall support sign-in via Google OAuth 2.0 | **High** | V1-MVP |
| FR-AUTH-003 | System shall support sign-in via phone number + OTP (India) | **High** | V1-MVP |
| FR-AUTH-004 | System shall enforce email verification before granting full access | **High** | V1-MVP |
| FR-AUTH-005 | System shall support password reset via email link | **High** | V1-MVP |
| FR-AUTH-006 | System shall support multi-factor authentication (TOTP or SMS OTP) | **Medium** | V1 |
| FR-AUTH-007 | System shall allow users to delete their account and all associated data | **High** | V1 |
| FR-AUTH-008 | Sessions shall expire after 30 days of inactivity | **High** | V1-MVP |
| FR-AUTH-009 | System shall log all authentication events with IP, timestamp, device fingerprint | **Medium** | V1 |

---

### 3.2 Document Upload and Management

#### 3.2.1 Description

The document upload module is the primary data ingestion point. Patients upload digital-origin PDF documents — prescriptions, lab reports, discharge summaries, diagnostic reports — which are then processed by the server-side extraction pipeline.

> **V1 Scope Note:** Only digital-origin PDFs are accepted in V1. Image files (JPEG, PNG, HEIC) and scanned PDFs require OCR and are deferred to V2.

#### 3.2.2 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-DOC-001 | System shall accept digital-origin PDF documents up to 20MB per file | **High** | V1-MVP |
| FR-DOC-002 | System shall reject non-PDF file formats with a clear error message explaining V1 scope | **High** | V1-MVP |
| FR-DOC-003 | System shall detect and reject scanned/image-based PDFs (no embedded text layer) with a user-friendly message | **High** | V1-MVP |
| FR-DOC-004 | System shall support multi-file upload (up to 10 PDFs simultaneously) | **Medium** | V1 |
| FR-DOC-005 | System shall display a real-time upload progress indicator | **Medium** | V1-MVP |
| FR-DOC-006 | System shall allow users to assign a document type at upload (Lab Report, Prescription, Discharge Summary, Scan/Imaging, Other) | **High** | V1-MVP |
| FR-DOC-007 | System shall allow users to assign a document date if not auto-detected from the PDF | **High** | V1-MVP |
| FR-DOC-008 | System shall store the original uploaded PDF and provide download access to the patient | **High** | V1-MVP |
| FR-DOC-009 | System shall display a document library listing all uploaded files with type, date, and processing status | **High** | V1-MVP |
| FR-DOC-010 | System shall allow patients to delete any uploaded document and its extracted data | **High** | V1 |
| FR-DOC-011 | System shall allow patients to manually correct auto-extracted fields on any document | **High** | V1 |
| FR-DOC-012 | System shall virus-scan all uploaded files before processing | **High** | V1-MVP |
| FR-DOC-013 | System shall reject documents that fail format or content validation with a clear error message | **High** | V1-MVP |

---

### 3.3 PDF Text Extraction Pipeline

#### 3.3.1 Description

Upon upload, documents enter an asynchronous server-side processing pipeline. All text extraction in V1 is performed using PDF parsing libraries running on the application's own backend infrastructure — no external API calls are made. Extracted raw text is then passed to the medical NLP parser.

**V1 uses only digital-origin PDFs.** These are PDFs generated by hospital software, diagnostic lab report systems, or clinic management software — they contain an embedded text layer that can be extracted directly and reliably without any image recognition.

#### 3.3.2 Library Options (to be finalised at implementation)

| Library | Language | Notes |
|---|---|---|
| **Apache Tika** | Java / REST API wrapper | Broad format support, production-grade, REST server mode available for language-agnostic use |
| **Apache PDFBox** | Java | Fine-grained PDF control, good for structured medical PDFs |
| **pdfminer.six** | Python | Strong layout-aware text extraction, excellent for tabular lab report formats |
| **pypdf** | Python | Lightweight and fast for simple text extraction |

> **Decision:** `pdfminer.six` is the selected extraction library. The backend is Python (FastAPI), making pdfminer.six the native choice. It provides superior layout-aware and positional text extraction — critical for tabular lab report formats common in Indian diagnostic PDFs (SRL, Metropolis, Thyrocare). Apache Tika or pypdf serve as fallback libraries if pdfminer.six fails on a specific document.

#### 3.3.3 Processing Flow

1. Patient uploads PDF via browser
2. Backend validates file: format check → virus scan → embedded text detection
3. If no embedded text layer detected → reject with message: *"This appears to be a scanned document. MediVault currently supports digital PDFs only. Scanned document support is coming soon."*
4. PDF stored encrypted in per-user object storage partition
5. Extraction job pushed to async processing queue (Redis)
6. PDF extraction worker picks up job → runs Tika / PDFBox / pdfminer → outputs raw text string
7. Raw text stored in database alongside document metadata
8. NLP parser processes raw text → extracts structured medical entities → stores to database
9. Confidence scores assigned to each extracted field
10. Patient notified of processing completion
11. Health profile updated with new entities

#### 3.3.4 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-EXT-001 | System shall extract raw text from digital-origin PDFs using a server-side library (Tika / PDFBox / pdfminer) | **High** | V1-MVP |
| FR-EXT-002 | System shall detect whether a PDF contains an embedded text layer before processing | **High** | V1-MVP |
| FR-EXT-003 | System shall reject PDFs with no embedded text layer and display an explanatory message to the patient | **High** | V1-MVP |
| FR-EXT-004 | System shall process documents asynchronously and notify user upon completion | **High** | V1-MVP |
| FR-EXT-005 | System shall display processing status per document: Queued / Processing / Complete / Failed | **High** | V1-MVP |
| FR-EXT-006 | System shall retry failed extraction jobs up to 3 times before marking as failed | **Medium** | V1 |
| FR-EXT-007 | System shall store raw extracted text for auditability and reprocessing | **Medium** | V1 |
| FR-EXT-008 | Extraction pipeline shall complete within 15 seconds for 95% of standard documents under 5MB | **High** | V1-MVP |
| FR-EXT-009 | System shall extract document metadata (author, creation date, software) from PDF properties where available | **Medium** | V1 |
| FR-EXT-010 | No PHI shall be transmitted to any external API during the V1 extraction process | **High** | V1-MVP |

---

### 3.4 Medical Data Extraction and Structuring

#### 3.4.1 Description

The NLP/NER parser processes raw text output from the PDF extraction stage to identify and extract structured medical entities. Extracted data forms the foundation of the patient health profile and all visualizations.

#### 3.4.2 Extracted Entity Types

| Entity Type | Fields Extracted | Source Documents |
|---|---|---|
| **Medications** | Drug name, dosage, frequency, duration, route | Prescription, Discharge Summary |
| **Lab Results** | Test name, value, unit, reference range, flag (H/L) | Lab Report |
| **Diagnoses** | Condition name, ICD-10 code (if present), date, status | All document types |
| **Allergies** | Allergen name, reaction type, severity | Prescription, Discharge Summary |
| **Vitals** | BP, pulse, weight, height, BMI, SpO2, temperature | Discharge Summary, Visit Note |
| **Doctor Info** | Doctor name, specialization, facility | All document types |
| **Visit Dates** | Consultation date, admission/discharge dates | All document types |
| **Procedures** | Procedure name, date, outcome | Discharge Summary, Scan Report |
| **Imaging Findings** | Modality, body part, impression/findings | Radiology Report |

#### 3.4.3 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-NLP-001 | System shall extract medication name, dosage, frequency, and duration from prescriptions | **High** | V1-MVP |
| FR-NLP-002 | System shall extract lab test names, values, units, and reference ranges from lab reports | **High** | V1-MVP |
| FR-NLP-003 | System shall extract diagnosis names and associated dates from all document types | **High** | V1-MVP |
| FR-NLP-004 | System shall extract allergy information where present | **High** | V1 |
| FR-NLP-005 | System shall extract vital signs where present in documents | **Medium** | V1 |
| FR-NLP-006 | System shall extract doctor name, facility, and consultation date from all documents | **High** | V1-MVP |
| FR-NLP-007 | System shall flag lab values outside reference range with H (High) or L (Low) indicator | **High** | V1 |
| FR-NLP-008 | System shall deduplicate chronic conditions across multiple documents | **High** | V1 |
| FR-NLP-009 | System shall handle medication name variants (generic vs brand) via a drug synonym dictionary | **Medium** | V1 |
| FR-NLP-010 | System shall assign a confidence score (High / Medium / Low) to each extracted field | **High** | V1 |
| FR-NLP-011 | System shall flag Low confidence fields for patient review and correction | **High** | V1 |
| FR-NLP-012 | System shall allow patients to manually add, edit, or delete any extracted data point | **High** | V1-MVP |
| FR-NLP-013 | System shall maintain a version history of manual corrections for audit purposes | **Low** | V2 |

---

### 3.5 Patient Health Profile

#### 3.5.1 Description

The Health Passport is the default landing screen of MediVault post-authentication. It provides an instant, scannable overview of the user's (and their family's) health identity. The Health Profile is a deeper data view accessible from the navigation — it aggregates all extracted data from all uploaded documents and is designed to answer the question a doctor would ask in the first 30 seconds of a consultation.

#### 3.5.2 Profile Sections

- **Summary Card:** Name, age, blood group, active chronic conditions, known allergies
- **Current Medications:** Active prescriptions with name, dose, frequency
- **Conditions / Diagnoses:** All conditions with first-seen date and current status
- **Allergies:** Consolidated allergy list with reaction severity
- **Recent Vitals:** Most recent BP, weight, BMI, blood sugar from documents
- **Recent Lab Summary:** Latest values for commonly tracked tests (HbA1c, cholesterol, CBC, etc.)
- **Doctors / Facilities:** List of providers seen with dates

#### 3.5.3 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-PROF-001 | System shall display a patient summary card with name, age, blood group, and active conditions | **High** | V1-MVP |
| FR-PROF-002 | System shall display a consolidated active medications list derived from all prescriptions | **High** | V1-MVP |
| FR-PROF-003 | System shall display a consolidated conditions list with dates and status | **High** | V1-MVP |
| FR-PROF-004 | System shall display a consolidated allergies list with severity | **High** | V1-MVP |
| FR-PROF-005 | System shall display most recent vitals extracted from documents | **Medium** | V1 |
| FR-PROF-006 | System shall display a recent labs summary highlighting abnormal values | **High** | V1 |
| FR-PROF-007 | System shall allow patients to manually add conditions, medications, allergies not present in any document | **High** | V1 |
| FR-PROF-008 | System shall clearly distinguish between auto-extracted and manually entered data | **High** | V1 |
| FR-PROF-009 | System shall display the source document for each data point (tappable to view original PDF) | **Medium** | V1 |
| FR-PROF-010 | System shall allow patients to mark a medication as discontinued | **Medium** | V1 |

---

### 3.6 Health Timeline

#### 3.6.1 Description

The health timeline is a chronological view of all medical events derived from uploaded documents. It provides a longitudinal view of the patient's health history — consultations, diagnoses, medications, procedures, and lab events — ordered by date on a scrollable vertical axis.

#### 3.6.2 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-TIME-001 | System shall render a vertically scrollable chronological timeline of all medical events | **High** | V1-MVP |
| FR-TIME-002 | System shall display event type (Visit, Lab, Prescription, Procedure) as visually distinct icons or color codes | **High** | V1-MVP |
| FR-TIME-003 | System shall allow filtering the timeline by event type | **Medium** | V1 |
| FR-TIME-004 | System shall allow filtering the timeline by date range | **Medium** | V1 |
| FR-TIME-005 | System shall allow filtering by doctor or facility | **Low** | V2 |
| FR-TIME-006 | Each timeline event shall be expandable to show extracted details and link to source PDF | **High** | V1 |
| FR-TIME-007 | System shall group events by month/year with collapsible year sections for long histories | **Medium** | V1 |
| FR-TIME-008 | Timeline shall be rendered correctly on mobile viewport (single column, touch-friendly) | **High** | V1-MVP |

---

### 3.7 Diagnostic and Trend Visualizations

#### 3.7.1 Description

For patients with recurring lab tests and vitals, MediVault renders trend charts showing how values have changed over time. This is particularly valuable for chronic condition management — tracking HbA1c for diabetes, lipid panels for cardiovascular risk, kidney function markers, and thyroid values over months and years.

#### 3.7.2 Chart Types

- **Lab Value Trend Line** — time series chart for a single test parameter across multiple reports
- **Medication Duration Bar** — Gantt-style bars showing medication start and end dates
- **Diagnosis Timeline** — horizontal bars for each condition showing active duration
- **Vitals Trend** — BP systolic/diastolic over time; weight over time
- **Abnormal Value Frequency** — bar chart of how often a test has flagged out of range

#### 3.7.3 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-VIZ-001 | System shall render a trend line chart for any lab parameter that appears in 2 or more reports | **High** | V1-MVP |
| FR-VIZ-002 | System shall overlay the normal reference range band on lab trend charts | **High** | V1 |
| FR-VIZ-003 | System shall highlight out-of-range data points in red on trend charts | **High** | V1 |
| FR-VIZ-004 | System shall render a Gantt-style medication timeline showing active periods | **High** | V1 |
| FR-VIZ-005 | System shall render a diagnosis duration chart showing condition active periods | **Medium** | V1 |
| FR-VIZ-006 | System shall support zooming and panning on all trend charts | **Medium** | V1 |
| FR-VIZ-007 | System shall allow user to select which parameters to display on the trend view | **Medium** | V1 |
| FR-VIZ-008 | Charts shall render correctly on mobile viewports with touch interaction | **High** | V1-MVP |
| FR-VIZ-009 | System shall display a 'not enough data' state when fewer than 2 data points exist for a chart | **High** | V1-MVP |
| FR-VIZ-010 | System shall allow chart export as PNG image | **Low** | V2 |

---

### 3.8 Health Passport — Shareable Summary

#### 3.8.1 Description

The Health Passport is a read-only, shareable snapshot of the patient's critical health information. It is designed to be shown to a doctor at the start of a consultation — either as a QR code, a link, or a screen on the patient's phone. No doctor login or app installation is required.

#### 3.8.2 Passport Contents

- Patient name and age
- Blood group
- Active chronic conditions
- Known allergies with severity
- Current medications with dosage
- Last visit summary (date, doctor, key findings)
- Critical recent lab flags (out-of-range values from last 90 days)

#### 3.8.3 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-PASS-001 | System shall generate a shareable URL for the health passport viewable without login | **High** | V1-MVP |
| FR-PASS-002 | System shall generate a QR code linking to the shareable health passport URL | **High** | V1-MVP |
| FR-PASS-003 | Shared passport links shall be patient-controlled with the ability to revoke at any time | **High** | V1-MVP |
| FR-PASS-004 | Shared passport links shall support optional expiry (24 hours, 7 days, no expiry) | **Medium** | V1 |
| FR-PASS-005 | Patient shall be able to control which sections are visible in the shared passport | **Medium** | V1 |
| FR-PASS-006 | Shared passport shall be clearly labelled as patient-reported data, not clinically verified | **High** | V1-MVP |
| FR-PASS-007 | System shall log each access to a shared passport URL with timestamp | **Medium** | V1 |
| FR-PASS-008 | Shared passport page shall be print-friendly (A4 layout) | **Low** | V2 |

---

### 3.9 Family Circle — Invite-Based Family Network

#### 3.9.1 Description

The Family Circle is a visual, interactive family tree that shows all members of a user's family network. It supports two distinct member types:

- **Managed Profiles** — people without their own MediVault account (e.g., young children, elderly parents). Created directly by the account owner. Health data is owned and managed entirely by the owner.
- **Linked Accounts** — other MediVault users who have been invited to and accepted membership in the family. Each person's vault remains their own; access is explicitly granted by the family admin.

The family admin (creator) can invite any email address. If the invitee already has an account, they receive an in-app notification and email. If they do not, they receive an email to create an account and then join the family.

#### 3.9.2 Family Tree Visual

The Family Circle page displays a visual family tree:
- The account owner (SELF) is the root node
- Nodes are arranged by relationship: parents above, spouse at same level, children below, siblings at same level
- Each node shows: name, avatar/initials, relationship badge, membership type (managed vs linked account)
- Pending invitations shown as dashed-border nodes
- "+" buttons on each relationship level to invite or add a member

#### 3.9.3 Permission Model

| Permission | Default | Who can grant it |
|---|---|---|
| View family member list | Yes (all members) | N/A |
| View another member's vault | No | Family admin only |
| Invite new members | No | Family admin only |
| Manage permissions | No | Family admin only |

Accepting an invitation does **not** automatically grant vault access. The admin must explicitly grant vault visibility per member.

#### 3.9.4 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-FAM-001 | System shall auto-create a family for each new user on first login | **High** | V1-MVP |
| FR-FAM-002 | Family admin shall be able to invite any email address to join the family | **High** | V1-MVP |
| FR-FAM-003 | System shall send an invitation email with a one-time token link | **High** | V1-MVP |
| FR-FAM-004 | If invitee has a MediVault account, system shall also deliver an in-app notification | **High** | V1-MVP |
| FR-FAM-005 | If invitee has no MediVault account, invitation email shall include a signup link with token pre-filled | **High** | V1-MVP |
| FR-FAM-006 | Invitations shall expire after 7 days if not accepted | **Medium** | V1 |
| FR-FAM-007 | Invitee shall be able to accept or decline an invitation | **High** | V1-MVP |
| FR-FAM-008 | Family admin shall be able to revoke a pending invitation at any time | **Medium** | V1 |
| FR-FAM-009 | Family admin shall be able to remove a member from the family at any time | **Medium** | V1 |
| FR-FAM-010 | Family admin shall be able to grant vault read access to any member for any other member's vault | **High** | V1-MVP |
| FR-FAM-011 | Family admin shall be able to revoke vault access at any time | **High** | V1-MVP |
| FR-FAM-012 | Family admin shall be able to grant a member the "can invite" permission | **Medium** | V1 |
| FR-FAM-013 | Each user may create and manage their own family circle independently | **High** | V1-MVP |
| FR-FAM-014 | Managed profiles (no MediVault account) shall remain supported alongside linked accounts | **High** | V1-MVP |
| FR-FAM-015 | Family tree shall be displayed as a visual tree with relationship-based layout | **Medium** | V1 |

---

### 3.10 Notifications

#### 3.10.1 Description

MediVault delivers notifications through two channels: **in-app** (bell icon in top nav, notification centre page) and **email** (via SendGrid). Notifications are non-blocking — they do not prevent the user from using the app.

#### 3.10.2 Notification Types (V1)

| Type | In-App | Email | Trigger |
|---|---|---|---|
| `FAMILY_INVITATION_RECEIVED` | ✓ | ✓ | Invited user receives a family invitation |
| `FAMILY_INVITATION_ACCEPTED` | ✓ | ✓ | Admin is notified that an invitee accepted |
| `FAMILY_INVITATION_DECLINED` | ✓ | — | Admin is notified that an invitee declined |
| `VAULT_ACCESS_GRANTED` | ✓ | — | User is told they can now see a specific vault |
| `DOCUMENT_PROCESSED` | ✓ | ✓ | Document extraction complete |
| `DOCUMENT_FAILED` | ✓ | ✓ | Document extraction failed |

#### 3.10.3 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-NOTIF-001 | System shall persist in-app notifications in the database | **High** | V1-MVP |
| FR-NOTIF-002 | User shall be able to view all notifications in a notification centre | **High** | V1-MVP |
| FR-NOTIF-003 | Bell icon in top nav shall show an unread count badge | **High** | V1-MVP |
| FR-NOTIF-004 | User shall be able to mark individual notifications or all as read | **Medium** | V1 |
| FR-NOTIF-005 | Notifications shall include a deep link to the relevant in-app page | **Medium** | V1 |
| FR-NOTIF-006 | Patient shall receive an in-app notification when a provider requests access via passport lookup, with Accept and Decline action buttons | **High** | V1 |
| FR-NOTIF-007 | Provider shall receive an in-app notification when the patient accepts or declines their access request | **High** | V1 |

---

### 3.11 User Onboarding

#### 3.11.1 Description

On first login, every user is directed through a mandatory multi-step onboarding flow before accessing the main application. The flow collects a health baseline (DOB, approximate height and weight, blood group, known allergies) and establishes the user's role (PATIENT or PROVIDER). Providers must supply an Indian medical licence number for verification against the NMC (National Medical Commission) public registry before they can use provider-only features.

#### 3.11.2 Onboarding Steps

| Step | Shown To | Fields |
|---|---|---|
| 1 — Personal Info | All | Date of birth (pre-fills age dynamically), approximate height (cm), approximate weight (kg) |
| 2 — Blood Group | All | Blood group selector (A+/A-/B+/B-/O+/O-/AB+/AB-/Unknown) |
| 3 — Known Allergies | All | Free-text allergy input with add/remove chips; creates allergy entities on the self member |
| 4 — Role Selection | All | PATIENT (default) or PROVIDER (healthcare professional) |
| 5 — Licence Verification | PROVIDER only | Medical licence number, registration council (state or NMC); async verification against NMC registry |
| 6 — Complete | All | Summary screen; provider shown verification status (Pending/Verified) |

#### 3.11.3 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-ONB-001 | System shall redirect unauthenticated-onboarding users to /onboarding immediately after first login | **High** | V1 |
| FR-ONB-002 | Onboarding page shall be full-screen and not render the main AppShell nav until complete | **High** | V1 |
| FR-ONB-003 | System shall persist DOB to the self FamilyMember record; height_cm and weight_kg to the family_members row | **High** | V1 |
| FR-ONB-004 | Blood group entered at onboarding shall update the self FamilyMember blood_group field | **High** | V1 |
| FR-ONB-005 | Allergies entered at onboarding shall be created as is_manual_entry allergy entities on the self member | **High** | V1 |
| FR-ONB-006 | System shall store user role (PATIENT | PROVIDER) on the users table | **High** | V1 |
| FR-ONB-007 | PROVIDER users shall supply a medical licence number and registration council at onboarding | **High** | V1 |
| FR-ONB-008 | System shall verify the licence number against the NMC public registry asynchronously | **High** | V1 |
| FR-ONB-009 | Provider may proceed to use patient features while verification is PENDING; provider-only features (patient lookup) require VERIFIED status | **High** | V1 |
| FR-ONB-010 | Displayed age shall be computed dynamically from DOB (changes automatically on birthday) | **Medium** | V1 |
| FR-ONB-011 | System shall mark onboarding_completed = TRUE on the users record upon completion | **High** | V1 |
| FR-ONB-012 | Users who skip or close mid-onboarding shall be returned to onboarding on the next login | **Medium** | V1 |

---

### 3.12 Provider / Doctor Workflow

#### 3.12.1 Description

Authenticated PROVIDER-role users (licence verified) can initiate a patient session by entering the patient's Health Passport UUID. This triggers a consent request to the patient. Once the patient accepts, the provider sees a read-only clinical view of that patient's data and can log the medical encounter. Both the consent request and the encounter record are visible to the patient in their notification history and encounter feed.

#### 3.12.2 Provider Access Flow

```
Provider enters passport UUID
       ↓
System validates: passport active + non-expired + non-revoked
       ↓
System creates provider_access_requests record (status=PENDING, TTL=15 min)
       ↓
Patient receives in-app notification: "Dr. [Name] is requesting to view your profile — Accept / Decline"
       ↓
  Patient ACCEPTS → request status=ACCEPTED
       ↓                    ↓
  Provider sees    Patient DECLINES → request status=DECLINED
  clinical view    → Provider sees "Patient declined" screen
       ↓
Provider views: health profile (read-only) + timeline + lab trends + treatment pathway graph
       ↓
Provider logs encounter (chief complaint, diagnosis notes, prescriptions, follow-up date)
       ↓
Encounter saved; patient receives notification with encounter summary
```

#### 3.12.3 Provider Patient View — Panels

| Panel | Content |
|---|---|
| Identity & Baseline | Name (from self member), age, blood group, height/weight (from onboarding), known allergies |
| Health Timeline | Chronological event feed (diagnoses, encounters, documents) |
| Lab Trend Chart | Recharts line chart for selected lab parameter; reference range band; same as Insights tab |
| Treatment Pathway Graph | "Clinical Curator" visual (see stitch_health_passport/treatment_pathway/DESIGN.md) — chronological narrative of diagnoses + encounters + medications on a vertical timeline |
| Log Encounter (form) | Encounter date (default today), chief complaint, diagnosis notes, prescriptions note, follow-up date; Submit button |

#### 3.12.4 Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-PROV-001 | Only users with role=PROVIDER and licence_verified=TRUE shall access provider-only routes | **High** | V1 |
| FR-PROV-002 | Provider shall be able to enter a Health Passport UUID to initiate a patient access request | **High** | V1 |
| FR-PROV-003 | System shall validate the passport is active, non-expired, and non-revoked before creating an access request | **High** | V1 |
| FR-PROV-004 | Patient shall receive an in-app notification with Accept / Decline actions within 5 seconds of the provider's request | **High** | V1 |
| FR-PROV-005 | Access request shall expire after 15 minutes if the patient does not respond | **High** | V1 |
| FR-PROV-006 | Provider shall see a real-time waiting state while the request is PENDING, and an error state if DECLINED or EXPIRED | **High** | V1 |
| FR-PROV-007 | Provider clinical view shall be read-only; no writes to patient's core health profile are permitted | **High** | V1 |
| FR-PROV-008 | Provider shall be able to log a medical encounter (date, complaint, diagnosis notes, prescriptions note, follow-up date) | **High** | V1 |
| FR-PROV-009 | Logged encounter shall be visible to the patient in their encounter history feed | **High** | V1 |
| FR-PROV-010 | Treatment pathway graph shall display diagnoses, encounters, and medications as a chronological narrative | **Medium** | V1 |
| FR-PROV-011 | All provider access sessions shall be logged in provider_access_requests for the patient to review | **High** | V1 |
| FR-PROV-012 | Patient shall be able to view their full provider access request history (accepted/declined/expired) in their notification centre | **Medium** | V1 |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| NFR-PERF-001 | Page load time (LCP) shall be under 2.5 seconds on a 4G mobile connection | **High** | V1-MVP |
| NFR-PERF-002 | File upload shall begin within 1 second of user initiating upload | **High** | V1-MVP |
| NFR-PERF-003 | PDF extraction pipeline shall complete within 15 seconds for 95% of documents under 5MB | **High** | V1-MVP |
| NFR-PERF-004 | Health profile and timeline shall render within 1.5 seconds after authentication | **High** | V1-MVP |
| NFR-PERF-005 | Chart rendering shall complete within 500ms for datasets up to 200 data points | **Medium** | V1 |
| NFR-PERF-006 | System shall support 10,000 concurrent users without performance degradation | **Medium** | V1 |

> **Note:** The V1 extraction pipeline is significantly faster than a cloud OCR pipeline. PDF text extraction via Tika/PDFBox typically completes in under 2 seconds for standard medical documents. The 15-second SLA accounts for NLP processing time on top of raw extraction.

### 4.2 Security

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| NFR-SEC-001 | All data in transit shall use TLS 1.3 encryption | **High** | V1-MVP |
| NFR-SEC-002 | All PHI stored at rest shall use AES-256 encryption | **High** | V1-MVP |
| NFR-SEC-003 | Each user's documents and data shall be stored in isolated storage partitions | **High** | V1-MVP |
| NFR-SEC-004 | System shall implement OWASP Top 10 protections | **High** | V1-MVP |
| NFR-SEC-005 | All API endpoints shall require valid JWT authentication except public health passport | **High** | V1-MVP |
| NFR-SEC-006 | Shared passport URLs shall use non-guessable UUIDs (minimum 128-bit entropy) | **High** | V1-MVP |
| NFR-SEC-007 | System shall implement rate limiting on upload and auth endpoints | **High** | V1 |
| NFR-SEC-008 | System shall conduct automated dependency vulnerability scanning in CI/CD pipeline | **Medium** | V1 |
| NFR-SEC-009 | System shall undergo a third-party security audit before public launch | **High** | V1 |
| NFR-SEC-010 | No PHI shall leave the system's own infrastructure during document processing in V1 | **High** | V1-MVP |

### 4.3 Privacy and Compliance

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| NFR-PRIV-001 | System shall comply with India DPDPA 2023 for health data handling | **High** | V1-MVP |
| NFR-PRIV-002 | System shall obtain explicit, informed consent at registration for data processing | **High** | V1-MVP |
| NFR-PRIV-003 | System shall provide a data export feature (complete patient data as JSON/PDF) | **High** | V1 |
| NFR-PRIV-004 | System shall provide complete account deletion with data purge within 30 days | **High** | V1 |
| NFR-PRIV-005 | System shall not use patient data for model training without explicit opt-in | **High** | V1-MVP |
| NFR-PRIV-006 | System shall publish a clear, plain-language Privacy Policy and Terms of Service | **High** | V1-MVP |

### 4.4 Reliability and Availability

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| NFR-REL-001 | System shall maintain 99.5% uptime for patient-facing services | **High** | V1 |
| NFR-REL-002 | Extraction pipeline failures shall not result in data loss — documents shall be retryable | **High** | V1-MVP |
| NFR-REL-003 | System shall implement automated daily backups of all user data | **High** | V1-MVP |
| NFR-REL-004 | Recovery Point Objective (RPO) shall be less than 24 hours | **High** | V1 |
| NFR-REL-005 | Recovery Time Objective (RTO) shall be less than 4 hours for complete system failure | **Medium** | V1 |

### 4.5 Usability

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| NFR-USE-001 | A first-time user shall be able to upload their first document within 3 minutes of account creation | **High** | V1-MVP |
| NFR-USE-002 | The health profile shall be readable without any tutorial or onboarding for a moderately tech-literate user | **High** | V1-MVP |
| NFR-USE-003 | The shareable health passport shall be legible and usable by a clinician with no product training | **High** | V1-MVP |
| NFR-USE-004 | All interactive elements shall have minimum touch target size of 44x44 pixels | **High** | V1-MVP |
| NFR-USE-005 | System shall support font scaling up to 200% without breaking layout | **Medium** | V1 |
| NFR-USE-006 | System shall achieve WCAG 2.1 AA compliance for color contrast and screen reader support | **Medium** | V1 |

### 4.6 Maintainability

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| NFR-MAIN-001 | Codebase shall maintain minimum 80% test coverage for backend services | **High** | V1 |
| NFR-MAIN-002 | NLP parser rules and entity patterns shall be configurable without code deployment | **Medium** | V1 |
| NFR-MAIN-003 | System shall expose structured application logs for all pipeline stages | **High** | V1-MVP |
| NFR-MAIN-004 | System shall implement health check endpoints for all microservices | **High** | V1 |
| NFR-MAIN-005 | All infrastructure shall be defined as code (Terraform or equivalent) | **Medium** | V1 |

---

## 5. System Architecture Overview

### 5.1 Architecture Pattern

MediVault follows a layered microservices architecture with the following primary layers:

- **Presentation Layer** — React PWA (responsive web)
- **API Gateway** — single entry point, JWT validation, rate limiting
- **Application Layer** — Python + FastAPI backend
- **Core Services** — Auth Service (Auth0), Document Service, Extraction Orchestrator, Profile Service, Sharing Service
- **Processing Pipeline** — async queue-based PDF extraction (pdfminer.six) + NLP processing (spaCy + Med7); entirely on-infrastructure, no external APIs in V1
- **Data Layer** — PostgreSQL (structured data), MinIO (local S3-compatible object storage for raw documents), Redis (cache/queue/sessions)

### 5.2 Component Descriptions

| Component | Description |
|---|---|
| **React PWA** | Frontend application. Responsive, installable on mobile. Communicates with backend via REST API over HTTPS. |
| **API Gateway** | Validates JWT tokens, enforces rate limits, routes to downstream services. Handles CORS. |
| **Auth Service** | Delegates to Auth0. Manages user registration, login, OTP (SMS), Google OAuth. Auth0 issues signed JWTs validated at the API Gateway. |
| **Document Service** | Accepts PDF uploads, validates format and embedded text presence, stores encrypted files in object storage, triggers pipeline. |
| **Extraction Orchestrator** | Manages async extraction jobs via Celery + Redis. Invokes pdfminer.six (primary) with Tika/pypdf as fallback. Runs entirely on-infrastructure. Handles retry logic, stores raw text. |
| **NLP Parser** | Processes raw text using spaCy + Med7 for NER. Extracts medical entities. Assigns confidence scores. Medical entity rules added iteratively. Stores structured data to DB. |
| **Profile Service** | Aggregates all extracted entities across documents into unified patient profile. Handles deduplication. |
| **Sharing Service** | Generates and manages shareable passport UUIDs, expiry, access logs, and revocation. |
| **Notification Service** | Sends email/SMS notifications for processing completion, upload confirmations. |
| **PostgreSQL** | Primary relational database. Stores user accounts, extracted medical entities, document metadata. |
| **Object Storage** | MinIO — local S3-compatible encrypted storage for raw uploaded PDFs. Isolated per-user partitions. S3-compatible API allows future migration to AWS S3 with no code changes. |
| **Redis** | Session cache, processing job queue, rate limit counters. |

### 5.3 Data Flow — Document Upload to Profile

1. Patient uploads PDF
2. API Gateway validates JWT and forwards to Document Service
3. Document Service: virus scan → format validation → embedded text detection → encrypt → store to Object Storage
4. Document Service pushes extraction job to Redis queue
5. Extraction Orchestrator picks up job → runs Tika / PDFBox / pdfminer on-infrastructure → outputs raw text
6. Raw text stored to PostgreSQL alongside document metadata
7. NLP Parser processes raw text: entity extraction → confidence scoring → structured data to PostgreSQL
8. Profile Service updates patient health profile with new entities
9. Notification Service sends processing complete notification to patient
10. Patient views updated health profile in React PWA

> **Key architecture point:** Steps 5–7 are entirely self-contained within the system's own infrastructure. No PHI leaves the platform during processing in V1.

### 5.4 V2 Extension Point — OCR

When V2 introduces support for scanned PDFs and image uploads, the Extraction Orchestrator will be extended with an additional routing step:

- If embedded text detected → existing PDF extraction path (unchanged from V1)
- If no embedded text detected → OCR API path (new in V2)

The V1 pipeline remains unchanged. OCR is an additive layer, not a replacement.

---

## 6. Data Model

### 6.1 Core Entities

#### User

| Field | Type / Notes |
|---|---|
| `user_id` | UUID — Primary Key |
| `email` | Unique, verified |
| `phone_number` | Optional, verified via OTP |
| `name` | Display name |
| `date_of_birth` | Date |
| `blood_group` | A+/A-/B+/B-/O+/O-/AB+/AB-/Unknown |
| `created_at` | Timestamp |
| `last_login_at` | Timestamp |
| `is_active` | Boolean |

#### Document

| Field | Type / Notes |
|---|---|
| `document_id` | UUID — Primary Key |
| `user_id` | FK → User |
| `document_type` | ENUM: LAB_REPORT \| PRESCRIPTION \| DISCHARGE \| SCAN \| OTHER |
| `document_date` | Date (auto-detected from PDF metadata or manually set) |
| `facility_name` | String (optional) |
| `doctor_name` | String (optional) |
| `storage_path` | Encrypted object storage path |
| `file_format` | PDF (only in V1) |
| `has_text_layer` | Boolean — true for valid V1 documents |
| `processing_status` | ENUM: QUEUED \| PROCESSING \| COMPLETE \| FAILED \| MANUAL_REVIEW |
| `extracted_raw_text` | Text (output of PDF extraction library, nullable) |
| `extraction_library` | String — records which library was used (Tika / PDFBox / pdfminer) |
| `uploaded_at` | Timestamp |

#### Medication

| Field | Type / Notes |
|---|---|
| `medication_id` | UUID |
| `user_id` | FK → User |
| `document_id` | FK → Document (source) |
| `drug_name` | String (normalized) |
| `dosage` | String (e.g., 500mg) |
| `frequency` | String (e.g., twice daily) |
| `start_date` | Date |
| `end_date` | Date (nullable — null = ongoing) |
| `is_active` | Boolean |
| `confidence_score` | ENUM: HIGH \| MEDIUM \| LOW |
| `is_manual_entry` | Boolean |

#### LabResult

| Field | Type / Notes |
|---|---|
| `result_id` | UUID |
| `user_id` | FK → User |
| `document_id` | FK → Document |
| `test_name` | String (normalized) |
| `value` | Numeric |
| `unit` | String |
| `reference_low` | Numeric (nullable) |
| `reference_high` | Numeric (nullable) |
| `flag` | ENUM: NORMAL \| HIGH \| LOW \| CRITICAL |
| `test_date` | Date |
| `confidence_score` | ENUM: HIGH \| MEDIUM \| LOW |

#### Diagnosis

| Field | Type / Notes |
|---|---|
| `diagnosis_id` | UUID |
| `user_id` | FK → User |
| `document_id` | FK → Document |
| `condition_name` | String (normalized) |
| `icd10_code` | String (nullable) |
| `diagnosed_date` | Date |
| `status` | ENUM: ACTIVE \| RESOLVED \| CHRONIC \| UNKNOWN |
| `confidence_score` | ENUM: HIGH \| MEDIUM \| LOW |
| `is_manual_entry` | Boolean |

#### SharedPassport

| Field | Type / Notes |
|---|---|
| `passport_id` | UUID — Public URL token (128-bit entropy) |
| `user_id` | FK → User |
| `created_at` | Timestamp |
| `expires_at` | Timestamp (nullable) |
| `is_active` | Boolean |
| `visible_sections` | JSON array of section names |
| `access_log` | JSON array of `{timestamp, ip_hash}` |

---

## 7. UI/UX Requirements

### 7.1 Design Principles

- **Mobile-first:** all screens designed for 375px viewport upward
- **Clarity over density:** health data should be immediately readable, never cluttered
- **Trust signals:** clear distinction between auto-extracted and manually entered data
- **Progressive disclosure:** summary first, detail on demand
- **Accessibility:** WCAG 2.1 AA minimum standard

### 7.2 Key Screens

| Screen | Description |
|---|---|
| **Onboarding / Auth** | Sign up, login, OTP verification. Minimal fields. Google OAuth prominent. |
| **Document Library** | Grid/list of all uploaded PDFs with status badges. Upload button always visible. |
| **Upload Flow** | File picker (PDF only). Document type selection. Date confirmation. Embedded text check feedback. Progress indicator. |
| **Health Passport** *(default landing)* | Family health overview. Member cards showing blood group, active conditions, allergies. QR code generation. Share/Revoke controls. Default route `/` post-authentication. |
| **Health Profile** | Deep health data view at `/health`. Summary card at top. Sectioned cards for medications, conditions, allergies, labs. |
| **Timeline View** | Chronological vertical timeline. Filterable by type and date. Expandable events. |
| **Charts / Trends** | Parameter selector at top. Trend chart with reference band. Medication Gantt below. |
| **Document Detail** | PDF viewer alongside extracted data panel. Edit/correct extracted fields inline. |

### 7.3 Mobile-Specific Requirements

- Bottom navigation bar for primary sections (Passport, Records, Insights, Health, Family)
- Settings accessible from avatar/profile menu (top nav on desktop; top-right icon on mobile) — not a bottom nav tab
- Swipe gestures for timeline navigation
- PDF file picker from device storage
- Offline state handled gracefully with clear messaging
- PWA install prompt shown after 3rd session

### 7.4 Upload State Communication

Since V1 only accepts digital-origin PDFs, the UI must communicate clearly to users who attempt invalid uploads:

- If a non-PDF file is selected → *"MediVault currently accepts PDF documents only."*
- If a scanned/image-based PDF is detected → *"This PDF appears to be a scanned document. MediVault currently supports digital PDFs only — scanned document support is coming soon."*

---

## 8. External Interface Requirements

### 8.1 PDF Extraction Library Interface

| Attribute | Detail |
|---|---|
| **Library Options** | Apache Tika (REST server mode), Apache PDFBox (Java), pdfminer.six (Python) |
| **Input** | PDF file bytes or file path |
| **Output** | Raw extracted text string + document metadata (author, creation date, page count) |
| **Invocation** | Called from Extraction Orchestrator on backend only — synchronous or async |
| **Data Privacy** | Runs entirely within the system's own infrastructure — no external API calls, no PHI transmitted externally |
| **Fallback** | If primary library fails, retry with alternate library before marking job as failed |

### 8.2 Authentication Provider

| Attribute | Detail |
|---|---|
| **Provider** | Auth0 |
| **Protocols** | OAuth 2.0, OIDC, JWT |
| **Supported Methods** | Email/Password, Google OAuth, Phone OTP |
| **Token Lifetime** | Access token: 1 hour; Refresh token: 30 days |

### 8.3 Notification Service

| Channel | Detail |
|---|---|
| **Email** | Transactional email via SendGrid or AWS SES |
| **SMS/OTP** | Twilio or AWS SNS for phone OTP delivery |
| **Triggers** | Document processing complete, account verification, shared passport accessed |

---

## 9. Testing Requirements

### 9.1 Testing Strategy

MediVault follows a test pyramid approach: extensive unit tests, integration tests for pipeline components, and end-to-end tests for critical user journeys. Since V1 relies entirely on PDF text extraction, test coverage must include a diverse corpus of real-world digital-origin medical PDFs from Indian labs and clinics (SRL, Metropolis, Thyrocare, Apollo, Fortis, etc.).

### 9.2 Test Categories

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| TEST-001 | Unit tests for all NLP parser extraction functions with a labeled medical document corpus | **High** | V1-MVP |
| TEST-002 | Integration tests for PDF upload → extraction → NLP parse → profile pipeline end-to-end | **High** | V1-MVP |
| TEST-003 | PDF extraction accuracy benchmarking: minimum 95% raw text extraction fidelity on test PDF set | **High** | V1-MVP |
| TEST-004 | NLP extraction accuracy benchmarking: minimum 90% field extraction accuracy on structured medical PDFs | **High** | V1-MVP |
| TEST-005 | Embedded text detection testing: verify correct rejection of scanned PDFs across common scan formats | **High** | V1-MVP |
| TEST-006 | Security penetration testing: OWASP Top 10 coverage before launch | **High** | V1 |
| TEST-007 | Cross-browser compatibility testing (Chrome, Safari, Firefox, Edge — desktop and mobile) | **High** | V1-MVP |
| TEST-008 | Mobile responsiveness testing on iOS Safari and Android Chrome at 375px and 414px | **High** | V1-MVP |
| TEST-009 | Performance load testing: 10,000 concurrent users, PDF upload and extraction throughput | **Medium** | V1 |
| TEST-010 | Data privacy testing: verify storage isolation between user accounts | **High** | V1-MVP |
| TEST-011 | Shared passport access testing: verify revocation, expiry, and non-guessable URL entropy | **High** | V1 |
| TEST-012 | Accessibility audit: WCAG 2.1 AA with automated (axe) and manual screen reader testing | **Medium** | V1 |

---

## 10. MVP Definition and Phased Roadmap

### 10.1 V1 MVP — Core Value Loop

The MVP must deliver the complete core value loop: **upload a digital PDF → see structured data in your health profile.** Everything else is layered on top of this foundation.

| Included in V1 MVP | Deferred to V1 Full / V2 |
|---|---|
| Email + Google OAuth + Phone OTP login | MFA (TOTP) |
| Digital-origin PDF upload only | Image file uploads (JPEG, PNG, HEIC) |
| Server-side PDF text extraction (Tika / PDFBox / pdfminer) | Scanned PDF support via cloud OCR |
| Medication, diagnosis, lab entity extraction | Handwritten prescription parsing |
| Health profile dashboard | Hindi language UI |
| Chronological health timeline | Family account management |
| Lab trend charts (2+ data points) | Chart PNG export |
| Shareable health passport + QR code | ABHA integration |
| Manual data correction | WhatsApp bot intake |
| Account deletion / data export | Medication reminders |
| Family accounts (owner + members, isolated per-member records) | Wearable data integration |
| | Voice interface |

### 10.2 V2 Roadmap — OCR Extension

V2 will extend the extraction pipeline to support:

- Image file uploads (JPEG, PNG, HEIC)
- Scanned PDF processing via cloud OCR (Google Cloud Vision / AWS Textract)
- Handwritten prescription parsing (with mandatory patient verification step given inherent accuracy limitations)

The V1 architecture is specifically designed to accommodate this as an additive extension — only the Extraction Orchestrator's routing logic changes. No V1 components are replaced.

### 10.3 Success Metrics for V1

| Metric | Target |
|---|---|
| **Activation** | User uploads first document within 7 days of sign-up: >60% |
| **PDF Extraction Accuracy** | Raw text fidelity from digital PDFs: >95% |
| **NLP Field Accuracy** | Entity extraction accuracy on structured medical PDFs: >90% |
| **Profile Completeness** | Users with >3 documents uploaded at 30 days: >40% |
| **Passport Usage** | Users who generate a shareable passport: >30% |
| **Retention (30-day)** | Users who return to view profile at least once in 30 days: >50% |
| **Pipeline Reliability** | Extraction pipeline failure rate: <5% |
| **Scanned PDF Rejections** | Volume tracked as a demand signal for V2 OCR prioritization |

---

## 11. Open Issues and Decisions Pending

| # | Open Issue | Owner | Status |
|---|---|---|---|
| 1 | PDF extraction library selection: Apache Tika vs PDFBox vs pdfminer.six — performance, accuracy on Indian medical PDFs, and infrastructure footprint comparison needed | Engineering | **Resolved: pdfminer.six selected** (Python-native, best tabular layout extraction; Tika/pypdf as fallback) |
| 2 | NLP parser: build vs buy — custom spaCy/Med7 model vs Amazon Comprehend Medical. **Note:** Comprehend Medical transmits PHI externally — must evaluate against CON-006 before selecting | Engineering | **Resolved: spaCy + Med7 selected** (self-hosted; PHI stays on-infrastructure; medical entity rules added iteratively) |
| 3 | Auth provider selection: Firebase Auth vs Auth0 — pricing at scale and India data residency requirements | Engineering | **Resolved: Auth0 selected** |
| 4 | Data residency: all PHI must reside in India-region cloud zones — confirm availability (AWS ap-south-1, GCP asia-south1) | Legal / Eng | Open |
| 5 | DPDPA 2023 Data Fiduciary registration requirements — legal review required before launch | Legal | Open |
| 6 | Scanned PDF detection heuristic: define minimum embedded character count threshold before classifying as image-based and rejecting | Engineering | Open |
| 7 | Family account model: single login managing multiple profiles (e.g., parent managing children's records) — defer to V2 or include in V1? | Product | **Resolved: included in V1** — account owner + family members list; each member has an isolated health profile/documents/timeline window |
| 8 | If Amazon Comprehend Medical is selected for NLP, a Data Processing Agreement (DPA) is required and CON-006 must be updated to reflect approved external PHI transmission | Legal / Eng | **Resolved: N/A** — spaCy + Med7 selected; Comprehend Medical not used; CON-006 satisfied |

---

## 12. Revision History

| Version | Date | Description | Author |
|---|---|---|---|
| 1.0 | March 2026 | Initial draft — full V1 scope definition with cloud OCR pipeline | Product Team |
| 1.1 | March 2026 | Revised extraction pipeline: replaced cloud OCR with server-side PDF text extraction (Tika / PDFBox / pdfminer); scoped V1 to digital-origin PDFs only; image uploads and OCR deferred to V2; updated all related requirements, constraints, architecture, dependencies, open issues, and test cases accordingly | Product Team |
| 1.2 | March 2026 | Resolved all open stack decisions: backend — Python + FastAPI; PDF extraction — pdfminer.six (primary); NLP — spaCy + Med7 (self-hosted); auth — Auth0; object storage — MinIO (local, S3-compatible); family accounts — included in V1 scope; all resolved open issues updated in §11 | Product Team |

---

*End of Document — MediVault SRS v1.1*
*This document is confidential. Do not distribute without authorization.*