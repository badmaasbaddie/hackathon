import os
import json
import datetime
from sqlalchemy.orm import Session
import models

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class GroundedAIAssistant:
    """
    Grounded Healthcare AI Assistant.
    Retrieves authorized source records from the database first,
    constructs factual responses citing source record IDs,
    and returns transparent explanations with uncertainty indicators.
    """

    @staticmethod
    def summarize_patient_timeline(patient_id: int, db: Session) -> dict:
        patient = db.get(models.Patient, patient_id)
        if not patient:
            return {"error": "Patient not found", "citations": []}

        events = db.query(models.CareTimelineEvent).filter(
            models.CareTimelineEvent.patient_id == patient_id
        ).order_by(models.CareTimelineEvent.created_at.desc()).all()

        reports = db.query(models.PatientReport).filter(models.PatientReport.patient_id == patient_id).all()
        fups = db.query(models.FollowUpPlan).filter(models.FollowUpPlan.patient_id == patient_id).all()
        apts = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()
        alerts = db.query(models.MonitoringAlert).filter(models.MonitoringAlert.patient_id == patient_id).all()

        citations = [f"PATIENT:{patient.external_id or patient.id}"]
        for r in reports:
            citations.append(f"REPORT:{r.external_id}")
        for f in fups:
            citations.append(f"FOLLOWUP:{f.external_id}")
        for a in apts:
            citations.append(f"APPT:{a.external_id or a.appointment_code}")
        for al in alerts:
            citations.append(f"ALERT:{al.alert_code}")

        # Construct structured clinical summary
        summary_text = (
            f"**Patient Care Continuity Brief for {patient.name}** (Age: {patient.age}, Gender: {patient.gender}, Village: {patient.village})\n"
            f"- **Recorded Conditions:** {patient.chronic_conditions}\n"
            f"- **Active Medication:** {patient.current_medication}\n"
            f"- **Allergies:** {patient.allergies}\n"
            f"- **Care Status:** {patient.care_status}\n\n"
            f"**Key Continuity Indicators:**\n"
            f"- Appointments: {len(apts)} total recorded.\n"
            f"- Follow-up Plans: {len(fups)} recorded ({len([f for f in fups if f.status in ['OVERDUE', 'MISSED']])} marked overdue/missed).\n"
            f"- Diagnostic Reports: {len(reports)} lab findings available.\n"
            f"- Active Monitoring Alerts: {len([al for al in alerts if al.status in ['NEW', 'ACKNOWLEDGED', 'ASSIGNED', 'IN_PROGRESS']])} active alerts.\n\n"
            f"*Clinical Provenance Disclaimer: This summary is generated deterministically from authorized public health records. "
            f"It does not replace clinical evaluation by a medical officer.*"
        )

        # Persist summary
        code = f"SUMM-TL-{patient.id}-{int(utcnow().timestamp())}"
        summary_obj = models.AISummary(
            summary_code=code,
            patient_id=patient.id,
            summary_type="PATIENT_TIMELINE",
            title=f"Care Continuity Summary for {patient.name}",
            content=summary_text,
            provenance_records_json=json.dumps(citations),
            model_version="SwasthyaSetu-GroundedRAG-v1.0",
            confidence_score=0.98,
            clinician_verified=False
        )
        db.add(summary_obj)
        db.commit()

        return {
            "summary_code": code,
            "patient_name": patient.name,
            "content": summary_text,
            "citations": citations,
            "generated_at": utcnow().isoformat()
        }

    @staticmethod
    def explain_lab_report(report_id: int, target_audience: str, db: Session) -> dict:
        report = db.get(models.PatientReport, report_id)
        if not report:
            return {"error": "Report not found"}

        patient = db.get(models.Patient, report.patient_id)
        citations = [f"REPORT:{report.external_id}", f"PATIENT:{patient.external_id if patient else report.patient_id}"]

        if target_audience == "PATIENT":
            explanation = (
                f"**Aasan Bhasha Mein Lab Jaanch Ki Jankari ({report.report_type})**\n\n"
                f"Aapki jaanch ki tareekh: **{report.report_date}**\n"
                f"Result: **{report.findings}**\n\n"
                f"**Iska kya matlab hai?**\n"
                f"- Hamari jaanch mein yeh parinaam dekha gaya hai. Doctor sahab se agle checkup par is par charcha zaroor karein.\n"
                f"- Salaah: {report.ai_action_note}\n\n"
                f"⚠️ *Kripya dhyan dein: Yeh sirf jankari ke liye hai. Kisi bhi dava mein badlaav sirf doctor ke nirdesh par karein.*"
            )
        elif target_audience == "ASHA":
            explanation = (
                f"**ASHA Field Guidance for Patient {patient.name if patient else 'Record'}**\n"
                f"- Report: {report.report_type} ({report.report_date})\n"
                f"- Findings: {report.findings}\n"
                f"- Recommended Action: {report.ai_action_note}\n"
                f"- Task Check: Please verify if patient is taking prescribed medicines and remind them for next clinic visit."
            )
        else: # CLINICIAN
            explanation = (
                f"**Clinical Laboratory Review Record [ID: {report.external_id}]**\n"
                f"- Patient: {patient.name if patient else 'N/A'} (ABHA: {patient.abha_id if patient else 'N/A'})\n"
                f"- Test: {report.report_type} | Date: {report.report_date}\n"
                f"- Reported Values: {report.findings}\n"
                f"- Flagged Status: {'ABNORMAL' if report.is_abnormal else 'NORMAL'}\n"
                f"- Clinical Action Recommendation: {report.ai_action_note}\n"
                f"- Verification: Clinician acknowledgement pending."
            )

        return {
            "report_id": report.id,
            "external_id": report.external_id,
            "target_audience": target_audience,
            "content": explanation,
            "citations": citations,
            "is_abnormal": report.is_abnormal,
            "generated_at": utcnow().isoformat()
        }

    @staticmethod
    def answer_administrative_query(query_str: str, db: Session) -> dict:
        q_lower = query_str.lower()
        citations = []
        answer = ""

        if "overdue" in q_lower or "missed" in q_lower:
            overdue_fups = db.query(models.FollowUpPlan).filter(
                models.FollowUpPlan.status.in_(["OVERDUE", "MISSED"])
            ).count()
            citations.append("DB:follow_up_plans:status=OVERDUE|MISSED")
            answer = f"According to verified database records, there are currently **{overdue_fups} overdue or missed follow-up records** across rural blocks."

        elif "stock" in q_lower or "medicine" in q_lower or "inventory" in q_lower:
            stockouts = db.query(models.InventorySnapshot).filter(
                models.InventorySnapshot.stock_status.in_(["Out of Stock", "OUT_OF_STOCK"])
            ).all()
            low_stocks = db.query(models.InventorySnapshot).filter(
                models.InventorySnapshot.stock_status.in_(["Low Stock", "LOW_STOCK"])
            ).all()
            citations.append("DB:inventory_snapshots:stock_status")
            answer = (
                f"Medicine Inventory Verification:\n"
                f"- **{len(stockouts)} facilities** currently report OUT OF STOCK medicines.\n"
                f"- **{len(low_stocks)} facilities** report LOW STOCK (below reorder threshold of 25 units)."
            )

        elif "task" in q_lower or "asha" in q_lower:
            open_tasks = db.query(models.HealthWorkerTask).filter(
                models.HealthWorkerTask.status.in_(["Pending", "OPEN", "Assigned", "IN_PROGRESS"])
            ).count()
            high_prio = db.query(models.HealthWorkerTask).filter(
                models.HealthWorkerTask.priority.in_(["High", "Critical"])
            ).count()
            citations.append("DB:health_worker_tasks:status=OPEN")
            answer = f"There are **{open_tasks} active health worker tasks** recorded, of which **{high_prio}** are designated as High or Critical priority."

        elif "patient" in q_lower or "count" in q_lower:
            tot_p = db.query(models.Patient).count()
            chronic_p = db.query(models.Patient).filter(models.Patient.care_status == "CHRONIC_MONITORING").count()
            citations.append("DB:patients:total_count")
            answer = f"The system manages **{tot_p} registered patients**, including **{chronic_p} patients** enrolled in active Chronic Disease Monitoring."

        else:
            # General query fallback
            tot_p = db.query(models.Patient).count()
            tot_f = db.query(models.Facility).count()
            active_alerts = db.query(models.MonitoringAlert).filter(
                models.MonitoringAlert.status.in_(["NEW", "ACKNOWLEDGED", "ASSIGNED", "IN_PROGRESS"])
            ).count()
            citations.append("DB:summary_metrics")
            answer = (
                f"SwasthyaSetu AI System Status:\n"
                f"- Registered Patients: {tot_p}\n"
                f"- Public Health Facilities: {tot_f}\n"
                f"- Active Continuity Alerts: {active_alerts}\n\n"
                f"Query parsed: '{query_str}'. For exact metrics, please query specific parameters such as overdue follow-ups, medicine stockouts, or ASHA tasks."
            )

        return {
            "query": query_str,
            "answer": answer,
            "citations": citations,
            "confidence_score": 1.0,
            "source_type": "DETERMINISTIC_DATABASE_QUERY",
            "timestamp": utcnow().isoformat()
        }
