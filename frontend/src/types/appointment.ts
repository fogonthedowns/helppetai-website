/**
 * Appointment TypeScript types
 * Based on backend appointment models and API
 */

export enum AppointmentType {
  CHECKUP = 'checkup',
  EMERGENCY = 'emergency',
  SURGERY = 'surgery',
  CONSULTATION = 'consultation'
}

export enum AppointmentStatus {
  SCHEDULED = 'scheduled',
  CONFIRMED = 'confirmed',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show'
}

export interface PetSummary {
  id: string;
  name: string;
  species: string;
  breed?: string;
}

export interface Appointment {
  id: string;
  practice_id: string;
  pet_owner_id: string;
  assigned_vet_user_id?: string;
  created_by_user_id: string;
  appointment_date: string; // ISO datetime string
  duration_minutes: number;
  appointment_type: AppointmentType;
  status: AppointmentStatus;
  title: string;
  description?: string;
  notes?: string;
  pets: PetSummary[];
  created_at: string;
  updated_at: string;
}

export interface AppointmentCreate {
  practice_id: string;
  pet_owner_id: string;
  assigned_vet_user_id?: string;
  appointment_date: string;
  duration_minutes?: number;
  appointment_type?: AppointmentType;
  title: string;
  description?: string;
  notes?: string;
  pet_ids: string[];
}

export interface AppointmentUpdate {
  assigned_vet_user_id?: string;
  appointment_date?: string;
  duration_minutes?: number;
  appointment_type?: AppointmentType;
  status?: AppointmentStatus;
  title?: string;
  description?: string;
  notes?: string;
  pet_ids?: string[];
}
