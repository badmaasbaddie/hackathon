import datetime
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Use a throwaway database so running the tests never wipes the demo database.
_TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_swasthyasetu.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"

from main import app
from seed_data import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    seed_database()

client = TestClient(app)

def as_user(username):
    return {"X-Demo-User": username}

def days_from_today(n):
    return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()

def paud_chc():
    return next(f for f in client.get("/api/facilities").json() if f["name"].startswith("Paud"))

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

def test_unknown_login_and_unauthenticated_requests_rejected():
    assert client.post("/api/auth/login", json={"username": "nobody"}).status_code == 401
    assert client.get("/api/patients").status_code == 401
    assert client.get("/api/patients/1").status_code == 401

def test_emergency_triage_scenario_e():
    # Scenario E: Severe chest discomfort in Hinglish
    payload = {
        "patient_id": 1,
        "raw_input": "Mujhe pichle 2 ghante se chest mein severe pain aur saans lene mein dikkat ho rahi hai.",
        "language": "hi",
        "duration_days": 1
    }
    res = client.post("/api/symptom-intake", json=payload, headers=as_user("ramesh"))
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency"] is True
    assert data["triage_level"] == "EMERGENCY"
    assert "112" in data["emergency_number"]
    assert "Emergency Medicine" in data["recommended_specialty"]

def test_emergency_triage_devanagari_voice_input():
    # Voice input in hi-IN arrives in Devanagari script
    payload = {"patient_id": 1, "raw_input": "मुझे सीने में दर्द है और सांस लेने में तकलीफ हो रही है", "language": "hi"}
    data = client.post("/api/symptom-intake", json=payload, headers=as_user("ramesh")).json()
    assert data["is_emergency"] is True

def test_no_false_emergency_on_common_words():
    # "dauran" (during) must not match "daura" (seizure); "benefits" must not match "fits"
    for text in ["Yatra ke dauran halka sir dard hua", "What are the benefits of walking for BP?"]:
        data = client.post("/api/symptom-intake", json={"patient_id": 1, "raw_input": text, "language": "en"}, headers=as_user("ramesh")).json()
        assert data["is_emergency"] is False, text

def test_routine_triage_scenario_a():
    payload = {"patient_id": 1, "raw_input": "Halka sirdard aur sardi hai kal se.", "language": "hi", "duration_days": 1}
    res = client.post("/api/symptom-intake", json=payload, headers=as_user("ramesh"))
    assert res.status_code == 200
    data = res.json()
    assert data["is_emergency"] is False
    assert data["triage_level"] == "ROUTINE"

def test_ai_chat_grounded_answer(monkeypatch):
    monkeypatch.setenv("AI_ASSISTANT_MODE", "fallback")
    res = client.post("/api/ai/chat", headers=as_user("ramesh"), json={
        "language": "en", "messages": [{"role": "user", "content": "I have mild fever and body pain since yesterday"}]})
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "DEMO_FALLBACK"
    assert data["sources"][0]["id"] == "REF-FEVER-01"
    assert data["triage"]["triage_level"] == "ROUTINE"

