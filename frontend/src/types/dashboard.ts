/**
 * Vet Dashboard TypeScript types
 * Based on spec in docs/0011_my_appointments_dashboard.md
 */

import { Appointment } from './appointment';
import { MedicalRecord } from './medicalRecord';
import { VisitTranscript } from './visitTranscript';

export interface DashboardStats {
  appointments_today: number;
  completed_visits: number;
}

export interface VetDashboard {
  today_appointments: Appointment[];
  stats: DashboardStats;
}

export interface TodayWorkSummary {
  appointments_today: Appointment[];
  next_appointment?: Appointment;
  current_appointment?: Appointment;
  completed_count: number;
  remaining_count: number;
}
