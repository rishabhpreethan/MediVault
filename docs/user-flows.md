# MediVault — User Flows

All actors, their goals, and their complete journeys through the system.

---

## Actors

| Actor | Description | Auth Required |
|---|---|---|
| **Account Owner** | Primary user who creates the account and manages the family | Yes |
| **Family Member (Self)** | The account owner's own health profile (first member auto-created) | Via owner |
| **Managed Profile** | Dependent without their own account (child, elderly parent) — managed entirely by the account owner | Via owner |
| **Linked Account** | Another MediVault user who has accepted a family invitation — has their own account and vault | Yes (own account) |
| **Clinician** | Doctor/nurse who views a shared Health Passport via link/QR | No |
| **Provider (Doctor)** | Licensed medical practitioner who has completed onboarding as PROVIDER role; can look up patients via passport UUID and log encounters | Yes (own account, PROVIDER role) |
| **System** | Background processing (extraction pipeline, notifications) | N/A |

---

## UF-001 — Account Registration and Onboarding

**Actor:** Account Owner (new user)
**Goal:** Create an account and land on their Health Passport overview ready to upload

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
5. Lands on Health Passport overview (default route `/`) with an onboarding prompt:
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
**Goal:** Access their Health Passport overview

```
1. User visits MediVault
2. Clicks "Log In"
3. Chooses method:
   a. Email + password → enters credentials → authenticated
   b. Google OAuth → single click → authenticated
   c. Phone OTP → enters number → receives OTP → enters OTP → authenticated
4. If session is still valid (within 30-day inactivity window) → auto-logged in
5. Lands on Health Passport overview (default route `/`) for their account —
   shows family member cards with blood group, active conditions, allergies summary
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

## UF-009 — Manage Managed Profiles (Dependents Without Accounts)

**Actor:** Account Owner
**Goal:** Create and manage health profiles for dependents who do not have their own MediVault account (e.g., young children, elderly parents)

```
ADD MANAGED PROFILE:
1. User navigates to Family Circle tab → clicks "Add Member" on the family tree
2. Selects "This person doesn't have a MediVault account" (Managed Profile)
3. Enters: Full name, relationship (Spouse / Parent / Child / Other), date of birth, blood group (optional)
4. Clicks "Create Profile"
5. New managed profile node appears on the family tree
6. Profile starts with an empty health history
7. Owner can now upload documents, view records, and manage the passport for this profile

VIEW/SWITCH TO MANAGED PROFILE:
1. From Family Circle tab, owner clicks a managed profile node on the tree
2. "Viewing [Name]'s vault" banner appears at top of screen
3. All health screens (Records, Insights, Health, Passport) switch context to this profile
4. Banner shows "Switch back to my vault" button to return to own vault

EDIT/REMOVE MANAGED PROFILE:
1. User opens managed profile from the family tree → taps edit icon
2. Edit: update name / DOB / blood group → save
3. Remove: confirmation dialog → "This will permanently delete all records for [name]. This cannot be undone."
4. On confirm: all documents, extracted data, and passports for this profile are deleted
```

**Note:** Managed profiles are distinct from Linked Accounts (see UF-015, UF-016). Both types appear on the family tree. Managed profiles show a "Managed by you" badge; Linked Accounts show the member's own avatar.

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

---

## UF-014 — View Family Circle (Family Tree)

**Actor:** Account Owner
**Goal:** See the full family and navigate to any member's vault

```
1. User taps the "Family" tab in the bottom nav (or top nav on desktop)
2. Family Circle page loads, showing:
   - A visual family tree centred on the account owner's node
   - Parents shown above the owner's node
   - Spouse shown at the same level to the left/right
   - Children shown below the owner's node
   - Each node shows: avatar/initials, name, relationship label, member type badge
     (green "You", blue "Account" for linked users, grey "Managed" for managed profiles)
   - Pending invitations shown as dashed-border nodes with "Pending" badge
