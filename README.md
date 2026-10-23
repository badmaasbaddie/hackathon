# SwasthyaSetu AI (स्वास्थ्यसेतु)
### AI-Powered Rural Healthcare Navigation, Coordination & Continuity Platform

> **Government of Maharashtra — Hacktoberfest**  
> **Theme**: Healthcare AI + Digital Health (Rural-First)  
> **Challenge**: *"Accessibility and quality of public healthcare services, particularly in rural and underserved areas."*  
> **Team AI Avengers**: Rishabh, Sanay Prabhat, Ambuj Kumar  
> **Institution**: GL Bajaj Institute of Technology and Management  
> **Slogan**: *"Doctor tak pahunchna hi nahi, poori healthcare journey ko complete karna."*

---

## 1. Executive Summary & Core USP

Traditional rural healthcare solutions address isolated stages (such as standalone telemedicine apps or basic appointment booking portals), but fail when hand-offs between steps break down. 

**SwasthyaSetu AI** provides an end-to-end **Navigation, Coordination & Continuity Layer** across the rural care continuum:
1. **UNDERSTAND** — Multilingual symptom intake in Hindi and English with safe, deterministic clinical emergency screening.
2. **NAVIGATE** — Care route optimization with transparent facility readiness (travel times, doctor roster timestamps, diagnostic test availability, and dispensary stock).
3. **COORDINATE** — Digital consultations, OPD queue tokens, e-prescriptions, diagnostic test orders, and longitudinal digital health timelines linked to ABHA IDs.
4. **CONTINUE** — Follow-up adherence monitoring and automated missed-care detection that escalates overdue chronic care cases into actionable home-visit tasks for village ASHA workers.

---

## 2. Architecture & Technology Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite bundler.
- **Backend**: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0.
- **Database**: SQLite (Zero-config local ACID store with foreign keys and indexes; PostgreSQL-ready).
- **Offline First**: IndexedDB/LocalStorage persistent action queue with UUID-based idempotency keys and batch reconciliation.
- **AI & Safety**: Deterministic clinical safety rules engine with fallback LLM capability (never delays emergency escalation).
- **Speech**: Web Speech API for voice recognition and text-to-speech with manual typed fallback.
- **Testing**: Pytest with HTTPX test client and end-to-end live integration test suite.

---

## 3. Quick Start (local website)

Requirements: Python 3.10+ and Node.js 18+.

### One command (Windows)
```powershell
.\start.ps1        # or double-click start.bat
```
This installs backend dependencies, builds the frontend if `frontend/dist` is missing (`.\start.ps1 --rebuild` forces a rebuild), reseeds the fictional demo database and serves everything at **http://127.0.0.1:8000**.

