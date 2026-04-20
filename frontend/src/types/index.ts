export interface ApiError {
  error: string
  message: string
}

export interface FamilyMember {
  member_id: string
  user_id: string
  full_name: string
  relationship: 'SELF' | 'SPOUSE' | 'PARENT' | 'CHILD' | 'OTHER'
  date_of_birth: string | null
  blood_group: string | null
  is_self: boolean
}

export type DocumentType = 'LAB_REPORT' | 'PRESCRIPTION' | 'DISCHARGE_SUMMARY' | 'OTHER'
export type ProcessingStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETE' | 'FAILED' | 'MANUAL_REVIEW'
export type ConfidenceScore = 'HIGH' | 'MEDIUM' | 'LOW'
export type LabFlag = 'NORMAL' | 'HIGH' | 'LOW' | 'CRITICAL'

export interface Document {
  document_id: string
  member_id: string
  document_type: DocumentType
  document_date: string | null
  facility_name: string | null
  doctor_name: string | null
  processing_status: ProcessingStatus
  uploaded_at: string
  processed_at: string | null
}

export interface Medication {
  medication_id: string
  drug_name: string
  drug_name_normalized: string | null
  dosage: string | null
  frequency: string | null
  route: string | null
  start_date: string | null
  end_date: string | null
  is_active: boolean
  confidence_score: ConfidenceScore
  is_manual_entry: boolean
}

export interface LabResult {
  result_id: string
  test_name: string
  test_name_normalized: string | null
  value: number | null
  value_text: string | null
  unit: string | null
  reference_low: number | null
  reference_high: number | null
  flag: LabFlag
  test_date: string | null
  confidence_score: ConfidenceScore
  is_manual_entry: boolean
}

export interface Diagnosis {
  diagnosis_id: string
  condition_name: string
  icd10_code: string | null
  diagnosed_date: string | null
  status: 'ACTIVE' | 'RESOLVED' | 'CHRONIC' | 'UNKNOWN'
  confidence_score: ConfidenceScore
  is_manual_entry: boolean
}

export interface Allergy {
  allergy_id: string
  allergen_name: string
  reaction_type: string | null
  severity: 'MILD' | 'MODERATE' | 'SEVERE' | 'UNKNOWN'
  confidence_score: ConfidenceScore
  is_manual_entry: boolean
}

export interface Vital {
  vital_id: string
  vital_type: string
  value: number
  unit: string | null
  recorded_date: string | null
  confidence_score: ConfidenceScore
}

export interface HealthProfile {
  member: FamilyMember
  medications: Medication[]
  diagnoses: Diagnosis[]
  allergies: Allergy[]
  recent_labs: LabResult[]
  recent_vitals: Vital[]
}

export interface SharedPassport {
  passport_id: string
  member_id: string
  is_active: boolean
  expires_at: string | null
  visible_sections: string[]
  created_at: string
  access_count: number
}

export interface TimelineEvent {
  event_id: string
  event_type: 'VISIT' | 'LAB' | 'PRESCRIPTION' | 'PROCEDURE'
  date: string
  title: string
  summary: string
  document_id: string | null
}

// Family Circle types
export type InvitationStatus = 'PENDING' | 'ACCEPTED' | 'DECLINED' | 'EXPIRED' | 'REVOKED'
export type MembershipRole = 'ADMIN' | 'MEMBER'

export interface Family {
  family_id: string
  name: string | null
  created_by_user_id: string
  created_at: string
}

export interface FamilyInvitation {
  invitation_id: string
  family_id: string
  invited_by_user_id: string
  invited_email: string
  invited_user_id: string | null
  relationship: string
  status: InvitationStatus
  token: string
  expires_at: string
  created_at: string
}

export interface FamilyMembership {
  membership_id: string
  family_id: string
  user_id: string
  role: MembershipRole
  can_invite: boolean
  joined_at: string
  family_owner_user_id: string | null
  family_owner_name: string | null
  relationship: string | null
}

export interface VaultAccessGrant {
  grant_id: string
  family_id: string
  grantee_user_id: string
  target_user_id: string
  access_type: string
  granted_by_user_id: string
  granted_at: string
}

export interface FamilyCircle {
  family: Family | null
  self_member: FamilyMember | null
  managed_profiles: FamilyMember[]
  memberships: FamilyMembership[]
  family_members: FamilyMembership[]
  pending_invitations_sent: FamilyInvitation[]
  pending_invitations_received: FamilyInvitation[]
}

export interface InviteTokenInfo {
  invitation_id: string
  family_id: string
  inviter_name: string | null
  relationship: string
  status: InvitationStatus
  expires_at: string
}

// Notification types
export type NotificationType =
  | 'FAMILY_INVITE'
  | 'INVITE_ACCEPTED'
  | 'INVITE_DECLINED'
  | 'VAULT_ACCESS_GRANTED'
  | 'VAULT_ACCESS_REVOKED'
  | 'PROCESSING_COMPLETE'
  | 'EXTRACTION_FAILED'

export interface Notification {
  notification_id: string
  user_id: string
  type: NotificationType
  title: string
  body: string
  is_read: boolean
  action_url: string | null
  metadata: Record<string, unknown> | null
  created_at: string
}

export interface PaginatedNotifications {
  items: Notification[]
  total: number
  page: number
  limit: number
}
