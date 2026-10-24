from lifestyle_engine import generate_chronic_care_lifestyle_plan
import os
import io
import csv
import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

import models
import schemas
from database import get_db, DEFAULT_DB_PATH
from dataset_ingestion import ingest_dataset
from monitoring_engine import run_continuous_monitoring, DEFAULT_REFERENCE_DATE
from ai_assistant import GroundedAIAssistant

router = APIRouter(prefix="/api", tags=["Monitoring & Intelligence"])

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

# ----------------- MODULE 1 & 8: INGESTION & DATA QUALITY -----------------

@router.post("/ingestion/run")
def trigger_ingestion(reset_db: bool = False, db: Session = Depends(get_db)):
    summary = ingest_dataset(db=db, reset_db=reset_db)
    # Automatically initialize continuous monitoring after ingestion
    run_continuous_monitoring(db=db)
    return {
        "status": "SUCCESS",
        "message": f"Successfully ingested dataset. Processed {summary['total_processed']} records, {summary['total_imported']} imported.",
        "summary": summary
    }

@router.get("/ingestion/jobs", response_model=List[schemas.IngestionJobOut])
def list_ingestion_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.IngestionJob).order_by(desc(models.IngestionJob.started_at)).all()
    return jobs

@router.get("/ingestion/jobs/{job_id}/errors", response_model=List[schemas.IngestionValidationErrorOut])
def get_job_validation_errors(job_id: int, db: Session = Depends(get_db)):
    errors = db.query(models.IngestionValidationError).filter(
        models.IngestionValidationError.job_id == job_id
    ).all()
    return errors

@router.get("/data-quality-report")
def get_data_quality_report(db: Session = Depends(get_db)):
    report_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DATA_QUALITY_REPORT.json")
    if os.path.exists(report_file):
        with open(report_file, "r") as f:
            return json.load(f)
    
    # Generate live fallback
    tot_p = db.query(models.Patient).count()
    tot_d = db.query(models.Doctor).count()
    tot_f = db.query(models.Facility).count()
    validation_errs = db.query(models.IngestionValidationError).count()
    return {
        "analyzed_at": utcnow().isoformat(),
        "summary": {
            "patients": tot_p, "doctors": tot_d, "facilities": tot_f,
            "validation_errors": validation_errs
        },
        "integrity_checks": {
            "validation_errors_count": validation_errs,
            "database_status": "ONLINE"
        }
    }

# ----------------- MODULE 3: PATIENT MASTER PROFILE -----------------

@router.get("/patients/{patient_id}/master-profile", response_model=schemas.PatientMasterProfileOut)
def get_patient_master_profile(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Fetch all linked care records
    apts = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()
    encounters = db.query(models.ClinicalEncounter).filter(models.ClinicalEncounter.patient_id == patient_id).all()
    prescriptions = db.query(models.Prescription).filter(models.Prescription.patient_id == patient_id).all()
    diag_orders = db.query(models.DiagnosticOrder).filter(models.DiagnosticOrder.patient_id == patient_id).all()
    reports = db.query(models.PatientReport).filter(models.PatientReport.patient_id == patient_id).all()
    fups = db.query(models.FollowUpPlan).filter(models.FollowUpPlan.patient_id == patient_id).all()
    tasks = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.patient_id == patient_id).all()
    alerts = db.query(models.MonitoringAlert).filter(models.MonitoringAlert.patient_id == patient_id).all()
    timeline = db.query(models.CareTimelineEvent).filter(
        models.CareTimelineEvent.patient_id == patient_id
    ).order_by(desc(models.CareTimelineEvent.created_at)).all()
    consents = db.query(models.ConsentRecord).filter(models.ConsentRecord.patient_id == patient_id).all()
    ai_summaries = db.query(models.AISummary).filter(models.AISummary.patient_id == patient_id).all()

    # Determine assigned facility
    assigned_fac = None
    if apts and len(apts) > 0:
        assigned_fac = db.get(models.Facility, apts[0].facility_id)
    if not assigned_fac:
        assigned_fac = db.query(models.Facility).first()

    provenance_counts = {
        "imported_records": len(apts) + len(reports) + len(fups),
        "clinician_entered": len(encounters) + len(prescriptions),
        "ai_summaries": len(ai_summaries),
        "active_alerts": len([a for a in alerts if a.status in ["NEW", "ACKNOWLEDGED", "ASSIGNED", "IN_PROGRESS"]])
    }

    # Generate personalized post-consultation / chronic lifestyle plan
    med_names = []
    for pr in prescriptions:
        if hasattr(pr, 'items'):
            for it in pr.items:
                med_names.append(it.medicine_name)
    recent_diag = ", ".join([e.diagnosis for e in encounters if e.diagnosis]) if encounters else ""
    combined_cond = f"{patient.chronic_conditions or ''} {recent_diag}".strip()
    lifestyle_plan = generate_chronic_care_lifestyle_plan(combined_cond, med_names, language="hi")

    return schemas.PatientMasterProfileOut(
        patient=patient,
        external_id=patient.external_id,
        conditions=patient.chronic_conditions,
        current_medication=patient.current_medication or "None",
        allergies=patient.allergies or "No known allergy",
        blood_group=patient.blood_group,
        assigned_facility=assigned_fac,
        appointments=apts,
        clinical_encounters=encounters,
        prescriptions=prescriptions,
        diagnostic_orders=diag_orders,
        reports=reports,
        follow_up_plans=fups,
        tasks=tasks,
        alerts=alerts,
        timeline_events=timeline,
        consents=consents,
        ai_summaries=ai_summaries,
        provenance_counts=provenance_counts,
        lifestyle_guidance=schemas.LifestyleGuidanceOut(**lifestyle_plan) if lifestyle_plan else None
    )

