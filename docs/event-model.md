# MediVault — Event Model

Captures the system as a sequence of **Commands** → **Events** → **Read Models** across actor swim lanes.

Format per entry: `[Actor] → Command → Event(s) → Read Model(s) updated`

---

## Legend

| Symbol | Meaning |
|---|---|
| **CMD** | Command — intent from an actor |
| **EVT** | Domain Event — something that happened (past tense, immutable) |
| **RM** | Read Model — projection/view updated as a result |
| **POLICY** | Automated reaction: when EVT happens, system does X |

---

## Swim Lane 1 — Authentication & Identity

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 1.1 | Owner | RegisterWithEmail(email, password) | UserRegistered, VerificationEmailSent | UserAccountRM |
| 1.2 | Owner | VerifyEmail(token) | EmailVerified | UserAccountRM |
| 1.3 | Owner | RegisterWithGoogle(oauth_token) | UserRegistered, EmailVerified | UserAccountRM |
| 1.4 | Owner | RegisterWithPhone(phone, otp) | UserRegistered, PhoneVerified | UserAccountRM |
| 1.5 | Owner | Login(credentials) | SessionCreated | SessionRM |
| 1.6 | Owner | RequestPasswordReset(email) | PasswordResetRequested, ResetEmailSent | — |
| 1.7 | Owner | ResetPassword(token, new_password) | PasswordReset | SessionRM (invalidated) |
| 1.8 | System | SessionInactivityCheck | SessionExpired | SessionRM |
| 1.9 | Owner | DeleteAccount | AccountDeletionInitiated | UserAccountRM, all member RMs purged |

**POLICY:** On UserRegistered → auto-create SelfFamilyMember for this user

---

## Swim Lane 2 — Family Management

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 2.1 | Owner | CreateSelfProfile(name, dob, blood_group) | SelfMemberProfileCreated | FamilyMembersRM, HealthProfileRM |
| 2.2 | Owner | AddFamilyMember(name, relationship, dob) | FamilyMemberAdded | FamilyMembersRM |
| 2.3 | Owner | UpdateFamilyMember(member_id, fields) | FamilyMemberUpdated | FamilyMembersRM, HealthProfileRM |
| 2.4 | Owner | RemoveFamilyMember(member_id) | FamilyMemberRemoved, AllMemberDataPurged | FamilyMembersRM, HealthProfileRM, DocumentsRM, TimelineRM |
| 2.5 | Owner | SelectActiveMember(member_id) | ActiveMemberChanged | ActiveMemberSessionRM |

---

## Swim Lane 3 — Document Upload

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 3.1 | Owner | SelectFiles(files[], member_id) | FilesSelected | UploadQueueRM |
| 3.2 | System | ValidateFile(file) | FileValidated OR FileRejected(reason) | UploadQueueRM |
| 3.3 | System | VirusScanFile(file) | VirusScanPassed OR VirusScanFailed | UploadQueueRM |
| 3.4 | System | DetectTextLayer(file) | TextLayerDetected OR ScannedDocumentDetected | UploadQueueRM |
| 3.5 | Owner | ConfirmDocumentMetadata(doc_id, type, date) | DocumentMetadataConfirmed | DocumentsRM |
| 3.6 | System | StoreEncryptedFile(file, member_id) | FileStoredInMinIO | DocumentsRM |
| 3.7 | System | EnqueueExtractionJob(doc_id) | ExtractionJobQueued | DocumentsRM(status=QUEUED) |
| 3.8 | Owner | DeleteDocument(doc_id) | DocumentDeleted, ExtractedDataPurged | DocumentsRM, HealthProfileRM, TimelineRM |
| 3.9 | Owner | RetryFailedDocument(doc_id) | ExtractionJobQueued | DocumentsRM(status=QUEUED) |

**POLICY:** On ScannedDocumentDetected → reject file, notify user with friendly message
**POLICY:** On ExtractionJobQueued → trigger Swim Lane 4 (Extraction Pipeline)

