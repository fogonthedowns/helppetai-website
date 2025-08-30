/**
 * Medical Record TypeScript types
 */

export interface MedicalRecord {
  id: string;
  pet_id: string;
  version: number;
  is_current: boolean;
  record_type: string;
  title: string;
  description?: string;
  medical_data?: Record<string, any>;
  visit_date: string; // ISO date string
  veterinarian_name?: string;
  clinic_name?: string;
  diagnosis?: string;
  treatment?: string;
  medications?: string;
  follow_up_required: boolean;
  follow_up_date?: string; // ISO date string
  weight?: number;
  temperature?: number;
  cost?: number;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  is_follow_up_due: boolean;
  days_since_visit: number;
}

export interface MedicalRecordWithRelations extends MedicalRecord {
  pet: {
    id: string;
    name: string;
    species: string;
    breed?: string;
  };
  created_by: {
    id: string;
    full_name?: string;
    email?: string;
  };
}

export interface MedicalRecordFormData {
  record_type: string;
  title: string;
  description?: string;
  medical_data?: Record<string, any>;
  visit_date: string;
  veterinarian_name?: string;
  clinic_name?: string;
  diagnosis?: string;
  treatment?: string;
  medications?: string;
  follow_up_required: boolean;
  follow_up_date?: string;
  weight?: number;
  temperature?: number;
  cost?: number;
}

export interface MedicalRecordCreateRequest extends MedicalRecordFormData {
  pet_id: string;
}

export interface MedicalRecordUpdateRequest extends Partial<MedicalRecordFormData> {}

export interface MedicalRecordListResponse {
  records: MedicalRecord[];
  total: number;
  current_records_count: number;
  historical_records_count: number;
}

export interface MedicalRecordTimelineResponse {
  pet_id: string;
  pet_name: string;
  records_by_date: MedicalRecord[];
  follow_up_due: MedicalRecord[];
  recent_weight?: number;
  weight_trend?: string;
}

export const MEDICAL_RECORD_TYPES = [
  'checkup',
  'vaccination',
  'surgery',
  'emergency',
  'dental',
  'grooming',
  'diagnostic',
  'treatment',
  'follow_up',
  'other'
] as const;

export type MedicalRecordType = typeof MEDICAL_RECORD_TYPES[number];

export const MEDICAL_RECORD_TYPE_LABELS: Record<MedicalRecordType, string> = {
  checkup: 'Regular Checkup',
  vaccination: 'Vaccination',
  surgery: 'Surgery',
  emergency: 'Emergency Visit',
  dental: 'Dental Care',
  grooming: 'Grooming',
  diagnostic: 'Diagnostic Test',
  treatment: 'Treatment',
  follow_up: 'Follow-up Visit',
  other: 'Other'
};

export const MEDICAL_RECORD_TYPE_COLORS: Record<MedicalRecordType, string> = {
  checkup: 'bg-blue-100 text-blue-800',
  vaccination: 'bg-green-100 text-green-800',
  surgery: 'bg-red-100 text-red-800',
  emergency: 'bg-red-100 text-red-800',
  dental: 'bg-yellow-100 text-yellow-800',
  grooming: 'bg-purple-100 text-purple-800',
  diagnostic: 'bg-indigo-100 text-indigo-800',
  treatment: 'bg-orange-100 text-orange-800',
  follow_up: 'bg-teal-100 text-teal-800',
  other: 'bg-gray-100 text-gray-800'
};

export const MEDICAL_DATA_TEMPLATES: Record<string, Record<string, string>> = {
  vaccination: {
    vaccine_name: '',
    vaccine_type: '',
    batch_number: '',
    expiration_date: '',
    next_due_date: '',
    adverse_reactions: ''
  },
  surgery: {
    procedure_name: '',
    anesthesia_type: '',
    complications: '',
    recovery_notes: '',
    suture_removal_date: '',
    activity_restrictions: ''
  },
  checkup: {
    heart_rate: '',
    respiratory_rate: '',
    blood_pressure: '',
    body_condition_score: '',
    dental_condition: '',
    skin_condition: '',
    eye_condition: '',
    ear_condition: ''
  },
  diagnostic: {
    test_type: '',
    test_results: '',
    reference_ranges: '',
    abnormal_findings: '',
    recommendations: ''
  }
};