3. User can:
   a. Tap any active node → opens that member's vault (see UF-009 or UF-019)
   b. Tap any "Pending" node → sees invitation status and option to resend/cancel
   c. Tap the "+" Add to tree button → starts invite flow (UF-015)
   d. Long-press a node → context menu (View vault / Edit / Remove)
```

**Happy path:** Owner with 3 members sees tree → taps child node → switches vault context in < 2 seconds

---

## UF-015 — Invite an Existing MediVault User to the Family

**Actor:** Account Owner
**Goal:** Invite another MediVault user (who already has an account) to join the family circle

```
1. On Family Circle page, owner taps "+ Add to tree"
2. Selects "Invite via email"
3. Enters the invitee's email address
4. Selects relationship: Parent / Spouse / Child / Sibling / Other
5. Optionally positions the node on the tree (parent level / same level / child level)
6. Taps "Send Invitation"
7. System:
   a. Looks up the email → finds an existing MediVault account
   b. Creates a family_invitation record (status=PENDING, token=UUID, expires 7 days)
   c. Sends an in-app notification to the invitee (type=FAMILY_INVITE)
   d. Sends an invitation email to the invitee's registered address
   e. Returns confirmation to the owner
8. A dashed-border "Pending" node appears on the family tree at the chosen position
9. Owner sees: "Invitation sent to [email]. Waiting for them to accept."
```

**Error paths:**
- Email not found in MediVault → system routes to UF-016 (new user invite) automatically
- Invitation already pending for this email → "You've already invited [email]. Resend?"
- Invitee has already declined → "This person declined your last invitation. Send a new one?"

---

## UF-016 — Invite a New User (No MediVault Account Yet)

**Actor:** Account Owner
**Goal:** Invite someone who does not yet have a MediVault account

```
1. Owner enters an email that is not found in the MediVault user database (during UF-015 step 3)
2. System detects: email not registered
3. Owner sees: "[email] doesn't have a MediVault account yet. Send them an invitation to join?"
4. Owner taps "Send Invitation Anyway"
5. System:
   a. Creates a family_invitation record (invited_user_id = NULL, status=PENDING, token=UUID, expires 7 days)
   b. Sends an invitation email to that address:
      "You've been invited by [Owner Name] to join their family on MediVault.
       Click here to create your account and accept the invitation."
   c. The invite link contains the invitation token: /invite/:token
6. "Pending" node appears on the family tree
7. When the recipient creates a MediVault account and visits /invite/:token:
   a. Invitation is matched to their new user_id
   b. They are shown the acceptance screen (UF-017)
```

**Error paths:**
- Invitee creates account but token is expired (>7 days) → "This invitation has expired. Ask [Owner Name] to resend it."
- Invitee tries to use token after already accepting → "You're already part of this family."

---

## UF-017 — Accept a Family Invitation (Invitee Flow)

**Actor:** Linked Account (invitee — existing or newly registered MediVault user)
**Goal:** Accept the family invitation and join the family circle

```
EXISTING USER — IN-APP NOTIFICATION:
1. Invitee logs into MediVault
2. Sees a notification badge on the bell icon
3. Opens notification centre → sees "Family invitation from [Owner Name]"
   - Notification body: "[Owner Name] has invited you to join their family as [Relationship]."
   - Two action buttons: "Accept" and "Decline"
4. Taps "Accept":
   a. family_memberships record created (role=MEMBER, can_invite=FALSE)
   b. invitation status → ACCEPTED
   c. Invitee appears as a solid node on the owner's family tree
   d. In-app notification sent to the owner: "[Invitee Name] accepted your family invitation"
   e. Invitee's own family tree now shows the owner's node as well

EXISTING USER — EMAIL LINK:
1. Invitee clicks the link in the invitation email
2. Redirected to /invite/:token → prompted to log in if not already
3. After login, sees the acceptance screen (same as notification flow above from step 4)

NEW USER — AFTER ACCOUNT CREATION:
1. Invitee visits /invite/:token → prompted to create an account
2. Creates account → completes onboarding
3. Immediately shown the acceptance screen:
   "[Owner Name] has invited you to join their family as [Relationship]. Accept?"
