# MediVault — User Flows

All actors, their goals, and their complete journeys through the system.

---

## Actors

| Actor | Description | Auth Required |
|---|---|---|
| **Account Owner** | Primary user who creates the account and manages the family | Yes |
| **Family Member (Self)** | The account owner's own health profile (first member auto-created) | Via owner |
| **Family Member (Other)** | Dependent added by the owner (child, parent, spouse) | Via owner |
| **Clinician** | Doctor/nurse who views a shared Health Passport via link/QR | No |
| **System** | Background processing (extraction pipeline, notifications) | N/A |

---

## UF-001 — Account Registration and Onboarding

**Actor:** Account Owner (new user)
**Goal:** Create an account and get to an empty health dashboard ready to upload

```
1. User visits MediVault web app
2. Lands on marketing/auth page — sees "Sign Up" and "Log In"
3. Chooses sign-up method:
   a. Email + password → enters email, sets password → clicks Sign Up
      → receives verification email → clicks link → email verified
   b. Google OAuth → clicks "Continue with Google" → Google consent screen
      → redirected back, account created
   c. Phone OTP → enters Indian mobile number → receives OTP SMS
      → enters OTP → verified
4. Lands on onboarding screen:
   - Prompted to enter: Full name, date of birth, blood group (optional)
   - These fields populate the "self" family member profile
5. Sees empty Health Profile with an onboarding prompt:
   "Upload your first document to get started"
6. Onboarding complete → user is in the app
```

**Happy path:** Google OAuth → fill profile → done in < 2 min
**Error paths:**
- Email already registered → "Account exists, log in instead"
- OTP expired (5 min TTL) → "OTP expired, request a new one"
- Invalid OTP → "Incorrect OTP, try again" (max 3 attempts before lockout)

---

## UF-002 — Log In (Returning User)

**Actor:** Account Owner (returning)
**Goal:** Access their health dashboard

```
1. User visits MediVault
2. Clicks "Log In"
3. Chooses method:
   a. Email + password → enters credentials → authenticated
   b. Google OAuth → single click → authenticated
   c. Phone OTP → enters number → receives OTP → enters OTP → authenticated
4. If session is still valid (within 30-day inactivity window) → auto-logged in
5. Lands on Health Profile dashboard for their default family member (self)
```

**Error paths:**
- Wrong password → "Incorrect email or password" (no enumeration)
- Forgotten password → "Forgot password?" → email reset link sent
- Account suspended → "Your account has been suspended. Contact support."

---

## UF-003 — Upload a Document

**Actor:** Account Owner
**Goal:** Add a new medical document (lab report, prescription, etc.) to a family member's records

```
1. User is on the Document Library page (or clicks the floating Upload button)
2. Selects the family member this document belongs to (defaults to self)
3. Clicks "Upload Document" → file picker opens (PDF only filter)
4. Selects one or more PDF files (up to 10, 20MB each)
5. For each file:
   a. Client-side validation: checks file extension = .pdf
   b. If invalid format → inline error: "MediVault accepts PDF files only"
5. Upload begins → progress bar shown per file
6. Backend processing:
   a. Virus scan
   b. Embedded text layer check
      - If no text layer detected → file marked REJECTED
        → UI shows: "This appears to be a scanned document. Digital PDFs only — scanned support coming soon."
      - If text layer present → file stored in MinIO, queued for extraction
7. For accepted files: user confirms or corrects:
   a. Document type (auto-suggested or manually selected):
      Lab Report | Prescription | Discharge Summary | Scan/Imaging | Other
   b. Document date (auto-detected from PDF metadata, or user sets manually)
8. User clicks "Confirm" → documents submitted to extraction pipeline
9. Document Library shows new documents with status "Processing"
10. When extraction complete:
    → Status changes to "Complete" (or "Failed" with retry option)
    → Toast notification: "Your lab report has been processed"
    → Health profile updated with new entities
```

**Error paths:**
- File > 20MB → "File too large. Maximum size is 20MB per file."
- More than 10 files → "You can upload up to 10 files at once."
- Upload fails (network) → "Upload failed. Check your connection and try again." with retry button
- Extraction permanently fails (after 3 retries) → status badge "Processing failed" with "Retry" CTA

---

## UF-004 — View Health Profile

**Actor:** Account Owner (viewing self or a family member)
**Goal:** Get a quick, complete overview of a person's health status

