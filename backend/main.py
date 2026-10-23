import os
import json
import uuid
import random
import logging
import datetime
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, inspect

import models
import schemas
import ai_assistant
from database import get_db, engine, Base, SessionLocal
from triage_engine import analyze_symptoms
from seed_data import seed_database
from ml_model import train_model, predict_care_pathway, INFO_FILE

logger = logging.getLogger("swasthyasetu")


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def local_today() -> datetime.date:
    # Clinic days (OPD dates, follow-up due dates) follow the server's local calendar.
    return datetime.date.today()


def today_str() -> str:
    return local_today().isoformat()


# ----------------- STARTUP -----------------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed on first run, or when the database predates the current schema/seed.
        consent_cols = {c["name"] for c in inspect(engine).get_columns("consent_records")}
        if (not db.query(models.User).filter(models.User.username == "admin_paud").first()
                or "granted_to_user_id" not in consent_cols
                or not db.query(models.Facility).filter(models.Facility.name == "Malihabad Community Health Centre").first()):
            db.close()
            seed_database()
            db = SessionLocal()
        detect_missed_care(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="SwasthyaSetu AI API",
    description="Rural Healthcare Navigation, Coordination & Continuity Platform API (demo prototype, fictional data)",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- AUTH & RBAC HELPERS -----------------
ROLES = ("PATIENT", "ASHA", "DOCTOR", "FACILITY_ADMIN", "SUPER_ADMIN")


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_demo_user: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Demo authentication: `Authorization: Bearer <username>` or `X-Demo-User: <username>`.
    The token is the username returned by /api/auth/login. This is clearly a prototype
    scheme (no passwords) and must be replaced with real auth (e.g. OTP + JWT) before use
    with real patient data.
    """
    username = None
    if authorization and authorization.startswith("Bearer "):
        username = authorization.split("Bearer ", 1)[1].strip()
    elif x_demo_user:
        username = x_demo_user.strip()

    if not username:
        raise HTTPException(status_code=401, detail="Not signed in")
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user - please sign in again")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    return user


def require_roles(*roles: str):
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"This action requires role: {', '.join(roles)}")
        return user
    return checker


def record_audit(db: Session, user: Optional[models.User], action: str, resource_type: str, resource_id: Optional[str] = None, outcome: str = "SUCCESS", details: dict = None):
    db.add(models.AuditEvent(
        user_id=user.id if user else None,
        user_name=user.full_name if user else "SwasthyaSetu System",
        role=user.role if user else "SYSTEM",
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        outcome=outcome,
        ip_address="127.0.0.1",
        details_json=json.dumps(details or {})
    ))
    db.commit()


def notify_patient(db: Session, patient_id: int, title: str, message: str, kind: str = "SMS"):
    """Simulated SMS/WhatsApp to the patient's phone; shown in the patient's 'phone' panel."""
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if patient and patient.user_id:
        db.add(models.Notification(user_id=patient.user_id, title=title, message=message, notification_type=kind))


def consent_revoked(db: Session, patient_id: int, user_id: int) -> bool:
    """The patient's latest decision for this specific clinician / ASHA worker wins."""
    latest = (
        db.query(models.ConsentRecord)
        .filter(models.ConsentRecord.patient_id == patient_id, models.ConsentRecord.granted_to_user_id == user_id)
        .order_by(desc(models.ConsentRecord.id)).first()
    )
    return latest is not None and latest.status == "REVOKED"


def doctor_for_user(db: Session, user: models.User) -> Optional[models.Doctor]:
    return db.query(models.Doctor).filter(models.Doctor.user_id == user.id).first()


def patient_for_user(db: Session, user: models.User) -> Optional[models.Patient]:
    return db.query(models.Patient).filter(models.Patient.user_id == user.id).first()


def can_access_patient(db: Session, user: models.User, patient: models.Patient) -> bool:
    if user.role == "SUPER_ADMIN":
        return True
    if user.role == "PATIENT":
        return patient.user_id == user.id
    if user.role in ("ASHA", "DOCTOR") and consent_revoked(db, patient.id, user.id):
        return False
    if user.role == "ASHA":
        return patient.assigned_asha_id == user.id
    if user.role == "DOCTOR":
        doc = doctor_for_user(db, user)
        if not doc:
            return False
        # A doctor may see a patient they have a care relationship with.
        return any(
            q.first() is not None for q in (
                db.query(models.Appointment.id).filter(models.Appointment.patient_id == patient.id, models.Appointment.doctor_id == doc.id),
                db.query(models.ClinicalEncounter.id).filter(models.ClinicalEncounter.patient_id == patient.id, models.ClinicalEncounter.doctor_id == doc.id),
                db.query(models.FollowUpPlan.id).filter(models.FollowUpPlan.patient_id == patient.id, models.FollowUpPlan.doctor_id == doc.id),
            )
        )
    if user.role == "FACILITY_ADMIN":
        return db.query(models.Appointment.id).filter(
            models.Appointment.patient_id == patient.id, models.Appointment.facility_id == user.facility_id
        ).first() is not None
    return False


def ensure_patient_access(db: Session, user: models.User, patient_id: int, action: str = "VIEW_PATIENT_RECORD") -> models.Patient:
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not can_access_patient(db, user, patient):
        record_audit(
            db, user, "UNAUTHORIZED_PATIENT_ACCESS_DENIED", "PATIENT_RECORD", patient_id, outcome="DENIED",
            details={"attempted_action": action, "patient_village": patient.village, "actor": user.full_name}
        )
        if consent_revoked(db, patient.id, user.id):
            detail = f"Access Denied: the patient has withdrawn consent for {user.full_name} to view their health record."
        elif user.role == "ASHA":
            detail = (f"Access Denied: ASHA worker '{user.full_name}' is not authorized to access patient records "
                      f"outside the assigned catchment (patient from {patient.village}).")
        else:
            detail = f"Access Denied: {user.role} '{user.full_name}' has no authorized care relationship with this patient."
        raise HTTPException(status_code=403, detail=detail)
    return patient


def ensure_facility_manager(user: models.User, facility_id: int):
    if user.role == "SUPER_ADMIN":
        return
    if user.role == "FACILITY_ADMIN" and user.facility_id == facility_id:
        return
    raise HTTPException(status_code=403, detail="Only this facility's administrators can update it")


# ----------------- CONTINUITY ENGINE -----------------
def detect_missed_care(db: Session) -> dict:
    """
    Automated missed-care detection:
      - follow-ups past their due date and not completed become OVERDUE and generate a
        high-priority home-visit task for the patient's ASHA worker;
      - reminders whose time has come are dispatched through the (simulated) SMS adapter.
    Idempotent: safe to run on every request that shows continuity data.
    """
    today = today_str()
    newly_overdue = 0
    tasks_created = 0

    due = db.query(models.FollowUpPlan).filter(
        models.FollowUpPlan.status == "SCHEDULED", models.FollowUpPlan.due_date < today
    ).all()
    for fup in due:
        fup.status = "OVERDUE"
        newly_overdue += 1
        patient = db.query(models.Patient).filter(models.Patient.id == fup.patient_id).first()
        existing = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.follow_up_id == fup.id).first()
        if patient and patient.assigned_asha_id and not existing:
            db.add(models.HealthWorkerTask(
                patient_id=fup.patient_id, asha_worker_id=patient.assigned_asha_id, follow_up_id=fup.id,
                task_type="MISSED_FOLLOW_UP", priority="HIGH", due_date=fup.due_date, status="OPEN"
            ))
            tasks_created += 1
        notify_patient(db, fup.patient_id, "Missed follow-up",
                       f"SwasthyaSetu: You missed your follow-up due {fup.due_date}. Your ASHA worker will contact you to help you reach the clinic.")
        db.add(models.CareTimelineEvent(
            patient_id=fup.patient_id, event_type="FOLLOW_UP", title="Scheduled Follow-up Review Missed",
            description=f"Follow-up due {fup.due_date} was not completed. "
                        + ("An ASHA home-visit task was created automatically." if patient and patient.assigned_asha_id else "No ASHA assigned - flagged for facility outreach."),
            facility_id=fup.facility_id, doctor_id=fup.doctor_id,
            actor_name="SwasthyaSetu Continuity Engine", actor_role="SYSTEM",
            metadata_json=json.dumps({"follow_up_id": fup.id, "status": "OVERDUE"})
        ))

    now_naive = utcnow().replace(tzinfo=None)
    sent = 0
    for rem in db.query(models.Reminder).filter(models.Reminder.status == "PENDING", models.Reminder.scheduled_time <= now_naive).all():
        rem.status = "SENT"
        rem.sent_at = now_naive
        notify_patient(db, rem.patient_id, "Follow-up reminder", rem.message, rem.channel)
        sent += 1

    db.commit()
    if newly_overdue or sent:
        record_audit(db, None, "CONTINUITY_ENGINE_RUN", "SYSTEM", None, "SUCCESS",
                     {"newly_overdue": newly_overdue, "tasks_created": tasks_created, "reminders_sent": sent})
    return {"newly_overdue": newly_overdue, "tasks_created": tasks_created, "reminders_sent": sent}