---

## Swim Lane 4 — PDF Extraction Pipeline

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 4.1 | System | PickUpExtractionJob(job_id) | ExtractionJobStarted | DocumentsRM(status=PROCESSING) |
| 4.2 | System | ExtractText_pdfminer(doc_id) | RawTextExtracted(text, library=pdfminer) OR ExtractionAttemptFailed |  DocumentsRM |
| 4.3 | System | ExtractText_pypdf(doc_id) | RawTextExtracted(text, library=pypdf) OR ExtractionAttemptFailed | DocumentsRM |
| 4.4 | System | StoreRawText(doc_id, text) | RawTextStored | DocumentsRM |
| 4.5 | System | RecordExtractionFailure(doc_id, attempt) | ExtractionAttemptFailed(attempt=N) | DocumentsRM |
| 4.6 | System | MarkDocumentFailed(doc_id) | ExtractionPermanentlyFailed | DocumentsRM(status=FAILED) |

**POLICY:** On RawTextStored → trigger Swim Lane 5 (NLP Processing)
**POLICY:** On ExtractionAttemptFailed AND attempt < 3 → re-enqueue job (retry after backoff)
**POLICY:** On ExtractionAttemptFailed AND attempt = 3 → MarkDocumentFailed, send failure notification

---

## Swim Lane 5 — NLP Medical Data Extraction

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 5.1 | System | ParseMedications(raw_text, doc_id) | MedicationsExtracted([{name, dosage, freq, duration, confidence}]) | MedicationsRM |
| 5.2 | System | ParseLabResults(raw_text, doc_id) | LabResultsExtracted([{test, value, unit, ref_range, flag, confidence}]) | LabResultsRM |
| 5.3 | System | ParseDiagnoses(raw_text, doc_id) | DiagnosesExtracted([{condition, icd10, date, status, confidence}]) | DiagnosesRM |
| 5.4 | System | ParseAllergies(raw_text, doc_id) | AllergiesExtracted([{allergen, reaction, severity, confidence}]) | AllergiesRM |
| 5.5 | System | ParseVitals(raw_text, doc_id) | VitalsExtracted([{type, value, unit, date, confidence}]) | VitalsRM |
| 5.6 | System | ParseDoctorInfo(raw_text, doc_id) | DoctorInfoExtracted({name, specialization, facility, date}) | DoctorsRM |
| 5.7 | System | DeduplicateConditions(member_id) | ChronicConditionConsolidated OR NewConditionAdded | DiagnosesRM, HealthProfileRM |
| 5.8 | System | AssignConfidenceScores(doc_id) | ConfidenceScoresAssigned | All entity RMs |
| 5.9 | System | FlagLowConfidenceFields(doc_id) | LowConfidenceFieldsFlagged | ReviewQueueRM |
| 5.10 | System | MarkDocumentComplete(doc_id) | DocumentProcessingComplete | DocumentsRM(status=COMPLETE) |

**POLICY:** On DocumentProcessingComplete → rebuild HealthProfileRM for member, trigger notification

---

## Swim Lane 6 — Manual Data Management

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 6.1 | Owner | CorrectExtractedField(entity_id, corrected_value) | ExtractedFieldCorrected | entity RM, HealthProfileRM |
| 6.2 | Owner | AddMedicationManually(member_id, data) | MedicationManuallyAdded | MedicationsRM, HealthProfileRM |
| 6.3 | Owner | AddDiagnosisManually(member_id, data) | DiagnosisManuallyAdded | DiagnosesRM, HealthProfileRM |
| 6.4 | Owner | AddAllergyManually(member_id, data) | AllergyManuallyAdded | AllergiesRM, HealthProfileRM |
| 6.5 | Owner | MarkMedicationDiscontinued(med_id) | MedicationDiscontinued | MedicationsRM, HealthProfileRM |
| 6.6 | Owner | DeleteExtractedEntity(entity_id) | ExtractedEntityDeleted | entity RM, HealthProfileRM |

