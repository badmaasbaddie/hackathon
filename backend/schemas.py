from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str
    full_name: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    village: Optional[str] = None
    facility_id: Optional[int] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}
class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = "demo"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class FamilyMemberCreate(BaseModel):
    full_name: str
    relationship_type: str
    age: int
    gender: str
    chronic_conditions: Optional[str] = "None"

class FamilyMemberOut(FamilyMemberCreate):
    id: int
    patient_id: int
    model_config = {"from_attributes": True}

class PatientBase(BaseModel):
    abha_id: str
    name: str
    age: int
    gender: str
    village: str
    block: Optional[str] = "Primary Block"
    district: Optional[str] = "District HQ"
    phone: str
    blood_group: Optional[str] = "B+"
    emergency_contact: Optional[str] = None
    chronic_conditions: Optional[str] = "None"
    current_medication: Optional[str] = "None"
    allergies: Optional[str] = "No known allergy"
    care_status: Optional[str] = "ROUTINE"
    external_id: Optional[str] = None
    assigned_asha_id: Optional[int] = None

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    family_members: List[FamilyMemberOut] = []
    model_config = {"from_attributes": True}

class SymptomIntakeRequest(BaseModel):
    patient_id: int
    raw_input: str
    language: Optional[str] = "hi" # hi or en
    duration_days: Optional[int] = 2

class SymptomIntakeResponse(BaseModel):
    intake_id: int
    patient_id: int
    language: str
    primary_complaint: str
    duration_days: int
    severity: str
    is_emergency: bool
    triage_level: str # EMERGENCY, URGENT, ROUTINE
    red_flags: List[str]
    emergency_advice: Optional[str] = None
    emergency_number: str = "112"
    recommended_specialty: str
    recommended_facility_type: str
    ai_doctor_summary: str
    explanation_patient: str
    is_simulated_ai: bool = True
    what_to_do: List[str] = []
    what_not_to_do: List[str] = []
    diet_to_eat: List[str] = []
    diet_to_avoid: List[str] = []
    activity_and_work_guidance: List[str] = []
    red_flag_warnings: List[str] = []

class LifestyleGuidanceOut(BaseModel):
    condition_title: str
    dietary_recommendations: List[str] = []
    dietary_restrictions: List[str] = []
    work_recommendations: List[str] = []
    work_restrictions: List[str] = []
    medicine_adherence_tips: List[str] = []
    warning_signs: List[str] = []
    disclaimer: str = "Clinical dietary & lifestyle guidance is for decision-support and preventive care. Must be reviewed with the treating physician."


class FacilityReadinessOut(BaseModel):
    id: int
    name: str
    facility_type: str
    address: str
    village_block: str
    district: str
    distance_km: float
    travel_time_mins: int
    phone: str
    emergency_contact: str
    operating_hours: str
    is_open_now: bool
    is_simulated: bool
    last_verified_at: datetime
    available_doctors_count: int
    doctor_names: List[str]
    diagnostic_tests_available: List[str]
    diagnostic_tests_missing: List[str]
    medicine_stock_summary: Dict[str, str] # e.g. {"Paracetamol": "IN_STOCK", "Amoxicillin": "OUT_OF_STOCK"}
    estimated_queue_wait_mins: int
    freshness_label: str

class FacilityOut(BaseModel):
    id: int
    external_id: Optional[str] = None
    name: str
    facility_type: str
    address: str
    village_block: str
    district: str
    state: Optional[str] = "Uttar Pradesh"
    phone: str
    emergency_contact: str
    operating_hours: str
    is_open_now: bool
    languages: Optional[str] = "Hindi,English"
    services: Optional[str] = "General OPD;Pharmacy"
    last_verified_at: datetime
    model_config = {"from_attributes": True}

class DoctorOut(BaseModel):
    id: int
    external_id: Optional[str] = None
    facility_id: int
    name: str
    specialty: str
    qualification: str
    experience_years: int
    phone: Optional[str] = None
    languages: Optional[str] = "Hindi,English"
    available_days: Optional[str] = "Mon-Fri"
    available_time: Optional[str] = "10:00-14:00"
    telemedicine: bool = True
    is_available_today: bool = True
    model_config = {"from_attributes": True}

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    facility_id: int
    scheduled_date: str # YYYY-MM-DD
    scheduled_time: Optional[str] = "10:30 AM"
    consultation_type: Optional[str] = "IN_PERSON"
    reason: Optional[str] = "General checkup"
    idempotency_key: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    external_id: Optional[str] = None
    appointment_code: str
    patient_id: int
    doctor_id: int
    facility_id: int
    scheduled_date: str
    scheduled_time: str
    consultation_type: str
    status: str
    reason: Optional[str]
    queue_token: str
    is_simulated: bool
    created_at: datetime
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    model_config = {"from_attributes": True}

