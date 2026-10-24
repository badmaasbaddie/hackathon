import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), nullable=False, index=True)  # PATIENT, ASHA, DOCTOR, FACILITY_ADMIN, SUPER_ADMIN
    phone = Column(String(20), nullable=True)
    village = Column(String(100), nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    hashed_password = Column(String(200), default="demo_hash_pw")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=True) # e.g. P0001
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    abha_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    village = Column(String(100), nullable=False, index=True)
    block = Column(String(100), default="Primary Health Block")
    district = Column(String(100), default="District Health HQ")
    phone = Column(String(20), nullable=False)
    blood_group = Column(String(10), default="B+")
    emergency_contact = Column(String(50), nullable=True)
    chronic_conditions = Column(String(255), default="None")
    current_medication = Column(String(255), default="None")
    allergies = Column(String(255), default="No known allergy")
    care_status = Column(String(50), default="ROUTINE") # ROUTINE, CHRONIC_MONITORING, HIGH_RISK, FOLLOWUP_DUE, OVERDUE_CARE
    assigned_asha_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow)

    family_members = relationship("FamilyMember", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient")
    encounters = relationship("ClinicalEncounter", back_populates="patient")
    timeline_events = relationship("CareTimelineEvent", back_populates="patient")
    tasks = relationship("HealthWorkerTask", back_populates="patient")
    reports = relationship("PatientReport", back_populates="patient")
    alerts = relationship("MonitoringAlert", back_populates="patient")
    ai_summaries = relationship("AISummary", back_populates="patient")

class FamilyMember(Base):
    __tablename__ = "family_members"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    relationship_type = Column(String(50), nullable=False) # SPOUSE, CHILD, PARENT, SIBLING
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    chronic_conditions = Column(String(255), default="None")

    patient = relationship("Patient", back_populates="family_members")

class ConsentRecord(Base):
    __tablename__ = "consent_records"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    granted_to_role = Column(String(50), nullable=False) # DOCTOR, ASHA, FACILITY, ADMIN
    purpose = Column(String(255), nullable=False)
    status = Column(String(20), default="GRANTED") # GRANTED, REVOKED, EXPIRED
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    revoked_at = Column(DateTime, nullable=True)

class Facility(Base):
    __tablename__ = "facilities"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=True) # e.g. H001
    name = Column(String(150), nullable=False)
    facility_type = Column(String(50), nullable=False) # PHC, CHC, SUB_DISTRICT, DISTRICT_HOSPITAL
    address = Column(String(255), nullable=False)
    village_block = Column(String(100), nullable=False)
    district = Column(String(100), default="District Health HQ")
    state = Column(String(100), default="Uttar Pradesh")
    phone = Column(String(20), default="1800-11-4477")
    emergency_contact = Column(String(20), default="112")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_km = Column(Float, default=5.0)
    travel_time_mins = Column(Integer, default=20)
    operating_hours = Column(String(100), default="08:00-16:00")
    languages = Column(String(100), default="Hindi,English")
    services = Column(String(255), default="General OPD;Pharmacy")
    is_open_now = Column(Boolean, default=True)
    is_simulated = Column(Boolean, default=False)
    last_verified_at = Column(DateTime, default=utcnow)

    doctors = relationship("Doctor", back_populates="facility")
    inventory = relationship("InventorySnapshot", back_populates="facility")
    diagnostic_services = relationship("DiagnosticAvailability", back_populates="facility")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    name = Column(String(100), nullable=False)
    head_doctor_name = Column(String(100), nullable=True)

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=True) # e.g. D001
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False, index=True)
    qualification = Column(String(100), default="MBBS, MD")
    experience_years = Column(Integer, default=8)
    phone = Column(String(20), nullable=True)
    languages = Column(String(100), default="Hindi,English")
    available_days = Column(String(50), default="Mon-Fri")
    available_time = Column(String(50), default="10:00-14:00")
    telemedicine = Column(Boolean, default=True)
    is_available_today = Column(Boolean, default=True)
    last_roster_update = Column(DateTime, default=utcnow)

    facility = relationship("Facility", back_populates="doctors")
    availabilities = relationship("DoctorAvailability", back_populates="doctor")