def test_ai_chat_emergency_never_waits_for_llm(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-not-be-used")
    res = client.post("/api/ai/chat", headers=as_user("ramesh"), json={
        "language": "en", "messages": [{"role": "user", "content": "my father has slurred speech and face drooping"}]})
    data = res.json()
    assert data["mode"] == "SAFETY_RULES"
    assert data["triage"]["is_emergency"] is True
    assert "112" in data["reply"]

def test_facility_readiness_and_test_unavailability_scenario_b():
    facilities = client.get("/api/facilities?district=Pune").json()
    assert {f["facility_type"] for f in facilities} >= {"CHC", "PHC", "DISTRICT_HOSPITAL"}
    chc = paud_chc()
    dh = next(f for f in facilities if f["facility_type"] == "DISTRICT_HOSPITAL")
    assert "Ultrasound Abdomen (USG)" in chc["diagnostic_tests_missing"]
    assert "Electrocardiogram (ECG)" in chc["diagnostic_tests_available"]
    assert "Ultrasound Abdomen (USG)" in dh["diagnostic_tests_available"]
    assert any(d["name"] == "Dr. Anand Deshmukh" for d in chc["doctors"])

def test_medicine_stock_scenario_c():
    chc = paud_chc()
    assert chc["medicine_stock_summary"]["Amlodipine"] == "OUT_OF_STOCK"
    assert chc["medicine_stock_summary"]["Paracetamol"] == "IN_STOCK"

def test_appointment_booking_and_idempotency_scenario_f():
    payload = {
        "patient_id": 1, "doctor_id": 1, "facility_id": 1,
        "scheduled_date": days_from_today(1), "scheduled_time": "10:00 AM",
        "consultation_type": "IN_PERSON", "reason": "Chest discomfort review",
        "idempotency_key": "idem-test-key-999"
    }
    apt1 = client.post("/api/appointments", json=payload, headers=as_user("ramesh")).json()
    apt2 = client.post("/api/appointments", json=payload, headers=as_user("ramesh")).json()
    assert apt1["id"] == apt2["id"]
    assert apt1["appointment_code"] == apt2["appointment_code"]
    assert apt1["doctor_name"] == "Dr. Anand Deshmukh"

def test_booking_validation():
    base = {"patient_id": 1, "doctor_id": 1, "facility_id": 1, "scheduled_date": days_from_today(2)}
    # doctor does not practise at that facility
    assert client.post("/api/appointments", json={**base, "facility_id": 2}, headers=as_user("ramesh")).status_code == 422
    # past date
    assert client.post("/api/appointments", json={**base, "scheduled_date": days_from_today(-1)}, headers=as_user("ramesh")).status_code == 422
    # a patient cannot book for somebody else
    assert client.post("/api/appointments", json={**base, "patient_id": 2}, headers=as_user("ramesh")).status_code == 403

def test_patient_registration_and_health_record():
    reg = client.post("/api/auth/register", json={"name": "Lata Shinde", "age": 31, "gender": "Female", "phone": "9000011122", "village": "Pirangut"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    me = client.get("/api/patients/me", headers=as_user(token)).json()
    assert me["abha_id"].startswith("91-")
    kavita = client.post("/api/auth/login", json={"username": "asha_kavita"}).json()["user"]
    assert me["assigned_asha_id"] == kavita["id"]
    # duplicate mobile number
    assert client.post("/api/auth/register", json={"name": "Lata S", "age": 31, "gender": "Female", "phone": "9000011122", "village": "Pirangut"}).status_code == 409

    apt = client.post("/api/appointments", headers=as_user(token), json={
        "patient_id": me["id"], "doctor_id": 1, "facility_id": 1, "scheduled_date": days_from_today(1), "reason": "Fever"}).json()
    record = client.get(f"/api/patients/{me['id']}/record", headers=as_user(token)).json()
    assert record["appointments"][0]["appointment_code"] == apt["appointment_code"]
    # other patients cannot read it
    assert client.get(f"/api/patients/{me['id']}/record", headers=as_user("ramesh")).status_code == 403

def test_encounter_and_follow_up_creation():
    payload = {
        "patient_id": 1,
        "chief_complaints": "Chest heaviness and fatigue on exertion",
        "clinical_notes": "Heart sounds normal. S1, S2 audible. No murmurs. Advised ECG.",
        "diagnosis": "Mild Atypical Angina / Exertional Fatigue",
        "vital_bp": "130/84", "vital_pulse": 78, "vital_temp": 98.4, "vital_spo2": 99,
        "clinician_risk_flag": "MODERATE_RISK",
        "prescriptions": [
            {"medicine_name": "Amlodipine 5mg", "dosage": "5mg", "frequency": "Once daily", "duration_days": 30}
        ],
        "diagnostic_test_names": ["Electrocardiogram (ECG)", "Ultrasound Abdomen (USG)"],
        "follow_up_days": 7,
        "follow_up_instructions": "Review with ECG report in 1 week"
    }
    res = client.post("/api/encounters", json=payload, headers=as_user("dr_deshmukh"))
    assert res.status_code == 200
    assert res.json()["diagnosis"] == "Mild Atypical Angina / Exertional Fatigue"

    record = client.get("/api/patients/1/record", headers=as_user("ramesh")).json()
    orders = {o["test_name"]: o["status"] for o in record["diagnostic_orders"]}
    assert orders["Electrocardiogram (ECG)"] == "ORDERED"
    assert orders["Ultrasound Abdomen (USG)"] == "UNAVAILABLE"
    assert record["encounters"][0]["prescriptions"][0]["items"][0]["collected_status"] == "OUT_OF_STOCK"
    assert any(f["due_date"] == days_from_today(7) for f in record["follow_ups"])
    assert "Dr. Anand Deshmukh" in record["reminders"][0]["message"]

def test_only_doctors_record_encounters():
    res = client.post("/api/encounters", headers=as_user("asha_kavita"), json={
        "patient_id": 1, "chief_complaints": "x", "clinical_notes": "x", "diagnosis": "x"})
    assert res.status_code == 403

def test_missed_care_and_asha_task_resolution_scenario_d():
    tasks = client.get("/api/tasks?status=OPEN", headers=as_user("asha_kavita")).json()
    sunita_task = next((t for t in tasks if t["patient_name"] == "Sunita Devi"), None)
    assert sunita_task is not None
    assert sunita_task["task_type"] == "MISSED_FOLLOW_UP"
    # Kavita only sees her own tasks
    assert all(t["asha_worker_id"] == sunita_task["asha_worker_id"] for t in tasks)

    update_payload = {
        "status": "RESOLVED",
        "visit_notes": "Visited Sunita Devi at home. Random blood sugar 164 mg/dL. Missed follow-up due to no bus; accompanied her to CHC.",
        "outcome": "PATIENT_VISITED_CLINIC"
    }
    updated = client.patch(f"/api/tasks/{sunita_task['id']}", json=update_payload, headers=as_user("asha_kavita")).json()
    assert updated["status"] == "RESOLVED"
    assert updated["outcome"] == "PATIENT_VISITED_CLINIC"

def test_access_control_scenario_g():
    anita = next(p for p in client.get("/api/patients?village=Kamshet", headers=as_user("admin_district")).json() if p["name"] == "Anita More")

    # Kavita cannot see Anita in her roster, nor open her record
    roster = client.get("/api/patients", headers=as_user("asha_kavita")).json()
    assert all(p["id"] != anita["id"] for p in roster)
    res = client.get(f"/api/patients/{anita['id']}", headers=as_user("asha_kavita"))
    assert res.status_code == 403
    assert "Access Denied" in res.json()["detail"]

    audits = client.get("/api/audit-events", headers=as_user("admin_district")).json()
    denied_audit = next((a for a in audits if a["action"] == "UNAUTHORIZED_PATIENT_ACCESS_DENIED"), None)
    assert denied_audit is not None
    assert denied_audit["outcome"] == "DENIED"

    # admin-only endpoints
    assert client.get("/api/audit-events", headers=as_user("asha_kavita")).status_code == 403
    assert client.get("/api/admin/metrics", headers=as_user("ramesh")).status_code == 403

def test_facility_admin_updates_roster_services_and_stock():
    manage = client.get("/api/facilities/1/manage", headers=as_user("admin_paud")).json()
    usg = next(s for s in manage["services"] if s["name"].startswith("Ultrasound"))
    assert client.patch(f"/api/facilities/1/services/{usg['id']}", json={"is_available": True}, headers=as_user("admin_paud")).json()["is_available"] is True

    amlo = next(i for i in manage["inventory"] if i["medicine_name"].startswith("Amlodipine"))
    assert client.patch(f"/api/facilities/1/inventory/{amlo['id']}", json={"quantity_in_stock": 10}, headers=as_user("admin_paud")).json()["stock_status"] == "LOW_STOCK"

    doc = client.patch("/api/doctors/1", headers=as_user("admin_paud"), json={
        "is_available_today": False, "schedule": [{"day_of_week": "Monday", "start_time": "10:00", "end_time": "13:00"}]}).json()
    assert doc["is_available_today"] is False and len(doc["schedule"]) == 1
    # off-duty doctors cannot be booked for today
    assert client.post("/api/appointments", headers=as_user("ramesh"), json={
        "patient_id": 1, "doctor_id": 1, "facility_id": 1, "scheduled_date": days_from_today(0)}).status_code == 409

    chc = paud_chc()
    assert "Ultrasound Abdomen (USG)" in chc["diagnostic_tests_available"]
    assert chc["medicine_stock_summary"]["Amlodipine"] == "LOW_STOCK"

    # cannot manage another facility
    assert client.get("/api/facilities/2/manage", headers=as_user("admin_paud")).status_code == 403
    assert client.patch("/api/doctors/2", json={"is_available_today": False}, headers=as_user("admin_paud")).status_code == 403
    client.patch("/api/doctors/1", headers=as_user("admin_paud"), json={"is_available_today": True})

def test_admin_activity_monitoring():
    metrics = client.get("/api/admin/metrics", headers=as_user("admin_district")).json()
    assert metrics["total_patients"] >= 1003
    activity = client.get("/api/admin/activity", headers=as_user("admin_district")).json()
    assert activity["appointments_by_status"]
    assert activity["recent_appointments"]

def test_offline_sync_batch():
    batch = {
        "user_id": 1,
        "actions": [{
            "idempotency_key": "sync-batch-item-101",
            "action_type": "BOOK_APPOINTMENT",
            "payload": {"patient_id": 1, "doctor_id": 1, "facility_id": 1,
                        "scheduled_date": days_from_today(2), "reason": "Follow-up synced from offline cache"}
        }]
    }
    data = client.post("/api/sync/batch", json=batch, headers=as_user("ramesh")).json()
    assert data["synced_count"] == 1
    assert data["results"][0]["status"] == "SYNCED"
    again = client.post("/api/sync/batch", json=batch, headers=as_user("ramesh")).json()
    assert again["results"][0]["status"] == "ALREADY_SYNCED"

def test_marathi_emergency_and_assistant(monkeypatch):
    monkeypatch.setenv("AI_ASSISTANT_MODE", "fallback")
    data = client.post("/api/symptom-intake", headers=as_user("ramesh"), json={
        "patient_id": 1, "raw_input": "मला छातीत दुखत आहे आणि श्वास घ्यायला त्रास होत आहे", "language": "mr"}).json()
    assert data["is_emergency"] is True
    assert "112" in data["emergency_advice"]
    # "विषयावर" (about the topic) contains "विष" (poison) but must not trigger an emergency
    data = client.post("/api/symptom-intake", headers=as_user("ramesh"), json={
        "patient_id": 1, "raw_input": "या विषयावर माहिती द्या", "language": "mr"}).json()
    assert data["is_emergency"] is False

    chat = client.post("/api/ai/chat", headers=as_user("ramesh"), json={
        "language": "mr", "messages": [{"role": "user", "content": "मला दोन दिवसांपासून ताप आहे"}]}).json()
    assert chat["sources"][0]["id"] == "REF-FEVER-01"
    assert "विश्रांती" in chat["reply"]  # Marathi summary of the fever guidance

def test_patient_consent_withdrawal_blocks_doctor():
    team = client.get("/api/patients/me/care-team", headers=as_user("ramesh")).json()
    doctor = next(m for m in team if m["role"] == "DOCTOR")
    assert doctor["consent_status"] == "GRANTED"
    assert client.get("/api/patients/1/record", headers=as_user("dr_deshmukh")).status_code == 200

    team = client.put("/api/patients/me/consents", headers=as_user("ramesh"), json={"user_id": doctor["user_id"], "granted": False}).json()
    assert next(m for m in team if m["user_id"] == doctor["user_id"])["consent_status"] == "REVOKED"
    res = client.get("/api/patients/1/record", headers=as_user("dr_deshmukh"))
    assert res.status_code == 403
    assert "withdrawn consent" in res.json()["detail"]

    client.put("/api/patients/me/consents", headers=as_user("ramesh"), json={"user_id": doctor["user_id"], "granted": True})
    assert client.get("/api/patients/1/record", headers=as_user("dr_deshmukh")).status_code == 200

def test_sms_inbox_and_map_coordinates():
    client.post("/api/appointments", headers=as_user("ramesh"), json={
        "patient_id": 1, "doctor_id": 1, "facility_id": 1, "scheduled_date": days_from_today(3), "reason": "BP review"})
    inbox = client.get("/api/notifications/me", headers=as_user("ramesh")).json()
    assert inbox[0]["title"] == "Appointment confirmed"
    chc = paud_chc()
    assert 18 < chc["latitude"] < 19 and 73 < chc["longitude"] < 74
    impact = client.get("/api/admin/activity", headers=as_user("admin_district")).json()["impact"]
    assert impact["sms_reminders_sent"] >= 1

def test_read_aloud_with_elevenlabs(monkeypatch):
    import tts
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert client.get("/api/tts/status").json()["provider"] == "browser"
    assert client.post("/api/tts", headers=as_user("ramesh"), json={"text": "नमस्ते", "language": "hi"}).status_code == 503

    sent = {}
    class FakeResponse:
        status_code = 200
        content = b"ID3-fake-mp3"
    def fake_post(url, params=None, headers=None, json=None, timeout=None):
        sent.update(url=url, headers=headers, json=json)
        return FakeResponse()
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(tts.httpx, "post", fake_post)
    tts._cache.clear()

    assert client.get("/api/tts/status").json()["provider"] == "elevenlabs"
    assert client.post("/api/tts", json={"text": "x"}).status_code == 401  # login required
    res = client.post("/api/tts", headers=as_user("ramesh"), json={
        "text": "आपके लक्षण (PHC/CHC) में दिखाने योग्य हैं।\n\nस्रोत: Fever: home care", "language": "mr"})
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/mpeg"
    assert res.content == b"ID3-fake-mp3"
    assert sent["headers"]["xi-api-key"] == "test-key"
    assert sent["json"]["model_id"] == "eleven_v4_turbo" and sent["json"]["language_code"] == "mr"
    assert "स्रोत" not in sent["json"]["text"] and "PHC/CHC" not in sent["json"]["text"]


def test_read_aloud_streaming(monkeypatch):
    import tts
    calls = {}

    class FakeStream:
        status_code = 200
        def iter_bytes(self):
            yield b"ID3-part1-"
            yield b"part2"
        def read(self): return b""
        def close(self): calls["closed"] = True

    class FakeClient:
        def __init__(self, *a, **k): pass
        def build_request(self, method, url, params=None, headers=None, json=None):
            calls.update(url=url, json=json)
            return object()
        def send(self, request, stream=False): return FakeStream()
        def close(self): pass

    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(tts.httpx, "Client", FakeClient)
    tts._cache.clear()

    assert client.post("/api/tts/prepare", json={"text": "x"}).status_code == 401
    url = client.post("/api/tts/prepare", headers=as_user("ramesh"), json={"text": "नमस्ते, आराम करें।", "language": "hi"}).json()["url"]
    res = client.get(url)
    assert res.status_code == 200 and res.content == b"ID3-part1-part2"
    assert calls["url"].endswith("/stream") and calls["json"]["language_code"] == "hi"
    assert client.get(url).status_code == 404  # single use

def test_voice_input_with_elevenlabs(monkeypatch):
    import tts
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    monkeypatch.setattr(tts, "_stt_denied", False)
    monkeypatch.setattr(tts, "_stt_probed", True)

    class Ok:
        status_code = 200
        def json(self): return {"text": "मला ताप आहे"}
    sent = {}
    def fake_post(url, headers=None, data=None, files=None, timeout=None, **kw):
        sent.update(url=url, data=data, file=files["file"])
        return Ok()
    monkeypatch.setattr(tts.httpx, "post", fake_post)

    assert client.get("/api/stt/status").json()["provider"] == "elevenlabs"
    audio = b"\x1aE\xdf\xa3" + b"0" * 4000
    assert client.post("/api/stt?language=mr", content=audio, headers={"Content-Type": "audio/webm"}).status_code == 401
    res = client.post("/api/stt?language=mr", content=audio, headers={**as_user("ramesh"), "Content-Type": "audio/webm;codecs=opus"})
    assert res.json()["text"] == "मला ताप आहे"
    assert sent["url"].endswith("/speech-to-text") and sent["data"]["language_code"] == "mr"
    assert sent["file"][0] == "recording.webm"

    # A key without the speech_to_text permission switches the app to browser recognition
    class Denied:
        status_code = 401
        def json(self): return {"detail": {"message": "The API key you used is missing the permission speech_to_text"}}
    monkeypatch.setattr(tts.httpx, "post", lambda *a, **k: Denied())
    assert client.post("/api/stt?language=hi", content=audio, headers={**as_user("ramesh"), "Content-Type": "audio/webm"}).status_code == 502
    assert client.get("/api/stt/status").json()["provider"] == "browser"