4. Accepts → same as step 4a–4e above

DECLINE FLOW:
1. Invitee taps "Decline"
2. Invitation status → DECLINED
3. In-app notification sent to owner: "[Invitee Name] declined your family invitation"
4. Owner sees a prompt on the family tree node: "Declined — resend invitation?"
```

**Key rule:** Accepting an invitation does NOT automatically share any vault data.
Vault sharing requires an explicit vault access grant (see UF-018).

---

## UF-018 — Manage Vault Access Permissions

**Actor:** Account Owner (the family creator / family admin)
**Goal:** Grant or revoke access to a family member's vault

```
GRANT ACCESS:
1. Owner opens Family Circle → taps a linked account member's node
2. Taps "Manage Access"
3. Sees two permission panels:
   a. "Access to [Member]'s vault" — toggle: can this person view [Member]'s records?
   b. "[Member]'s access to others" — toggle per member: can [Member] view [other]'s records?
4. Owner enables "Can view [Target Member]'s vault" for the grantee
5. System creates a vault_access_grant record:
   (grantee_user_id=[member], target_user_id=[target], access_type=READ)
6. Grantee immediately sees the target member's node on their family tree as accessible
7. Email/in-app notification sent to the grantee:
   "[Owner Name] has shared [Target Name]'s health records with you."

GRANT INVITE PERMISSION:
1. Owner enables "Can invite others to the family" for a member
2. family_memberships.can_invite → TRUE for that member
3. That member can now send invitations on behalf of the family

REVOKE ACCESS:
1. Owner disables a previously enabled toggle
2. vault_access_grant record deleted
3. Grantee can no longer access the target vault
4. If grantee is currently viewing the target vault → banner shows "Access has been revoked"
   and they are redirected to their own vault
5. In-app notification sent to grantee: "Your access to [Target Name]'s records has been removed."
```

**Access model summary:**
- Only the family creator (owner) can manage access by default
- Any member with `can_invite=TRUE` can also send invitations
- Access grants are explicitly set — no implicit sharing on family join

---

## UF-019 — View a Delegated Vault (Linked Account Accessing Another Member's Vault)

**Actor:** Linked Account (with a vault access grant)
**Goal:** View health records of a family member whose vault has been shared with them

```
1. Linked account user opens Family Circle tab
2. Sees the family tree with nodes they have access to highlighted (accessible = solid, no-access = greyed with lock icon)
3. Taps an accessible node (e.g., parent's node)
4. "Viewing [Parent Name]'s vault" banner appears (teal) at top of screen
5. All health screens (Records, Insights, Health, Passport) switch context to the parent's records
6. This user can view records but cannot:
   - Upload documents on behalf of the parent
   - Edit extracted data
   - Create/revoke passports
   - Manage other members' access
7. To return: taps "Switch back to my vault" in the banner
```

**Read-only rule:** Vault access grants are READ access only in V1. Write access is out of scope.
**Error path:** If access grant has been revoked since last session → user sees "You no longer have access to [Name]'s vault." and is redirected to their own vault.

---

## UF-020 — User Onboarding (Post-Registration)

**Actor:** Account Owner (newly registered)
**Goal:** Complete mandatory onboarding to set up health baseline and choose role

```
PATIENT PATH:
1. After first login (onboarding_completed=false), user is redirected to /onboarding
2. Step 1: Confirm/enter full name, date of birth
3. Step 2: Select blood group (pill buttons: A+, A-, B+, B-, O+, O-, AB+, AB-, Unknown)
4. Step 3: Choose role — "I'm a Patient" or "I'm a Healthcare Provider"
5. Step 4 (if Patient): Enter height (cm) and weight (kg) — optional but encouraged
6. Step 5: Add known allergies (free-text tags, comma-separated)
7. Submit → POST /auth/onboarding → onboarding_completed=true, role=PATIENT
8. Redirect to home page (/)

PROVIDER PATH:
1–3. Same as Patient path
4. Step 4 (if Provider): Enter medical licence number + registration council (e.g., NMC, state medical council)
5. Step 5: Allergies (same as patient — providers also have a health profile)
6. Submit → POST /auth/onboarding → onboarding_completed=true, role=PROVIDER
7. System queues licence verification task (verify_licence_task)
8. Provider sees "Provider" tab in nav; can access /provider dashboard
9. Until licence is verified, provider can still use patient features but lookup may be gated
```

**Error paths:**
- If onboarding_completed=false, all protected routes redirect to /onboarding
- If mandatory fields missing → inline validation errors

---

## UF-021 — Provider Looks Up Patient via Passport UUID

**Actor:** Provider (Doctor)
**Goal:** Access a patient's health records using their shared passport UUID

```
1. Provider navigates to Provider tab (/provider)
2. Enters the patient's passport UUID (shown on patient's Health Passport page or shared via QR code)
3. Clicks "Request Access"
4. System:
   a. Validates the passport UUID exists and is active
   b. Identifies the patient (family member + owning user)
   c. Creates a provider_access_request (status=PENDING, expires_at=now+15min)
   d. Sends in-app notification to the patient (type=PROVIDER_ACCESS_REQUEST)