### Manual
```bash
cd backend
python -m pip install -r requirements.txt
cd ../frontend && npm install && npm run build && cd ../backend
python seed_data.py                      # optional: reset to the clean demo dataset
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
For frontend development with hot reload, keep the backend running and use `cd frontend && npm run dev` (http://localhost:5173, proxies `/api` to port 8000).

### AI assistant mode
- **No API key (default):** the assistant runs the deterministic safety screen, retrieves approved reference notes and the patient's own record, and composes a clearly labelled *demo* answer.
- **With `ANTHROPIC_API_KEY` set:** answers are written by Claude (`claude-opus-5-5`, override with `AI_MODEL_NAME`) grounded only in the retrieved reference material and patient record. Emergencies are always answered by the safety rules first and never wait for the model.

### Demo logins (use the role buttons in the header; no passwords in this prototype)
| Role | Username | What to try |
|---|---|---|
| Patient | `ramesh` (or **Register** a new patient) | AI assistant (Hindi/English, voice), facilities, booking, health record, reminders, family |
| ASHA / ANM | `asha_kavita` | Assigned patients, overdue follow-up tasks, home-visit recording, Scenario G access test (patient #3) |
| Doctor | `dr_deshmukh` | Own OPD queue, AI intake summary, consultation, prescriptions with stock check, tests, follow-up |
| Hospital | `admin_paud` | Doctor duty and OPD schedules, diagnostic service availability, medicine stock |
| District admin | `admin_district` | Appointment monitoring, platform activity, audit trail, missed-care check |

All data is fictional (including the hospital names). ABHA, eSanjeevani and SMS are simulated adapters; nothing is sent to external systems.

### Presenting it: the guided demo
Click **Guided demo** in the top bar, keep "Reset demo data first" ticked and press **Start the demo**. Nine steps walk through one patient's journey across every role, and each step has a **Do it for me** button:

1. Ramesh reports chest pain in his own language → instant 112/108 advice and the nearest emergency-ready centre (safety rules, no AI wait).
2. An everyday fever question → answer grounded in approved references and his record, with sources; **Listen** reads it aloud.
3. The facility map and cards show Paud CHC lacks ultrasound and is out of Amlodipine *before he travels*; he books and gets a token.
4. Dr. Deshmukh sees his queue and the AI intake summary; the stock warning and ultrasound referral appear; a follow-up and SMS reminder are scheduled.
5. Paud CHC staff restock Amlodipine and mark ultrasound available.
6. ASHA Kavita Tai records a home visit for Sunita Devi's automatically flagged missed follow-up.
7. Kavita Tai tries to open a patient from another village and is blocked (and audited).
8. Ramesh withdraws Dr. Deshmukh's access in the Privacy tab; the doctor can no longer open his record.
9. The district dashboard shows appointments, impact numbers and the audit trail.

### Highlights
- **Hindi, Marathi and English** across the patient screens, the AI assistant and the emergency screening (including Marathi voice input). Staff screens fall back to Hindi where a Marathi label is missing.
- **Read aloud:** answers and emergency advice can be spoken using the browser's voices (a Hindi voice is used when no Marathi voice is installed).
- **Facility map** (OpenStreetMap, needs internet for the map tiles).
- **Patient-controlled consent:** withdrawing access is enforced by the server, not just shown in the UI.
- **Impact panel:** follow-ups recovered, emergencies sent to 112, wasted trips avoided, consent withdrawals honoured - all counted from recorded events.

---

## 4. Feature Checklist Mapped to Hacktoberfest PPT

| PPT Requirement | Implementation in SwasthyaSetu AI | Status |
|---|---|---|
| **Pillar 1: Understand** (Slide 3) | Multilingual voice/text input (Hindi/English), structured intake summary, deterministic emergency rules | **Completed** |
| **Pillar 2: Navigate** (Slide 3) | Facility discovery, travel time, verified doctor roster, diagnostic availability, dispensary inventory | **Completed** |
| **Pillar 3: Coordinate** (Slide 3) | Appointments, OPD queue tokens, e-prescriptions, diagnostic orders, authorized health timeline | **Completed** |
| **Pillar 4: Continue** (Slide 3) | Automated missed follow-up detection, high-priority ASHA task creation, home visit recording | **Completed** |
| **Patient Portal** (Slide 4, Step 1-5) | Multilingual triage, emergency 112 guidance, hospital readiness view, demo booking, family card | **Completed** |
| **ASHA Worker Portal** (Slide 4, Step 10) | Catchment search, overdue follow-ups, home visit recording modal, task resolution outcome | **Completed** |
| **Doctor Portal** (Slide 4, Step 6-9) | OPD queue, clinical encounter note, vitals, prescriptions with stock alert, follow-up scheduling | **Completed** |
| **Hospital Readiness Portal** (Slide 4, Step 4) | Verified doctor roster, equipment availability (ECG ready, USG missing), dispensary stock | **Completed** |
| **Administration Dashboard** (Slide 5-6) | District metrics, overdue counts, open ASHA tasks, audit event viewer, ecosystem adapter matrix | **Completed** |
| **Offline-First & Low Connectivity** (Slide 5) | Simulated offline mode switch, persistent action queue, idempotent sync batch API | **Completed** |

---

## 5. Automated Test Suite & Actual Results

### Backend Unit & Integration Tests (`cd backend && python -m pytest tests`)
Tests run against a throwaway `tests/test_swasthyasetu.db`, so they never wipe the demo database. 24 tests cover auth/RBAC, Hindi and Marathi emergency screening, consent withdrawal, the AI assistant, registration, booking validation, encounters, hospital updates, ASHA tasks, admin monitoring and offline sync.

Earlier output (before the MVP fixes) for reference:
```
tests/test_api.py::test_health_check PASSED                              [  9%]
tests/test_api.py::test_login PASSED                                     [ 18%]
tests/test_api.py::test_emergency_triage_scenario_e PASSED               [ 27%]
tests/test_api.py::test_routine_triage_scenario_a PASSED                 [ 36%]
tests/test_api.py::test_facility_readiness_and_test_unavailability_scenario_b PASSED [ 45%]
tests/test_api.py::test_medicine_stock_scenario_c PASSED                 [ 54%]
tests/test_api.py::test_appointment_booking_and_idempotency_scenario_f PASSED [ 63%]
tests/test_api.py::test_encounter_and_follow_up_creation PASSED          [ 72%]
tests/test_api.py::test_missed_care_and_asha_task_resolution_scenario_d PASSED [ 81%]
tests/test_api.py::test_access_control_scenario_g PASSED                 [ 90%]
tests/test_api.py::test_offline_sync_batch PASSED                        [100%]