@router.get("/patients/{patient_id}/lifestyle-guidance", response_model=schemas.LifestyleGuidanceOut)
def get_patient_lifestyle_guidance(
    patient_id: int,
    language: str = "hi",
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    encounters = db.query(models.ClinicalEncounter).filter(models.ClinicalEncounter.patient_id == patient_id).all()
    recent_diag = ", ".join([e.diagnosis for e in encounters if e.diagnosis]) if encounters else ""
    combined_cond = f"{patient.chronic_conditions or ''} {recent_diag}".strip()

    prescriptions = db.query(models.Prescription).filter(models.Prescription.patient_id == patient_id).all()
    med_names = []
    for pr in prescriptions:
        if hasattr(pr, 'items'):
            for it in pr.items:
                med_names.append(it.medicine_name)

    plan = generate_chronic_care_lifestyle_plan(combined_cond, med_names, language=language)
    return schemas.LifestyleGuidanceOut(**plan)

@router.get("/patients/{patient_id}/family", response_model=List[schemas.FamilyMemberOut])
def get_patient_family_view(patient_id: int, db: Session = Depends(get_db)):
    members = db.query(models.FamilyMember).filter(models.FamilyMember.patient_id == patient_id).all()
    return members

# ----------------- MODULE 4 & 5: MONITORING & ALERTS -----------------

@router.post("/monitoring/run")
def trigger_monitoring_run(
    ref_date: Optional[str] = Query(None, description="Evaluation reference date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    summary = run_continuous_monitoring(db=db, ref_date_str=ref_date)
    return {
        "status": "SUCCESS",
        "message": f"Evaluated monitoring rules. Created {summary['new_alerts_created']} new alerts, {summary['existing_active_alerts']} active, {summary['tasks_generated']} tasks generated.",
        "summary": summary
    }

@router.get("/alerts", response_model=List[schemas.MonitoringAlertOut])
def list_alerts(
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    patient_id: Optional[int] = None,
    assigned_role: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    q = db.query(models.MonitoringAlert)
    if category:
        q = q.filter(models.MonitoringAlert.category == category)
    if status:
        q = q.filter(models.MonitoringAlert.status == status)
    if priority:
        q = q.filter(models.MonitoringAlert.priority == priority)
    if patient_id:
        q = q.filter(models.MonitoringAlert.patient_id == patient_id)
    if assigned_role:
        q = q.filter(models.MonitoringAlert.assigned_role == assigned_role)

    alerts = q.order_by(desc(models.MonitoringAlert.created_at)).offset(offset).limit(limit).all()
    return alerts

@router.get("/alerts/{alert_id}", response_model=schemas.MonitoringAlertOut)
def get_alert_detail(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(models.MonitoringAlert).filter(models.MonitoringAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/alerts/{alert_id}/action", response_model=schemas.MonitoringAlertOut)
def update_alert_action(
    alert_id: int,
    req: schemas.AlertActionRequest,
    db: Session = Depends(get_db)
):
    alert = db.query(models.MonitoringAlert).filter(models.MonitoringAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    action = req.action.upper()
    now_dt = utcnow()

    if action in ["RESOLVED"]:
        alert.status = "RESOLVED"
        alert.resolution_notes = req.notes or "Alert resolved by authorized health official."
        alert.resolution_timestamp = now_dt
    elif action in ["DISMISSED"]:
        alert.status = "DISMISSED"
        alert.dismissed_reason = req.dismissed_reason or req.notes or "Dismissed with clinical/operational reason."
        alert.resolution_timestamp = now_dt
    elif action in ["ACKNOWLEDGED"]:
        alert.status = "ACKNOWLEDGED"
    elif action in ["IN_PROGRESS"]:
        alert.status = "IN_PROGRESS"
    elif action in ["ASSIGNED"]:
        alert.status = "ASSIGNED"
        if req.assigned_role:
            alert.assigned_role = req.assigned_role
        if req.assigned_user_id:
            alert.assigned_user_id = req.assigned_user_id
    elif action in ["REOPENED"]:
        alert.status = "NEW"
        alert.resolution_timestamp = None

    alert.updated_at = now_dt

    # Record in history
    history = models.AlertResolutionHistory(
        alert_id=alert.id,
        actor_name="Health Administrator / Provider",
        actor_role="ADMIN",
        action=action,
        notes=req.notes or f"Transitioned to {alert.status}",
        created_at=now_dt
    )
    db.add(history)
    db.commit()
    db.refresh(alert)
    return alert

# ----------------- MODULE 6: GROUNDED AI ASSISTANT -----------------

@router.post("/ai/patient-summary/{patient_id}")
def get_ai_patient_summary(patient_id: int, db: Session = Depends(get_db)):
    return GroundedAIAssistant.summarize_patient_timeline(patient_id, db)

@router.post("/ai/explain-report")
def explain_report_endpoint(req: schemas.AIExplainReportRequest, db: Session = Depends(get_db)):
    return GroundedAIAssistant.explain_lab_report(req.report_id, req.target_audience or "PATIENT", db)

@router.post("/ai/query")
def administrative_query_endpoint(req: schemas.AIQueryRequest, db: Session = Depends(get_db)):
    return GroundedAIAssistant.answer_administrative_query(req.query, db)

# ----------------- MODULE 7 & 8: LAB REPORTS & CLINICIAN REVIEW -----------------

@router.get("/reports", response_model=List[schemas.PatientReportOut])
def list_patient_reports(
    patient_id: Optional[int] = None,
    unreviewed_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    q = db.query(models.PatientReport)
    if patient_id:
        q = q.filter(models.PatientReport.patient_id == patient_id)
    if unreviewed_only:
        q = q.filter(models.PatientReport.doctor_reviewed == False)

    reports = q.order_by(desc(models.PatientReport.report_date)).limit(limit).all()
    return reports

@router.get("/reports/{report_id}", response_model=schemas.PatientReportOut)
def get_single_report(report_id: int, db: Session = Depends(get_db)):
    rep = db.query(models.PatientReport).filter(models.PatientReport.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")
    return rep

@router.post("/reports/{report_id}/review", response_model=schemas.PatientReportOut)
def review_report(report_id: int, req: schemas.ReportReviewRequest, db: Session = Depends(get_db)):
    rep = db.query(models.PatientReport).filter(models.PatientReport.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")

    rep.doctor_reviewed = True
    rep.review_notes = req.review_notes
    rep.reviewed_at = utcnow()
    if req.doctor_id:
        rep.reviewed_by_doctor_id = req.doctor_id

    # If active alert exists for this report, resolve it!
    alert = db.query(models.MonitoringAlert).filter(
        models.MonitoringAlert.patient_id == rep.patient_id,
        models.MonitoringAlert.category == "REPORT_REVIEW",
        models.MonitoringAlert.status.in_(["NEW", "ACKNOWLEDGED", "IN_PROGRESS", "ASSIGNED"])
    ).first()
    if alert:
        alert.status = "RESOLVED"
        alert.resolution_notes = f"Clinician reviewed report {rep.external_id}: {req.review_notes}"
        alert.resolution_timestamp = utcnow()

    db.commit()
    db.refresh(rep)
    return rep

# ----------------- MODULE 8: DATABASE HEALTH & RECONCILIATION -----------------

@router.get("/database/health", response_model=schemas.DatabaseHealthOut)
def get_database_health(db: Session = Depends(get_db)):
    file_size_mb = 0.0
    if os.path.exists(DEFAULT_DB_PATH):
        file_size_mb = round(os.path.getsize(DEFAULT_DB_PATH) / (1024 * 1024), 2)

    tot_p = db.query(models.Patient).count()
    tot_d = db.query(models.Doctor).count()
    tot_f = db.query(models.Facility).count()
    tot_a = db.query(models.Appointment).count()
    tot_fup = db.query(models.FollowUpPlan).count()
    tot_t = db.query(models.HealthWorkerTask).count()
    tot_r = db.query(models.PatientReport).count()
    tot_al = db.query(models.MonitoringAlert).count()
    act_al = db.query(models.MonitoringAlert).filter(
        models.MonitoringAlert.status.in_(["NEW", "ACKNOWLEDGED", "ASSIGNED", "IN_PROGRESS"])
    ).count()
    res_al = db.query(models.MonitoringAlert).filter(
        models.MonitoringAlert.status.in_(["RESOLVED", "DISMISSED"])
    ).count()
    inv_count = db.query(models.InventorySnapshot).count()
    diag_count = db.query(models.DiagnosticAvailability).count()
    err_count = db.query(models.IngestionValidationError).count()

    last_job = db.query(models.IngestionJob).order_by(desc(models.IngestionJob.started_at)).first()

    return schemas.DatabaseHealthOut(
        status="HEALTHY",
        database_connected=True,
        db_file_size_mb=file_size_mb,
        total_patients=tot_p,
        total_doctors=tot_d,
        total_facilities=tot_f,
        total_appointments=tot_a,
        total_followups=tot_fup,
        total_tasks=tot_t,
        total_reports=tot_r,
        total_alerts=tot_al,
        active_alerts=act_al,
        resolved_alerts=res_al,
        inventory_items=inv_count,
        diagnostic_availability_records=diag_count,
        last_monitoring_run_at=utcnow(),
        last_ingestion_job=last_job,
        data_quality_issues_count=err_count
    )

# ----------------- MODULE 9: REPORTING & CSV EXPORTS -----------------

@router.get("/reports/export/{report_type}")
def export_csv_report(report_type: str, db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "patient-followups":
        writer.writerow(["FollowUp_ID", "Patient_ID", "Patient_Name", "Due_Date", "Care_Type", "Status", "Next_Action"])
        fups = db.query(models.FollowUpPlan).limit(500).all()
        for f in fups:
            p = db.get(models.Patient, f.patient_id)
            writer.writerow([f.external_id or f.id, f.patient_id, p.name if p else "N/A", f.due_date, f.care_type, f.status, f.next_action])

    elif report_type == "overdue-care":
        writer.writerow(["FollowUp_ID", "Patient_ID", "Patient_Name", "Village", "Due_Date", "Care_Type", "Status"])
        overdue_fups = db.query(models.FollowUpPlan).filter(models.FollowUpPlan.status.in_(["OVERDUE", "MISSED"])).all()
        for f in overdue_fups:
            p = db.get(models.Patient, f.patient_id)
            writer.writerow([f.external_id or f.id, f.patient_id, p.name if p else "N/A", p.village if p else "N/A", f.due_date, f.care_type, f.status])

    elif report_type == "health-worker-tasks":
        writer.writerow(["Task_ID", "Patient_ID", "Task_Type", "Priority", "Status", "Due_Date", "Outcome", "Visit_Notes"])
        tasks = db.query(models.HealthWorkerTask).limit(500).all()
        for t in tasks:
            writer.writerow([t.external_id or t.id, t.patient_id, t.task_type, t.priority, t.status, t.due_date, t.outcome, t.visit_notes])

    elif report_type == "facility-readiness":
        writer.writerow(["Facility_ID", "Name", "Facility_Type", "District", "Operating_Hours", "Open_Now"])
        facs = db.query(models.Facility).all()
        for f in facs:
            writer.writerow([f.external_id or f.id, f.name, f.facility_type, f.district, f.operating_hours, f.is_open_now])

    elif report_type == "medicine-inventory":
        writer.writerow(["Facility_ID", "Medicine_Name", "Quantity", "Stock_Status", "Reorder_Level"])
        invs = db.query(models.InventorySnapshot).limit(500).all()
        for i in invs:
            writer.writerow([i.facility_id, i.medicine_name, i.quantity_in_stock, i.stock_status, i.reorder_level])

    elif report_type == "diagnostic-availability":
        writer.writerow(["Facility_ID", "Test_Code", "Test_Name", "Available", "Availability_Note"])
        diags = db.query(models.DiagnosticAvailability).limit(500).all()
        for d in diags:
            writer.writerow([d.facility_id, d.test_code, d.test_name, d.available, d.availability_note])

    elif report_type == "alert-resolution":
        writer.writerow(["Alert_Code", "Patient_ID", "Category", "Triggering_Rule", "Priority", "Status", "Resolution_Notes", "Resolved_At"])
        alerts = db.query(models.MonitoringAlert).limit(500).all()
        for a in alerts:
            writer.writerow([a.alert_code, a.patient_id, a.category, a.triggering_rule, a.priority, a.status, a.resolution_notes, a.resolution_timestamp])

    else: # Default: Data Quality summary
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Patients", db.query(models.Patient).count()])
        writer.writerow(["Total Facilities", db.query(models.Facility).count()])
        writer.writerow(["Total Doctors", db.query(models.Doctor).count()])
        writer.writerow(["Active Alerts", db.query(models.MonitoringAlert).filter(models.MonitoringAlert.status == "NEW").count()])
        writer.writerow(["Overdue Care Cases", db.query(models.FollowUpPlan).filter(models.FollowUpPlan.status.in_(["OVERDUE", "MISSED"])).count()])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=swasthyasetu_{report_type}.csv"}
    )