class DoctorAvailability(Base):
    __tablename__ = "doctor_availabilities"
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    start_time = Column(String(10), default="09:00")
    end_time = Column(String(10), default="14:00")
    slot_duration_minutes = Column(Integer, default=15)

    doctor = relationship("Doctor", back_populates="availabilities")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=True) # e.g. A0001
    appointment_code = Column(String(30), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    scheduled_date = Column(String(20), nullable=False)
    scheduled_time = Column(String(20), default="10:30 AM")
    consultation_type = Column(String(30), default="IN_PERSON")
    status = Column(String(30), default="BOOKED") # BOOKED, CONFIRMED, PENDING, COMPLETED, CANCELLED, NO_SHOW, MISSED
    reason = Column(String(255), nullable=True)
    queue_token = Column(String(20), default="T-12")
    is_simulated = Column(Boolean, default=True)
    idempotency_key = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="appointments")

class QueueEntry(Base):
    __tablename__ = "queue_entries"
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    token_number = Column(String(20), nullable=False)
    patient_name = Column(String(100), nullable=False)
    estimated_wait_minutes = Column(Integer, default=15)
    status = Column(String(30), default="WAITING")
    created_at = Column(DateTime, default=utcnow)

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True, index=True)
    referral_code = Column(String(30), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    source_facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    target_facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    referring_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    reason = Column(String(255), nullable=False)
    specialty_needed = Column(String(100), nullable=False)
    urgency = Column(String(20), default="ROUTINE")
    status = Column(String(30), default="PENDING")
    created_at = Column(DateTime, default=utcnow)

class SymptomIntake(Base):
    __tablename__ = "symptom_intakes"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    raw_input = Column(Text, nullable=False)
    language = Column(String(10), default="hi")
    primary_complaint = Column(String(255), nullable=False)
    duration_days = Column(Integer, default=2)
    severity = Column(String(20), default="MODERATE")
    red_flags_detected = Column(String(255), default="None")
    emergency_triaged = Column(Boolean, default=False)
    triage_level = Column(String(20), default="ROUTINE")
    ai_summary_for_doctor = Column(Text, nullable=True)
    recommended_specialty = Column(String(100), default="General Medicine")
    recommended_facility_type = Column(String(50), default="PHC")
    created_at = Column(DateTime, default=utcnow)

class ClinicalEncounter(Base):
    __tablename__ = "clinical_encounters"
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    encounter_date = Column(DateTime, default=utcnow)
    chief_complaints = Column(Text, nullable=False)
    clinical_notes = Column(Text, nullable=False)
    diagnosis = Column(String(255), nullable=False)
    vital_bp = Column(String(20), default="120/80")
    vital_pulse = Column(Integer, default=74)
    vital_temp = Column(Float, default=98.6)
    vital_spo2 = Column(Integer, default=98)
    clinician_risk_flag = Column(String(50), default="NORMAL")
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="encounters")
    prescriptions = relationship("Prescription", back_populates="encounter")
    diagnostic_orders = relationship("DiagnosticOrder", back_populates="encounter")
    follow_up_plans = relationship("FollowUpPlan", back_populates="encounter")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    prescription_code = Column(String(30), unique=True, index=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    encounter = relationship("ClinicalEncounter", back_populates="prescriptions")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=True)
    medicine_name = Column(String(100), nullable=False)
    dosage = Column(String(50), nullable=False)
    frequency = Column(String(50), default="Twice daily after food")
    duration_days = Column(Integer, default=5)
    instructions = Column(String(255), nullable=True)
    collected_status = Column(String(30), default="PENDING") # PENDING, DISPENSED, OUT_OF_STOCK

    prescription = relationship("Prescription", back_populates="items")

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"
    id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String(30), unique=True, nullable=False) # e.g. T001
    name = Column(String(100), nullable=False)
    category = Column(String(50), default="PATHOLOGY")
    standard_turnaround_hours = Column(Integer, default=4)
    requires_fasting = Column(Boolean, default=False)

class DiagnosticAvailability(Base):
    __tablename__ = "diagnostic_availability"
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    test_code = Column(String(30), nullable=False) # T001..T008
    test_name = Column(String(100), nullable=False)
    available = Column(Boolean, default=True)
    availability_note = Column(String(100), default="Same day")
    last_verified_at = Column(DateTime, default=utcnow)

    facility = relationship("Facility", back_populates="diagnostic_services")

