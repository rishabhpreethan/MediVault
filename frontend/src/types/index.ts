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

export type DocumentType = 'LAB_REPORT' | 'PRESCRIPTION' | 'DISCHARGE' | 'SCAN' | 'OTHER'
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
