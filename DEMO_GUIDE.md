# SwasthyaSetu AI — Judge Demonstration Guide

## Quick Start
1. The application is running at **`http://127.0.0.1:8000`**.
2. Open your web browser and navigate to `http://127.0.0.1:8000`.
3. In the top navigation bar, click the gold **"Judge Scenarios"** button. This opens a modal allowing one-click execution of any demonstration scenario.

---

## Testing the 7 Evaluation Scenarios

### Scenario A — Successful Routine Care
1. In the top bar, ensure the active role is **"मरीज़ / परिवार (Patient)"** (`ramesh`).
2. In the AI Assistant tab, click the chip: `"बुखार और शरीर दर्द (सामान्य)"` or type: *"Halka bukhar aur badan dard hai"*.
3. Click **"जांच करें (Analyze & Screen)"**.
4. Observe the green non-emergency triage banner recommending **Primary Health Centre (PHC) / CHC**.
5. Click **"Book at Paud CHC"** to create a demo appointment.
6. Switch role to **"डॉक्टर पोर्टल (Doctor)"** in the top bar.
7. Observe patient Ramesh Kumar in the consultation queue.
8. Enter examination notes and click **"Complete Consultation & Issue Orders"**.
9. Switch back to **"मरीज़ / परिवार (Patient)"** and click **"३. डिजिटल स्वास्थ्य टाइमलाइन"** to view the completed consultation, e-prescription, and follow-up plan.

### Scenario B — Diagnostic Test Unavailable
1. Switch to **"अस्पताल / CHC (Facility)"** portal or inspect the Patient Facility Readiness tab.
2. Select **Paud Community Health Centre (CHC)**.
3. Observe the diagnostic tests list:
   - **ECG Machine**: Marked as **Operational ✓**.
   - **Ultrasound Abdomen (USG)**: Marked as **Unavailable ✕ (Lacking at CHC tier; referral directed to Aundh District Hospital)**.
4. Verify that data freshness indicators clearly distinguish verified local resources from regional fallback referrals.

### Scenario C — Medicine Out-of-Stock
1. Switch to **"डॉक्टर पोर्टल (Doctor)"**.
2. In the prescription dropdown, select **Amlodipine 5mg**.
3. Notice the immediate amber/red stock alert:
   > *"Warning: Amlodipine 5mg currently out-of-stock at Paud CHC Dispensary. Available at Aundh DH (26 km)."*
4. Confirm that the AI does **not** alter the doctor's prescription autonomously or substitute unapproved drugs.

### Scenario D — Missed Follow-up & ASHA Escalation
1. Switch role to **"आशा कार्यकर्ता (ASHA / ANM)"** (`asha_kavita`).
2. Observe the high-priority alert card for **Sunita Devi (Pirangut village)**:
   - Chronic diabetic patient passed her scheduled 30-day review date.
   - Continuity Engine automatically flagged the overdue status and spawned an ASHA home-visit task.
3. Click **"Record Home Visit"**.
4. Enter visit notes (e.g., *"Visited Sunita Devi at home, checked blood glucose (164 mg/dL), assisted with clinic transport"*), select outcome, and click **"Mark Resolved & Synchronize"**.
5. Observe the task status change to **RESOLVED** and the District Admin metrics update immediately.

### Scenario E — Conservative Emergency Warning
1. Switch to **"मरीज़ / परिवार (Patient)"**.
2. Click the quick chip: `"सीने में दर्द व सांस में तकलीफ (आपातकाल)"` or type:
   *"Mujhe chest mein severe pain aur saans lene mein dikkat ho rahi hai"*.
3. Click **"जांच करें (Analyze & Screen)"**.
4. Observe the **red Emergency Warning Banner** that appears immediately.
5. Notice that it does **not** delay for an appointment booking; it prominently displays:
   - Emergency 112 / 108 direct ambulance dialer.
   - Advice to proceed directly to the nearest emergency-ready casualty (Paud CHC 24x7 with ECG).

### Scenario F — Offline Synchronization & Idempotency
1. In the top bar, click the **"Online"** toggle. The badge switches to **"Simulating Offline"**.
2. Book an appointment or resolve a task while offline.
3. Notice that the action is stored locally in the persistent offline queue (indicated by the badge in the top bar: e.g. *"1 queued"*).
4. Click the offline toggle again to restore **"Online"** status.
5. Click the **"Sync"** button. The action is transmitted to `/api/sync/batch` and committed to the backend with an idempotency key preventing duplicate appointments.

### Scenario G — Access Control & Role Permissions (ABDM Compliance)
1. Switch role to **"आशा कार्यकर्ता (ASHA / ANM)"** (`asha_kavita`).
2. In the right column ("Patient Catchment Roster"), locate patient **Anita More** (Village: Kamshet, assigned to Rekha Tai Shinde).
3. Click **"Test Access (Scenario G)"**.
4. Observe the security alert: **HTTP 403 Forbidden** with a clear explanation that ASHA Kavita is not authorized to access patient records outside her jurisdiction.
5. Switch to **"जिला प्रशासन (Admin Analytics)"** and review the **Audit Trail** to see the logged `UNAUTHORIZED_PATIENT_ACCESS_DENIED` security event.