class DiagnosticOrder(Base):
    __tablename__ = "diagnostic_orders"
    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("diagnostic_tests.id"), nullable=True)
    test_name = Column(String(100), nullable=False)
    urgency = Column(String(20), default="ROUTINE")
    status = Column(String(30), default="ORDERED") # ORDERED, SCHEDULED, COMPLETED, REPORT_AVAILABLE, AWAITING_REVIEW, UNAVAILABLE, CANCELLED
    scheduled_date = Column(String(20), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    encounter = relationship("ClinicalEncounter", back_populates="diagnostic_orders")
    results = relationship("DiagnosticResult", back_populates="order")

class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("diagnostic_orders.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    test_name = Column(String(100), nullable=False)
    result_summary = Column(Text, nullable=False)
    normal_range = Column(String(100), nullable=True)
    interpretation = Column(Text, nullable=True)
    is_abnormal = Column(Boolean, default=False)
    doctor_reviewed = Column(Boolean, default=False)
    report_file_mock = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    order = relationship("DiagnosticOrder", back_populates="results")

class PatientReport(Base):
    __tablename__ = "patient_reports"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=False) # R0001
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    report_type = Column(String(100), nullable=False) # Lipid Profile, HbA1c, CBC, etc.
    report_date = Column(String(20), nullable=False)
    findings = Column(Text, nullable=False)
    ai_action_note = Column(String(255), default="Doctor review recommended")
    ai_extracted_values = Column(Text, nullable=True)
    is_abnormal = Column(Boolean, default=False)
    doctor_reviewed = Column(Boolean, default=False)
    review_notes = Column(Text, nullable=True)
    reviewed_by_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="reports")

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=True) # M001
    code = Column(String(30), unique=True, nullable=False)
    generic_name = Column(String(100), nullable=False)
    brand_name = Column(String(100), nullable=True)
    category = Column(String(50), default="GENERAL")
    strength = Column(String(50), default="500mg")
    dosage_form = Column(String(30), default="TABLET")
    use_category = Column(String(100), default="General")

class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    medicine_name = Column(String(100), nullable=False)
    quantity_in_stock = Column(Integer, default=100)
    unit = Column(String(20), default="strips")
    reorder_level = Column(Integer, default=20)
    stock_status = Column(String(30), default="Available") # Available, Low Stock, Out of Stock
    last_verified_at = Column(DateTime, default=utcnow)
    is_simulated = Column(Boolean, default=False)

    facility = relationship("Facility", back_populates="inventory")

class FollowUpPlan(Base):
    __tablename__ = "follow_up_plans"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=True) # F0001
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    due_date = Column(String(20), nullable=False) # YYYY-MM-DD
    care_type = Column(String(100), default="Routine consultation")
    instructions = Column(Text, nullable=False)
    next_action = Column(String(255), nullable=True)
    status = Column(String(30), default="SCHEDULED") # Scheduled, Due, Missed, Completed, Overdue, Cancelled
    created_at = Column(DateTime, default=utcnow)

    encounter = relationship("ClinicalEncounter", back_populates="follow_up_plans")
    reminders = relationship("Reminder", back_populates="follow_up_plan")
    tasks = relationship("HealthWorkerTask", back_populates="follow_up_plan")

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    follow_up_id = Column(Integer, ForeignKey("follow_up_plans.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    channel = Column(String(20), default="SMS")
    message = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, default=utcnow)
    status = Column(String(20), default="PENDING")
    sent_at = Column(DateTime, nullable=True)

    follow_up_plan = relationship("FollowUpPlan", back_populates="reminders")

class HealthWorkerTask(Base):
    __tablename__ = "health_worker_tasks"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(50), unique=True, index=True, nullable=True) # W0001
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    asha_worker_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    follow_up_id = Column(Integer, ForeignKey("follow_up_plans.id"), nullable=True)
    task_type = Column(String(50), default="MISSED_FOLLOW_UP")
    description = Column(Text, default="Home visit / patient confirmation")
    priority = Column(String(20), default="Medium") # Low, Medium, High, Critical
    due_date = Column(String(20), nullable=False)
    status = Column(String(30), default="Pending") # Pending, Assigned, Completed, In Progress, Resolved, Escalated
    visit_notes = Column(Text, nullable=True)
    outcome = Column(String(100), nullable=True)
    escalated_to_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="tasks")
    follow_up_plan = relationship("FollowUpPlan", back_populates="tasks")

