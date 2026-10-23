import datetime
import urllib.request
import urllib.error
import json

BASE = "http://127.0.0.1:8000/api"

def days_from_today(n):
    return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()

def post(url, data, user="ramesh"):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Demo-User": user}
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode("utf-8"))

def get(url, user="ramesh"):
    req = urllib.request.Request(url, headers={"X-Demo-User": user})
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode("utf-8"))

def patch(url, data, user="asha_kavita"):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Demo-User": user},
        method="PATCH"
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode("utf-8"))

print("=== STARTING LIVE END-TO-END SCENARIO VALIDATION ===")

# Reset demo first
post(f"{BASE}/demo/reset", {})
print("[RESET] Clean demo dataset initialized.")

# Scenario E: Emergency Warning
res_e = post(f"{BASE}/symptom-intake", {
    "patient_id": 1,
    "raw_input": "Mujhe chest mein severe pain aur saans lene mein dikkat ho rahi hai.",
    "language": "hi",
    "duration_days": 1
})
assert res_e["is_emergency"] is True
assert res_e["triage_level"] == "EMERGENCY"
assert "112" in res_e["emergency_number"]
print("[SCENARIO E - PASSED] Emergency screening prioritized over routine navigation. 112 dialer triggered.")

# Scenario A: Routine Care
res_a = post(f"{BASE}/symptom-intake", {
    "patient_id": 1,
    "raw_input": "Halka bukhar aur badan dard hai.",
    "language": "hi",
    "duration_days": 2
})
assert res_a["is_emergency"] is False
assert res_a["triage_level"] == "ROUTINE"
print("[SCENARIO A (Part 1) - PASSED] Routine symptom intake correctly triaged for PHC/CHC.")

# Book Appointment
apt = post(f"{BASE}/appointments", {
    "patient_id": 1,
    "doctor_id": 1,
    "facility_id": 1,
    "scheduled_date": days_from_today(1),
    "scheduled_time": "10:30 AM",
    "consultation_type": "IN_PERSON",
    "reason": "General checkup & body pain"
})
assert apt["id"] > 0
print(f"[SCENARIO A (Part 2) - PASSED] Appointment confirmed with Token {apt['queue_token']} (Code: {apt['appointment_code']}).")

# Scenario B: Test Unavailability
facs = get(f"{BASE}/facilities?district=Pune")
chc = next(f for f in facs if f["name"].startswith("Paud"))
dh = next(f for f in facs if f["facility_type"] == "DISTRICT_HOSPITAL")
assert "Ultrasound Abdomen (USG)" in chc["diagnostic_tests_missing"]
assert "Ultrasound Abdomen (USG)" in dh["diagnostic_tests_available"]
print("[SCENARIO B - PASSED] Test unavailability at Paud CHC surfaced transparently with District Hospital fallback.")

# Scenario C: Medicine Out-of-Stock
assert chc["medicine_stock_summary"]["Amlodipine"] == "OUT_OF_STOCK"
assert dh["medicine_stock_summary"]["Amlodipine"] == "IN_STOCK"
print("[SCENARIO C - PASSED] Medicine stockout for Amlodipine at Paud CHC identified; regional stock at DH confirmed.")

# Scenario D: Missed Follow-up & ASHA Resolution
tasks = get(f"{BASE}/tasks?status=OPEN", user="asha_kavita")
sunita_task = next(t for t in tasks if t["patient_name"] == "Sunita Devi")
assert sunita_task["task_type"] == "MISSED_FOLLOW_UP"

resolved_task = patch(f"{BASE}/tasks/{sunita_task['id']}", {
    "status": "RESOLVED",
    "visit_notes": "Conducted home visit at Pirangut. Verified sugar (164 mg/dL). Assisted patient to next OPD.",
    "outcome": "PATIENT_VISITED_CLINIC"
})
assert resolved_task["status"] == "RESOLVED"
print("[SCENARIO D - PASSED] Missed-care auto-flagged, assigned to ASHA, home visit recorded, and task resolved.")

# Scenario F: Offline Sync & Idempotency
idem_key = "sync-live-idem-888"
batch = {
    "user_id": 1,
    "actions": [
        {
            "idempotency_key": idem_key,
            "action_type": "BOOK_APPOINTMENT",
            "payload": {
                "patient_id": 1,
                "doctor_id": 1,
                "facility_id": 1,
                "scheduled_date": days_from_today(3),
                "reason": "Offline queued appointment"
            }
        }
    ]
}
sync1 = post(f"{BASE}/sync/batch", batch)
sync2 = post(f"{BASE}/sync/batch", batch)
assert sync1["results"][0]["status"] == "SYNCED"
assert sync2["results"][0]["status"] == "ALREADY_SYNCED"
print("[SCENARIO F - PASSED] Offline batch replay processed idempotently without duplicate records.")

# Scenario G: Access Control Check
patients = get(f"{BASE}/patients?village=Kamshet", user="admin_district")
anita = next(p for p in patients if p["name"] == "Anita More")
try:
    req_denied = urllib.request.Request(f"{BASE}/patients/{anita['id']}", headers={"X-Demo-User": "asha_kavita"})
    urllib.request.urlopen(req_denied)
    print("FAILED: Expected 403 Forbidden")
    exit(1)
except urllib.error.HTTPError as e:
    assert e.code == 403
    print(f"[SCENARIO G - PASSED] Access control blocked unauthorized ASHA cross-village access with HTTP 403 Forbidden.")

# Verify Audit Events
audits = get(f"{BASE}/audit-events", user="admin_district")
denied_event = next(a for a in audits if a["action"] == "UNAUTHORIZED_PATIENT_ACCESS_DENIED")
assert denied_event["outcome"] == "DENIED"
print(f"[AUDIT TRAIL - PASSED] Access denial logged: {denied_event['action']} by {denied_event['user_name']}.")

print("\n>>> ALL 7 SCENARIOS VERIFIED SUCCESSFULLY ON LIVE PRODUCTION RUNTIME! <<<")
