import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from database import SessionLocal
import models

client = TestClient(app)

def test_patient_master_profile():
    # 1. Fetch patient list
    res = client.get("/api/patients?limit=5")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) > 0
    p = patients[0]

    # 2. Fetch Master Profile
    res_prof = client.get(f"/api/patients/{p['id']}/master-profile")
    assert res_prof.status_code == 200
    prof = res_prof.json()
    assert prof["patient"]["id"] == p["id"]
    assert "conditions" in prof
    assert "current_medication" in prof
    assert "allergies" in prof
    assert "provenance_counts" in prof
    assert "imported_records" in prof["provenance_counts"]

def test_patient_search_and_filters():
    # Filter by village
    res_v = client.get("/api/patients?village=Pirangut")
    assert res_v.status_code == 200
    for pat in res_v.json():
        assert "Pirangut" in pat["village"]

    # Search by patient ID or Name
    res_s = client.get("/api/patients?search=Ramesh")
    assert res_s.status_code == 200
    assert any("Ramesh" in p["name"] for p in res_s.json())

    # Filter overdue only
    res_od = client.get("/api/patients?overdue_only=true")
    assert res_od.status_code == 200
    assert len(res_od.json()) > 0

def test_monitoring_alerts_listing_and_deduplication():
    # Trigger monitoring run
    res_run = client.post("/api/monitoring/run")
    assert res_run.status_code == 200
    summary = res_run.json()["summary"]
    assert "categories_evaluated" in summary

    # List alerts
    res_alerts = client.get("/api/alerts?limit=20")
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()
    assert len(alerts) > 0
    first_alert = alerts[0]
    assert "alert_code" in first_alert
    assert "category" in first_alert
    assert "triggering_rule" in first_alert

    # Verify deduplication: second run should have 0 new alerts
    res_run2 = client.post("/api/monitoring/run")
    assert res_run2.status_code == 200
    summary2 = res_run2.json()["summary"]
    assert summary2["new_alerts_created"] == 0

def test_alert_action_lifecycle():
    # Get active alert
    res = client.get("/api/alerts?status=NEW&limit=1")
    alerts = res.json()
    if not alerts:
        res = client.get("/api/alerts?limit=1")
        alerts = res.json()
    alert = alerts[0]
    a_id = alert["id"]

    # 1. Acknowledge
    res_ack = client.patch(f"/api/alerts/{a_id}/action", json={"action": "ACKNOWLEDGED", "notes": "Seen by supervisor"})
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "ACKNOWLEDGED"

    # 2. Resolve
    res_res = client.patch(f"/api/alerts/{a_id}/action", json={"action": "RESOLVED", "notes": "Care continuity visit completed."})
    assert res_res.status_code == 200
    resolved = res_res.json()
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolution_notes"] is not None

def test_lab_report_explanation_and_review():
    # Fetch sample reports
    res_rep = client.get("/api/reports?limit=5")
    assert res_rep.status_code == 200
    reps = res_rep.json()
    assert len(reps) > 0
    rep = reps[0]

    # AI Explain Report
    res_exp = client.post("/api/ai/explain-report", json={"report_id": rep["id"], "target_audience": "PATIENT"})
    assert res_exp.status_code == 200
    exp = res_exp.json()
    assert "content" in exp
    assert len(exp["citations"]) > 0

    # Clinician Review
    res_rev = client.post(f"/api/reports/{rep['id']}/review", json={
        "doctor_reviewed": True,
        "review_notes": "Findings reviewed. Medication dose adequate, maintain current regimen.",
        "doctor_id": 1
    })
    assert res_rev.status_code == 200
    assert res_rev.json()["doctor_reviewed"] is True

def test_grounded_ai_assistant_timeline_summary():
    # Request AI Patient Summary
    res = client.get("/api/patients?limit=1")
    p_id = res.json()[0]["id"]

    res_sum = client.post(f"/api/ai/patient-summary/{p_id}")
    assert res_sum.status_code == 200
    summ = res_sum.json()
    assert "content" in summ
    assert "citations" in summ
    assert len(summ["citations"]) > 0
    assert "Disclaimer" in summ["content"]

def test_grounded_ai_administrative_queries():
    # Administrative natural language queries grounded in database
    queries = [
        "How many overdue follow-up records are there?",
        "Check medicine stock and inventory shortages",
        "How many active health worker tasks exist?"
    ]
    for q in queries:
        res = client.post("/api/ai/query", json={"query": q})
        assert res.status_code == 200
        ans = res.json()
        assert "answer" in ans
        assert len(ans["citations"]) > 0

def test_database_health_and_quality():
    res = client.get("/api/database/health")
    assert res.status_code == 200
    health = res.json()
    assert health["database_connected"] is True
    assert health["total_patients"] >= 1000
    assert health["total_facilities"] >= 50
    assert health["total_doctors"] >= 150
    assert health["active_alerts"] > 0

def test_csv_report_exports():
    export_types = [
        "patient-followups",
        "overdue-care",
        "health-worker-tasks",
        "facility-readiness",
        "medicine-inventory",
        "diagnostic-availability",
        "alert-resolution"
    ]
    for r_type in export_types:
        res = client.get(f"/api/reports/export/{r_type}")
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert f"swasthyasetu_{r_type}.csv" in res.headers["content-disposition"]
        assert len(res.text) > 0

def test_early_precaution_guidance_minor_symptoms():
    res = client.post("/api/symptom-intake", json={
        "patient_id": 1,
        "raw_input": "Mujhe pet me dard aur dast loose motion ho raha hai kal se",
        "language": "hi",
        "duration_days": 1
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["what_to_do"]) > 0
    assert len(data["what_not_to_do"]) > 0
    assert len(data["diet_to_eat"]) > 0
    assert len(data["diet_to_avoid"]) > 0
    assert len(data["activity_and_work_guidance"]) > 0
    assert len(data["red_flag_warnings"]) > 0
    assert "ORS" in " ".join(data["what_to_do"])

def test_post_consultation_disease_lifestyle_guidance():
    res = client.get("/api/patients/1/lifestyle-guidance?language=hi")
    assert res.status_code == 200
    guide = res.json()
    assert "condition_title" in guide
    assert len(guide["dietary_recommendations"]) > 0
    assert len(guide["dietary_restrictions"]) > 0
    assert len(guide["work_recommendations"]) > 0
    assert len(guide["work_restrictions"]) > 0
    assert len(guide["medicine_adherence_tips"]) > 0