```
1. User is on the main Health Profile page
2. If multiple family members: member selector at top (pill tabs or dropdown)
3. Profile loads for selected member:
   - Summary Card: name, age, blood group, active chronic conditions, known allergies
   - Current Medications section: each med shows name, dosage, frequency, active status
   - Conditions / Diagnoses: list with first-seen date and current status
   - Allergies: list with severity badge
   - Recent Vitals: latest BP, weight, BMI, blood sugar
   - Recent Lab Summary: key tests with latest value, normal/abnormal flag
   - Doctors & Facilities: providers seen with last visit date
4. Each data point shows its source:
   - "From Lab Report — SRL Diagnostics — 12 Jan 2026" (tappable → opens PDF)
   - "Manually entered" badge (for manually added items)
   - Confidence badge: LOW confidence items show a "Review needed" warning
5. User can:
   - Tap any field to see detail or edit
   - Click source to open the original PDF in the document detail view
   - Click "Add manually" in any section to add a condition/medication/allergy
   - Toggle a medication as "Discontinued"
```

**States:**
- Empty (no documents uploaded): onboarding nudge "Upload your first document"
- Partial (some documents, limited data): shows what exists, nudges for more
- Rich (many documents): full dashboard as described above

---

## UF-005 — Manually Correct or Add Data

**Actor:** Account Owner
**Goal:** Fix an incorrectly extracted field or add information not present in any document

```
CORRECTION FLOW:
1. User sees a field with a "Review needed" badge (Low confidence) or notices an error
2. Clicks the field or the edit icon
3. Inline edit form appears with the current value pre-filled
4. User makes correction → clicks "Save"
5. Field updates, source label changes to "Edited by you on [date]"
6. Original extracted value preserved in audit trail

MANUAL ADD FLOW:
1. User clicks "Add [medication / condition / allergy]" in the relevant section
2. Form appears: enters name, relevant details (dosage, severity, etc.)
3. Clicks "Save"
4. New entry appears with "Manually entered" badge
5. Item is included in Health Profile and Health Passport
```

---

## UF-006 — View Health Timeline

**Actor:** Account Owner
**Goal:** See a chronological history of all medical events for a family member

```
1. User navigates to Timeline tab
2. Selects family member (if applicable)
3. Timeline renders as a vertical scrollable list, newest at top
4. Each event shows:
   - Date (prominent)
   - Event type icon (Visit / Lab / Prescription / Procedure)
   - Brief summary: "Lab Report — SRL Diagnostics" or "Prescription — Dr. Mehta"
5. User can:
   a. Filter by event type (toggle pills at top)
   b. Filter by date range (date picker)
   c. Tap any event → expands to show extracted details + link to source PDF
   d. Scroll up to see older events
6. Events grouped by month/year with collapsible year sections
```

**Mobile:** Swipe left/right on an event to quick-access the source document.

---

## UF-007 — View Trend Charts

**Actor:** Account Owner
**Goal:** Understand how lab values or vitals have changed over time

```
1. User navigates to Charts/Trends tab
2. Selects family member
3. Page shows:
   - Lab parameter selector (chips/dropdown): shows all parameters with ≥ 2 data points
   - Default view: most clinically relevant parameters for that person (based on diagnosed conditions)
4. Trend line chart renders:
   - X axis: date
   - Y axis: value + unit (e.g., mg/dL)
   - Green band: normal reference range
   - Data points: green = normal, red = out of range
5. Medication Gantt chart below: horizontal bars per medication showing active period
6. User can:
   a. Select/deselect which parameters to show
   b. Pinch to zoom or use date range selector
   c. Tap a data point → tooltip shows exact value, date, source document
7. If fewer than 2 data points for any test → shows "Not enough data yet" card with message
```

---

## UF-008 — Generate and Share Health Passport

**Actor:** Account Owner (generating) → Clinician (viewing)
**Goal:** Create a shareable, read-only health summary to show a doctor

**Account Owner side:**
```
1. User navigates to Health Passport tab
2. Selects family member
3. Sees a preview of the passport: name, age, blood group, active conditions,
   allergies, current medications, last visit summary, recent abnormal labs
4. Clicks "Generate Passport" (or if one already exists, sees the existing one)
5. Options:
   a. Expiry: 24 hours / 7 days / No expiry
   b. Visible sections: toggles for each section (conditions, medications, allergies, labs)
6. Clicks "Share" → gets:
   a. A shareable URL (copy to clipboard)
   b. A QR code (download or show on screen)
7. Passport appears in "Active Passports" list with creation date, expiry, access count
8. User can:
   - Revoke a passport at any time (link immediately becomes invalid)
   - Create multiple passports (for different contexts / expiry windows)
```

