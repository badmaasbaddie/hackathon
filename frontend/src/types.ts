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
  care_pathways?: CarePathway[];
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
  clinical_services_available?: string[];
  clinical_services_missing?: string[];
  medicine_stock_summary: Record<string, 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK'>;
  estimated_queue_wait_mins: number;
  freshness_label: string;
  latitude: number;
  longitude: number;
  doctors: Doctor[];
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
  total_asha_workers: number;
  total_authorities: number;
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

export interface ScheduleSlot {
  day_of_week: string;
  start_time: string;
  end_time: string;
}

export interface Doctor {
  id: number;
  name: string;
  specialty: string;
  qualification: string;
  experience_years: number;
  facility_id: number;
  phone?: string;
  is_available_today: boolean;
  last_roster_update: string;
  schedule: ScheduleSlot[];
}

export interface FacilityService {
  id: number;
  facility_id: number;
  name: string;
  category: string;
  is_available: boolean;
  notes?: string;
  updated_at: string;
}

export interface InventoryItem {
  id: number;
  facility_id: number;
  medicine_name: string;
  quantity_in_stock: number;
  unit: string;
  reorder_level: number;
  stock_status: 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK';
  last_verified_at: string;
}

export interface FacilityManage {
  facility: FacilityReadiness;
  doctors: Doctor[];
  services: FacilityService[];
  inventory: InventoryItem[];
}

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string;
  mode: 'SAFETY_RULES' | 'LLM' | 'DEMO_FALLBACK';
  model?: string;
  triage: SymptomIntakeResponse;
  sources: { id: string; title: string; source: string }[];
}

export interface PrescriptionItem {
  id: number;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration_days: number;
  instructions?: string;
  collected_status: string;
}

export interface EncounterDetail {
  id: number;
  appointment_id?: number;
  patient_id: number;
  doctor_id: number;
  facility_id: number;
  encounter_date: string;
  chief_complaints: string;
  clinical_notes: string;
  diagnosis: string;
  vital_bp: string;
  vital_pulse: number;
  vital_temp: number;
  vital_spo2: number;
  clinician_risk_flag: string;
  doctor_name?: string;
  facility_name?: string;
  prescriptions: { id: number; prescription_code: string; created_at: string; items: PrescriptionItem[] }[];
}

export interface Reminder {
  id: number;
  follow_up_id: number;
  channel: string;
  message: string;
  scheduled_time: string;
  status: string;
}

export interface Intake {
  id: number;
  raw_input: string;
  language: string;
  primary_complaint: string;
  triage_level: string;
  red_flags_detected: string;
  ai_summary_for_doctor?: string;
  recommended_specialty: string;
  created_at: string;
}

export interface PatientRecord {
  patient: Patient;
  encounters: EncounterDetail[];
  diagnostic_orders: DiagnosticOrder[];
  follow_ups: FollowUpPlan[];
  reminders: Reminder[];
  appointments: Appointment[];
  latest_intake?: Intake;
}

export interface RegisterPayload {
  name: string;
  age: number;
  gender: string;
  phone: string;
  village: string;
  block?: string;
  district?: string;
  blood_group?: string;
  emergency_contact?: string;
  chronic_conditions?: string;
}

export interface AdminActivity {
  appointments_by_status: Record<string, number>;
  appointments_by_facility: { facility: string; count: number }[];
  intakes_by_triage_level: Record<string, number>;
  registrations_last_24h: number;
  logins_last_24h: number;
  access_denials_total: number;
  impact: ImpactMetrics;
  recent_appointments: Appointment[];
}

export type Lang = 'hi' | 'en' | 'mr';

export interface CareTeamMember {
  user_id: number;
  name: string;
  role: 'DOCTOR' | 'ASHA';
  detail: string;
  consent_status: 'GRANTED' | 'REVOKED';
  updated_at?: string;
}

export interface ImpactMetrics {
  missed_follow_ups_recovered: number;
  emergencies_directed_to_112: number;
  wasted_trips_avoided: number;
  consent_withdrawals_honoured: number;
}

export interface PathwayFacility {
  id: number;
  name: string;
  facility_type: string;
  distance_km: number;
  travel_time_mins: number;
  phone: string;
}

export interface CarePathway {
  condition: string;
  condition_key: string;
  label: string;
  needs_facility: string;
  needs_specialist: string;
  needs_tests: string;
  required_services: string[];
  recommended_facility: PathwayFacility | null;
  nearest_facility: PathwayFacility | null;
  nearest_facility_missing: string[];
  case_reviews: { cases: number; median_distance_km: number; median_delay_hrs: number; main_barrier: string };
}

export interface CaseReviewSummary {
  notice: string;
  excluded_fields: Record<string, string>;
  total_cases: number;
  median_distance_km: number;
  median_delay_hrs: number;
  conditions: {
    condition: string; label: string; cases: number; needs_facility: string; needs_specialist: string; needs_tests: string;
    median_distance_km: number; median_delay_hrs: number; main_barrier: string;
    facilities_ready: number; facilities_total: number; ready_facility_names: string[];
  }[];
  barriers: { barrier: string; cases: number; how_swasthyasetu_helps: string | null }[];
}
