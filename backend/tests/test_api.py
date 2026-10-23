import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from seed_data import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    seed_database()

client = TestClient(app)

def test_health_check():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_login():
    res = client.post("/api/auth/login", json={"username": "dr_deshmukh"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "DOCTOR"
    assert "Dr. Anand Deshmukh" in data["user"]["full_name"]

def test_emergency_triage_scenario_e():
    # Scenario E: Severe chest discomfort in Hindi
    payload = {
        "patient_id": 1,
        "raw_input": "Mujhe pichle 2 ghante se chest mein severe pain aur saans lene mein dikkat ho rahi hai.",
        "language": "hi",
        "duration_days": 1
    }
    res = client.post("/api/symptom-intake", json=payload, headers={"X-Demo-User": "ramesh"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency"] is True
    assert data["triage_level"] == "EMERGENCY"
    assert "112" in data["emergency_number"]
    assert "Emergency Medicine" in data["recommended_specialty"]

def test_routine_triage_scenario_a():
    # Scenario A: Routine minor symptoms
    payload = {
        "patient_id": 1,
        "raw_input": "Halka sirdard aur sardi hai kal se.",
        "language": "hi",
        "duration_days": 1
    }
    res = client.post("/api/symptom-intake", json=payload, headers={"X-Demo-User": "ramesh"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency"] is False
    assert data["triage_level"] == "ROUTINE"

def test_facility_readiness_and_test_unavailability_scenario_b():
    # Scenario B: Nearest CHC lacks Ultrasound, District Hospital has it
    res = client.get("/api/facilities")
    assert res.status_code == 200
    facilities = res.json()
    assert len(facilities) >= 2
    
    chc = next((f for f in facilities if f["facility_type"] == "CHC"), None)
    dh = next((f for f in facilities if f["facility_type"] == "DISTRICT_HOSPITAL"), None)
    
    assert chc is not None
    assert "Ultrasound Abdomen (USG)" in chc["diagnostic_tests_missing"]
    assert "Electrocardiogram (ECG)" in chc["diagnostic_tests_available"]
    
    assert dh is not None
    assert "Ultrasound Abdomen (USG)" in dh["diagnostic_tests_available"]

def test_medicine_stock_scenario_c():
    # Scenario C: Amlodipine out of stock at CHC Paud
    res = client.get("/api/facilities")
    facilities = res.json()
    chc = next((f for f in facilities if f["facility_type"] == "CHC"), None)
    assert chc["medicine_stock_summary"]["Amlodipine"] == "OUT_OF_STOCK"
    assert chc["medicine_stock_summary"]["Paracetamol"] == "IN_STOCK"

def test_appointment_booking_and_idempotency_scenario_f():
    # Scenario F: Appointment creation with idempotency key
    key = "idem-test-key-999"
    payload = {
        "patient_id": 1,
        "doctor_id": 1,
        "facility_id": 1,
        "scheduled_date": "2026-10-25",
        "scheduled_time": "10:00 AM",
        "consultation_type": "IN_PERSON",
        "reason": "Chest discomfort review",
        "idempotency_key": key
    }
    res1 = client.post("/api/appointments", json=payload, headers={"X-Demo-User": "ramesh"})
    assert res1.status_code == 200
    apt1 = res1.json()

    # Retry same action
    res2 = client.post("/api/appointments", json=payload, headers={"X-Demo-User": "ramesh"})
    assert res2.status_code == 200
    apt2 = res2.json()

    assert apt1["id"] == apt2["id"]
    assert apt1["appointment_code"] == apt2["appointment_code"]

def test_encounter_and_follow_up_creation():
    payload = {
        "patient_id": 1,
        "doctor_id": 1,
        "facility_id": 1,
        "chief_complaints": "Chest heaviness and fatigue on exertion",
        "clinical_notes": "Heart sounds normal. S1, S2 audible. No murmurs. Advised ECG.",
        "diagnosis": "Mild Atypical Angina / Exertional Fatigue",
        "vital_bp": "130/84",
        "vital_pulse": 78,
        "vital_temp": 98.4,
        "vital_spo2": 99,
        "clinician_risk_flag": "MODERATE_RISK",
        "prescriptions": [
            {
                "medicine_name": "Paracetamol 500mg",
                "dosage": "500mg",
                "frequency": "SOS",
                "duration_days": 3,
                "instructions": "Take after food if discomfort occurs"
            }
        ],
        "diagnostic_test_names": ["Electrocardiogram (ECG)"],
        "follow_up_days": 7,
        "follow_up_instructions": "Review with ECG report in 1 week"
    }
    res = client.post("/api/encounters", json=payload, headers={"X-Demo-User": "dr_deshmukh"})
    assert res.status_code == 200
    data = res.json()
    assert data["diagnosis"] == "Mild Atypical Angina / Exertional Fatigue"

def test_missed_care_and_asha_task_resolution_scenario_d():
    # Scenario D: ASHA task for Sunita Devi's overdue follow-up
    res = client.get("/api/tasks?status=OPEN")
    assert res.status_code == 200
    tasks = res.json()
    sunita_task = next((t for t in tasks if t["patient_name"] == "Sunita Devi"), None)
    assert sunita_task is not None
    assert sunita_task["task_type"] == "MISSED_FOLLOW_UP"

    # ASHA worker completes home visit and updates task
    update_payload = {
        "status": "RESOLVED",
        "visit_notes": "Visited Sunita Devi at Pirangut home. Checked random blood sugar (164 mg/dL). She missed follow-up due to lack of bus. Accompanied her to CHC next day.",
        "outcome": "PATIENT_VISITED_CLINIC"
    }
    res_update = client.patch(f"/api/tasks/{sunita_task['id']}", json=update_payload, headers={"X-Demo-User": "asha_kavita"})
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["status"] == "RESOLVED"
    assert updated["outcome"] == "PATIENT_VISITED_CLINIC"

def test_access_control_scenario_g():
    # Scenario G: ASHA Kavita Tai attempts to access patient Anita More (assigned to ASHA Rekha)
    res_pat = client.get("/api/patients")
    patients = res_pat.json()
    anita = next((p for p in patients if p["name"] == "Anita More"), None)
    assert anita is not None

    # Kavita attempts to view Anita's protected medical record
    res = client.get(f"/api/patients/{anita['id']}", headers={"X-Demo-User": "asha_kavita"})
    assert res.status_code == 403
    assert "Access Denied" in res.json()["detail"]

    # Verify audit event recorded denial
    audit_res = client.get("/api/audit-events")
    audits = audit_res.json()
    denied_audit = next((a for a in audits if a["action"] == "UNAUTHORIZED_PATIENT_ACCESS_DENIED"), None)
    assert denied_audit is not None
    assert denied_audit["outcome"] == "DENIED"

def test_offline_sync_batch():
    batch = {
        "user_id": 1,
        "actions": [
            {
                "idempotency_key": "sync-batch-item-101",
                "action_type": "BOOK_APPOINTMENT",
                "payload": {
                    "patient_id": 1,
                    "doctor_id": 1,
                    "facility_id": 1,
                    "scheduled_date": "2026-10-26",
                    "reason": "Follow-up synced from offline cache"
                }
            }
        ]
    }
    res = client.post("/api/sync/batch", json=batch, headers={"X-Demo-User": "ramesh"})
    assert res.status_code == 200
    data = res.json()
    assert data["synced_count"] == 1
    assert data["results"][0]["status"] == "SYNCED"
