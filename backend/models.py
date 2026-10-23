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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    abha_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    village = Column(String(100), nullable=False, index=True)
    block = Column(String(100), default="Mulshi")
    district = Column(String(100), default="Pune")
    phone = Column(String(20), nullable=False)
    blood_group = Column(String(10), default="B+")
    emergency_contact = Column(String(50), nullable=True)
    chronic_conditions = Column(String(255), default="None")
    assigned_asha_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow)

    family_members = relationship("FamilyMember", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient")
    encounters = relationship("ClinicalEncounter", back_populates="patient")
    timeline_events = relationship("CareTimelineEvent", back_populates="patient")
    tasks = relationship("HealthWorkerTask", back_populates="patient")

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
    granted_to_role = Column(String(50), nullable=False) # DOCTOR, ASHA, FACILITY
    granted_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # a specific clinician / ASHA
    purpose = Column(String(255), nullable=False)
    status = Column(String(20), default="GRANTED") # GRANTED, REVOKED, EXPIRED
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    revoked_at = Column(DateTime, nullable=True)

class Facility(Base):
    __tablename__ = "facilities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    facility_type = Column(String(50), nullable=False) # PHC, CHC, SUB_DISTRICT, DISTRICT_HOSPITAL
    address = Column(String(255), nullable=False)
    village_block = Column(String(100), nullable=False)
    district = Column(String(100), default="Pune")
    phone = Column(String(20), default="1800-11-4477")
    emergency_contact = Column(String(20), default="112")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_km = Column(Float, default=5.0)
    travel_time_mins = Column(Integer, default=20)
    operating_hours = Column(String(100), default="24x7 Emergency / OPD 8:00 AM - 2:00 PM")
    is_open_now = Column(Boolean, default=True)
    is_simulated = Column(Boolean, default=False)
    last_verified_at = Column(DateTime, default=utcnow)

    doctors = relationship("Doctor", back_populates="facility")
    inventory = relationship("InventorySnapshot", back_populates="facility")

class FacilityService(Base):
    """A diagnostic test or clinical service offered at a facility, maintained by the hospital."""
    __tablename__ = "facility_services"
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(30), default="DIAGNOSTIC") # DIAGNOSTIC, CLINICAL
    is_available = Column(Boolean, default=True)
    notes = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=utcnow)

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    name = Column(String(100), nullable=False)
    head_doctor_name = Column(String(100), nullable=True)

class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False, index=True) # General Medicine, Cardiology, Obstetrics, Pediatrics, Orthopedics
    qualification = Column(String(100), default="MBBS, MD")
    experience_years = Column(Integer, default=8)
    phone = Column(String(20), nullable=True)
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
    appointment_code = Column(String(30), unique=True, index=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    scheduled_date = Column(String(20), nullable=False)
    scheduled_time = Column(String(20), default="10:30 AM")
    consultation_type = Column(String(30), default="IN_PERSON") # IN_PERSON, TELEMEDICINE
    status = Column(String(30), default="BOOKED") # BOOKED, IN_QUEUE, COMPLETED, CANCELLED, NO_SHOW
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
    status = Column(String(30), default="WAITING") # WAITING, IN_CONSULTATION, COMPLETED
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
    urgency = Column(String(20), default="ROUTINE") # ROUTINE, URGENT, EMERGENCY
    status = Column(String(30), default="PENDING") # PENDING, ACCEPTED, COMPLETED
    created_at = Column(DateTime, default=utcnow)

class SymptomIntake(Base):
    __tablename__ = "symptom_intakes"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    raw_input = Column(Text, nullable=False)
    language = Column(String(10), default="hi") # hi, en
    primary_complaint = Column(String(255), nullable=False)
    duration_days = Column(Integer, default=2)
    severity = Column(String(20), default="MODERATE") # MILD, MODERATE, SEVERE
    red_flags_detected = Column(String(255), default="None")
    emergency_triaged = Column(Boolean, default=False)
    triage_level = Column(String(20), default="ROUTINE") # EMERGENCY, URGENT, ROUTINE
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
    clinician_risk_flag = Column(String(50), default="NORMAL") # NORMAL, MODERATE_RISK, HIGH_RISK
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="encounters")
    prescriptions = relationship("Prescription", back_populates="encounter")
    diagnostic_orders = relationship("DiagnosticOrder", back_populates="encounter")
    follow_up_plans = relationship("FollowUpPlan", back_populates="encounter")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=False)
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
    test_code = Column(String(30), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(50), default="PATHOLOGY") # PATHOLOGY, RADIOLOGY, CARDIOLOGY
    standard_turnaround_hours = Column(Integer, default=4)
    requires_fasting = Column(Boolean, default=False)

