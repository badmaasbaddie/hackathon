import os
import json
import uuid
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

import models
import schemas
from database import get_db, engine, Base
from triage_engine import analyze_symptoms
from seed_data import seed_database
from ml_model import train_model, predict_care_pathway, INFO_FILE
import monitoring_routes

app = FastAPI(
    title="SwasthyaSetu AI API",
    description="Rural Healthcare Navigation, Coordination & Continuity Platform API",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitoring_routes.router)

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

# ----------------- AUTH & RBAC HELPER -----------------
def get_current_user(
    authorization: Optional[str] = Header(None),
    x_demo_user: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Lightweight, demo-friendly bearer/header authentication.
    Pass Authorization: Bearer <username> OR X-Demo-User: <username>.
    Defaults to 'ramesh' if unauthenticated for smooth demo experience.
    """
    username = None
    if authorization and authorization.startswith("Bearer "):
        username = authorization.split("Bearer ")[1].strip()
    elif x_demo_user:
        username = x_demo_user.strip()

    if not username:
        username = "ramesh"

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        # Fallback to first user in db
        user = db.query(models.User).first()
    return user

def record_audit(db: Session, user: models.User, action: str, resource_type: str, resource_id: Optional[str] = None, outcome: str = "SUCCESS", details: dict = None):
    audit = models.AuditEvent(
        user_id=user.id if user else None,
        user_name=user.full_name if user else "Anonymous",
        role=user.role if user else "GUEST",
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        outcome=outcome,
        ip_address="127.0.0.1",
        details_json=json.dumps(details or {})
    )
    db.add(audit)
    db.commit()

# ----------------- SYSTEM & DEMO MANAGEMENT -----------------
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SwasthyaSetu AI API",
        "version": "1.0.0",
        "timestamp": utcnow().isoformat()
    }

@app.post("/api/demo/reset")
def reset_demo(db: Session = Depends(get_db)):
    seed_database()
    return {"status": "success", "message": "Demo database successfully reset to clean baseline state."}

@app.get("/api/adapters/status")
def get_adapters_status():
    return {
        "adapters": [
            {
                "name": "ABDM / ABHA Health ID",
                "type": "NATIONAL_ID",
                "status": "SIMULATED",
                "description": "Deterministic mock adapter generating compliant 14-digit ABHA IDs and consent records."
            },
            {
                "name": "eSanjeevani Teleconsultation",
                "type": "TELEMEDICINE",
                "status": "SIMULATED",
                "description": "Standardized WebRTC video link dispatch & doctor queue interface."
            },
            {
                "name": "National Emergency 112 Gateway",
                "type": "EMERGENCY",
                "status": "ACTIVE_DIRECT",
                "description": "Direct emergency protocol dialer routing to district 112 emergency response dispatch."
            },
            {
                "name": "AI Triage & Clinical Summarizer",
                "type": "INTELLIGENCE",
                "status": "LOCAL_DETERMINISTIC",
                "description": "Deterministic clinical safety rules with fallback LLM capability (simulated offline-safe)."
            },
            {
                "name": "SMS & WhatsApp Continuity Dispatcher",
                "type": "NOTIFICATION",
                "status": "SIMULATED",
                "description": "Simulates rural telecom SMS delivery with timestamps and delivery acknowledgment."
            }
        ]
    }

# ----------------- AUTHENTICATION -----------------
@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    record_audit(db, user, "USER_LOGIN", "AUTH", str(user.id), "SUCCESS", {"username": user.username})
    return {
        "access_token": user.username,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# ----------------- PATIENTS & FAMILY -----------------
@app.get("/api/patients", response_model=List[schemas.PatientOut])
def list_patients(
    search: Optional[str] = None,
    village: Optional[str] = None,
    condition: Optional[str] = None,
    care_status: Optional[str] = None,
    overdue_only: Optional[bool] = False,
    limit: int = 1500,
    offset: int = 0,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Patient)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (models.Patient.name.ilike(s)) |
            (models.Patient.external_id.ilike(s)) |
            (models.Patient.abha_id.ilike(s))
        )
    if village:
        query = query.filter(models.Patient.village.ilike(f"%{village.strip()}%"))
    if condition:
        query = query.filter(models.Patient.chronic_conditions.ilike(f"%{condition.strip()}%"))
    if care_status:
        query = query.filter(models.Patient.care_status == care_status.strip().upper())
    if overdue_only:
        # Filter patients who have overdue follow-ups
        overdue_patient_ids = [
            f.patient_id for f in db.query(models.FollowUpPlan.patient_id).filter(
                models.FollowUpPlan.status.in_(["OVERDUE", "MISSED"])
            ).all()
        ]
        query = query.filter(models.Patient.id.in_(overdue_patient_ids))

    patients = query.order_by(models.Patient.id).offset(offset).limit(limit).all()
    return patients

@app.get("/api/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Scenario G: Access Control Verification
    # If user is ASHA and patient is NOT assigned to them, deny access!
    if current_user.role == "ASHA" and patient.assigned_asha_id is not None and patient.assigned_asha_id != current_user.id:
        record_audit(
            db, current_user, "UNAUTHORIZED_PATIENT_ACCESS_DENIED", "PATIENT_RECORD", 
            str(patient_id), outcome="DENIED", 
            details={"patient_name": patient.name, "patient_village": patient.village, "worker_name": current_user.full_name}
        )
        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: ASHA worker '{current_user.full_name}' is not authorized to access patient records outside assigned sub-centre/village (Patient from {patient.village})."
        )

    record_audit(
        db, current_user, "VIEW_PATIENT_RECORD", "PATIENT_RECORD", str(patient_id),
        outcome="SUCCESS", details={"patient_abha": patient.abha_id}
    )
    return patient

# ----------------- SYMPTOM INTAKE & SAFETY SCREENING -----------------
@app.post("/api/symptom-intake", response_model=schemas.SymptomIntakeResponse)
def submit_symptom_intake(
    req: schemas.SymptomIntakeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(models.Patient.id == req.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    triage_result = analyze_symptoms(
        text=req.raw_input,
        language=req.language or "hi",
        duration_days=req.duration_days or 2
    )

    intake = models.SymptomIntake(
        patient_id=req.patient_id,
        raw_input=req.raw_input,
        language=req.language or "hi",
        primary_complaint=triage_result["primary_complaint"],
        duration_days=req.duration_days or 2,
        severity=triage_result["severity"],
        red_flags_detected=", ".join(triage_result["red_flags"]) if triage_result["red_flags"] else "None",
        emergency_triaged=triage_result["is_emergency"],
        triage_level=triage_result["triage_level"],
        ai_summary_for_doctor=triage_result["ai_doctor_summary"],
        recommended_specialty=triage_result["recommended_specialty"],
        recommended_facility_type=triage_result["recommended_facility_type"]
    )
    db.add(intake)
    db.commit()
    db.refresh(intake)

    # Add timeline event
    tl_event = models.CareTimelineEvent(
        patient_id=req.patient_id,
        event_type="EMERGENCY_TRIAGE" if triage_result["is_emergency"] else "INTAKE",
        title="Emergency Warning Triggered" if triage_result["is_emergency"] else "AI Symptom Intake Completed",
        description=triage_result["emergency_advice"] if triage_result["is_emergency"] else f"Reported: {req.raw_input[:120]}...",
        actor_name="SwasthyaSetu AI Triage Engine",
        actor_role="AI_ASSISTANT",
        metadata_json=json.dumps({"triage_level": triage_result["triage_level"], "intake_id": intake.id})
    )
    db.add(tl_event)
    db.commit()

    record_audit(
        db, current_user, "SYMPTOM_INTAKE_PROCESSED", "INTAKE", str(intake.id),
        outcome="SUCCESS", details={"is_emergency": triage_result["is_emergency"], "triage_level": triage_result["triage_level"]}
    )

    return schemas.SymptomIntakeResponse(
        intake_id=intake.id,
        patient_id=req.patient_id,
        language=req.language or "hi",
        primary_complaint=triage_result["primary_complaint"],
        duration_days=req.duration_days or 2,
        severity=triage_result["severity"],
        is_emergency=triage_result["is_emergency"],
        triage_level=triage_result["triage_level"],
        red_flags=triage_result["red_flags"],
        emergency_advice=triage_result["emergency_advice"],
        emergency_number=triage_result["emergency_number"],
        recommended_specialty=triage_result["recommended_specialty"],
        recommended_facility_type=triage_result["recommended_facility_type"],
        ai_doctor_summary=triage_result["ai_doctor_summary"],
        explanation_patient=triage_result["explanation_patient"],
        is_simulated_ai=True
    )

# ----------------- FACILITIES & READINESS -----------------
@app.get("/api/facilities", response_model=List[schemas.FacilityReadinessOut])
def list_facilities(
    required_test: Optional[str] = None,
    required_medicine: Optional[str] = None,
    db: Session = Depends(get_db)
):
    facilities = db.query(models.Facility).all()
    out = []

    for fac in facilities:
        # Available doctors
        docs = db.query(models.Doctor).filter(models.Doctor.facility_id == fac.id, models.Doctor.is_available_today == True).all()
        doc_names = [f"{d.name} ({d.specialty})" for d in docs]

        # Diagnostic tests
        if fac.facility_type == "DISTRICT_HOSPITAL":
            avail_tests = ["Electrocardiogram (ECG)", "Complete Blood Count (CBC)", "Ultrasound Abdomen (USG)", "Fasting Blood Sugar (FBS)", "Chest X-Ray Digital"]
            miss_tests = []
        elif fac.facility_type == "CHC":
            avail_tests = ["Electrocardiogram (ECG)", "Complete Blood Count (CBC)", "Fasting Blood Sugar (FBS)", "Chest X-Ray Digital"]
            miss_tests = ["Ultrasound Abdomen (USG)"] # Demonstrates Scenario B!
        else: # PHC
            avail_tests = ["Fasting Blood Sugar (FBS)", "Urine Albumin"]
            miss_tests = ["Electrocardiogram (ECG)", "Complete Blood Count (CBC)", "Ultrasound Abdomen (USG)", "Chest X-Ray Digital"]

        # Inventory
        inv_items = db.query(models.InventorySnapshot).filter(models.InventorySnapshot.facility_id == fac.id).all()
        med_summary = {item.medicine_name.split()[0]: item.stock_status for item in inv_items}

        # Freshness label
        mins_ago = int((utcnow() - fac.last_verified_at.replace(tzinfo=datetime.timezone.utc)).total_seconds() / 60)
        if mins_ago < 60:
            freshness = f"Verified {mins_ago}m ago (Real-time sync)"
        else:
            freshness = f"Updated {mins_ago // 60}h ago (Routine sync)"

        queue_wait = 15 if fac.facility_type == "PHC" else (30 if fac.facility_type == "CHC" else 55)

        out.append(schemas.FacilityReadinessOut(
            id=fac.id,
            name=fac.name,
            facility_type=fac.facility_type,
            address=fac.address,
            village_block=fac.village_block,
            district=fac.district,
            distance_km=fac.distance_km,
            travel_time_mins=fac.travel_time_mins,
            phone=fac.phone,
            emergency_contact=fac.emergency_contact,
            operating_hours=fac.operating_hours,
            is_open_now=fac.is_open_now,
            is_simulated=fac.is_simulated,
            last_verified_at=fac.last_verified_at,
            available_doctors_count=len(docs),
            doctor_names=doc_names,
            diagnostic_tests_available=avail_tests,
            diagnostic_tests_missing=miss_tests,
            medicine_stock_summary=med_summary,
            estimated_queue_wait_mins=queue_wait,
            freshness_label=freshness
        ))

    return out

# ----------------- APPOINTMENTS & QUEUE -----------------
@app.post("/api/appointments", response_model=schemas.AppointmentOut)
def create_appointment(
    req: schemas.AppointmentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Idempotency check for offline retries (Scenario F)
    if req.idempotency_key:
        existing = db.query(models.Appointment).filter(models.Appointment.idempotency_key == req.idempotency_key).first()
        if existing:
            return existing

    apt_code = f"APT-{uuid.uuid4().hex[:6].upper()}"
    queue_num = f"T-{db.query(models.Appointment).count() + 1}"

    apt = models.Appointment(
        appointment_code=apt_code,
        patient_id=req.patient_id,
        doctor_id=req.doctor_id,
        facility_id=req.facility_id,
        scheduled_date=req.scheduled_date,
        scheduled_time=req.scheduled_time or "10:30 AM",
        consultation_type=req.consultation_type or "IN_PERSON",
        status="BOOKED",
        reason=req.reason,
        queue_token=queue_num,
        is_simulated=True,
        idempotency_key=req.idempotency_key
    )
    db.add(apt)
    db.commit()
    db.refresh(apt)

    # Queue Entry
    pat = db.query(models.Patient).filter(models.Patient.id == req.patient_id).first()
    q_entry = models.QueueEntry(
        facility_id=req.facility_id,
        appointment_id=apt.id,
        token_number=queue_num,
        patient_name=pat.name if pat else "Patient",
        estimated_wait_minutes=20,
        status="WAITING"
    )
    db.add(q_entry)

    # Timeline event
    tl = models.CareTimelineEvent(
        patient_id=req.patient_id,
        event_type="APPOINTMENT",
        title=f"Appointment Confirmed ({apt_code})",
        description=f"Token {queue_num} booked for {req.scheduled_date} at {req.scheduled_time}. Consultation: {req.consultation_type}.",
        facility_id=req.facility_id,
        doctor_id=req.doctor_id,
        actor_name=current_user.full_name,
        actor_role=current_user.role,
        metadata_json=json.dumps({"appointment_code": apt_code, "token": queue_num})
    )
    db.add(tl)
    db.commit()

    record_audit(db, current_user, "BOOK_APPOINTMENT", "APPOINTMENT", str(apt.id), "SUCCESS", {"code": apt_code})

    # Attach names for output
    apt.patient_name = pat.name if pat else ""
    doc = db.query(models.Doctor).filter(models.Doctor.id == req.doctor_id).first()
    apt.doctor_name = doc.name if doc else ""
    fac = db.query(models.Facility).filter(models.Facility.id == req.facility_id).first()
    apt.facility_name = fac.name if fac else ""

    return apt

@app.get("/api/appointments", response_model=List[schemas.AppointmentOut])
def list_appointments(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    facility_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Appointment)
    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if facility_id:
        query = query.filter(models.Appointment.facility_id == facility_id)
    if status:
        query = query.filter(models.Appointment.status == status)

    appointments = query.order_by(desc(models.Appointment.id)).all()
    for a in appointments:
        pat = db.query(models.Patient).filter(models.Patient.id == a.patient_id).first()
        doc = db.query(models.Doctor).filter(models.Doctor.id == a.doctor_id).first()
        fac = db.query(models.Facility).filter(models.Facility.id == a.facility_id).first()
        a.patient_name = pat.name if pat else ""
        a.doctor_name = doc.name if doc else ""
        a.facility_name = fac.name if fac else ""
    return appointments

# ----------------- CLINICAL ENCOUNTERS, PRESCRIPTIONS & DIAGNOSTICS -----------------
@app.post("/api/encounters", response_model=schemas.EncounterOut)
def create_clinical_encounter(
    req: schemas.EncounterCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Encounter
    enc = models.ClinicalEncounter(
        appointment_id=req.appointment_id,
        patient_id=req.patient_id,
        doctor_id=req.doctor_id,
        facility_id=req.facility_id,
        chief_complaints=req.chief_complaints,
        clinical_notes=req.clinical_notes,
        diagnosis=req.diagnosis,
        vital_bp=req.vital_bp or "120/80",
        vital_pulse=req.vital_pulse or 74,
        vital_temp=req.vital_temp or 98.6,
        vital_spo2=req.vital_spo2 or 98,
        clinician_risk_flag=req.clinician_risk_flag or "NORMAL"
    )
    db.add(enc)
    db.commit()
    db.refresh(enc)

    # If linked to appointment, mark it completed
    if req.appointment_id:
        apt = db.query(models.Appointment).filter(models.Appointment.id == req.appointment_id).first()
        if apt:
            apt.status = "COMPLETED"

    # 2. Prescriptions
    if req.prescriptions:
        rx = models.Prescription(
            encounter_id=enc.id,
            patient_id=req.patient_id,
            doctor_id=req.doctor_id,
            prescription_code=f"RX-{uuid.uuid4().hex[:6].upper()}",
            notes=f"Prescribed for {req.diagnosis}"
        )
        db.add(rx)
        db.commit()
        db.refresh(rx)

        for p_item in req.prescriptions:
            # Check inventory status at this facility
            inv = db.query(models.InventorySnapshot).filter(
                models.InventorySnapshot.facility_id == req.facility_id,
                models.InventorySnapshot.medicine_name.ilike(f"%{p_item.medicine_name.split()[0]}%")
            ).first()
            coll_status = "PENDING"
            if inv and inv.stock_status == "OUT_OF_STOCK":
                coll_status = "OUT_OF_STOCK"

            item = models.PrescriptionItem(
                prescription_id=rx.id,
                medicine_name=p_item.medicine_name,
                dosage=p_item.dosage,
                frequency=p_item.frequency,
                duration_days=p_item.duration_days,
                instructions=p_item.instructions,
                collected_status=coll_status
            )
            db.add(item)
        db.commit()

        tl_rx = models.CareTimelineEvent(
            patient_id=req.patient_id,
            event_type="PRESCRIPTION",
            title=f"Digital Prescription Issued ({rx.prescription_code})",
            description=f"{len(req.prescriptions)} medicines prescribed for {req.diagnosis}.",
            facility_id=req.facility_id,
            doctor_id=req.doctor_id,
            actor_name=current_user.full_name,
            actor_role="DOCTOR",
            metadata_json=json.dumps({"prescription_code": rx.prescription_code})
        )
        db.add(tl_rx)

    # 3. Diagnostic Orders
    if req.diagnostic_test_names:
        for t_name in req.diagnostic_test_names:
            # Check if available at current facility
            order_status = "ORDERED"
            if "Ultrasound" in t_name and req.facility_id == 1: # Paud CHC lacks USG
                order_status = "UNAVAILABLE"

            order = models.DiagnosticOrder(
                encounter_id=enc.id,
                patient_id=req.patient_id,
                doctor_id=req.doctor_id,
                facility_id=req.facility_id,
                test_name=t_name,
                urgency="ROUTINE",
                status=order_status,
                scheduled_date=(utcnow() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                notes=f"Clinical order following encounter for {req.diagnosis}"
            )
            db.add(order)
            db.commit()

            tl_diag = models.CareTimelineEvent(
                patient_id=req.patient_id,
                event_type="DIAGNOSTIC",
                title=f"Diagnostic Ordered: {t_name}",
                description=f"Status: {order_status}. Ordered by {current_user.full_name}.",
                facility_id=req.facility_id,
                doctor_id=req.doctor_id,
                actor_name=current_user.full_name,
                actor_role="DOCTOR",
                metadata_json=json.dumps({"test_name": t_name, "status": order_status})
            )
            db.add(tl_diag)

    # 4. Follow-up scheduling
    if req.follow_up_days and req.follow_up_days > 0:
        due = (utcnow() + datetime.timedelta(days=req.follow_up_days)).strftime("%Y-%m-%d")
        fup = models.FollowUpPlan(
            encounter_id=enc.id,
            patient_id=req.patient_id,
            doctor_id=req.doctor_id,
            facility_id=req.facility_id,
            due_date=due,
            instructions=req.follow_up_instructions or "Routine review of clinical symptoms",
            status="SCHEDULED"
        )
        db.add(fup)
        db.commit()

        # Create scheduled reminder
        rem = models.Reminder(
            follow_up_id=fup.id,
            patient_id=req.patient_id,
            channel="SMS",
            message=f"SwasthyaSetu Reminder: Your follow-up with Dr. Deshmukh is scheduled on {due}. Please bring previous reports.",
            scheduled_time=utcnow() + datetime.timedelta(days=req.follow_up_days - 1),
            status="PENDING"
        )
        db.add(rem)

        tl_fup = models.CareTimelineEvent(
            patient_id=req.patient_id,
            event_type="FOLLOW_UP",
            title="Follow-Up Review Scheduled",
            description=f"Due date: {due}. Instructions: {req.follow_up_instructions}.",
            facility_id=req.facility_id,
            doctor_id=req.doctor_id,
            actor_name=current_user.full_name,
            actor_role="DOCTOR",
            metadata_json=json.dumps({"due_date": due})
        )
        db.add(tl_fup)

    # Encounter timeline event
    tl_enc = models.CareTimelineEvent(
        patient_id=req.patient_id,
        event_type="CONSULTATION",
        title=f"Clinical Consultation Completed - {req.diagnosis}",
        description=f"BP: {req.vital_bp}, Pulse: {req.vital_pulse}, Notes: {req.clinical_notes[:100]}...",
        facility_id=req.facility_id,
        doctor_id=req.doctor_id,
        actor_name=current_user.full_name,
        actor_role="DOCTOR",
        metadata_json=json.dumps({"diagnosis": req.diagnosis, "risk_flag": req.clinician_risk_flag})
    )
    db.add(tl_enc)
    db.commit()

    record_audit(db, current_user, "CREATE_CLINICAL_ENCOUNTER", "ENCOUNTER", str(enc.id), "SUCCESS", {"diagnosis": req.diagnosis})
    return enc

@app.get("/api/diagnostics/orders", response_model=List[schemas.DiagnosticOrderOut])
def list_diagnostic_orders(
    patient_id: Optional[int] = None,
    facility_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.DiagnosticOrder)
    if patient_id:
        q = q.filter(models.DiagnosticOrder.patient_id == patient_id)
    if facility_id:
        q = q.filter(models.DiagnosticOrder.facility_id == facility_id)
    orders = q.order_by(desc(models.DiagnosticOrder.id)).all()
    for o in orders:
        fac = db.query(models.Facility).filter(models.Facility.id == o.facility_id).first()
        o.facility_name = fac.name if fac else ""
    return orders

# ----------------- FOLLOW-UPS & ASHA HEALTH WORKER TASKS -----------------
@app.get("/api/follow-ups", response_model=List[schemas.FollowUpOut])
def list_follow_ups(
    patient_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.FollowUpPlan)
    if patient_id:
        q = q.filter(models.FollowUpPlan.patient_id == patient_id)
    if status:
        q = q.filter(models.FollowUpPlan.status == status)
    plans = q.order_by(desc(models.FollowUpPlan.id)).all()
    for p in plans:
        pat = db.query(models.Patient).filter(models.Patient.id == p.patient_id).first()
        p.patient_name = pat.name if pat else ""
    return plans

@app.get("/api/tasks", response_model=List[schemas.HealthWorkerTaskOut])
def list_health_worker_tasks(
    asha_worker_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.HealthWorkerTask)
    if asha_worker_id:
        q = q.filter(models.HealthWorkerTask.asha_worker_id == asha_worker_id)
    if status:
        q = q.filter(models.HealthWorkerTask.status.ilike(f"%{status}%"))
    
    tasks = q.order_by(desc(models.HealthWorkerTask.priority)).all()
    for t in tasks:
        pat = db.query(models.Patient).filter(models.Patient.id == t.patient_id).first()
        if pat:
            t.patient_name = pat.name
            t.patient_village = pat.village
            t.patient_phone = pat.phone
    return tasks

@app.patch("/api/tasks/{task_id}", response_model=schemas.HealthWorkerTaskOut)
def update_task(
    task_id: int,
    req: schemas.TaskUpdateIn,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = req.status
    task.visit_notes = req.visit_notes
    task.outcome = req.outcome
    if req.escalated_to_doctor_id:
        task.escalated_to_doctor_id = req.escalated_to_doctor_id
    if req.status == "RESOLVED":
        task.resolved_at = utcnow()
        # Also update linked follow_up_plan if any
        if task.follow_up_id:
            fup = db.query(models.FollowUpPlan).filter(models.FollowUpPlan.id == task.follow_up_id).first()
            if fup:
                fup.status = "COMPLETED"

    # Timeline event
    tl = models.CareTimelineEvent(
        patient_id=task.patient_id,
        event_type="HOME_VISIT",
        title=f"ASHA Home Visit Recorded - {req.status}",
        description=f"Notes: {req.visit_notes}. Outcome: {req.outcome or 'Pending review'}.",
        actor_name=current_user.full_name,
        actor_role="ASHA",
        metadata_json=json.dumps({"outcome": req.outcome, "status": req.status})
    )
    db.add(tl)
    db.commit()
    db.refresh(task)

    pat = db.query(models.Patient).filter(models.Patient.id == task.patient_id).first()
    if pat:
        task.patient_name = pat.name
        task.patient_village = pat.village
        task.patient_phone = pat.phone

    record_audit(db, current_user, "UPDATE_HEALTH_WORKER_TASK", "TASK", str(task.id), "SUCCESS", {"status": req.status})
    return task

# ----------------- TIMELINE & AUDIT -----------------
@app.get("/api/timeline/{patient_id}", response_model=List[schemas.CareTimelineEventOut])
def get_patient_timeline(patient_id: int, db: Session = Depends(get_db)):
    events = db.query(models.CareTimelineEvent).filter(
        models.CareTimelineEvent.patient_id == patient_id
    ).order_by(desc(models.CareTimelineEvent.created_at)).all()
    return events

@app.get("/api/audit-events")
def list_audit_events(limit: int = 50, db: Session = Depends(get_db)):
    events = db.query(models.AuditEvent).order_by(desc(models.AuditEvent.created_at)).limit(limit).all()
    return events

# ----------------- OFFLINE SYNC BATCH -----------------
@app.post("/api/sync/batch")
def sync_offline_actions(
    req: schemas.SyncBatchRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = []
    for item in req.actions:
        existing = db.query(models.SyncOperation).filter(models.SyncOperation.idempotency_key == item.idempotency_key).first()
        if existing:
            results.append({
                "idempotency_key": item.idempotency_key,
                "status": "ALREADY_SYNCED",
                "message": "Duplicate skipped idempotently."
            })
            continue

        # Process action
        if item.action_type == "BOOK_APPOINTMENT":
            p = item.payload
            apt_code = f"APT-SYNC-{uuid.uuid4().hex[:4].upper()}"
            apt = models.Appointment(
                appointment_code=apt_code,
                patient_id=p.get("patient_id", 1),
                doctor_id=p.get("doctor_id", 1),
                facility_id=p.get("facility_id", 1),
                scheduled_date=p.get("scheduled_date", "2026-10-24"),
                scheduled_time=p.get("scheduled_time", "11:00 AM"),
                consultation_type=p.get("consultation_type", "IN_PERSON"),
                status="BOOKED",
                reason=p.get("reason", "Offline scheduled sync appointment"),
                queue_token=f"T-SYNC-{db.query(models.Appointment).count() + 1}",
                is_simulated=True,
                idempotency_key=item.idempotency_key
            )
            db.add(apt)
            db.commit()

        elif item.action_type == "RESOLVE_TASK":
            p = item.payload
            task = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.id == p.get("task_id")).first()
            if task:
                task.status = "RESOLVED"
                task.visit_notes = p.get("visit_notes", "Synced from offline ASHA mobile queue")
                task.outcome = p.get("outcome", "HOME_CHECK_COMPLETED")
                task.resolved_at = utcnow()
                db.commit()

        sync_op = models.SyncOperation(
            idempotency_key=item.idempotency_key,
            user_id=req.user_id,
            action_type=item.action_type,
            payload_json=json.dumps(item.payload),
            status="SYNCED"
        )
        db.add(sync_op)
        db.commit()

        results.append({
            "idempotency_key": item.idempotency_key,
            "status": "SYNCED",
            "message": "Successfully synchronized and committed."
        })

    return {"synced_count": len(results), "results": results}

# ----------------- ADMIN OPERATIONAL METRICS -----------------
@app.get("/api/admin/metrics", response_model=schemas.AdminMetricsOut)
def get_admin_metrics(db: Session = Depends(get_db)):
    tot_patients = db.query(models.Patient).count()
    tot_facilities = db.query(models.Facility).count()
    tot_doctors = db.query(models.Doctor).count()
    tot_ashas = db.query(models.User).filter(models.User.role == "ASHA").count()
    tot_authorities = db.query(models.User).filter(models.User.role.in_(["ADMIN", "SUPER_ADMIN"])).count()
    tot_apts = db.query(models.Appointment).count()
    completed_apts = db.query(models.Appointment).filter(models.Appointment.status == "COMPLETED").count()
    pending_apts = db.query(models.Appointment).filter(models.Appointment.status == "BOOKED").count()
    overdue_fups = db.query(models.FollowUpPlan).filter(models.FollowUpPlan.status.in_(["OVERDUE", "MISSED"])).count()
    open_tasks = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.status.in_(["OPEN", "IN_PROGRESS"])).count()
    resolved_tasks = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.status == "RESOLVED").count()
    emergency_alerts = db.query(models.SymptomIntake).filter(models.SymptomIntake.emergency_triaged == True).count()
    diag_orders = db.query(models.DiagnosticOrder).count()
    stock_alerts = db.query(models.InventorySnapshot).filter(models.InventorySnapshot.stock_status == "OUT_OF_STOCK").count()

    return schemas.AdminMetricsOut(
        total_patients=tot_patients,
        total_facilities=tot_facilities,
        total_doctors=tot_doctors,
        total_asha_workers=tot_ashas,
        total_authorities=tot_authorities,
        total_appointments=tot_apts,
        completed_appointments=completed_apts,
        pending_appointments=pending_apts,
        overdue_followups_count=overdue_fups,
        open_asha_tasks=open_tasks,
        resolved_asha_tasks=resolved_tasks,
        critical_emergency_alerts_count=emergency_alerts,
        diagnostic_tests_ordered=diag_orders,
        medicine_stock_alerts_count=stock_alerts,
        data_freshness_pct=98.4,
        is_demo_metric=True
    )

# ----------------- TRAINED AI/ML MODEL ENDPOINTS -----------------
@app.get("/api/ai/model-info")
def get_ai_model_info():
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r") as f:
            return json.load(f)
    return {"status": "NOT_TRAINED", "message": "Model not trained yet."}

@app.post("/api/ai/train")
def trigger_model_training(current_user: models.User = Depends(get_current_user)):
    summary = train_model()
    return {"status": "success", "message": "Model retrained successfully on 1,000 patient records.", "summary": summary}

@app.post("/api/ai/predict-care")
def predict_care_endpoint(payload: dict):
    result = predict_care_pathway(payload)
    return result

# ----------------- STATIC FRONTEND SERVING -----------------
frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")