---

## Swim Lane 7 — Health Profile

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 7.1 | Owner | ViewHealthProfile(member_id) | HealthProfileViewed | — (read only) |
| 7.2 | System | RebuildHealthProfile(member_id) | HealthProfileRebuilt | HealthProfileRM |

**POLICY:** On any entity EVT (extracted, corrected, added, deleted) → RebuildHealthProfile

---

## Swim Lane 8 — Health Timeline

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 8.1 | Owner | ViewTimeline(member_id, filters) | TimelineViewed | — (read only) |
| 8.2 | System | AddTimelineEvent(event_type, date, member_id, doc_id) | TimelineEventAdded | TimelineRM |
| 8.3 | System | RemoveTimelineEvent(doc_id) | TimelineEventsRemovedForDocument | TimelineRM |

**POLICY:** On DocumentProcessingComplete → AddTimelineEvent for each extracted entity
**POLICY:** On DocumentDeleted → RemoveTimelineEvent for all events from that document

---

## Swim Lane 9 — Health Passport

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 9.1 | Owner | GeneratePassport(member_id, expiry, sections) | PassportGenerated(uuid) | PassportsRM |
| 9.2 | Owner | UpdatePassportSettings(passport_id, settings) | PassportSettingsUpdated | PassportsRM |
| 9.3 | Owner | RevokePassport(passport_id) | PassportRevoked | PassportsRM |
| 9.4 | Clinician | ViewPassport(uuid) | PassportViewed(timestamp, ip_hash) | PassportAccessLogRM |
| 9.5 | System | CheckPassportExpiry(passport_id) | PassportExpired | PassportsRM |

**POLICY:** On PassportGenerated → generate QR code
**POLICY:** On PassportViewed → append to access log, update view count on PassportsRM

---

## Swim Lane 10 — Notifications

| # | Actor | CMD | EVT | RM Updated |
|---|---|---|---|---|
| 10.1 | System | SendProcessingCompleteNotification(user_id, doc_id) | NotificationSent | NotificationsRM |
| 10.2 | System | SendExtractionFailedNotification(user_id, doc_id) | NotificationSent | NotificationsRM |
| 10.3 | System | SendPassportAccessedNotification(user_id, passport_id) | NotificationSent | NotificationsRM |
| 10.4 | System | SendVerificationEmail(user_id) | NotificationSent | NotificationsRM |

---

## Read Models Summary

| Read Model | Description | Rebuilt By |
|---|---|---|
| `UserAccountRM` | User account status, email, phone, auth state | Auth events |
| `SessionRM` | Active sessions | Login/logout events |
| `FamilyMembersRM` | List of all family members for a user | Family management events |
| `ActiveMemberSessionRM` | Which member is currently selected in the UI session | SelectActiveMember |
| `DocumentsRM` | Document library with status, metadata per member | Document + extraction events |
| `UploadQueueRM` | Current upload/validation progress | Upload events |
| `HealthProfileRM` | Aggregated health profile per member | All entity events |
| `MedicationsRM` | Extracted + manual medications per member | Medication events |
| `LabResultsRM` | Extracted lab results per member | Lab events |
| `DiagnosesRM` | Extracted + manual diagnoses per member | Diagnosis events |
| `AllergiesRM` | Extracted + manual allergies per member | Allergy events |
| `VitalsRM` | Extracted vitals per member | Vitals events |
| `DoctorsRM` | Extracted doctor/facility info per member | Doctor events |
| `TimelineRM` | Chronological medical events per member | Timeline events |
| `PassportsRM` | Active/revoked passports per member | Passport events |
| `PassportAccessLogRM` | Who accessed which passport when | PassportViewed events |
| `ReviewQueueRM` | Fields flagged for patient review (low confidence) | Confidence scoring events |
| `NotificationsRM` | Notification history | Notification sent events |