class PrescriptionItemIn(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: Optional[str] = None

class PrescriptionItemOut(PrescriptionItemIn):
    id: int
    collected_status: str
    model_config = {"from_attributes": True}

class PrescriptionOut(BaseModel):
    id: int
    prescription_code: str
    encounter_id: Optional[int] = None
    patient_id: int
    doctor_id: int
    notes: Optional[str] = None
    created_at: datetime
    items: List[PrescriptionItemOut] = []
    model_config = {"from_attributes": True}

class EncounterCreate(BaseModel):
    appointment_id: Optional[int] = None
    patient_id: int
    doctor_id: int
    facility_id: int
    chief_complaints: str
    clinical_notes: str
    diagnosis: str
    vital_bp: Optional[str] = "120/80"
    vital_pulse: Optional[int] = 74
    vital_temp: Optional[float] = 98.6
    vital_spo2: Optional[int] = 98
    clinician_risk_flag: Optional[str] = "NORMAL"
    prescriptions: List[PrescriptionItemIn] = []
    diagnostic_test_names: List[str] = []
    follow_up_days: Optional[int] = 7
    follow_up_instructions: Optional[str] = "Review symptoms and test results"

class EncounterOut(BaseModel):
    id: int
    appointment_id: Optional[int]
    patient_id: int
    doctor_id: int
    facility_id: int
    encounter_date: datetime
    chief_complaints: str
    clinical_notes: str
    diagnosis: str
    vital_bp: str
    vital_pulse: int
    vital_temp: float
    vital_spo2: int
    clinician_risk_flag: str
    created_at: datetime
    model_config = {"from_attributes": True}

ClinicalEncounterOut = EncounterOut
class DiagnosticOrderOut(BaseModel):
    id: int
    encounter_id: Optional[int]
    patient_id: int
    doctor_id: int
    facility_id: int
    test_name: str
    urgency: str
    status: str
    scheduled_date: Optional[str]
    created_at: datetime
    facility_name: Optional[str] = None
    model_config = {"from_attributes": True}

class DiagnosticResultIn(BaseModel):
    order_id: int
    result_summary: str
    normal_range: Optional[str] = None
    interpretation: Optional[str] = None
    is_abnormal: bool = False

class FollowUpOut(BaseModel):
    id: int
    external_id: Optional[str] = None
    encounter_id: Optional[int]
    patient_id: int
    patient_name: Optional[str] = None
    doctor_id: Optional[int] = None
    facility_id: Optional[int] = None
    due_date: str
    care_type: Optional[str] = "Routine consultation"
    instructions: str
    next_action: Optional[str] = None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
FollowUpPlanOut = FollowUpOut

class HealthWorkerTaskOut(BaseModel):
    id: int
    external_id: Optional[str] = None
    patient_id: int
    patient_name: Optional[str] = None
    patient_village: Optional[str] = None
    patient_phone: Optional[str] = None
    asha_worker_id: Optional[int] = None
    follow_up_id: Optional[int] = None
    task_type: str
    description: Optional[str] = "Home visit / patient confirmation"
    priority: str
    due_date: str
    status: str
    visit_notes: Optional[str] = None
    outcome: Optional[str] = None
    escalated_to_doctor_id: Optional[int] = None
    created_at: datetime
    model_config = {"from_attributes": True}
class TaskUpdateIn(BaseModel):
    status: str # IN_PROGRESS, RESOLVED, ESCALATED
    visit_notes: str
    outcome: Optional[str] = None
    escalated_to_doctor_id: Optional[int] = None

class CareTimelineEventOut(BaseModel):
    id: int
    patient_id: int
    event_type: str
    title: str
    description: str
    facility_id: Optional[int] = None
    doctor_id: Optional[int] = None
    actor_name: str
    actor_role: str
    metadata_json: str
    created_at: datetime
    model_config = {"from_attributes": True}
class SyncActionItem(BaseModel):
    idempotency_key: str
    action_type: str
    payload: Dict[str, Any]

class SyncBatchRequest(BaseModel):
    user_id: int
    actions: List[SyncActionItem]

class AdminMetricsOut(BaseModel):
    total_patients: int
    total_facilities: int
    total_doctors: int
    total_asha_workers: int = 200
    total_authorities: int = 10
    total_appointments: int
    completed_appointments: int
    pending_appointments: int
    overdue_followups_count: int
    open_asha_tasks: int
    resolved_asha_tasks: int
    critical_emergency_alerts_count: int
    diagnostic_tests_ordered: int
    medicine_stock_alerts_count: int
    data_freshness_pct: float
    is_demo_metric: bool = True

class PatientReportOut(BaseModel):
    id: int
    external_id: str
    patient_id: int
    report_type: str
    report_date: str
    findings: str
    ai_action_note: Optional[str] = None
    ai_extracted_values: Optional[str] = None
    is_abnormal: bool = False
    doctor_reviewed: bool = False
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}
class ReportReviewRequest(BaseModel):
    doctor_reviewed: bool = True
    review_notes: str
    doctor_id: Optional[int] = None