# ----------------- SYSTEM & DEMO MANAGEMENT -----------------
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "SwasthyaSetu AI API", "version": "1.1.0", "timestamp": utcnow().isoformat()}


@app.post("/api/demo/reset")
def reset_demo(current_user: models.User = Depends(get_current_user)):
    seed_database()
    return {"status": "success", "message": "Demo database reset to the clean fictional baseline."}


@app.get("/api/adapters/status")
def get_adapters_status():
    llm_on = ai_assistant._llm_enabled()
    return {
        "adapters": [
            {"name": "ABDM / ABHA Health ID", "type": "NATIONAL_ID", "status": "SIMULATED",
             "description": "Demo adapter: ABHA-format IDs are generated locally. No connection to the national ABDM gateway."},
            {"name": "eSanjeevani Teleconsultation", "type": "TELEMEDICINE", "status": "SIMULATED",
             "description": "Demo adapter: teleconsult bookings are recorded locally; no video session is created."},
            {"name": "National Emergency 112 / 108", "type": "EMERGENCY", "status": "PHONE_GUIDANCE",
             "description": "Patients are told to dial 112/108 themselves. The platform does not dispatch ambulances."},
            {"name": "AI Health Assistant (LLM + approved references)", "type": "INTELLIGENCE",
             "status": "LIVE_LLM" if llm_on else "DEMO_FALLBACK",
             "description": (f"Claude ({ai_assistant.MODEL_ID}) answers from approved reference material and the patient's record, after deterministic safety screening."
                             if llm_on else "No ANTHROPIC_API_KEY set: deterministic safety screening + retrieved reference text are used to compose answers.")},
            {"name": "SMS & WhatsApp Reminder Dispatcher", "type": "NOTIFICATION", "status": "SIMULATED",
             "description": "Demo adapter: reminders are marked SENT when due; no real SMS is delivered."},
            {"name": "Medicine Inventory Feed", "type": "SUPPLY_CHAIN", "status": "MANUAL_ENTRY",
             "description": "Stock levels are entered by facility staff. Real-time inventory integration is a later phase."},
        ]
    }


# ----------------- AUTHENTICATION & REGISTRATION -----------------
def _token_response(user: models.User):
    return {"access_token": user.username, "token_type": "bearer", "user": user}


@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == req.username.strip()).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    record_audit(db, user, "USER_LOGIN", "AUTH", user.id, "SUCCESS", {"username": user.username})
    return _token_response(user)