class CareTimelineEvent(Base):
    __tablename__ = "care_timeline_events"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    actor_name = Column(String(100), nullable=False)
    actor_role = Column(String(50), nullable=False) # IMPORTED, CLINICIAN, AI, ASHA, SYSTEM
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="timeline_events")

class MonitoringAlert(Base):
    __tablename__ = "monitoring_alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_code = Column(String(30), unique=True, index=True, nullable=False) # ALT-00123
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True) # MISSED_APPOINTMENT, OVERDUE_FOLLOWUP, CHRONIC_CARE, DIAGNOSTIC_PENDING, MEDICINE_STOCKOUT, REPORT_REVIEW, DATA_STALENESS, REPEATED_MISSED_CARE
    triggering_rule = Column(String(100), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    supporting_record_ids = Column(Text, default="{}") # JSON of related IDs
    priority = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), default="NEW", index=True) # NEW, ACKNOWLEDGED, ASSIGNED, IN_PROGRESS, RESOLVED, DISMISSED
    assigned_role = Column(String(50), default="ASHA") # DOCTOR, ASHA, FACILITY_ADMIN, SUPER_ADMIN
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(String(20), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_timestamp = Column(DateTime, nullable=True)
    dismissed_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    patient = relationship("Patient", back_populates="alerts")
    resolutions = relationship("AlertResolutionHistory", back_populates="alert", cascade="all, delete-orphan")

class AlertResolutionHistory(Base):
    __tablename__ = "alert_resolution_history"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("monitoring_alerts.id"), nullable=False, index=True)
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(100), default="System")
    actor_role = Column(String(50), default="SYSTEM")
    action = Column(String(50), nullable=False) # CREATED, ACKNOWLEDGED, ASSIGNED, STATUS_CHANGE, RESOLVED, DISMISSED, REOPENED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    alert = relationship("MonitoringAlert", back_populates="resolutions")

class AISummary(Base):
    __tablename__ = "ai_summaries"
    id = Column(Integer, primary_key=True, index=True)
    summary_code = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True, index=True)
    summary_type = Column(String(50), nullable=False) # PATIENT_TIMELINE, CLINICAL_ENCOUNTER, REPORT_EXPLANATION, HEALTH_WORKER_BRIEF, ADMIN_QUERY, DATA_ANOMALY
    title = Column(String(150), nullable=False)
    content = Column(Text, nullable=False)
    provenance_records_json = Column(Text, default="[]") # Array of cited record IDs
    model_version = Column(String(100), default="SwasthyaSetu-GroundedRAG-v1.0")
    confidence_score = Column(Float, default=1.0)
    clinician_verified = Column(Boolean, default=False)
    verified_by_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="ai_summaries")

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String(100), nullable=False)
    source_files_count = Column(Integer, default=10)
    total_records_processed = Column(Integer, default=0)
    valid_records_imported = Column(Integer, default=0)
    rejected_records_count = Column(Integer, default=0)
    status = Column(String(30), default="RUNNING") # RUNNING, COMPLETED, FAILED
    summary_json = Column(Text, default="{}")
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

    errors = relationship("IngestionValidationError", back_populates="job", cascade="all, delete-orphan")

class IngestionValidationError(Base):
    __tablename__ = "ingestion_validation_errors"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("ingestion_jobs.id"), nullable=False, index=True)
    file_name = Column(String(100), nullable=False)
    row_identifier = Column(String(100), nullable=True)
    error_type = Column(String(100), nullable=False)
    details = Column(Text, nullable=False)
    raw_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    job = relationship("IngestionJob", back_populates="errors")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="SYSTEM")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

class SyncOperation(Base):
    __tablename__ = "sync_operations"
    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(30), default="SYNCED")
    created_at = Column(DateTime, default=utcnow)
    synced_at = Column(DateTime, default=utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_name = Column(String(100), default="Anonymous")
    role = Column(String(50), default="GUEST")
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    outcome = Column(String(20), default="SUCCESS")
    ip_address = Column(String(50), default="127.0.0.1")
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow)