5. Provider sees "Waiting for patient approval..." with a polling indicator
6. System polls GET /provider/access-requests/{id}/status every 3 seconds
7. If patient ACCEPTS → provider is redirected to /provider/patient/{requestId}
8. If patient DECLINES → provider sees "Access declined by patient"
9. If 15 minutes elapse → request expires, provider sees "Request expired"
```

**Error paths:**
- Invalid passport UUID → "No active passport found with this ID"
- Passport expired/revoked → "This passport is no longer active"
- Provider not verified → may be gated (depends on verification_status)

---

## UF-022 — Patient Responds to Provider Access Request

**Actor:** Account Owner (Patient)
**Goal:** Accept or decline a doctor's request to view health records

```
1. Patient receives in-app notification: "Dr. [Provider Name] is requesting access to your health records"
2. Notification appears in:
   a. Bell icon badge (unread count increments)
   b. Notification centre dropdown
3. Notification has inline "Accept" and "Decline" buttons
4. Patient taps "Accept":
   a. POST /provider/access-requests/{id}/respond with action=ACCEPT
   b. Request status → ACCEPTED
   c. Provider is notified (their polling picks up the status change)
   d. Provider can now view patient's clinical data for this session
5. Patient taps "Decline":
   a. POST /provider/access-requests/{id}/respond with action=DECLINE
   b. Request status → DECLINED
   c. Provider sees "Access declined" on their polling screen
```

**Key rules:**
- Access is time-limited: the provider_access_request has a 15-minute TTL from creation
- Patient can only respond while status=PENDING (not after expiry)
- All access requests are logged in notification history for auditability

---

## UF-023 — Provider Logs a Medical Encounter

**Actor:** Provider (Doctor)
**Goal:** Record clinical notes, diagnoses, and prescriptions after examining a patient

```
1. Provider has an ACCEPTED access request and is viewing /provider/patient/{requestId}
2. Left panel shows patient identity (name, DOB, blood group, height, weight)
3. Centre panel shows encounter history (previous encounters logged by this or other providers)
4. Right panel: "Log Encounter" form with fields:
   - Encounter date (defaults to today)
   - Chief complaint (free text)
   - Diagnoses (dynamic list: condition name per row)
   - Medications (dynamic list: drug name, dosage, frequency per row)
   - Follow-up date (optional date picker)
5. Provider fills out the form and clicks "Save Encounter"
6. System:
   a. POST /provider/encounters
   b. Creates medical_encounter record
   c. Creates Diagnosis records linked to the encounter (encounter_id FK)
   d. Creates Medication records linked to the encounter (encounter_id FK)
7. Encounter appears in the patient's timeline and health profile
8. Provider can log multiple encounters per access request session
```

**Error paths:**
- Access request expired → "Your access session has expired. Request new access."
- Missing required fields → inline validation