@app.post("/api/auth/register", response_model=schemas.TokenResponse)
def register_patient(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Self-registration for patients. Creates the login and the health record together."""
    phone = "".join(ch for ch in req.phone if ch.isdigit())
    if len(phone) < 10:
        raise HTTPException(status_code=422, detail="Enter a valid 10-digit mobile number")
    if db.query(models.User).filter(models.User.phone == phone, models.User.role == "PATIENT").first():
        raise HTTPException(status_code=409, detail="A patient with this mobile number is already registered")

    base = "".join(ch for ch in req.name.split()[0].lower() if ch.isalnum()) or "patient"
    username = f"{base}{phone[-4:]}"
    while db.query(models.User).filter(models.User.username == username).first():
        username = f"{base}{random.randint(1000, 9999)}"

    abha = f"91-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    while db.query(models.Patient).filter(models.Patient.abha_id == abha).first():
        abha = f"91-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

    # Route the patient to the ASHA worker who covers their village, if any.
    asha = db.query(models.User).filter(models.User.role == "ASHA", func.lower(models.User.village) == req.village.strip().lower()).first()
    if not asha and req.village.strip().lower() in ("paud", "pirangut", "mulshi"):
        asha = db.query(models.User).filter(models.User.username == "asha_kavita").first()

    user = models.User(username=username, full_name=req.name.strip(), role="PATIENT", phone=phone, village=req.village.strip())
    db.add(user)
    db.commit()
    db.refresh(user)

    patient = models.Patient(
        user_id=user.id, abha_id=abha, name=req.name.strip(), age=req.age, gender=req.gender,
        village=req.village.strip(), block=req.block or "Mulshi", district=req.district or "Pune",
        phone=phone, blood_group=req.blood_group or "Unknown", emergency_contact=req.emergency_contact,
        chronic_conditions=req.chronic_conditions or "None", assigned_asha_id=asha.id if asha else None
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    db.add(models.CareTimelineEvent(
        patient_id=patient.id, event_type="REGISTRATION", title="Registered on SwasthyaSetu",
        description=f"Demo ABHA-format ID {abha} issued. " + (f"Assigned ASHA worker: {asha.full_name}." if asha else "No ASHA worker covers this village yet."),
        actor_name=user.full_name, actor_role="PATIENT", metadata_json=json.dumps({"abha_id": abha})
    ))
    db.commit()
    record_audit(db, user, "PATIENT_REGISTERED", "PATIENT_RECORD", patient.id, "SUCCESS", {"village": patient.village})
    return _token_response(user)


@app.get("/api/auth/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# ----------------- PATIENTS & FAMILY -----------------
@app.get("/api/patients/me", response_model=schemas.PatientOut)
def get_my_patient_record(current_user: models.User = Depends(require_roles("PATIENT")), db: Session = Depends(get_db)):
    patient = patient_for_user(db, current_user)
    if not patient:
        raise HTTPException(status_code=404, detail="No health record linked to this account")
    return patient


@app.post("/api/patients/me/family", response_model=schemas.FamilyMemberOut)
def add_family_member(req: schemas.FamilyMemberCreate, current_user: models.User = Depends(require_roles("PATIENT")), db: Session = Depends(get_db)):
    patient = patient_for_user(db, current_user)
    if not patient:
        raise HTTPException(status_code=404, detail="No health record linked to this account")
    member = models.FamilyMember(patient_id=patient.id, **req.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    record_audit(db, current_user, "FAMILY_MEMBER_ADDED", "PATIENT_RECORD", patient.id)
    return member


@app.get("/api/patients/me/care-team", response_model=List[schemas.CareTeamMember])
def get_my_care_team(current_user: models.User = Depends(require_roles("PATIENT")), db: Session = Depends(get_db)):
    """Who can see my record, and whether I have allowed it."""
    patient = patient_for_user(db, current_user)
    if not patient:
        raise HTTPException(status_code=404, detail="No health record linked to this account")
    members = []
    if patient.assigned_asha_id:
        asha = db.query(models.User).filter(models.User.id == patient.assigned_asha_id).first()
        if asha:
            members.append((asha, "ASHA", f"ASHA worker for {patient.village}"))
    doctor_ids = {a.doctor_id for a in db.query(models.Appointment).filter(models.Appointment.patient_id == patient.id)} | \
                 {e.doctor_id for e in db.query(models.ClinicalEncounter).filter(models.ClinicalEncounter.patient_id == patient.id)}
    _, facilities = _names(db)
    for doc in db.query(models.Doctor).filter(models.Doctor.id.in_(doctor_ids)).all() if doctor_ids else []:
        if doc.user_id:
            user = db.query(models.User).filter(models.User.id == doc.user_id).first()
            fac = facilities.get(doc.facility_id)
            members.append((user, "DOCTOR", f"{doc.specialty}, {fac.name if fac else ''}"))

    out = []
    for user, role, detail in members:
        latest = (db.query(models.ConsentRecord)
                  .filter(models.ConsentRecord.patient_id == patient.id, models.ConsentRecord.granted_to_user_id == user.id)
                  .order_by(desc(models.ConsentRecord.id)).first())
        out.append(schemas.CareTeamMember(
            user_id=user.id, name=user.full_name, role=role, detail=detail,
            consent_status=latest.status if latest else "GRANTED",
            updated_at=(latest.revoked_at or latest.created_at) if latest else None,
        ))
    return out


@app.put("/api/patients/me/consents", response_model=List[schemas.CareTeamMember])
def set_my_consent(req: schemas.ConsentUpdateIn, current_user: models.User = Depends(require_roles("PATIENT")), db: Session = Depends(get_db)):
    patient = patient_for_user(db, current_user)
    if not patient:
        raise HTTPException(status_code=404, detail="No health record linked to this account")
    team = {m.user_id: m for m in get_my_care_team(current_user, db)}
    if req.user_id not in team:
        raise HTTPException(status_code=404, detail="That person is not part of your care team")
    member = team[req.user_id]
    status = "GRANTED" if req.granted else "REVOKED"
    db.add(models.ConsentRecord(
        patient_id=patient.id, granted_to_role=member.role, granted_to_user_id=member.user_id,
        purpose=f"Access to health record by {member.name}", status=status,
        valid_until=(utcnow() + datetime.timedelta(days=365)).replace(tzinfo=None) if req.granted else None,
        revoked_at=None if req.granted else utcnow().replace(tzinfo=None),
    ))
    db.add(models.CareTimelineEvent(
        patient_id=patient.id, event_type="CONSENT",
        title=f"Consent {'granted' if req.granted else 'withdrawn'}: {member.name}",
        description=f"{patient.name} {'allowed' if req.granted else 'stopped'} {member.name} ({member.role}) {'to view' if req.granted else 'from viewing'} the health record.",
        actor_name=patient.name, actor_role="PATIENT", metadata_json=json.dumps({"user_id": member.user_id, "status": status})
    ))
    db.commit()
    record_audit(db, current_user, "CONSENT_GRANTED" if req.granted else "CONSENT_REVOKED", "PATIENT_RECORD", patient.id,
                 "SUCCESS", {"for_user": member.name, "role": member.role})
    return get_my_care_team(current_user, db)


@app.get("/api/notifications/me", response_model=List[schemas.NotificationOut])
def get_my_notifications(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Simulated SMS inbox for the signed-in user."""
    detect_missed_care(db)
    return (db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
            .order_by(desc(models.Notification.id)).limit(50).all())


@app.get("/api/patients", response_model=List[schemas.PatientOut])
def list_patients(
    village: Optional[str] = None,
    limit: int = 200,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Patient)
    if current_user.role == "PATIENT":
        query = query.filter(models.Patient.user_id == current_user.id)
    elif current_user.role == "ASHA":
        query = query.filter(models.Patient.assigned_asha_id == current_user.id)
    elif current_user.role == "DOCTOR":
        doc = doctor_for_user(db, current_user)
        doc_id = doc.id if doc else -1
        query = query.filter(or_(
            models.Patient.id.in_(db.query(models.Appointment.patient_id).filter(models.Appointment.doctor_id == doc_id)),
            models.Patient.id.in_(db.query(models.ClinicalEncounter.patient_id).filter(models.ClinicalEncounter.doctor_id == doc_id)),
        ))
    elif current_user.role == "FACILITY_ADMIN":
        query = query.filter(models.Patient.id.in_(
            db.query(models.Appointment.patient_id).filter(models.Appointment.facility_id == current_user.facility_id)))

    if village:
        query = query.filter(models.Patient.village.ilike(f"%{village}%"))
    return query.order_by(models.Patient.id).limit(min(max(limit, 1), 1000)).all()


@app.get("/api/patients/{patient_id}", response_model=schemas.PatientOut)
def get_patient(patient_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    patient = ensure_patient_access(db, current_user, patient_id)
    record_audit(db, current_user, "VIEW_PATIENT_RECORD", "PATIENT_RECORD", patient_id, "SUCCESS", {"patient_abha": patient.abha_id})
    return patient


def _names(db: Session):
    doctors = {d.id: d for d in db.query(models.Doctor).all()}
    facilities = {f.id: f for f in db.query(models.Facility).all()}
    return doctors, facilities


def _appointment_out(apt: models.Appointment, patients: dict, doctors: dict, facilities: dict) -> schemas.AppointmentOut:
    out = schemas.AppointmentOut.model_validate(apt)
    out.patient_name = patients.get(apt.patient_id, "")
    out.doctor_name = doctors[apt.doctor_id].name if apt.doctor_id in doctors else ""
    out.facility_name = facilities[apt.facility_id].name if apt.facility_id in facilities else ""
    return out


@app.get("/api/patients/{patient_id}/record", response_model=schemas.PatientRecordOut)
def get_patient_health_record(patient_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The patient's digital health record: consultations, prescriptions, tests, follow-ups and reminders."""
    patient = ensure_patient_access(db, current_user, patient_id, "VIEW_HEALTH_RECORD")
    detect_missed_care(db)
    doctors, facilities = _names(db)

    encounters = []
    for enc in db.query(models.ClinicalEncounter).filter(models.ClinicalEncounter.patient_id == patient_id).order_by(desc(models.ClinicalEncounter.encounter_date)).all():
        e = schemas.EncounterDetailOut.model_validate(enc, from_attributes=True)
        e.doctor_name = doctors[enc.doctor_id].name if enc.doctor_id in doctors else None
        e.facility_name = facilities[enc.facility_id].name if enc.facility_id in facilities else None
        e.prescriptions = [schemas.PrescriptionOut.model_validate(rx) for rx in enc.prescriptions]
        encounters.append(e)

    orders = []
    for o in db.query(models.DiagnosticOrder).filter(models.DiagnosticOrder.patient_id == patient_id).order_by(desc(models.DiagnosticOrder.id)).all():
        out = schemas.DiagnosticOrderOut.model_validate(o)
        out.facility_name = facilities[o.facility_id].name if o.facility_id in facilities else ""
        orders.append(out)

    follow_ups = []
    for f in db.query(models.FollowUpPlan).filter(models.FollowUpPlan.patient_id == patient_id).order_by(desc(models.FollowUpPlan.due_date)).all():
        out = schemas.FollowUpOut.model_validate(f)
        out.patient_name = patient.name
        follow_ups.append(out)

    reminders = db.query(models.Reminder).filter(models.Reminder.patient_id == patient_id).order_by(desc(models.Reminder.scheduled_time)).all()
    appointments = [
        _appointment_out(a, {patient.id: patient.name}, doctors, facilities)
        for a in db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).order_by(desc(models.Appointment.id)).all()
    ]
    latest_intake = db.query(models.SymptomIntake).filter(models.SymptomIntake.patient_id == patient_id).order_by(desc(models.SymptomIntake.created_at)).first()

    record_audit(db, current_user, "VIEW_HEALTH_RECORD", "PATIENT_RECORD", patient_id)
    return schemas.PatientRecordOut(
        patient=schemas.PatientOut.model_validate(patient),
        encounters=encounters,
        diagnostic_orders=orders,
        follow_ups=follow_ups,
        reminders=[schemas.ReminderOut.model_validate(r) for r in reminders],
        appointments=appointments,
        latest_intake=schemas.IntakeOut.model_validate(latest_intake) if latest_intake else None,
    )


# ----------------- SYMPTOM INTAKE & AI ASSISTANT -----------------
def _record_intake(db: Session, user: models.User, patient: models.Patient, text: str, language: str, duration_days: int, triage: dict) -> models.SymptomIntake:
    intake = models.SymptomIntake(
        patient_id=patient.id, raw_input=text, language=language,
        primary_complaint=triage["primary_complaint"], duration_days=duration_days, severity=triage["severity"],
        red_flags_detected=", ".join(triage["red_flags"]) if triage["red_flags"] else "None",
        emergency_triaged=triage["is_emergency"], triage_level=triage["triage_level"],
        ai_summary_for_doctor=triage["ai_doctor_summary"], recommended_specialty=triage["recommended_specialty"],
        recommended_facility_type=triage["recommended_facility_type"]
    )
    db.add(intake)
    db.commit()
    db.refresh(intake)

    db.add(models.CareTimelineEvent(
        patient_id=patient.id,
        event_type="EMERGENCY_TRIAGE" if triage["is_emergency"] else "INTAKE",
        title="Emergency Warning Triggered" if triage["is_emergency"] else f"AI Symptom Check ({triage['triage_level']})",
        description=triage["emergency_advice"] if triage["is_emergency"] else f"Reported: {text[:160]}",
        actor_name="SwasthyaSetu AI Assistant", actor_role="AI_ASSISTANT",
        metadata_json=json.dumps({"triage_level": triage["triage_level"], "intake_id": intake.id})
    ))
    db.commit()
    record_audit(db, user, "SYMPTOM_INTAKE_PROCESSED", "INTAKE", intake.id, "SUCCESS",
                 {"is_emergency": triage["is_emergency"], "triage_level": triage["triage_level"]})
    return intake


def _intake_response(intake: models.SymptomIntake, language: str, triage: dict) -> schemas.SymptomIntakeResponse:
    return schemas.SymptomIntakeResponse(
        intake_id=intake.id, patient_id=intake.patient_id, language=language,
        primary_complaint=triage["primary_complaint"], duration_days=intake.duration_days,
        severity=triage["severity"], is_emergency=triage["is_emergency"], triage_level=triage["triage_level"],
        red_flags=triage["red_flags"], emergency_advice=triage["emergency_advice"],
        emergency_number=triage["emergency_number"], recommended_specialty=triage["recommended_specialty"],
        recommended_facility_type=triage["recommended_facility_type"], ai_doctor_summary=triage["ai_doctor_summary"],
        explanation_patient=triage["explanation_patient"], is_simulated_ai=True
    )


@app.post("/api/symptom-intake", response_model=schemas.SymptomIntakeResponse)
def submit_symptom_intake(req: schemas.SymptomIntakeRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    patient = ensure_patient_access(db, current_user, req.patient_id, "SYMPTOM_INTAKE")
    language = req.language or "hi"
    duration = req.duration_days or 2
    triage = analyze_symptoms(text=req.raw_input, language=language, duration_days=duration)
    intake = _record_intake(db, current_user, patient, req.raw_input, language, duration, triage)
    return _intake_response(intake, language, triage)


@app.post("/api/ai/chat", response_model=schemas.ChatResponse)
def ai_chat(req: schemas.ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Conversational AI assistant (Hindi/English) grounded in approved references + the patient's own record."""
    if current_user.role == "PATIENT":
        patient = patient_for_user(db, current_user)
        if not patient:
            raise HTTPException(status_code=404, detail="No health record linked to this account")
    else:
        if not req.patient_id:
            raise HTTPException(status_code=422, detail="patient_id is required")
        patient = ensure_patient_access(db, current_user, req.patient_id, "AI_ASSISTANT")

    history = [m.model_dump() for m in req.messages]
    if history[-1]["role"] != "user":
        raise HTTPException(status_code=422, detail="The last message must come from the user")
    language = req.language if req.language in ("hi", "en", "mr") else "hi"

    result = ai_assistant.respond(db, patient, history, language)
    intake = _record_intake(db, current_user, patient, history[-1]["content"], language, 2, result["triage"])
    return schemas.ChatResponse(
        reply=result["reply"], mode=result["mode"], model=result["model"],
        triage=_intake_response(intake, language, result["triage"]),
        sources=result["sources"],
    )


# ----------------- FACILITIES, DOCTORS & READINESS -----------------
def _doctor_out(d: models.Doctor, schedule: List[models.DoctorAvailability]) -> schemas.DoctorOut:
    return schemas.DoctorOut(
        id=d.id, name=d.name, specialty=d.specialty, qualification=d.qualification or "",
        experience_years=d.experience_years or 0, facility_id=d.facility_id, phone=d.phone,
        is_available_today=bool(d.is_available_today), last_roster_update=d.last_roster_update,
        schedule=[schemas.ScheduleSlot(day_of_week=s.day_of_week, start_time=s.start_time, end_time=s.end_time) for s in schedule]
    )


def _schedules_by_doctor(db: Session, doctor_ids: List[int]) -> dict:
    out = {}
    if not doctor_ids:
        return out
    for s in db.query(models.DoctorAvailability).filter(models.DoctorAvailability.doctor_id.in_(doctor_ids)).all():
        out.setdefault(s.doctor_id, []).append(s)
    return out


def _freshness_label(ts: datetime.datetime) -> str:
    mins_ago = max(0, int((utcnow() - ts.replace(tzinfo=datetime.timezone.utc)).total_seconds() / 60))
    if mins_ago < 60:
        return f"Updated {mins_ago}m ago by facility staff"
    if mins_ago < 60 * 48:
        return f"Updated {mins_ago // 60}h ago by facility staff"
    return f"Stale: last updated {mins_ago // 1440} days ago"


def _facility_readiness(db: Session, fac: models.Facility, docs: List[models.Doctor], schedules: dict) -> schemas.FacilityReadinessOut:
    available_docs = [d for d in docs if d.is_available_today]
    services = db.query(models.FacilityService).filter(models.FacilityService.facility_id == fac.id).all()
    inv_items = db.query(models.InventorySnapshot).filter(models.InventorySnapshot.facility_id == fac.id).all()
    queue_waiting = db.query(models.Appointment).filter(
        models.Appointment.facility_id == fac.id, models.Appointment.status.in_(["BOOKED", "IN_QUEUE"]),
        models.Appointment.scheduled_date == today_str()
    ).count()
    per_patient = 10 if fac.facility_type == "PHC" else 12
    timestamps = [fac.last_verified_at] + [d.last_roster_update for d in docs if d.last_roster_update] + [s.updated_at for s in services if s.updated_at]

    return schemas.FacilityReadinessOut(
        id=fac.id, name=fac.name, facility_type=fac.facility_type, address=fac.address,
        village_block=fac.village_block, district=fac.district, distance_km=fac.distance_km,
        travel_time_mins=fac.travel_time_mins, phone=fac.phone, emergency_contact=fac.emergency_contact,
        operating_hours=fac.operating_hours, is_open_now=fac.is_open_now, is_simulated=fac.is_simulated,
        last_verified_at=fac.last_verified_at,
        available_doctors_count=len(available_docs),
        doctor_names=[f"{d.name} ({d.specialty})" for d in available_docs],
        diagnostic_tests_available=[s.name for s in services if s.is_available],
        diagnostic_tests_missing=[s.name for s in services if not s.is_available],
        medicine_stock_summary={item.medicine_name.split()[0]: item.stock_status for item in inv_items},
        estimated_queue_wait_mins=queue_waiting * per_patient // max(len(available_docs), 1),
        freshness_label=_freshness_label(max(timestamps)),
        latitude=fac.latitude,
        longitude=fac.longitude,
        doctors=[_doctor_out(d, schedules.get(d.id, [])) for d in docs],
    )


@app.get("/api/facilities", response_model=List[schemas.FacilityReadinessOut])
def list_facilities(
    district: Optional[str] = None,
    required_test: Optional[str] = None,
    required_medicine: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.Facility)
    if district:
        q = q.filter(func.lower(models.Facility.district) == district.lower())
    facilities = q.order_by(models.Facility.distance_km).all()
    all_docs = db.query(models.Doctor).order_by(models.Doctor.name).all()
    schedules = _schedules_by_doctor(db, [d.id for d in all_docs])
    docs_by_fac = {}
    for d in all_docs:
        docs_by_fac.setdefault(d.facility_id, []).append(d)

    out = [_facility_readiness(db, fac, docs_by_fac.get(fac.id, []), schedules) for fac in facilities]
    if required_test:
        out = [f for f in out if any(required_test.lower() in t.lower() for t in f.diagnostic_tests_available)]
    if required_medicine:
        out = [f for f in out if f.medicine_stock_summary.get(required_medicine.split()[0].capitalize()) in ("IN_STOCK", "LOW_STOCK")]
    return out


@app.get("/api/doctors", response_model=List[schemas.DoctorOut])
def list_doctors(facility_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(models.Doctor)
    if facility_id:
        q = q.filter(models.Doctor.facility_id == facility_id)
    docs = q.order_by(models.Doctor.name).all()
    schedules = _schedules_by_doctor(db, [d.id for d in docs])
    return [_doctor_out(d, schedules.get(d.id, [])) for d in docs]


@app.get("/api/facilities/{facility_id}/manage", response_model=schemas.FacilityManageOut)
def get_facility_management(facility_id: int, current_user: models.User = Depends(require_roles("FACILITY_ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    ensure_facility_manager(current_user, facility_id)
    fac = db.query(models.Facility).filter(models.Facility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail="Facility not found")
    docs = db.query(models.Doctor).filter(models.Doctor.facility_id == facility_id).order_by(models.Doctor.name).all()
    schedules = _schedules_by_doctor(db, [d.id for d in docs])
    return schemas.FacilityManageOut(
        facility=_facility_readiness(db, fac, docs, schedules),
        doctors=[_doctor_out(d, schedules.get(d.id, [])) for d in docs],
        services=db.query(models.FacilityService).filter(models.FacilityService.facility_id == facility_id).order_by(models.FacilityService.name).all(),
        inventory=db.query(models.InventorySnapshot).filter(models.InventorySnapshot.facility_id == facility_id).order_by(models.InventorySnapshot.medicine_name).all(),
    )


@app.patch("/api/doctors/{doctor_id}", response_model=schemas.DoctorOut)
def update_doctor_schedule(doctor_id: int, req: schemas.DoctorUpdateIn, current_user: models.User = Depends(require_roles("FACILITY_ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    doc = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    ensure_facility_manager(current_user, doc.facility_id)

    if req.is_available_today is not None:
        doc.is_available_today = req.is_available_today
    if req.schedule is not None:
        for slot in req.schedule:
            if slot.start_time >= slot.end_time:
                raise HTTPException(status_code=422, detail=f"{slot.day_of_week}: start time must be before end time")
        db.query(models.DoctorAvailability).filter(models.DoctorAvailability.doctor_id == doc.id).delete()
        for slot in req.schedule:
            db.add(models.DoctorAvailability(doctor_id=doc.id, day_of_week=slot.day_of_week, start_time=slot.start_time, end_time=slot.end_time))
    doc.last_roster_update = utcnow()
    db.commit()
    record_audit(db, current_user, "DOCTOR_ROSTER_UPDATED", "DOCTOR", doc.id, "SUCCESS",
                 {"is_available_today": doc.is_available_today, "schedule_changed": req.schedule is not None})
    schedule = db.query(models.DoctorAvailability).filter(models.DoctorAvailability.doctor_id == doc.id).all()
    return _doctor_out(doc, schedule)


@app.patch("/api/facilities/{facility_id}/services/{service_id}", response_model=schemas.FacilityServiceOut)
def update_facility_service(facility_id: int, service_id: int, req: schemas.ServiceUpdateIn, current_user: models.User = Depends(require_roles("FACILITY_ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    ensure_facility_manager(current_user, facility_id)
    svc = db.query(models.FacilityService).filter(models.FacilityService.id == service_id, models.FacilityService.facility_id == facility_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found at this facility")
    svc.is_available = req.is_available
    svc.notes = req.notes
    svc.updated_at = utcnow()
    db.commit()
    db.refresh(svc)
    record_audit(db, current_user, "SERVICE_AVAILABILITY_UPDATED", "FACILITY", facility_id, "SUCCESS", {"service": svc.name, "is_available": svc.is_available})
    return svc


@app.patch("/api/facilities/{facility_id}/inventory/{item_id}", response_model=schemas.InventoryOut)
def update_inventory_item(facility_id: int, item_id: int, req: schemas.InventoryUpdateIn, current_user: models.User = Depends(require_roles("FACILITY_ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    ensure_facility_manager(current_user, facility_id)
    item = db.query(models.InventorySnapshot).filter(models.InventorySnapshot.id == item_id, models.InventorySnapshot.facility_id == facility_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found at this facility")
    item.quantity_in_stock = req.quantity_in_stock
    item.stock_status = "OUT_OF_STOCK" if req.quantity_in_stock == 0 else ("LOW_STOCK" if req.quantity_in_stock <= item.reorder_level else "IN_STOCK")
    item.last_verified_at = utcnow()
    db.commit()
    db.refresh(item)
    record_audit(db, current_user, "INVENTORY_UPDATED", "FACILITY", facility_id, "SUCCESS", {"medicine": item.medicine_name, "quantity": item.quantity_in_stock})
    return item


# ----------------- APPOINTMENTS & QUEUE -----------------
def _create_appointment(db: Session, user: models.User, req: schemas.AppointmentCreate) -> models.Appointment:
    if req.idempotency_key:
        existing = db.query(models.Appointment).filter(models.Appointment.idempotency_key == req.idempotency_key).first()
        if existing:
            return existing

    patient = db.query(models.Patient).filter(models.Patient.id == req.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if user.role in ("PATIENT", "ASHA"):
        ensure_patient_access(db, user, req.patient_id, "BOOK_APPOINTMENT")
    elif user.role not in ("FACILITY_ADMIN", "SUPER_ADMIN", "DOCTOR"):
        raise HTTPException(status_code=403, detail="Not allowed to book appointments")

    doc = db.query(models.Doctor).filter(models.Doctor.id == req.doctor_id).first()
    fac = db.query(models.Facility).filter(models.Facility.id == req.facility_id).first()
    if not doc or not fac:
        raise HTTPException(status_code=404, detail="Doctor or facility not found")
    if doc.facility_id != fac.id:
        raise HTTPException(status_code=422, detail=f"{doc.name} does not practise at {fac.name}")
    try:
        sched_date = datetime.date.fromisoformat(req.scheduled_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="scheduled_date must be YYYY-MM-DD")
    if sched_date < local_today():
        raise HTTPException(status_code=422, detail="Appointments cannot be booked in the past")
    if sched_date == local_today() and not doc.is_available_today:
        raise HTTPException(status_code=409, detail=f"{doc.name} is not on duty today - choose another doctor or date")

    same_day = db.query(models.Appointment).filter(models.Appointment.facility_id == fac.id, models.Appointment.scheduled_date == req.scheduled_date).count()
    queue_token = f"T-{same_day + 1}"
    apt_code = f"APT-{uuid.uuid4().hex[:6].upper()}"

    apt = models.Appointment(
        appointment_code=apt_code, patient_id=req.patient_id, doctor_id=doc.id, facility_id=fac.id,
        scheduled_date=req.scheduled_date, scheduled_time=req.scheduled_time or "10:30 AM",
        consultation_type=req.consultation_type or "IN_PERSON", status="BOOKED", reason=req.reason,
        queue_token=queue_token, is_simulated=True, idempotency_key=req.idempotency_key
    )
    db.add(apt)
    db.commit()
    db.refresh(apt)

    notify_patient(db, req.patient_id, "Appointment confirmed",
                   f"SwasthyaSetu: Appointment {apt_code} confirmed with {doc.name} at {fac.name} on {req.scheduled_date}, {apt.scheduled_time}. Token {queue_token}. Reply CANCEL to cancel (demo).")
    db.add(models.QueueEntry(facility_id=fac.id, appointment_id=apt.id, token_number=queue_token,
                             patient_name=patient.name, estimated_wait_minutes=same_day * 12, status="WAITING"))
    db.add(models.CareTimelineEvent(
        patient_id=req.patient_id, event_type="APPOINTMENT", title=f"Appointment Confirmed ({apt_code})",
        description=f"Token {queue_token} at {fac.name} with {doc.name} on {req.scheduled_date} at {apt.scheduled_time} ({apt.consultation_type}).",
        facility_id=fac.id, doctor_id=doc.id, actor_name=user.full_name, actor_role=user.role,
        metadata_json=json.dumps({"appointment_code": apt_code, "token": queue_token})
    ))
    db.commit()
    record_audit(db, user, "BOOK_APPOINTMENT", "APPOINTMENT", apt.id, "SUCCESS", {"code": apt_code, "facility": fac.name})
    return apt


@app.post("/api/appointments", response_model=schemas.AppointmentOut)
def create_appointment(req: schemas.AppointmentCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    apt = _create_appointment(db, current_user, req)
    doctors, facilities = _names(db)
    patient = db.query(models.Patient).filter(models.Patient.id == apt.patient_id).first()
    return _appointment_out(apt, {patient.id: patient.name}, doctors, facilities)


@app.get("/api/appointments", response_model=List[schemas.AppointmentOut])
def list_appointments(
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    facility_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 200,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Appointment)
    if current_user.role == "PATIENT":
        own = patient_for_user(db, current_user)
        query = query.filter(models.Appointment.patient_id == (own.id if own else -1))
    elif current_user.role == "DOCTOR":
        doc = doctor_for_user(db, current_user)
        query = query.filter(models.Appointment.doctor_id == (doc.id if doc else -1))
    elif current_user.role == "FACILITY_ADMIN":
        query = query.filter(models.Appointment.facility_id == current_user.facility_id)
    elif current_user.role == "ASHA":
        query = query.filter(models.Appointment.patient_id.in_(
            db.query(models.Patient.id).filter(models.Patient.assigned_asha_id == current_user.id)))

    if patient_id:
        query = query.filter(models.Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.filter(models.Appointment.doctor_id == doctor_id)
    if facility_id:
        query = query.filter(models.Appointment.facility_id == facility_id)
    if status:
        query = query.filter(models.Appointment.status == status)

    appointments = query.order_by(desc(models.Appointment.id)).limit(min(max(limit, 1), 1000)).all()
    doctors, facilities = _names(db)
    patient_ids = {a.patient_id for a in appointments}
    patients = {p.id: p.name for p in db.query(models.Patient).filter(models.Patient.id.in_(patient_ids)).all()} if patient_ids else {}
    return [_appointment_out(a, patients, doctors, facilities) for a in appointments]


@app.patch("/api/appointments/{appointment_id}", response_model=schemas.AppointmentOut)
def update_appointment_status(appointment_id: int, req: schemas.AppointmentStatusIn, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    apt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    allowed = {"CANCELLED", "NO_SHOW", "IN_QUEUE", "BOOKED"}
    if req.status not in allowed:
        raise HTTPException(status_code=422, detail=f"Status must be one of {sorted(allowed)}")
    if apt.status == "COMPLETED":
        raise HTTPException(status_code=409, detail="Completed appointments cannot be changed")

    if current_user.role == "PATIENT":
        own = patient_for_user(db, current_user)
        if not own or own.id != apt.patient_id or req.status != "CANCELLED":
            raise HTTPException(status_code=403, detail="Patients can only cancel their own appointments")
    elif current_user.role == "DOCTOR":
        doc = doctor_for_user(db, current_user)
        if not doc or doc.id != apt.doctor_id:
            raise HTTPException(status_code=403, detail="Not your appointment")
    elif current_user.role == "FACILITY_ADMIN":
        ensure_facility_manager(current_user, apt.facility_id)
    elif current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Not allowed")

    apt.status = req.status
    db.add(models.CareTimelineEvent(
        patient_id=apt.patient_id, event_type="APPOINTMENT", title=f"Appointment {apt.appointment_code}: {req.status.replace('_', ' ').title()}",
        description=f"Status changed to {req.status} by {current_user.full_name}.", facility_id=apt.facility_id, doctor_id=apt.doctor_id,
        actor_name=current_user.full_name, actor_role=current_user.role, metadata_json=json.dumps({"status": req.status})
    ))
    db.commit()
    record_audit(db, current_user, "APPOINTMENT_STATUS_CHANGED", "APPOINTMENT", apt.id, "SUCCESS", {"status": req.status})
    doctors, facilities = _names(db)
    patient = db.query(models.Patient).filter(models.Patient.id == apt.patient_id).first()
    return _appointment_out(apt, {patient.id: patient.name}, doctors, facilities)


# ----------------- CLINICAL ENCOUNTERS, PRESCRIPTIONS & DIAGNOSTICS -----------------
@app.post("/api/encounters", response_model=schemas.EncounterOut)
def create_clinical_encounter(req: schemas.EncounterCreate, current_user: models.User = Depends(require_roles("DOCTOR")), db: Session = Depends(get_db)):
    doc = doctor_for_user(db, current_user)
    if not doc:
        raise HTTPException(status_code=403, detail="No doctor profile linked to this account")
    ensure_patient_access(db, current_user, req.patient_id, "CREATE_ENCOUNTER")
    facility_id = doc.facility_id

    apt = None
    if req.appointment_id:
        apt = db.query(models.Appointment).filter(models.Appointment.id == req.appointment_id).first()
        if not apt or apt.patient_id != req.patient_id or apt.doctor_id != doc.id:
            raise HTTPException(status_code=422, detail="Appointment does not belong to this doctor and patient")

    enc = models.ClinicalEncounter(
        appointment_id=req.appointment_id, patient_id=req.patient_id, doctor_id=doc.id, facility_id=facility_id,
        chief_complaints=req.chief_complaints, clinical_notes=req.clinical_notes, diagnosis=req.diagnosis,
        vital_bp=req.vital_bp or "120/80", vital_pulse=req.vital_pulse or 74, vital_temp=req.vital_temp or 98.6,
        vital_spo2=req.vital_spo2 or 98, clinician_risk_flag=req.clinician_risk_flag or "NORMAL"
    )
    db.add(enc)
    db.commit()
    db.refresh(enc)

    if apt:
        apt.status = "COMPLETED"
        q = db.query(models.QueueEntry).filter(models.QueueEntry.appointment_id == apt.id).first()
        if q:
            q.status = "COMPLETED"

    # Prescriptions, checked against this facility's dispensary stock
    if req.prescriptions:
        rx = models.Prescription(encounter_id=enc.id, patient_id=req.patient_id, doctor_id=doc.id,
                                 prescription_code=f"RX-{uuid.uuid4().hex[:6].upper()}", notes=f"Prescribed for {req.diagnosis}")
        db.add(rx)
        db.commit()
        db.refresh(rx)
        out_of_stock = []
        for p_item in req.prescriptions:
            inv = db.query(models.InventorySnapshot).filter(
                models.InventorySnapshot.facility_id == facility_id,
                models.InventorySnapshot.medicine_name.ilike(f"%{p_item.medicine_name.split()[0]}%")
            ).first()
            coll_status = "OUT_OF_STOCK" if inv and inv.stock_status == "OUT_OF_STOCK" else "PENDING"
            if coll_status == "OUT_OF_STOCK":
                out_of_stock.append(p_item.medicine_name)
            db.add(models.PrescriptionItem(prescription_id=rx.id, medicine_name=p_item.medicine_name, dosage=p_item.dosage,
                                           frequency=p_item.frequency, duration_days=p_item.duration_days,
                                           instructions=p_item.instructions, collected_status=coll_status))
        notify_patient(db, req.patient_id, "Prescription issued",
                       f"SwasthyaSetu: Prescription {rx.prescription_code} issued by {doc.name}."
                       + (f" Not in stock at this centre: {', '.join(out_of_stock)} - see the app for facilities that have it." if out_of_stock else " Collect your medicines at the dispensary."))
        db.add(models.CareTimelineEvent(
            patient_id=req.patient_id, event_type="PRESCRIPTION", title=f"Digital Prescription Issued ({rx.prescription_code})",
            description=f"{len(req.prescriptions)} medicine(s) prescribed for {req.diagnosis}."
                        + (f" Not in stock at this facility: {', '.join(out_of_stock)}." if out_of_stock else ""),
            facility_id=facility_id, doctor_id=doc.id, actor_name=doc.name, actor_role="DOCTOR",
            metadata_json=json.dumps({"prescription_code": rx.prescription_code, "out_of_stock": out_of_stock})
        ))

    # Diagnostic orders, checked against the facility's maintained service list
    for t_name in req.diagnostic_test_names or []:
        svc = db.query(models.FacilityService).filter(models.FacilityService.facility_id == facility_id, models.FacilityService.name == t_name).first()
        order_status = "ORDERED" if svc and svc.is_available else "UNAVAILABLE"
        db.add(models.DiagnosticOrder(
            encounter_id=enc.id, patient_id=req.patient_id, doctor_id=doc.id, facility_id=facility_id, test_name=t_name,
            urgency="ROUTINE", status=order_status, scheduled_date=(local_today() + datetime.timedelta(days=1)).isoformat(),
            notes=f"Ordered after consultation for {req.diagnosis}" + ("" if order_status == "ORDERED" else " - not available here, refer to District Hospital")
        ))
        db.add(models.CareTimelineEvent(
            patient_id=req.patient_id, event_type="DIAGNOSTIC", title=f"Diagnostic Ordered: {t_name}",
            description=f"Status: {order_status}." + ("" if order_status == "ORDERED" else " Referral to a facility with this test is required."),
            facility_id=facility_id, doctor_id=doc.id, actor_name=doc.name, actor_role="DOCTOR",
            metadata_json=json.dumps({"test_name": t_name, "status": order_status})
        ))

    # Follow-up plan and SMS reminder
    if req.follow_up_days and req.follow_up_days > 0:
        due = (local_today() + datetime.timedelta(days=req.follow_up_days)).isoformat()
        fup = models.FollowUpPlan(encounter_id=enc.id, patient_id=req.patient_id, doctor_id=doc.id, facility_id=facility_id,
                                  due_date=due, instructions=req.follow_up_instructions or "Routine review of clinical symptoms", status="SCHEDULED")
        db.add(fup)
        db.commit()
        fac = db.query(models.Facility).filter(models.Facility.id == facility_id).first()
        db.add(models.Reminder(
            follow_up_id=fup.id, patient_id=req.patient_id, channel="SMS",
            message=f"SwasthyaSetu Reminder: your follow-up with {doc.name} at {fac.name if fac else 'the facility'} is due on {due}. Please bring previous reports.",
            scheduled_time=(utcnow() + datetime.timedelta(days=max(req.follow_up_days - 1, 0))).replace(tzinfo=None), status="PENDING"
        ))
        notify_patient(db, req.patient_id, "Follow-up scheduled",
                       f"SwasthyaSetu: {doc.name} has scheduled your follow-up on {due}. You will get a reminder the day before.")
        db.add(models.CareTimelineEvent(
            patient_id=req.patient_id, event_type="FOLLOW_UP", title="Follow-Up Review Scheduled",
            description=f"Due date: {due}. Instructions: {fup.instructions}. SMS reminder scheduled.",
            facility_id=facility_id, doctor_id=doc.id, actor_name=doc.name, actor_role="DOCTOR", metadata_json=json.dumps({"due_date": due})
        ))

    db.add(models.CareTimelineEvent(
        patient_id=req.patient_id, event_type="CONSULTATION", title=f"Consultation Completed - {req.diagnosis}",
        description=f"BP {enc.vital_bp}, Pulse {enc.vital_pulse}, SpO2 {enc.vital_spo2}%. Notes: {req.clinical_notes[:160]}",
        facility_id=facility_id, doctor_id=doc.id, actor_name=doc.name, actor_role="DOCTOR",
        metadata_json=json.dumps({"diagnosis": req.diagnosis, "risk_flag": enc.clinician_risk_flag})
    ))
    db.commit()
    record_audit(db, current_user, "CREATE_CLINICAL_ENCOUNTER", "ENCOUNTER", enc.id, "SUCCESS", {"diagnosis": req.diagnosis, "patient_id": req.patient_id})
    return enc


@app.get("/api/diagnostics/orders", response_model=List[schemas.DiagnosticOrderOut])
def list_diagnostic_orders(patient_id: Optional[int] = None, facility_id: Optional[int] = None, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.DiagnosticOrder)
    if patient_id:
        ensure_patient_access(db, current_user, patient_id, "VIEW_DIAGNOSTICS")
        q = q.filter(models.DiagnosticOrder.patient_id == patient_id)
    elif current_user.role == "FACILITY_ADMIN":
        q = q.filter(models.DiagnosticOrder.facility_id == current_user.facility_id)
    elif current_user.role == "DOCTOR":
        doc = doctor_for_user(db, current_user)
        q = q.filter(models.DiagnosticOrder.doctor_id == (doc.id if doc else -1))
    elif current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="patient_id is required")
    if facility_id:
        q = q.filter(models.DiagnosticOrder.facility_id == facility_id)
    _, facilities = _names(db)
    out = []
    for o in q.order_by(desc(models.DiagnosticOrder.id)).limit(500).all():
        item = schemas.DiagnosticOrderOut.model_validate(o)
        item.facility_name = facilities[o.facility_id].name if o.facility_id in facilities else ""
        out.append(item)
    return out


# ----------------- FOLLOW-UPS & ASHA HEALTH WORKER TASKS -----------------
@app.get("/api/follow-ups", response_model=List[schemas.FollowUpOut])
def list_follow_ups(patient_id: Optional[int] = None, status: Optional[str] = None, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    detect_missed_care(db)
    q = db.query(models.FollowUpPlan)
    if patient_id:
        ensure_patient_access(db, current_user, patient_id, "VIEW_FOLLOW_UPS")
        q = q.filter(models.FollowUpPlan.patient_id == patient_id)
    elif current_user.role == "ASHA":
        q = q.filter(models.FollowUpPlan.patient_id.in_(db.query(models.Patient.id).filter(models.Patient.assigned_asha_id == current_user.id)))
    elif current_user.role == "DOCTOR":
        doc = doctor_for_user(db, current_user)
        q = q.filter(models.FollowUpPlan.doctor_id == (doc.id if doc else -1))
    elif current_user.role == "FACILITY_ADMIN":
        q = q.filter(models.FollowUpPlan.facility_id == current_user.facility_id)
    elif current_user.role == "PATIENT":
        own = patient_for_user(db, current_user)
        q = q.filter(models.FollowUpPlan.patient_id == (own.id if own else -1))
    if status:
        q = q.filter(models.FollowUpPlan.status == status)
    plans = q.order_by(desc(models.FollowUpPlan.id)).limit(500).all()
    ids = {p.patient_id for p in plans}
    names = {p.id: p.name for p in db.query(models.Patient).filter(models.Patient.id.in_(ids)).all()} if ids else {}
    out = []
    for p in plans:
        item = schemas.FollowUpOut.model_validate(p)
        item.patient_name = names.get(p.patient_id, "")
        out.append(item)
    return out


def _task_out(db: Session, task: models.HealthWorkerTask) -> schemas.HealthWorkerTaskOut:
    out = schemas.HealthWorkerTaskOut.model_validate(task)
    pat = db.query(models.Patient).filter(models.Patient.id == task.patient_id).first()
    if pat:
        out.patient_name, out.patient_village, out.patient_phone = pat.name, pat.village, pat.phone
    return out


@app.get("/api/tasks", response_model=List[schemas.HealthWorkerTaskOut])
def list_health_worker_tasks(
    asha_worker_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: models.User = Depends(require_roles("ASHA", "SUPER_ADMIN")),
    db: Session = Depends(get_db)
):
    detect_missed_care(db)
    q = db.query(models.HealthWorkerTask)
    if current_user.role == "ASHA":
        q = q.filter(models.HealthWorkerTask.asha_worker_id == current_user.id)
    elif asha_worker_id:
        q = q.filter(models.HealthWorkerTask.asha_worker_id == asha_worker_id)
    if status:
        q = q.filter(models.HealthWorkerTask.status == status)
    priority_rank = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2}
    tasks = sorted(q.limit(500).all(), key=lambda t: (t.status == "RESOLVED", priority_rank.get(t.priority, 3), t.due_date))
    return [_task_out(db, t) for t in tasks]


def _update_task(db: Session, user: models.User, task: models.HealthWorkerTask, status: str, visit_notes: str, outcome: Optional[str], escalated_to_doctor_id: Optional[int] = None):
    if user.role == "ASHA" and task.asha_worker_id != user.id:
        record_audit(db, user, "UNAUTHORIZED_TASK_UPDATE_DENIED", "TASK", task.id, "DENIED")
        raise HTTPException(status_code=403, detail="This task is assigned to a different ASHA worker")
    if status not in ("OPEN", "IN_PROGRESS", "RESOLVED", "ESCALATED"):
        raise HTTPException(status_code=422, detail="Invalid task status")

    task.status = status
    task.visit_notes = visit_notes
    task.outcome = outcome
    if escalated_to_doctor_id:
        task.escalated_to_doctor_id = escalated_to_doctor_id
    if status == "RESOLVED":
        task.resolved_at = utcnow()
        if task.follow_up_id:
            fup = db.query(models.FollowUpPlan).filter(models.FollowUpPlan.id == task.follow_up_id).first()
            if fup:
                fup.status = "COMPLETED"

    if status in ("RESOLVED", "ESCALATED"):
        notify_patient(db, task.patient_id, "ASHA visit recorded",
                       f"SwasthyaSetu: {user.full_name} recorded a home visit. " + ("Your case has been escalated to the medical officer." if status == "ESCALATED" else "Thank you - your follow-up is marked complete."))
    db.add(models.CareTimelineEvent(
        patient_id=task.patient_id, event_type="HOME_VISIT", title=f"ASHA Home Visit Recorded - {status}",
        description=f"Notes: {visit_notes}. Outcome: {outcome or 'Pending review'}.",
        actor_name=user.full_name, actor_role=user.role, metadata_json=json.dumps({"outcome": outcome, "status": status})
    ))
    db.commit()
    db.refresh(task)
    record_audit(db, user, "UPDATE_HEALTH_WORKER_TASK", "TASK", task.id, "SUCCESS", {"status": status})
    return task


@app.patch("/api/tasks/{task_id}", response_model=schemas.HealthWorkerTaskOut)
def update_task(task_id: int, req: schemas.TaskUpdateIn, current_user: models.User = Depends(require_roles("ASHA", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    task = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _update_task(db, current_user, task, req.status, req.visit_notes, req.outcome, req.escalated_to_doctor_id)
    return _task_out(db, task)


@app.post("/api/continuity/run")
def run_continuity_engine(current_user: models.User = Depends(require_roles("SUPER_ADMIN", "FACILITY_ADMIN")), db: Session = Depends(get_db)):
    return detect_missed_care(db)


# ----------------- TIMELINE & AUDIT -----------------
@app.get("/api/timeline/{patient_id}", response_model=List[schemas.CareTimelineEventOut])
def get_patient_timeline(patient_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_patient_access(db, current_user, patient_id, "VIEW_TIMELINE")
    return db.query(models.CareTimelineEvent).filter(
        models.CareTimelineEvent.patient_id == patient_id
    ).order_by(desc(models.CareTimelineEvent.created_at)).all()


@app.get("/api/audit-events")
def list_audit_events(limit: int = 50, current_user: models.User = Depends(require_roles("SUPER_ADMIN")), db: Session = Depends(get_db)):
    events = db.query(models.AuditEvent).order_by(desc(models.AuditEvent.created_at)).limit(min(max(limit, 1), 500)).all()
    return [
        {"id": e.id, "user_id": e.user_id, "user_name": e.user_name, "role": e.role, "action": e.action,
         "resource_type": e.resource_type, "resource_id": e.resource_id, "outcome": e.outcome,
         "ip_address": e.ip_address, "details_json": e.details_json,
         "created_at": e.created_at.replace(tzinfo=datetime.timezone.utc).isoformat() if e.created_at else None}
        for e in events
    ]


# ----------------- OFFLINE SYNC BATCH -----------------
@app.post("/api/sync/batch")
def sync_offline_actions(req: schemas.SyncBatchRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = []
    for item in req.actions:
        if db.query(models.SyncOperation).filter(models.SyncOperation.idempotency_key == item.idempotency_key).first():
            results.append({"idempotency_key": item.idempotency_key, "status": "ALREADY_SYNCED", "message": "Duplicate skipped idempotently."})
            continue
        try:
            if item.action_type == "BOOK_APPOINTMENT":
                payload = dict(item.payload)
                payload["idempotency_key"] = item.idempotency_key
                _create_appointment(db, current_user, schemas.AppointmentCreate(**payload))
            elif item.action_type == "RESOLVE_TASK":
                p = item.payload
                task = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.id == p.get("task_id")).first()
                if not task:
                    raise HTTPException(status_code=404, detail="Task not found")
                _update_task(db, current_user, task, p.get("status", "RESOLVED"),
                             p.get("visit_notes", "Synced from offline ASHA queue"), p.get("outcome", "HOME_CHECK_COMPLETED"))
            else:
                raise HTTPException(status_code=422, detail=f"Unknown action type {item.action_type}")
        except HTTPException as e:
            db.rollback()
            results.append({"idempotency_key": item.idempotency_key, "status": "FAILED", "message": str(e.detail)})
            continue

        db.add(models.SyncOperation(idempotency_key=item.idempotency_key, user_id=current_user.id, action_type=item.action_type,
                                    payload_json=json.dumps(item.payload), status="SYNCED"))
        db.commit()
        results.append({"idempotency_key": item.idempotency_key, "status": "SYNCED", "message": "Successfully synchronized and committed."})

    return {"synced_count": sum(1 for r in results if r["status"] == "SYNCED"), "results": results}


# ----------------- ADMIN OPERATIONAL METRICS -----------------
@app.get("/api/admin/metrics", response_model=schemas.AdminMetricsOut)
def get_admin_metrics(current_user: models.User = Depends(require_roles("SUPER_ADMIN")), db: Session = Depends(get_db)):
    detect_missed_care(db)
    facilities = db.query(models.Facility).all()
    stale = sum(1 for f in facilities if (utcnow() - f.last_verified_at.replace(tzinfo=datetime.timezone.utc)).total_seconds() > 86400)
    return schemas.AdminMetricsOut(
        total_patients=db.query(models.Patient).count(),
        total_facilities=len(facilities),
        total_doctors=db.query(models.Doctor).count(),
        total_asha_workers=db.query(models.User).filter(models.User.role == "ASHA").count(),
        total_authorities=db.query(models.User).filter(models.User.role == "SUPER_ADMIN").count(),
        total_appointments=db.query(models.Appointment).count(),
        completed_appointments=db.query(models.Appointment).filter(models.Appointment.status == "COMPLETED").count(),
        pending_appointments=db.query(models.Appointment).filter(models.Appointment.status.in_(["BOOKED", "IN_QUEUE"])).count(),
        overdue_followups_count=db.query(models.FollowUpPlan).filter(models.FollowUpPlan.status == "OVERDUE").count(),
        open_asha_tasks=db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.status.in_(["OPEN", "IN_PROGRESS"])).count(),
        resolved_asha_tasks=db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.status == "RESOLVED").count(),
        critical_emergency_alerts_count=db.query(models.SymptomIntake).filter(models.SymptomIntake.emergency_triaged == True).count(),
        diagnostic_tests_ordered=db.query(models.DiagnosticOrder).count(),
        medicine_stock_alerts_count=db.query(models.InventorySnapshot).filter(models.InventorySnapshot.stock_status.in_(["OUT_OF_STOCK", "LOW_STOCK"])).count(),
        data_freshness_pct=round(100.0 * (len(facilities) - stale) / max(len(facilities), 1), 1),
        is_demo_metric=True
    )


@app.get("/api/admin/activity")
def get_admin_activity(current_user: models.User = Depends(require_roles("SUPER_ADMIN")), db: Session = Depends(get_db)):
    """Appointment monitoring and platform activity for district administrators."""
    by_status = dict(db.query(models.Appointment.status, func.count(models.Appointment.id)).group_by(models.Appointment.status).all())
    fac_rows = (
        db.query(models.Facility.name, func.count(models.Appointment.id))
        .join(models.Appointment, models.Appointment.facility_id == models.Facility.id)
        .group_by(models.Facility.name).order_by(desc(func.count(models.Appointment.id))).limit(10).all()
    )
    triage = dict(db.query(models.SymptomIntake.triage_level, func.count(models.SymptomIntake.id)).group_by(models.SymptomIntake.triage_level).all())
    since = (utcnow() - datetime.timedelta(days=1)).replace(tzinfo=None)
    recent = db.query(models.Appointment).order_by(desc(models.Appointment.id)).limit(25).all()
    doctors, facilities = _names(db)
    ids = {a.patient_id for a in recent}
    names = {p.id: p.name for p in db.query(models.Patient).filter(models.Patient.id.in_(ids)).all()} if ids else {}
    return {
        "appointments_by_status": by_status,
        "appointments_by_facility": [{"facility": n, "count": c} for n, c in fac_rows],
        "intakes_by_triage_level": triage,
        "registrations_last_24h": db.query(models.Patient).filter(models.Patient.created_at >= since).count(),
        "logins_last_24h": db.query(models.AuditEvent).filter(models.AuditEvent.action == "USER_LOGIN", models.AuditEvent.created_at >= since).count(),
        "access_denials_total": db.query(models.AuditEvent).filter(models.AuditEvent.outcome == "DENIED").count(),
        "impact": {
            "missed_follow_ups_recovered": db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.status.in_(["RESOLVED", "ESCALATED"])).count(),
            "emergencies_directed_to_112": db.query(models.SymptomIntake).filter(models.SymptomIntake.emergency_triaged == True).count(),
            "wasted_trips_avoided": db.query(models.DiagnosticOrder).filter(models.DiagnosticOrder.status == "UNAVAILABLE").count()
                                    + db.query(models.PrescriptionItem).filter(models.PrescriptionItem.collected_status == "OUT_OF_STOCK").count(),
            "sms_reminders_sent": db.query(models.Notification).count(),
            "consent_withdrawals_honoured": db.query(models.ConsentRecord).filter(models.ConsentRecord.status == "REVOKED").count(),
        },
        "recent_appointments": [_appointment_out(a, names, doctors, facilities).model_dump(mode="json") for a in recent],
    }


# ----------------- CARE-PATHWAY ML MODEL (trained on the fictional dataset) -----------------
@app.get("/api/ai/model-info")
def get_ai_model_info(current_user: models.User = Depends(get_current_user)):
    if os.path.exists(INFO_FILE):
        with open(INFO_FILE, "r") as f:
            return json.load(f)
    return {"status": "NOT_TRAINED", "message": "Model not trained yet."}


@app.post("/api/ai/train")
def trigger_model_training(current_user: models.User = Depends(require_roles("SUPER_ADMIN"))):
    summary = train_model()
    return {"status": "success", "message": f"Care-pathway model retrained on {summary['dataset_size']} fictional records.", "summary": summary}


@app.post("/api/ai/predict-care")
def predict_care_endpoint(payload: dict, current_user: models.User = Depends(require_roles("DOCTOR", "SUPER_ADMIN"))):
    return predict_care_pathway(payload)


# ----------------- STATIC FRONTEND SERVING -----------------
frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")
