from pydantic import BaseModel, Field, AfterValidator
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime, timezone

# SQLite returns naive datetimes; they are stored in UTC, so mark them as UTC
# before serialising so browsers convert them to local time correctly.
UTCDateTime = Annotated[datetime, AfterValidator(lambda v: v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v)]

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
    created_at: UTCDateTime
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
    block: Optional[str] = "Mulshi"
    district: Optional[str] = "Pune"
    phone: str
    blood_group: Optional[str] = "B+"
    emergency_contact: Optional[str] = None
    chronic_conditions: Optional[str] = "None"
    assigned_asha_id: Optional[int] = None

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int
    user_id: Optional[int] = None
    created_at: UTCDateTime
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
    # Condition patterns from the synthetic case reviews: what is needed and where to go
    care_pathways: List[Dict[str, Any]] = []

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
    last_verified_at: UTCDateTime
    available_doctors_count: int
    doctor_names: List[str]
    diagnostic_tests_available: List[str]
    diagnostic_tests_missing: List[str]
    clinical_services_available: List[str] = []
    clinical_services_missing: List[str] = []
    medicine_stock_summary: Dict[str, str] # e.g. {"Paracetamol": "IN_STOCK", "Amoxicillin": "OUT_OF_STOCK"}
    estimated_queue_wait_mins: int
    freshness_label: str
    latitude: float
    longitude: float
    doctors: List["DoctorOut"] = []

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
    created_at: UTCDateTime
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

class EncounterCreate(BaseModel):
    appointment_id: Optional[int] = None
    patient_id: int
    doctor_id: Optional[int] = None  # derived from the signed-in doctor
    facility_id: Optional[int] = None  # derived from the doctor's facility
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
    encounter_date: UTCDateTime
    chief_complaints: str
    clinical_notes: str
    diagnosis: str
    vital_bp: str
    vital_pulse: int
    vital_temp: float
    vital_spo2: int
    clinician_risk_flag: str
    created_at: UTCDateTime
    model_config = {"from_attributes": True}

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
    created_at: UTCDateTime
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
    encounter_id: Optional[int]
    patient_id: int
    patient_name: Optional[str] = None
    doctor_id: int
    facility_id: int
    due_date: str
    instructions: str
    status: str
    created_at: UTCDateTime
    model_config = {"from_attributes": True}

class HealthWorkerTaskOut(BaseModel):
    id: int
    patient_id: int
    patient_name: Optional[str] = None
    patient_village: Optional[str] = None
    patient_phone: Optional[str] = None
    asha_worker_id: Optional[int] = None
    follow_up_id: Optional[int] = None
    task_type: str
    priority: str
    due_date: str
    status: str
    visit_notes: Optional[str] = None
    outcome: Optional[str] = None
    escalated_to_doctor_id: Optional[int] = None
    created_at: UTCDateTime
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
    created_at: UTCDateTime
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

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=120)
    gender: str
    phone: str = Field(min_length=10, max_length=15)
    village: str = Field(min_length=2, max_length=100)
    block: Optional[str] = "Mulshi"
    district: Optional[str] = "Pune"
    blood_group: Optional[str] = "Unknown"
    emergency_contact: Optional[str] = None
    chronic_conditions: Optional[str] = "None"
    preferred_language: Optional[str] = "hi"

class ChatTurn(BaseModel):
    role: str  # user | assistant
    content: str = Field(min_length=1, max_length=2000)

class ChatRequest(BaseModel):
    patient_id: Optional[int] = None
    language: Optional[str] = "hi"
    messages: List[ChatTurn] = Field(min_length=1, max_length=20)

class ChatSource(BaseModel):
    id: str
    title: str
    source: str

class ChatResponse(BaseModel):
    reply: str
    mode: str  # SAFETY_RULES, LLM, DEMO_FALLBACK
    model: Optional[str] = None
    triage: SymptomIntakeResponse
    sources: List[ChatSource]

class ScheduleSlot(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str

class DoctorOut(BaseModel):
    id: int
    name: str
    specialty: str
    qualification: str
    experience_years: int
    facility_id: int
    phone: Optional[str] = None
    is_available_today: bool
    last_roster_update: UTCDateTime
    schedule: List[ScheduleSlot] = []

class DoctorUpdateIn(BaseModel):
    is_available_today: Optional[bool] = None
    schedule: Optional[List[ScheduleSlot]] = None

class FacilityServiceOut(BaseModel):
    id: int
    facility_id: int
    name: str
    category: str
    is_available: bool
    notes: Optional[str] = None
    updated_at: UTCDateTime
    model_config = {"from_attributes": True}

class ServiceUpdateIn(BaseModel):
    is_available: bool
    notes: Optional[str] = None

class InventoryOut(BaseModel):
    id: int
    facility_id: int
    medicine_name: str
    quantity_in_stock: int
    unit: str
    reorder_level: int
    stock_status: str
    last_verified_at: UTCDateTime
    model_config = {"from_attributes": True}

class InventoryUpdateIn(BaseModel):
    quantity_in_stock: int = Field(ge=0)

class FacilityManageOut(BaseModel):
    facility: FacilityReadinessOut
    doctors: List[DoctorOut]
    services: List[FacilityServiceOut]
    inventory: List[InventoryOut]

class AppointmentStatusIn(BaseModel):
    status: str  # CANCELLED, NO_SHOW, IN_QUEUE

class PrescriptionOut(BaseModel):
    id: int
    prescription_code: str
    created_at: UTCDateTime
    items: List[PrescriptionItemOut] = []
    model_config = {"from_attributes": True}

class EncounterDetailOut(EncounterOut):
    doctor_name: Optional[str] = None
    facility_name: Optional[str] = None
    prescriptions: List[PrescriptionOut] = []

class ReminderOut(BaseModel):
    id: int
    follow_up_id: int
    channel: str
    message: str
    scheduled_time: UTCDateTime
    status: str
    model_config = {"from_attributes": True}

class IntakeOut(BaseModel):
    id: int
    raw_input: str
    language: str
    primary_complaint: str
    triage_level: str
    red_flags_detected: str
    ai_summary_for_doctor: Optional[str] = None
    recommended_specialty: str
    created_at: UTCDateTime
    model_config = {"from_attributes": True}

class PatientRecordOut(BaseModel):
    patient: PatientOut
    encounters: List[EncounterDetailOut]
    diagnostic_orders: List[DiagnosticOrderOut]
    follow_ups: List[FollowUpOut]
    reminders: List[ReminderOut]
    appointments: List[AppointmentOut]
    latest_intake: Optional[IntakeOut] = None

class CareTeamMember(BaseModel):
    user_id: int
    name: str
    role: str  # DOCTOR, ASHA
    detail: str
    consent_status: str  # GRANTED, REVOKED
    updated_at: Optional[UTCDateTime] = None

class ConsentUpdateIn(BaseModel):
    user_id: int
    granted: bool

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: UTCDateTime
    model_config = {"from_attributes": True}

class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    language: Optional[str] = "hi"

FacilityReadinessOut.model_rebuild()
