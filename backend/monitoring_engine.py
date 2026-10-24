import os
import json
import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
import models

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

# Configurable reference date (defaulting to current date or simulation milestone)
DEFAULT_REFERENCE_DATE = os.getenv("MONITORING_REFERENCE_DATE", "2026-10-24")

def run_continuous_monitoring(db: Session = None, ref_date_str: str = None):
    """
    Evaluates all 8 continuous patient monitoring rules:
    Rule A: Missed Appointment Monitoring
    Rule B: Follow-up Monitoring (Upcoming, Due, Overdue, Escalation)
    Rule C: Chronic-Care Monitoring
    Rule D: Diagnostic Monitoring
    Rule E: Medicine Inventory Monitoring (Stockout & Low Stock)
    Rule F: Report Review Monitoring
    Rule G: Data Freshness Monitoring
    Rule H: Repeated Missed-Care Monitoring
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    ref_date = ref_date_str or DEFAULT_REFERENCE_DATE
    now_dt = utcnow()

    summary = {
        "run_at": now_dt.isoformat(),
        "reference_date": ref_date,
        "new_alerts_created": 0,
        "existing_active_alerts": 0,
        "tasks_generated": 0,
        "categories_evaluated": {}
    }

    try:
        # Helper: Deduplicated Alert Creation
        def create_or_dedup_alert(patient_id, category, triggering_rule, title, description, priority, assigned_role, supporting_ids, due_date=None):
            # Check if active alert already exists
            active = db.query(models.MonitoringAlert).filter(
                models.MonitoringAlert.patient_id == patient_id,
                models.MonitoringAlert.category == category,
                models.MonitoringAlert.triggering_rule == triggering_rule,
                models.MonitoringAlert.status.in_(["NEW", "ACKNOWLEDGED", "ASSIGNED", "IN_PROGRESS"])
            ).first()

            if active:
                summary["existing_active_alerts"] += 1
                return active

            # Generate new alert
            alert_count = db.query(models.MonitoringAlert).count() + 1
            code = f"ALT-{now_dt.strftime('%m%d')}-{alert_count:04d}"

            alert = models.MonitoringAlert(
                alert_code=code,
                patient_id=patient_id,
                category=category,
                triggering_rule=triggering_rule,
                title=title,
                description=description,
                supporting_record_ids=json.dumps(supporting_ids),
                priority=priority,
                status="NEW",
                assigned_role=assigned_role,
                due_date=due_date or ref_date,
                created_at=now_dt,
                updated_at=now_dt
            )
            db.add(alert)
            db.flush()

            # Record creation in resolution history
            history = models.AlertResolutionHistory(
                alert_id=alert.id,
                actor_id=None,
                actor_name="Continuous Monitoring Engine",
                actor_role="SYSTEM",
                action="CREATED",
                notes=f"Triggered by rule '{triggering_rule}' on {ref_date}.",
                created_at=now_dt
            )
            db.add(history)
            summary["new_alerts_created"] += 1
            return alert

        # -------------------------------------------------------------
        # RULE A: Missed Appointment Monitoring
        # -------------------------------------------------------------
        rule_a_alerts = 0
        apts = db.query(models.Appointment).filter(
            models.Appointment.status.in_(["MISSED", "NO_SHOW", "PENDING", "BOOKED"])
        ).all()

        for a in apts:
            # If date is in past or status explicitly MISSED/NO_SHOW
            if a.status in ["MISSED", "NO_SHOW"] or (a.scheduled_date and a.scheduled_date < ref_date and a.status in ["PENDING", "BOOKED"]):
                if a.status in ["PENDING", "BOOKED"]:
                    a.status = "MISSED" # Transition state
                create_or_dedup_alert(
                    patient_id=a.patient_id,
                    category="MISSED_APPOINTMENT",
                    triggering_rule="RULE_A_SCHEDULED_APPOINTMENT_MISSED",
                    title=f"Missed Appointment: {a.appointment_code}",
                    description=f"Appointment {a.appointment_code} on {a.scheduled_date} at {a.scheduled_time} was not completed.",
                    priority="MEDIUM",
                    assigned_role="ASHA",
                    supporting_ids={"appointment_id": a.id, "appointment_code": a.appointment_code, "scheduled_date": a.scheduled_date}
                )
                rule_a_alerts += 1
        summary["categories_evaluated"]["MISSED_APPOINTMENT"] = rule_a_alerts

        # -------------------------------------------------------------
        # RULE B: Follow-up Monitoring (Upcoming, Due, Overdue, Tasks)
        # -------------------------------------------------------------
        rule_b_alerts = 0
        fups = db.query(models.FollowUpPlan).all()
        for f in fups:
            is_overdue = False
            if f.status == "MISSED":
                is_overdue = True
            elif f.due_date and f.due_date < ref_date and f.status in ["DUE", "SCHEDULED", "PENDING"]:
                f.status = "OVERDUE"
                is_overdue = True
            elif f.due_date and f.due_date == ref_date and f.status == "SCHEDULED":
                f.status = "DUE"

            if is_overdue:
                # 1. Create monitoring alert
                create_or_dedup_alert(
                    patient_id=f.patient_id,
                    category="OVERDUE_FOLLOWUP",
                    triggering_rule="RULE_B_CARE_FOLLOWUP_OVERDUE",
                    title=f"Overdue Follow-up: {f.care_type}",
                    description=f"Follow-up for '{f.care_type}' due on {f.due_date} is overdue. Action required: {f.next_action or 'Contact patient'}.",
                    priority="HIGH",
                    assigned_role="ASHA",
                    supporting_ids={"follow_up_id": f.id, "external_id": f.external_id, "due_date": f.due_date, "care_type": f.care_type}
                )
                rule_b_alerts += 1

                # 2. Automatically ensure an actionable HealthWorkerTask exists!
                existing_task = db.query(models.HealthWorkerTask).filter(
                    models.HealthWorkerTask.patient_id == f.patient_id,
                    models.HealthWorkerTask.task_type == "Missed follow-up",
                    models.HealthWorkerTask.status.in_(["Pending", "OPEN", "Assigned", "IN_PROGRESS"])
                ).first()

                if not existing_task:
                    p = db.get(models.Patient, f.patient_id)
                    t_ext = f"W-AUTO-{f.id}"
                    new_task = models.HealthWorkerTask(
                        external_id=t_ext,
                        patient_id=f.patient_id,
                        asha_worker_id=p.assigned_asha_id if p else None,
                        follow_up_id=f.id,
                        task_type="Missed follow-up",
                        description=f"Conduct home visit or contact patient for overdue {f.care_type} (due {f.due_date}).",
                        priority="High",
                        due_date=ref_date,
                        status="Pending",
                        created_at=now_dt
                    )
                    db.add(new_task)
                    summary["tasks_generated"] += 1

        summary["categories_evaluated"]["OVERDUE_FOLLOWUP"] = rule_b_alerts

        # -------------------------------------------------------------
        # RULE C: Chronic-Care Monitoring
        # -------------------------------------------------------------
        rule_c_alerts = 0
        chronic_patients = db.query(models.Patient).filter(
            models.Patient.care_status == "CHRONIC_MONITORING"
        ).all()

        for cp in chronic_patients:
            # Check if patient has any overdue or missed follow-ups
            has_overdue = db.query(models.FollowUpPlan).filter(
                models.FollowUpPlan.patient_id == cp.id,
                models.FollowUpPlan.status.in_(["OVERDUE", "MISSED", "DUE"])
            ).first()

            if has_overdue:
                create_or_dedup_alert(
                    patient_id=cp.id,
                    category="CHRONIC_CARE",
                    triggering_rule="RULE_C_CHRONIC_CONDITION_OVERDUE",
                    title=f"Chronic Care Alert: {cp.name} ({cp.chronic_conditions})",
                    description=f"Patient with {cp.chronic_conditions} has an unresolved follow-up due on {has_overdue.due_date}. Medication: {cp.current_medication}.",
                    priority="HIGH",
                    assigned_role="DOCTOR",
                    supporting_ids={"patient_id": cp.id, "condition": cp.chronic_conditions, "follow_up_id": has_overdue.id}
                )
                rule_c_alerts += 1
        summary["categories_evaluated"]["CHRONIC_CARE"] = rule_c_alerts

        # -------------------------------------------------------------
        # RULE D: Diagnostic Monitoring (Pending Orders)
        # -------------------------------------------------------------
        rule_d_alerts = 0
        diag_orders = db.query(models.DiagnosticOrder).filter(
            models.DiagnosticOrder.status.in_(["ORDERED", "SCHEDULED", "AWAITING_REVIEW"])
        ).all()

        for d in diag_orders:
            create_or_dedup_alert(
                patient_id=d.patient_id,
                category="DIAGNOSTIC_PENDING",
                triggering_rule="RULE_D_DIAGNOSTIC_ORDER_PENDING",
                title=f"Pending Diagnostic Order: {d.test_name}",
                description=f"Test '{d.test_name}' ordered with status '{d.status}'. Awaiting specimen collection or report entry.",
                priority="MEDIUM",
                assigned_role="FACILITY_ADMIN",
                supporting_ids={"order_id": d.id, "test_name": d.test_name, "facility_id": d.facility_id}
            )
            rule_d_alerts += 1
        summary["categories_evaluated"]["DIAGNOSTIC_PENDING"] = rule_d_alerts

        # -------------------------------------------------------------
        # RULE E: Medicine Monitoring (Stockouts & Low Stock)
        # -------------------------------------------------------------
        rule_e_alerts = 0
        critical_inv = db.query(models.InventorySnapshot).filter(
            models.InventorySnapshot.stock_status.in_(["Out of Stock", "OUT_OF_STOCK", "Low Stock", "LOW_STOCK"])
        ).all()

        for inv in critical_inv:
            is_out = "out" in inv.stock_status.lower()
            prio = "CRITICAL" if is_out else "MEDIUM"
            rule_id = "RULE_E_MEDICINE_OUT_OF_STOCK" if is_out else "RULE_E_MEDICINE_LOW_STOCK"
            hosp = db.get(models.Facility, inv.facility_id)
            hosp_name = hosp.name if hosp else f"Facility #{inv.facility_id}"

            create_or_dedup_alert(
                patient_id=None,
                category="MEDICINE_STOCKOUT",
                triggering_rule=rule_id,
                title=f"Medicine Alert: {inv.medicine_name} ({inv.stock_status}) at {hosp_name}",
                description=f"{inv.medicine_name} currently has {inv.quantity_in_stock} {inv.unit} remaining at {hosp_name}. Reorder threshold: {inv.reorder_level}.",
                priority=prio,
                assigned_role="FACILITY_ADMIN",
                supporting_ids={"facility_id": inv.facility_id, "medicine_id": inv.medicine_id, "quantity": inv.quantity_in_stock}
            )
            rule_e_alerts += 1
        summary["categories_evaluated"]["MEDICINE_STOCKOUT"] = rule_e_alerts

        # -------------------------------------------------------------
        # RULE F: Report Review Monitoring (Clinician Review Required)
        # -------------------------------------------------------------
        rule_f_alerts = 0
        unreviewed_reports = db.query(models.PatientReport).filter(
            models.PatientReport.doctor_reviewed == False,
            models.PatientReport.is_abnormal == True
        ).all()

        for r in unreviewed_reports:
            p = db.get(models.Patient, r.patient_id)
            p_name = p.name if p else f"Patient #{r.patient_id}"
            create_or_dedup_alert(
                patient_id=r.patient_id,
                category="REPORT_REVIEW",
                triggering_rule="RULE_F_ABNORMAL_REPORT_AWAITING_REVIEW",
                title=f"Clinician Review Needed: {r.report_type} for {p_name}",
                description=f"Lab report ({r.report_type}) from {r.report_date} contains abnormal findings: '{r.findings}'. Note: {r.ai_action_note}.",
                priority="HIGH",
                assigned_role="DOCTOR",
                supporting_ids={"report_id": r.id, "external_id": r.external_id, "findings": r.findings}
            )
            rule_f_alerts += 1
        summary["categories_evaluated"]["REPORT_REVIEW"] = rule_f_alerts

        # -------------------------------------------------------------
        # RULE G: Data Freshness Monitoring
        # -------------------------------------------------------------
        rule_g_alerts = 0
        stale_threshold = now_dt - datetime.timedelta(days=14)
        stale_facilities = db.query(models.Facility).filter(
            models.Facility.last_verified_at < stale_threshold
        ).all()

        for sf in stale_facilities:
            create_or_dedup_alert(
                patient_id=None,
                category="DATA_STALENESS",
                triggering_rule="RULE_G_FACILITY_DATA_STALE",
                title=f"Stale Facility Data: {sf.name}",
                description=f"Facility schedule and resource inventory has not been verified since {sf.last_verified_at.strftime('%Y-%m-%d')}.",
                priority="LOW",
                assigned_role="SUPER_ADMIN",
                supporting_ids={"facility_id": sf.id, "last_verified_at": sf.last_verified_at.isoformat()}
            )
            rule_g_alerts += 1
        summary["categories_evaluated"]["DATA_STALENESS"] = rule_g_alerts

        # -------------------------------------------------------------
        # RULE H: Repeated Missed-Care Monitoring
        # -------------------------------------------------------------
        rule_h_alerts = 0
        # Find patients with >= 2 missed follow-ups or appointments
        from sqlalchemy import func
        missed_fups = db.query(
            models.FollowUpPlan.patient_id, func.count(models.FollowUpPlan.id).label("count")
        ).filter(
            models.FollowUpPlan.status.in_(["MISSED", "OVERDUE"])
        ).group_by(models.FollowUpPlan.patient_id).having(func.count(models.FollowUpPlan.id) >= 2).all()

        for p_id, m_count in missed_fups:
            p = db.get(models.Patient, p_id)
            p_name = p.name if p else f"Patient #{p_id}"
            create_or_dedup_alert(
                patient_id=p_id,
                category="REPEATED_MISSED_CARE",
                triggering_rule="RULE_H_REPEATED_MISSED_CARE_EPISODES",
                title=f"Care Continuity Risk: {p_name} ({m_count} Overdue Episodes)",
                description=f"Patient {p_name} has {m_count} separate missed or overdue follow-up care events. Requires direct ASHA home visit & medical officer review.",
                priority="CRITICAL",
                assigned_role="SUPER_ADMIN",
                supporting_ids={"patient_id": p_id, "missed_episodes_count": m_count}
            )
            rule_h_alerts += 1
        summary["categories_evaluated"]["REPEATED_MISSED_CARE"] = rule_h_alerts

        db.commit()
        print(f"[MONITORING ENGINE] Evaluated all rules. Created {summary['new_alerts_created']} new alerts, {summary['existing_active_alerts']} already active, {summary['tasks_generated']} new tasks.")
        return summary

    except Exception as e:
        db.rollback()
        print(f"[MONITORING ENGINE ERROR] {e}")
        raise e
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    run_continuous_monitoring()