======================= 11 passed, 1 warning in 4.06s =======================
```

### Live End-to-End Evaluation Scenarios (`python backend/tests/verify_scenarios_live.py`)
```
=== STARTING LIVE END-TO-END SCENARIO VALIDATION ===
[RESET] Clean demo dataset initialized.
[SCENARIO E - PASSED] Emergency screening prioritized over routine navigation. 112 dialer triggered.
[SCENARIO A (Part 1) - PASSED] Routine symptom intake correctly triaged for PHC/CHC.
[SCENARIO A (Part 2) - PASSED] Appointment confirmed with Token T-1 (Code: APT-29E4C9).
[SCENARIO B - PASSED] Test unavailability at Paud CHC surfaced transparently with District Hospital fallback.
[SCENARIO C - PASSED] Medicine stockout for Amlodipine at Paud CHC identified; regional stock at DH confirmed.
[SCENARIO D - PASSED] Missed-care auto-flagged, assigned to ASHA, home visit recorded, and task resolved.
[SCENARIO F - PASSED] Offline batch replay processed idempotently without duplicate records.
[SCENARIO G - PASSED] Access control blocked unauthorized ASHA cross-village access with HTTP 403 Forbidden.
[AUDIT TRAIL - PASSED] Access denial logged: UNAUTHORIZED_PATIENT_ACCESS_DENIED by Kavita Tai Patil (ASHA Worker).

>>> ALL 7 SCENARIOS VERIFIED SUCCESSFULLY ON LIVE PRODUCTION RUNTIME! <<<
```

---

## 6. Simulated vs Genuine Integrations

| Interface | Integration Type | Description |
|---|---|---|
| **National Emergency 112** | Live Protocol | Displays official 112 / 108 direct dialer and emergency casualty instructions. |
| **Clinical Safety Engine** | Live Local Engine | Deterministic keyword and symptom rules covering acute coronary and respiratory distress in Hindi and English. |
| **ABDM / ABHA ID** | Mock Adapter | Simulates 14-digit ABHA IDs (`91-XXXX-XXXX-XXXX`) and patient consent boundaries. |
| **eSanjeevani Teleconsultation** | Mock Adapter | Formats clinical encounter summaries for state teleconsultation gateways. |
| **SMS Continuity Dispatcher** | Mock Adapter | Simulates SMS delivery for appointment and follow-up reminders. |

---

## 7. Known Limitations & Production Roadmap

1. **Speech Recognition**: Uses browser-native Web Speech API. In production, an on-device Whisper or Bhashini ASR pipeline is recommended for regional dialects (Marathi, rural Hindi).
2. **Database Storage**: The prototype utilizes SQLite for instant, zero-configuration local evaluation. Production deployment should configure PostgreSQL with read-replicas.
3. **ABDM Certification**: While schemas adhere to Ayushman Bharat Digital Mission FHIR profiles, formal sandbox certification with the National Health Authority (NHA) is required for state-wide rollout.
4. **Clinical Oversight**: The AI assistant strictly performs assistive intake and triage screening. All definitive diagnoses, prescriptions, and escalations remain under qualified human medical officer authority.

---

## 8. Reliable Demo Reset Procedure

To reset the database back to clean baseline demo records at any time:
1. In the web application header, click the **"Reset"** button.
2. Alternatively, send an authenticated POST request:
   `curl -X POST -H "X-Demo-User: admin_district" http://127.0.0.1:8000/api/demo/reset`
3. Or run from the command line:  
   `python backend/seed_data.py`
