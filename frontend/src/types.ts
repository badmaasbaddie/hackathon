export type Role = 'PATIENT' | 'ASHA' | 'DOCTOR' | 'FACILITY_ADMIN' | 'SUPER_ADMIN';

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name: string;
  role: Role;
  phone?: string;
  village?: string;
  facility_id?: number;
  is_active: boolean;
}

export interface FamilyMember {
  id: number;
  full_name: string;
  relationship_type: string;
  age: number;
  gender: string;
  chronic_conditions: string;
}

export interface Patient {
  id: number;
  abha_id: string;
  name: string;
  age: number;
  gender: string;
  village: string;
  block: string;
  district: string;
  phone: string;
  blood_group: string;
  emergency_contact?: string;
  chronic_conditions: string;
  assigned_asha_id?: number;
  created_at: string;
  family_members?: FamilyMember[];
}

export interface SymptomIntakeResponse {
  intake_id: number;
  patient_id: number;
  language: string;
  primary_complaint: string;
  duration_days: number;
  severity: string;
  is_emergency: boolean;
  triage_level: 'EMERGENCY' | 'URGENT' | 'ROUTINE';
  red_flags: string[];
  emergency_advice?: string;
  emergency_number: string;
  recommended_specialty: string;
  recommended_facility_type: string;
  ai_doctor_summary: string;
  explanation_patient: string;
  is_simulated_ai: boolean;
}

export interface FacilityReadiness {
  id: number;
  name: string;
  facility_type: 'PHC' | 'CHC' | 'SUB_DISTRICT' | 'DISTRICT_HOSPITAL';
  address: string;
  village_block: string;
  district: string;
  distance_km: number;
  travel_time_mins: number;
  phone: string;
  emergency_contact: string;
  operating_hours: string;
  is_open_now: boolean;
  is_simulated: boolean;
  last_verified_at: string;
  available_doctors_count: number;
  doctor_names: string[];
  diagnostic_tests_available: string[];
  diagnostic_tests_missing: string[];
  medicine_stock_summary: Record<string, 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK'>;
  estimated_queue_wait_mins: number;
  freshness_label: string;
}

export interface Appointment {
  id: number;
  appointment_code: string;
  patient_id: number;
  doctor_id: number;
  facility_id: number;
  scheduled_date: string;
  scheduled_time: string;
  consultation_type: string;
  status: string;
  reason?: string;
  queue_token: string;
  is_simulated: boolean;
  created_at: string;
  patient_name?: string;
  doctor_name?: string;
  facility_name?: string;
}

export interface DiagnosticOrder {
  id: number;
  encounter_id?: number;
  patient_id: number;
  doctor_id: number;
  facility_id: number;
  test_name: string;
  urgency: string;
  status: string;
  scheduled_date?: string;
  created_at: string;
  facility_name?: string;
}

export interface FollowUpPlan {
  id: number;
  encounter_id?: number;
  patient_id: number;
  patient_name?: string;
  doctor_id: number;
  facility_id: number;
  due_date: string;
  instructions: string;
  status: 'SCHEDULED' | 'OVERDUE' | 'COMPLETED' | 'CANCELLED';
  created_at: string;
}

export interface HealthWorkerTask {
  id: number;
  patient_id: number;
  patient_name?: string;
  patient_village?: string;
  patient_phone?: string;
  asha_worker_id?: number;
  follow_up_id?: number;
  task_type: string;
  priority: 'NORMAL' | 'HIGH' | 'CRITICAL';
  due_date: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'ESCALATED';
  visit_notes?: string;
  outcome?: string;
  escalated_to_doctor_id?: number;
  created_at: string;
}

export interface CareTimelineEvent {
  id: number;
  patient_id: number;
  event_type: string;
  title: string;
  description: string;
  facility_id?: number;
  doctor_id?: number;
  actor_name: string;
  actor_role: string;
  metadata_json: string;
  created_at: string;
}

export interface AuditEvent {
  id: number;
  user_id?: number;
  user_name: string;
  role: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  outcome: string;
  ip_address: string;
  details_json: string;
  created_at: string;
}

export interface AdminMetrics {
  total_patients: number;
  total_facilities: number;
  total_doctors: number;
  total_appointments: number;
  completed_appointments: number;
  pending_appointments: number;
  overdue_followups_count: number;
  open_asha_tasks: number;
  resolved_asha_tasks: number;
  critical_emergency_alerts_count: number;
  diagnostic_tests_ordered: number;
  medicine_stock_alerts_count: number;
  data_freshness_pct: number;
  is_demo_metric: boolean;
}

export interface OfflineAction {
  id: string;
  idempotency_key: string;
  action_type: 'BOOK_APPOINTMENT' | 'RESOLVE_TASK';
  payload: any;
  created_at: string;
  status: 'QUEUED' | 'SYNCED' | 'FAILED';
}