class DiagnosticAvailabilityOut(BaseModel):
    id: int
    facility_id: int
    test_code: str
    test_name: str
    available: bool
    availability_note: Optional[str] = "Same day"
    last_verified_at: datetime
    model_config = {"from_attributes": True}

class AlertResolutionHistoryOut(BaseModel):
    id: int
    alert_id: int
    actor_id: Optional[int] = None
    actor_name: str
    actor_role: str
    action: str
    notes: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}
class MonitoringAlertOut(BaseModel):
    id: int
    alert_code: str
    patient_id: Optional[int] = None
    category: str
    triggering_rule: str
    title: str
    description: str
    supporting_record_ids: Optional[str] = "{}"
    priority: str
    status: str
    assigned_role: str
    assigned_user_id: Optional[int] = None
    due_date: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolution_timestamp: Optional[datetime] = None
    dismissed_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolutions: Optional[List[AlertResolutionHistoryOut]] = []
    model_config = {"from_attributes": True}

class AlertActionRequest(BaseModel):
    action: str # ACKNOWLEDGED, ASSIGNED, IN_PROGRESS, RESOLVED, DISMISSED, REOPENED
    notes: Optional[str] = None
    dismissed_reason: Optional[str] = None
    assigned_role: Optional[str] = None
    assigned_user_id: Optional[int] = None

class AISummaryOut(BaseModel):
    id: int
    summary_code: str
    patient_id: Optional[int] = None
    summary_type: str
    title: str
    content: str
    provenance_records_json: str
    model_version: str
    confidence_score: float
    clinician_verified: bool
    verified_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}
class AIQueryRequest(BaseModel):
    query: str
    patient_id: Optional[int] = None
    context_type: Optional[str] = "ADMIN"

class AIExplainReportRequest(BaseModel):
    report_id: int
    target_audience: Optional[str] = "PATIENT" # PATIENT, CLINICIAN, ASHA

class IngestionValidationErrorOut(BaseModel):
    id: int
    file_name: str
    row_identifier: Optional[str] = None
    error_type: str
    details: str
    created_at: datetime
    model_config = {"from_attributes": True}
class IngestionJobOut(BaseModel):
    id: int
    dataset_name: str
    source_files_count: int
    total_records_processed: int
    valid_records_imported: int
    rejected_records_count: int
    status: str
    summary_json: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    errors: Optional[List[IngestionValidationErrorOut]] = []
    model_config = {"from_attributes": True}

class ConsentRecordOut(BaseModel):
    id: int
    patient_id: int
    granted_to_role: str
    purpose: str
    status: str
    valid_until: Optional[datetime] = None
    created_at: datetime
    revoked_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class PatientMasterProfileOut(BaseModel):
    patient: PatientOut
    external_id: Optional[str] = None
    conditions: str
    current_medication: str
    allergies: str
    blood_group: str
    assigned_facility: Optional[FacilityOut] = None
    appointments: List[AppointmentOut] = []
    clinical_encounters: List[ClinicalEncounterOut] = []
    prescriptions: List[PrescriptionOut] = []
    diagnostic_orders: List[DiagnosticOrderOut] = []
    reports: List[PatientReportOut] = []
    follow_up_plans: List[FollowUpPlanOut] = []
    tasks: List[HealthWorkerTaskOut] = []
    alerts: List[MonitoringAlertOut] = []
    timeline_events: List[CareTimelineEventOut] = []
    consents: List[ConsentRecordOut] = []
    ai_summaries: List[AISummaryOut] = []
    lifestyle_guidance: Optional[LifestyleGuidanceOut] = None
    provenance_counts: Dict[str, int] = {}

class DatabaseHealthOut(BaseModel):
    status: str
    database_connected: bool
    db_file_size_mb: float
    total_patients: int
    total_doctors: int
    total_facilities: int
    total_appointments: int
    total_followups: int
    total_tasks: int
    total_reports: int
    total_alerts: int
    active_alerts: int
    resolved_alerts: int
    inventory_items: int
    diagnostic_availability_records: int
    last_monitoring_run_at: Optional[datetime] = None
    last_ingestion_job: Optional[IngestionJobOut] = None
    data_quality_issues_count: int = 0