**Clinician side:**
```
1. Patient shows QR code or shares the URL
2. Clinician scans QR or opens URL on any browser — no login, no app install
3. Sees the health passport:
   - Clear header: "Patient-reported health summary — not clinically verified"
   - Patient name and age
   - Blood group
   - Active conditions
   - Known allergies with severity
   - Current medications with dosage
   - Last visit summary
   - Recent abnormal lab flags (last 90 days)
4. Clinician can scroll and read — no interaction beyond viewing
5. Optional: print the passport (A4 print-friendly layout) [V2]
```

**Error paths:**
- Expired link → "This health passport has expired."
- Revoked link → "This health passport is no longer active."
- Invalid UUID → 404 page

---

## UF-009 — Manage Family Members

**Actor:** Account Owner
**Goal:** Add and manage health profiles for family members

```
ADD MEMBER:
1. User clicks "Add Family Member" (accessible from profile member selector or a Family settings screen)
2. Enters: Full name, relationship (Spouse / Parent / Child / Other), date of birth, blood group (optional)
3. Clicks "Add"
4. New member appears in the member selector
5. Member starts with an empty health profile
6. User can now upload documents for this member and manage their profile separately

VIEW/SWITCH MEMBER:
1. On any screen (Profile, Timeline, Charts, Documents, Passport), user sees member selector at top
2. Clicks a member name → all data on screen switches to that member's records
3. Document uploads, passports, edits all apply to the currently selected member

EDIT/REMOVE MEMBER:
1. User goes to Family settings
2. Clicks on a member → Edit (update name/DOB/blood group) or Remove
3. Remove: confirmation dialog → "This will delete all records for [name]. This cannot be undone."
4. On confirm: all documents, extracted data, passports for that member are deleted
```

---

## UF-010 — Document Library Management

**Actor:** Account Owner
**Goal:** View, manage, and delete uploaded documents

```
1. User navigates to Documents tab
2. Sees a list/grid of all uploaded documents for the selected family member
3. Each document card shows:
   - Document type badge (Lab Report, Prescription, etc.)
   - Document date
   - Facility/doctor name (if extracted)
   - Processing status badge (Queued / Processing / Complete / Failed)
   - Uploaded date
4. User can:
   a. Click document → opens Document Detail view
      - Left/top: PDF viewer (PDF.js)
      - Right/bottom: extracted data panel with all fields
      - Each extracted field is editable inline
   b. Download original PDF
   c. Delete document → confirmation dialog → removes document + all extracted data
   d. Retry failed document (re-queues extraction)
   e. Filter documents by type or date range
```

---

## UF-011 — Account Deletion

**Actor:** Account Owner
**Goal:** Permanently delete account and all data

```
1. User goes to Account Settings → "Delete Account"
2. Presented with a summary: "This will permanently delete your account,
   all family member profiles, all uploaded documents, and all extracted health data."
3. Required: user types "DELETE" to confirm
4. Optional: user can download a data export first (see UF-012)
5. On confirm:
   - All data queued for deletion (completed within 30 days per DPDPA 2023)
   - Auth0 account deactivated immediately
   - All active passport URLs revoked immediately
   - User logged out
6. Confirmation email sent: "Your account deletion has been initiated."
```

---

## UF-012 — Data Export

**Actor:** Account Owner
**Goal:** Download a copy of all personal health data

```
1. User goes to Account Settings → "Export My Data"
2. Selects family member(s) to include (default: all)
3. Selects format: JSON (machine-readable) or PDF summary
4. Clicks "Request Export"
5. System generates export asynchronously
6. Email sent when ready with a download link (24-hour expiry)
7. Download includes:
   - All document metadata
   - All extracted entities (medications, diagnoses, labs, etc.)
   - All manual corrections
   - Original PDF files (as a zip)
```

---

## UF-013 — System: Document Processing (Background)

**Actor:** System (Celery worker)
**Goal:** Process an uploaded PDF end-to-end without user interaction

```
1. Document uploaded and validated by Document Service
2. Extraction job pushed to Redis queue
3. Celery worker picks up job:
   a. Fetches PDF from MinIO
   b. Runs pdfminer.six → extracts raw text
   c. If pdfminer.six returns empty/minimal text → retry with pypdf
   d. If both fail → mark job as FAILED (attempt 1/3)
   e. On 3rd failure → mark document as FAILED permanently, trigger failure notification
4. Raw text stored to PostgreSQL on Document record
5. NLP parser processes raw text (spaCy + Med7):
   a. Named entity recognition for medical entities
   b. Rule-based extraction for structured fields (lab values, dosages)
   c. Confidence scoring for each extracted field
   d. Entity deduplication against existing profile
6. Extracted entities stored to respective tables
7. Profile Service rebuilds patient's aggregated profile
8. Notification Service sends "Processing complete" email/notification to user
9. Document status updated to COMPLETE
```