class DiagnosticOrder(Base):
    __tablename__ = "diagnostic_orders"
    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("diagnostic_tests.id"), nullable=True)
    test_name = Column(String(100), nullable=False)
    urgency = Column(String(20), default="ROUTINE") # ROUTINE, STAT
    status = Column(String(30), default="ORDERED") # ORDERED, SCHEDULED, COMPLETED, UNAVAILABLE, CANCELLED
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

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, nullable=False)
    generic_name = Column(String(100), nullable=False)
    brand_name = Column(String(100), nullable=True)
    category = Column(String(50), default="GENERAL") # ANTIBIOTIC, ANALGESIC, ANTIHYPERTENSIVE, ANTIDIABETIC
    strength = Column(String(50), default="500mg")
    dosage_form = Column(String(30), default="TABLET")

class InventorySnapshot(Base):
    __tablename__ = "inventory_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False, index=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    medicine_name = Column(String(100), nullable=False)
    quantity_in_stock = Column(Integer, default=100)
    unit = Column(String(20), default="strips")
    reorder_level = Column(Integer, default=20)
    stock_status = Column(String(20), default="IN_STOCK") # IN_STOCK, LOW_STOCK, OUT_OF_STOCK
    last_verified_at = Column(DateTime, default=utcnow)
    is_simulated = Column(Boolean, default=False)

    facility = relationship("Facility", back_populates="inventory")

class FollowUpPlan(Base):
    __tablename__ = "follow_up_plans"
    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    due_date = Column(String(20), nullable=False) # YYYY-MM-DD
    instructions = Column(Text, nullable=False)
    status = Column(String(30), default="SCHEDULED") # SCHEDULED, COMPLETED, OVERDUE, CANCELLED
    created_at = Column(DateTime, default=utcnow)

    encounter = relationship("ClinicalEncounter", back_populates="follow_up_plans")
    reminders = relationship("Reminder", back_populates="follow_up_plan")
    tasks = relationship("HealthWorkerTask", back_populates="follow_up_plan")

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    follow_up_id = Column(Integer, ForeignKey("follow_up_plans.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    channel = Column(String(20), default="SMS") # SMS, WHATSAPP, VOICE
    message = Column(Text, nullable=False)
    scheduled_time = Column(DateTime, default=utcnow)
    status = Column(String(20), default="PENDING") # PENDING, SENT, FAILED
    sent_at = Column(DateTime, nullable=True)

    follow_up_plan = relationship("FollowUpPlan", back_populates="reminders")

class HealthWorkerTask(Base):
    __tablename__ = "health_worker_tasks"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    asha_worker_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    follow_up_id = Column(Integer, ForeignKey("follow_up_plans.id"), nullable=True)
    task_type = Column(String(50), default="MISSED_FOLLOW_UP") # MISSED_FOLLOW_UP, CHRONIC_CARE_CHECK, IMMUNIZATION, HOME_VISIT
    priority = Column(String(20), default="NORMAL") # NORMAL, HIGH, CRITICAL
    due_date = Column(String(20), nullable=False)
    status = Column(String(30), default="OPEN") # OPEN, IN_PROGRESS, RESOLVED, ESCALATED
    visit_notes = Column(Text, nullable=True)
    outcome = Column(String(100), nullable=True) # PATIENT_VISITED_CLINIC, HOME_CHECK_COMPLETED, MEDICINE_REFILL_ARRANGED, ESCALATED_TO_MO
    escalated_to_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="tasks")
    follow_up_plan = relationship("FollowUpPlan", back_populates="tasks")

class CareTimelineEvent(Base):
    __tablename__ = "care_timeline_events"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # INTAKE, APPOINTMENT, CONSULTATION, PRESCRIPTION, DIAGNOSTIC, FOLLOW_UP, HOME_VISIT, EMERGENCY_TRIAGE
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    actor_name = Column(String(100), nullable=False)
    actor_role = Column(String(50), nullable=False)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow)

    patient = relationship("Patient", back_populates="timeline_events")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="SYSTEM") # REMINDER, TASK_ALERT, ESCALATION, APPOINTMENT
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

class SyncOperation(Base):
    __tablename__ = "sync_operations"
    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(30), default="SYNCED") # QUEUED, SYNCED, FAILED
    created_at = Column(DateTime, default=utcnow)
    synced_at = Column(DateTime, default=utcnow)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    user_name = Column(String(100), default="Anonymous")
    role = Column(String(50), default="GUEST")
    action = Column(String(100), nullable=False) # RECORD_ACCESS, CONSULTATION_CREATED, PERMISSION_DENIED, etc.
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    outcome = Column(String(20), default="SUCCESS") # SUCCESS, DENIED, ERROR
    ip_address = Column(String(50), default="127.0.0.1")
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow)
