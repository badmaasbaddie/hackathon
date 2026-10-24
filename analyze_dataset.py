import os
import json
import pandas as pd
from datetime import datetime

DATA_DIR = r"C:\Users\ambuj kumar\.gemini\antigravity\scratch\swasthyasetu-ai\dataset_extracted"

def analyze_dataset():
    report = {
        "analyzed_at": datetime.now().isoformat(),
        "summary": {},
        "integrity_checks": {
            "missing_duplicate_pks": {},
            "orphaned_foreign_keys": {},
            "inventory_anomalies": [],
            "date_anomalies": [],
            "status_anomalies": [],
            "duplicate_records": []
        },
        "rejected_rows": [],
        "valid_rows_summary": {}
    }

    # Load data
    hospitals = pd.read_csv(os.path.join(DATA_DIR, "hospitals.csv"))
    doctors = pd.read_csv(os.path.join(DATA_DIR, "doctors.csv"))
    patients = pd.read_csv(os.path.join(DATA_DIR, "patients.csv"))
    medicines = pd.read_csv(os.path.join(DATA_DIR, "medicines.csv"))
    medicine_inv = pd.read_csv(os.path.join(DATA_DIR, "medicine_inventory.csv"))
    diag_tests = pd.read_csv(os.path.join(DATA_DIR, "diagnostic_tests.csv"))
    appointments = pd.read_csv(os.path.join(DATA_DIR, "appointments.csv"))
    followups = pd.read_csv(os.path.join(DATA_DIR, "followups.csv"))
    hw_tasks = pd.read_csv(os.path.join(DATA_DIR, "health_worker_tasks.csv"))
    reports = pd.read_csv(os.path.join(DATA_DIR, "sample_reports.csv"))

    dfs = {
        "hospitals": (hospitals, "hospital_id"),
        "doctors": (doctors, "doctor_id"),
        "patients": (patients, "patient_id"),
        "medicines": (medicines, "medicine_id"),
        "medicine_inventory": (medicine_inv, None),
        "diagnostic_tests": (diag_tests, "test_id"),
        "appointments": (appointments, "appointment_id"),
        "followups": (followups, "followup_id"),
        "health_worker_tasks": (hw_tasks, "task_id"),
        "sample_reports": (reports, "report_id")
    }

    # 1. Counts and PK checks
    for name, (df, pk) in dfs.items():
        report["summary"][name] = {
            "row_count": len(df),
            "col_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        if pk:
            missing_pk = df[pk].isna().sum()
            dup_pk = df.duplicated(subset=[pk]).sum()
            report["integrity_checks"]["missing_duplicate_pks"][name] = {
                "missing_pk": int(missing_pk),
                "duplicate_pk": int(dup_pk)
            }

    # 2. Foreign Key References
    h_ids = set(hospitals["hospital_id"])
    d_ids = set(doctors["doctor_id"])
    p_ids = set(patients["patient_id"])
    m_ids = set(medicines["medicine_id"])

    # Doctors -> Hospital
    orphaned_doc_hosp = doctors[~doctors["hospital_id"].isin(h_ids)]
    report["integrity_checks"]["orphaned_foreign_keys"]["doctors_to_hospital"] = len(orphaned_doc_hosp)

    # Medicine Inventory -> Hospital, Medicine
    orph_inv_h = medicine_inv[~medicine_inv["hospital_id"].isin(h_ids)]
    orph_inv_m = medicine_inv[~medicine_inv["medicine_id"].isin(m_ids)]
    report["integrity_checks"]["orphaned_foreign_keys"]["inventory_to_hospital"] = len(orph_inv_h)
    report["integrity_checks"]["orphaned_foreign_keys"]["inventory_to_medicine"] = len(orph_inv_m)

    # Diag Tests -> Hospital
    orph_diag_h = diag_tests[~diag_tests["hospital_id"].isin(h_ids)]
    report["integrity_checks"]["orphaned_foreign_keys"]["diag_tests_to_hospital"] = len(orph_diag_h)

    # Appointments -> Patient, Doctor, Hospital
    orph_apt_p = appointments[~appointments["patient_id"].isin(p_ids)]
    orph_apt_d = appointments[~appointments["doctor_id"].isin(d_ids)]
    orph_apt_h = appointments[~appointments["hospital_id"].isin(h_ids)]
    report["integrity_checks"]["orphaned_foreign_keys"]["appointments_to_patient"] = len(orph_apt_p)
    report["integrity_checks"]["orphaned_foreign_keys"]["appointments_to_doctor"] = len(orph_apt_d)
    report["integrity_checks"]["orphaned_foreign_keys"]["appointments_to_hospital"] = len(orph_apt_h)

    # Check doctor belongs to the specified hospital in appointments
    doc_to_hosp_map = dict(zip(doctors["doctor_id"], doctors["hospital_id"]))
    apt_doc_mismatch = 0
    for _, row in appointments.iterrows():
        expected_h = doc_to_hosp_map.get(row["doctor_id"])
        if expected_h and expected_h != row["hospital_id"]:
            apt_doc_mismatch += 1
    report["integrity_checks"]["orphaned_foreign_keys"]["appointment_doctor_hospital_mismatches"] = apt_doc_mismatch

    # Followups -> Patient
    orph_fup_p = followups[~followups["patient_id"].isin(p_ids)]
    report["integrity_checks"]["orphaned_foreign_keys"]["followups_to_patient"] = len(orph_fup_p)

    # Health Worker Tasks -> Patient
    orph_hwt_p = hw_tasks[~hw_tasks["patient_id"].isin(p_ids)]
    report["integrity_checks"]["orphaned_foreign_keys"]["hw_tasks_to_patient"] = len(orph_hwt_p)

    # Reports -> Patient
    orph_rep_p = reports[~reports["patient_id"].isin(p_ids)]
    report["integrity_checks"]["orphaned_foreign_keys"]["reports_to_patient"] = len(orph_rep_p)

    # 3. Inventory Anomalies (Negative or Inconsistent status vs quantity)
    for idx, row in medicine_inv.iterrows():
        qty = row["quantity"]
        status = str(row["stock_status"]).strip().lower()
        if qty < 0:
            report["integrity_checks"]["inventory_anomalies"].append({
                "type": "NEGATIVE_QUANTITY",
                "hospital_id": row["hospital_id"],
                "medicine_id": row["medicine_id"],
                "quantity": qty
            })
        if qty == 0 and status != "out of stock":
            report["integrity_checks"]["inventory_anomalies"].append({
                "type": "ZERO_QTY_NOT_OUT_OF_STOCK",
                "hospital_id": row["hospital_id"],
                "medicine_id": row["medicine_id"],
                "quantity": qty,
                "status": row["stock_status"]
            })
        elif qty > 0 and status == "out of stock":
            report["integrity_checks"]["inventory_anomalies"].append({
                "type": "POSITIVE_QTY_MARKED_OUT_OF_STOCK",
                "hospital_id": row["hospital_id"],
                "medicine_id": row["medicine_id"],
                "quantity": qty,
                "status": row["stock_status"]
            })

    # 4. Date Anomalies and Statuses
    # Appointments
    today_str = "2026-10-24" # Reference date
    past_pending_apts = 0
    for _, row in appointments.iterrows():
        d_str = str(row["date"])
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            if str(d) < today_str and row["status"] in ["Pending", "Scheduled"]:
                past_pending_apts += 1
        except Exception as e:
            report["integrity_checks"]["date_anomalies"].append({
                "table": "appointments", "id": row["appointment_id"], "invalid_date": d_str
            })
    report["integrity_checks"]["date_anomalies"].append({
        "type": "PAST_PENDING_APPOINTMENTS", "count": past_pending_apts,
        "note": "Appointments with date < 2026-10-24 still marked Pending (potential missed care)"
    })

    # Followups
    past_due_fups = 0
    future_completed_fups = 0
    for _, row in followups.iterrows():
        d_str = str(row["due_date"])
        try:
            d = datetime.strptime(d_str, "%Y-%m-%d").date()
            if str(d) < today_str and row["status"] in ["Due", "Pending"]:
                past_due_fups += 1
            if str(d) > today_str and row["status"] == "Completed":
                future_completed_fups += 1
        except Exception as e:
            report["integrity_checks"]["date_anomalies"].append({
                "table": "followups", "id": row["followup_id"], "invalid_date": d_str
            })
    report["integrity_checks"]["date_anomalies"].append({
        "type": "PAST_DUE_FOLLOWUPS", "count": past_due_fups,
        "note": "Followups with due_date < 2026-10-24 still marked Due (overdue care events)"
    })
    report["integrity_checks"]["date_anomalies"].append({
        "type": "FUTURE_COMPLETED_FOLLOWUPS", "count": future_completed_fups,
        "note": "Followups marked Completed before scheduled due date"
    })

    # 5. Duplicate appointments and follow-ups
    dup_apts = appointments.duplicated(subset=["patient_id", "doctor_id", "date", "time"]).sum()
    dup_fups = followups.duplicated(subset=["patient_id", "due_date", "care_type"]).sum()
    report["integrity_checks"]["duplicate_records"].append({
        "type": "DUPLICATE_APPOINTMENT_SLOTS", "count": int(dup_apts)
    })
    report["integrity_checks"]["duplicate_records"].append({
        "type": "DUPLICATE_FOLLOWUP_DUE_DATES", "count": int(dup_fups)
    })

    # Output path
    out_path = os.path.join(r"C:\Users\ambuj kumar\.gemini\antigravity\scratch\swasthyasetu-ai", "DATA_QUALITY_REPORT.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print("Data Quality Analysis Complete!")
    print(json.dumps(report["integrity_checks"], indent=2))

if __name__ == "__main__":
    analyze_dataset()
