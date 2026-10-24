import os
import json
import datetime
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset_extracted")
if not os.path.exists(DATA_DIR):
    DATA_DIR = r"C:\Users\ambuj kumar\.gemini\antigravity\scratch\swasthyasetu-ai\dataset_extracted"

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

def ingest_dataset(db: Session = None, reset_db: bool = False):
    """
    Idempotent dataset ingestion from synthetic CSV files.
    Validates, logs errors, preserves external IDs, and creates baseline entities.
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    if reset_db:
        print("[INGESTION] Resetting database tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    # 1. Create Ingestion Job Record
    job = models.IngestionJob(
        dataset_name="SwasthyaSetu_AI_1000_Patients_150_Doctors",
        source_files_count=10,
        status="RUNNING",
        started_at=utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    validation_errors = []
    total_processed = 0
    total_imported = 0
    total_rejected = 0

    try:
        # ---------------------------------------------------------
        # A. Baseline Paud CHC & District Hospital (for Evaluation Scenarios B & C)
        # ---------------------------------------------------------
        chc_paud = models.Facility(
            external_id="H_PAUD", name="Paud Community Health Centre (CHC)", facility_type="CHC",
            address="Paud Main Road, Taluka Mulshi, Pune, Maharashtra", village_block="Paud", district="Pune",
            state="Maharashtra", latitude=18.5332, longitude=73.6154, distance_km=4.2, travel_time_mins=12,
            operating_hours="24x7 Emergency / OPD: 08:30 AM - 02:00 PM", is_open_now=True, is_simulated=True,
            last_verified_at=utcnow()
        )
        db.add(chc_paud)

        dist_hosp = models.Facility(
            external_id="H_DH", name="District Hospital Pune (Aundh)", facility_type="DISTRICT_HOSPITAL",
            address="Aundh District Hospital Complex, Pune", village_block="Pune Catchment", district="Pune",
            state="Maharashtra", latitude=18.5721, longitude=73.8042, distance_km=22.5, travel_time_mins=45,
            operating_hours="24x7 Emergency & Inpatient Care", is_open_now=True, is_simulated=True,
            last_verified_at=utcnow()
        )
        db.add(dist_hosp)
        db.commit()

        hosp_map = {"H_PAUD": chc_paud.id, "H_DH": dist_hosp.id}

        # ---------------------------------------------------------
        # B. Facilities / Hospitals (hospitals.csv - 50 rows)
        # ---------------------------------------------------------
        hospitals_csv = os.path.join(DATA_DIR, "hospitals.csv")
        if os.path.exists(hospitals_csv):
            df_hosp = pd.read_csv(hospitals_csv)
            for idx, row in df_hosp.iterrows():
                total_processed += 1
                ext_id = str(row["hospital_id"]).strip()
                existing = db.query(models.Facility).filter(models.Facility.external_id == ext_id).first()
                if existing:
                    hosp_map[ext_id] = existing.id
                    total_imported += 1
                    continue
                try:
                    f = models.Facility(
                        external_id=ext_id,
                        name=str(row["hospital_name"]),
                        facility_type=str(row["facility_type"]),
                        address=f"{row['district']}, {row['state']}",
                        village_block=str(row["district"]),
                        district=str(row["district"]),
                        state=str(row["state"]),
                        latitude=float(row["latitude"]),
                        longitude=float(row["longitude"]),
                        operating_hours=str(row["operating_hours"]),
                        languages=str(row["languages"]),
                        services=str(row["services"]),
                        distance_km=round(4.0 + (idx % 15) * 1.5, 1),
                        travel_time_mins=15 + (idx % 15) * 5,
                        is_open_now=True,
                        is_simulated=True,
                        last_verified_at=utcnow()
                    )
                    db.add(f)
                    db.flush()
                    hosp_map[ext_id] = f.id
                    total_imported += 1
                except Exception as e:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="hospitals.csv", row_identifier=ext_id,
                        error_type="INSERT_ERROR", details=str(e), raw_data_json=json.dumps(dict(row))
                    ))
            db.commit()

        # ---------------------------------------------------------
        # C. Baseline Administrative Roster (Jila Prashashan & Workers)
        # ---------------------------------------------------------
        jila_authorities = [
            ("admin_district", "dho.lucknow@gov.in", "Dr. Rajesh Kulkarni - District Health Officer (DHO Lucknow Central)", "Lucknow Headquarter"),
            ("jila_prashashan_02", "dho.lucknowrural@gov.in", "Dr. Sanjay Deshmukh - Civil Surgeon Lucknow Rural", "Lucknow Rural Zilla Parishad"),
            ("jila_prashashan_03", "cmo.mohanlalganj@gov.in", "Dr. Kavita Gavit - Chief Medical Officer Mohanlalganj", "Mohanlalganj Block"),
            ("jila_prashashan_04", "dho.malihabad@gov.in", "Dr. Pradeep Sharma - District Health Administrator Malihabad", "Malihabad"),
            ("jila_prashashan_05", "dho.kakori@gov.in", "Dr. Fatima Sheikh - DHO Kakori & Chinhat Division", "Kakori"),
            ("jila_prashashan_06", "cs.gosainganj@gov.in", "Dr. Vikram Patil - Civil Surgeon Gosainganj Division", "Gosainganj"),
            ("jila_prashashan_07", "dho.itaunja@gov.in", "Dr. Rameshwar Waghmare - District Health Officer Itaunja", "Itaunja"),
            ("jila_prashashan_08", "dho.amethi@gov.in", "Dr. Sunita Meshram - DHO Amethi Rural Healthcare", "Amethi"),
            ("jila_prashashan_09", "inspector.state@gov.in", "Dr. Harpreet Singh - State Health Quality Inspector", "State HQ"),
            ("jila_prashashan_10", "dho.lucknow@swasthyasetu.gov.in", "District Health Officer (DHO Lucknow Controller)", "Lucknow HQ")
        ]
        for uname, email, full_name, village in jila_authorities:
            if not db.query(models.User).filter(models.User.username == uname).first():
                db.add(models.User(
                    username=uname, email=email, full_name=full_name, role="SUPER_ADMIN", village=village, phone="1800-11-2233"
                ))
        db.commit()

        # Primary ASHA worker Kavita Tai Patil
        asha_kavita = db.query(models.User).filter(models.User.username == "asha_kavita").first()
        if not asha_kavita:
            asha_kavita = models.User(
                username="asha_kavita", email="kavita.asha@arogya.gov.in", full_name="Kavita Tai Patil (ASHA Worker)",
                role="ASHA", phone="9823011223", village="Pirangut"
            )
            db.add(asha_kavita)
            db.commit()

        # Additional ASHA workers
        for i in range(1, 201):
            a_uname = f"asha_lko_{i:03d}"
            if not db.query(models.User).filter(models.User.username == a_uname).first():
                db.add(models.User(
                    username=a_uname, email=f"{a_uname}@swasthyasetu.gov.in", full_name=f"ASHA Worker LKO-{i:03d}",
                    role="ASHA", phone=f"98391{i:05d}", village=f"Village-{(i % 100) + 1:03d}"
                ))
        db.commit()

        # ---------------------------------------------------------
        # D. Doctors (doctors.csv - 150 rows) + Baseline Demo Doctor
        # ---------------------------------------------------------
        u_deshmukh = db.query(models.User).filter(models.User.username == "dr_deshmukh").first()
        if not u_deshmukh:
            u_deshmukh = models.User(
                username="dr_deshmukh", email="dr.anand@gov.in", full_name="Dr. Anand Deshmukh",
                role="DOCTOR", phone="9822012345", village="Paud", facility_id=chc_paud.id
            )
            db.add(u_deshmukh)
            db.flush()

        dr_deshmukh = models.Doctor(
            external_id="D_DESHMUKH", user_id=u_deshmukh.id, facility_id=chc_paud.id, name="Dr. Anand Deshmukh", specialty="General Medicine",
            qualification="MBBS, MD (Internal Medicine)", experience_years=12, phone="9822012345", is_available_today=True,
            last_roster_update=utcnow()
        )
        db.add(dr_deshmukh)
        db.commit()

        doc_map = {"D_DESHMUKH": dr_deshmukh.id}

        doctors_csv = os.path.join(DATA_DIR, "doctors.csv")
        if os.path.exists(doctors_csv):
            df_doc = pd.read_csv(doctors_csv)
            for idx, row in df_doc.iterrows():
                total_processed += 1
                d_ext = str(row["doctor_id"]).strip()
                h_ext = str(row["hospital_id"]).strip()
                facility_id = hosp_map.get(h_ext, chc_paud.id)

                existing = db.query(models.Doctor).filter(models.Doctor.external_id == d_ext).first()
                if existing:
                    doc_map[d_ext] = existing.id
                    total_imported += 1
                    continue
                try:
                    d_uname = f"doctor_{d_ext.lower()}"
                    d_user = db.query(models.User).filter(models.User.username == d_uname).first()
                    if not d_user:
                        d_user = models.User(
                            username=d_uname, email=f"{d_ext.lower()}@hospital.gov.in", full_name=str(row["doctor_name"]),
                            role="DOCTOR", facility_id=facility_id, phone=f"98220{idx:05d}"
                        )
                        db.add(d_user)
                        db.flush()

                    d = models.Doctor(
                        external_id=d_ext,
                        user_id=d_user.id,
                        facility_id=facility_id,
                        name=str(row["doctor_name"]),
                        specialty=str(row["specialization"]),
                        qualification="MBBS, MD",
                        experience_years=5 + (idx % 20),
                        phone=d_user.phone,
                        languages=str(row.get("languages", "Hindi,English")),
                        available_days=str(row.get("available_days", "Mon-Fri")),
                        available_time=str(row.get("available_time", "10:00-14:00")),
                        telemedicine=bool(row.get("telemedicine", True)),
                        is_available_today=True,
                        last_roster_update=utcnow()
                    )
                    db.add(d)
                    db.flush()
                    doc_map[d_ext] = d.id
                    total_imported += 1
                except Exception as e:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="doctors.csv", row_identifier=d_ext,
                        error_type="INSERT_ERROR", details=str(e), raw_data_json=json.dumps(dict(row))
                    ))
            db.commit()

        # Demo doctor Dr. Rajesh Sharma
        dr_sharma_user = db.query(models.User).filter(models.User.username == "dr_sharma").first()
        if not dr_sharma_user:
            dr_sharma_user = models.User(
                username="dr_sharma", email="dr.sharma@paudchc.gov.in", full_name="Dr. Rajesh Sharma (Medical Officer)",
                role="DOCTOR", facility_id=chc_paud.id, phone="9822055667"
            )
            db.add(dr_sharma_user)
            db.commit()

        # ---------------------------------------------------------
        # E. Medicines (medicines.csv - 10 rows)
        # ---------------------------------------------------------
        med_csv = os.path.join(DATA_DIR, "medicines.csv")
        med_map = {}
        if os.path.exists(med_csv):
            df_med = pd.read_csv(med_csv)
            for idx, row in df_med.iterrows():
                total_processed += 1
                m_ext = str(row["medicine_id"]).strip()
                existing = db.query(models.Medicine).filter(models.Medicine.external_id == m_ext).first()
                if existing:
                    med_map[m_ext] = existing.id
                    total_imported += 1
                    continue
                try:
                    m = models.Medicine(
                        external_id=m_ext,
                        code=m_ext,
                        generic_name=str(row["generic_name"]),
                        brand_name=str(row["generic_name"]),
                        strength=str(row.get("strength", "500 mg")),
                        dosage_form=str(row.get("form", "Tablet")),
                        use_category=str(row.get("use_category", "General")),
                        category=str(row.get("use_category", "GENERAL")).upper()
                    )
                    db.add(m)
                    db.flush()
                    med_map[m_ext] = m.id
                    total_imported += 1
                except Exception as e:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="medicines.csv", row_identifier=m_ext,
                        error_type="INSERT_ERROR", details=str(e), raw_data_json=json.dumps(dict(row))
                    ))
            db.commit()

        # ---------------------------------------------------------
        # F. Medicine Inventory (medicine_inventory.csv - 500 rows) + Scenario C setup
        # ---------------------------------------------------------
        # Scenario C: Paud CHC has Amlodipine OUT_OF_STOCK, District Hospital has IN_STOCK!
        amlodipine_id = med_map.get("M002", 2)
        inv_paud_amlo = models.InventorySnapshot(
            facility_id=chc_paud.id, medicine_id=amlodipine_id, medicine_name="Amlodipine 5mg",
            quantity_in_stock=0, unit="strips", reorder_level=20, stock_status="OUT_OF_STOCK",
            last_verified_at=utcnow(), is_simulated=True
        )
        db.add(inv_paud_amlo)

        inv_paud_para = models.InventorySnapshot(
            facility_id=chc_paud.id, medicine_id=amlodipine_id, medicine_name="Paracetamol 500mg",
            quantity_in_stock=100, unit="strips", reorder_level=20, stock_status="IN_STOCK",
            last_verified_at=utcnow(), is_simulated=True
        )
        db.add(inv_paud_para)

        inv_dh_amlo = models.InventorySnapshot(
            facility_id=dist_hosp.id, medicine_id=amlodipine_id, medicine_name="Amlodipine 5mg",
            quantity_in_stock=150, unit="strips", reorder_level=20, stock_status="IN_STOCK",
            last_verified_at=utcnow(), is_simulated=True
        )
        db.add(inv_dh_amlo)
        db.commit()

        inv_csv = os.path.join(DATA_DIR, "medicine_inventory.csv")
        if os.path.exists(inv_csv):
            df_inv = pd.read_csv(inv_csv)
            for idx, row in df_inv.iterrows():
                total_processed += 1
                h_ext = str(row["hospital_id"]).strip()
                m_ext = str(row["medicine_id"]).strip()
                facility_id = hosp_map.get(h_ext)
                medicine_id = med_map.get(m_ext)
                if not facility_id or not medicine_id:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="medicine_inventory.csv", row_identifier=f"{h_ext}-{m_ext}",
                        error_type="ORPHAN_REFERENCE", details=f"Unknown facility {h_ext} or medicine {m_ext}",
                        raw_data_json=json.dumps(dict(row))
                    ))
                    continue

                existing = db.query(models.InventorySnapshot).filter(
                    models.InventorySnapshot.facility_id == facility_id,
                    models.InventorySnapshot.medicine_id == medicine_id
                ).first()
                if existing:
                    existing.quantity_in_stock = int(row["quantity"])
                    existing.stock_status = str(row["stock_status"])
                    existing.last_verified_at = utcnow()
                    total_imported += 1
                    continue

                med_obj = db.get(models.Medicine, medicine_id)
                inv = models.InventorySnapshot(
                    facility_id=facility_id,
                    medicine_id=medicine_id,
                    medicine_name=med_obj.generic_name if med_obj else "Medicine",
                    quantity_in_stock=int(row["quantity"]),
                    stock_status=str(row["stock_status"]),
                    reorder_level=25,
                    unit="strips",
                    last_verified_at=utcnow(),
                    is_simulated=True
                )
                db.add(inv)
                total_imported += 1
            db.commit()

        # ---------------------------------------------------------
        # G. Diagnostic Availability (diagnostic_tests.csv - 400 rows)
        # ---------------------------------------------------------
        diag_csv = os.path.join(DATA_DIR, "diagnostic_tests.csv")
        if os.path.exists(diag_csv):
            df_diag = pd.read_csv(diag_csv)
            for idx, row in df_diag.iterrows():
                total_processed += 1
                h_ext = str(row["hospital_id"]).strip()
                t_code = str(row["test_id"]).strip()
                facility_id = hosp_map.get(h_ext)
                if not facility_id:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="diagnostic_tests.csv", row_identifier=f"{h_ext}-{t_code}",
                        error_type="ORPHAN_HOSPITAL", details=f"Unknown hospital {h_ext}",
                        raw_data_json=json.dumps(dict(row))
                    ))
                    continue

                existing = db.query(models.DiagnosticAvailability).filter(
                    models.DiagnosticAvailability.facility_id == facility_id,
                    models.DiagnosticAvailability.test_code == t_code
                ).first()
                if existing:
                    existing.available = bool(row["available"])
                    existing.availability_note = str(row.get("availability_note", "Same day"))
                    existing.last_verified_at = utcnow()
                    total_imported += 1
                    continue

                da = models.DiagnosticAvailability(
                    facility_id=facility_id,
                    test_code=t_code,
                    test_name=str(row["test_name"]),
                    available=bool(row["available"]),
                    availability_note=str(row.get("availability_note", "Same day")),
                    last_verified_at=utcnow()
                )
                db.add(da)
                total_imported += 1
            db.commit()

        # ---------------------------------------------------------
        # H. Patients (patients.csv - 1000 rows) + Baseline Demo Patients
        # ---------------------------------------------------------
        # Ramesh Shinde (Demo Patient 1)
        p_ramesh = models.Patient(
            external_id="P_RAMESH", abha_id="ABHA-1234-5678-9012", name="Ramesh Shinde", age=48, gender="MALE",
            village="Pirangut", block="Mulshi", district="Pune", phone="9876543210", blood_group="B+",
            chronic_conditions="Hypertension (Stage 1)", current_medication="Amlodipine 5mg",
            allergies="No known drug allergies", care_status="CHRONIC_MONITORING",
            assigned_asha_id=asha_kavita.id
        )
        db.add(p_ramesh)

        # Sunita Devi (Scenario D baseline)
        p_sunita = models.Patient(
            external_id="P_SUNITA", abha_id="91-5829-4411-9022", name="Sunita Devi", age=56, gender="Female",
            village="Pirangut", block="Mulshi", district="Pune", phone="9823456789", blood_group="O+",
            chronic_conditions="Type 2 Diabetes Mellitus, Mild Anemia", current_medication="Metformin 500mg",
            allergies="No known drug allergies", care_status="CHRONIC_MONITORING",
            assigned_asha_id=asha_kavita.id
        )
        db.add(p_sunita)

        # Anita More (Scenario G cross-village access test)
        p_anita = models.Patient(
            external_id="P_ANITA", abha_id="ABHA-9876-5432-1098", name="Anita More", age=32, gender="FEMALE",
            village="Lavasa", block="Mulshi", district="Pune", phone="9823099887", blood_group="A+",
            chronic_conditions="Asthma", current_medication="Salbutamol Inhaler",
            allergies="Penicillin", care_status="ROUTINE", assigned_asha_id=99999
        )
        db.add(p_anita)
        db.commit()

        # Create user accounts for demo patients
        u_ramesh = models.User(username="ramesh", email="ramesh.shinde@demo.swasthyasetu.gov.in", full_name="Ramesh Shinde", role="PATIENT", phone="9876543210", village="Pirangut")
        u_sunita = models.User(username="sunita", email="sunita.devi@demo.swasthyasetu.gov.in", full_name="Sunita Devi", role="PATIENT", phone="9823456789", village="Pirangut")
        db.add_all([u_ramesh, u_sunita])
        db.commit()

        pat_map = {
            "P_RAMESH": p_ramesh.id,
            "P_SUNITA": p_sunita.id,
            "P_ANITA": p_anita.id
        }

        # Ingest 1000 patients
        pat_csv = os.path.join(DATA_DIR, "patients.csv")
        if os.path.exists(pat_csv):
            df_pat = pd.read_csv(pat_csv)
            for idx, row in df_pat.iterrows():
                total_processed += 1
                p_ext = str(row["patient_id"]).strip()
                existing = db.query(models.Patient).filter(models.Patient.external_id == p_ext).first()
                if existing:
                    pat_map[p_ext] = existing.id
                    total_imported += 1
                    continue
                try:
                    p_name = str(row["patient_name"])
                    p_cond = str(row.get("condition", "Routine health monitoring"))
                    p_med = str(row.get("current_medication", "None"))
                    if pd.isna(p_med):
                        p_med = "None"
                    p_allg = str(row.get("allergies", "No known allergy"))
                    if pd.isna(p_allg):
                        p_allg = "No known allergy"
                    p_bg = str(row.get("blood_group", "O+"))
                    if pd.isna(p_bg):
                        p_bg = "O+"

                    care_status = "ROUTINE"
                    if "diabetes" in p_cond.lower() or "hypertension" in p_cond.lower() or "asthma" in p_cond.lower():
                        care_status = "CHRONIC_MONITORING"
                    elif "pregnancy" in p_cond.lower() or "maternal" in p_cond.lower():
                        care_status = "HIGH_RISK"

                    p = models.Patient(
                        external_id=p_ext,
                        abha_id=f"ABHA-{p_ext}-9920",
                        name=p_name,
                        age=int(row["age"]),
                        gender=str(row["gender"]),
                        village=str(row["village"]),
                        block=f"{row['village']} Block",
                        district="Public Health Division",
                        phone=f"98765{idx:05d}",
                        blood_group=p_bg,
                        chronic_conditions=p_cond,
                        current_medication=p_med,
                        allergies=p_allg,
                        care_status=care_status,
                        assigned_asha_id=asha_kavita.id,
                        created_at=utcnow()
                    )
                    db.add(p)
                    db.flush()
                    pat_map[p_ext] = p.id
                    total_imported += 1

                    db.add(models.CareTimelineEvent(
                        patient_id=p.id,
                        event_type="INTAKE",
                        title=f"Patient Registered: {p.name}",
                        description=f"Demographics and baseline intake recorded for {p.name} ({p.age}y, {p.gender}) from {p.village}. Primary condition: {p_cond}.",
                        actor_name="SwasthyaSetu Ingestion Engine",
                        actor_role="SYSTEM",
                        metadata_json=json.dumps({"external_id": p_ext, "condition": p_cond, "allergies": p_allg})
                    ))
                except Exception as e:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="patients.csv", row_identifier=p_ext,
                        error_type="INSERT_ERROR", details=str(e), raw_data_json=json.dumps(dict(row))
                    ))
            db.commit()

        # ---------------------------------------------------------
        # I. Appointments (appointments.csv - 1000 rows)
        # ---------------------------------------------------------
        apt_csv = os.path.join(DATA_DIR, "appointments.csv")
        apt_map = {}
        if os.path.exists(apt_csv):
            df_apt = pd.read_csv(apt_csv)
            for idx, row in df_apt.iterrows():
                total_processed += 1
                a_ext = str(row["appointment_id"]).strip()
                p_ext = str(row["patient_id"]).strip()
                d_ext = str(row["doctor_id"]).strip()
                h_ext = str(row["hospital_id"]).strip()

                patient_id = pat_map.get(p_ext)
                doctor_id = doc_map.get(d_ext, dr_deshmukh.id)
                facility_id = hosp_map.get(h_ext, chc_paud.id)

                if not patient_id:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="appointments.csv", row_identifier=a_ext,
                        error_type="ORPHAN_REFERENCE", details=f"Unknown patient {p_ext}",
                        raw_data_json=json.dumps(dict(row))
                    ))
                    continue

                existing = db.query(models.Appointment).filter(models.Appointment.external_id == a_ext).first()
                if existing:
                    apt_map[a_ext] = existing.id
                    total_imported += 1
                    continue

                apt = models.Appointment(
                    external_id=a_ext,
                    appointment_code=f"APT-{a_ext}",
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    facility_id=facility_id,
                    scheduled_date=str(row["date"]),
                    scheduled_time=str(row.get("time", "10:30")),
                    status=str(row["status"]).upper(),
                    reason=str(row.get("reason", "Follow-up / consultation")),
                    queue_token=f"T-{(idx % 30) + 1}",
                    is_simulated=True,
                    created_at=utcnow()
                )
                db.add(apt)
                db.flush()
                apt_map[a_ext] = apt.id
                total_imported += 1
            db.commit()

        # ---------------------------------------------------------
        # J. Follow-ups (followups.csv - 1000 rows) + Sunita Devi overdue setup
        # ---------------------------------------------------------
        # Sunita Devi Overdue follow-up for Scenario D
        fup_sunita = models.FollowUpPlan(
            external_id="F_SUNITA",
            patient_id=p_sunita.id,
            doctor_id=dr_deshmukh.id,
            facility_id=chc_paud.id,
            due_date=(utcnow() - datetime.timedelta(days=4)).strftime("%Y-%m-%d"),
            care_type="Diabetes follow-up",
            instructions="Check HbA1c, fasting blood sugar, and monitor for diabetic foot/neuropathy symptoms.",
            next_action="Automated missed-care trigger created task for ASHA worker Kavita Tai Patil.",
            status="OVERDUE",
            created_at=utcnow() - datetime.timedelta(days=20)
        )
        db.add(fup_sunita)
        db.commit()

        # Scenario D ASHA task for Sunita Devi
        task_sunita = models.HealthWorkerTask(
            external_id="W_SUNITA",
            patient_id=p_sunita.id,
            asha_worker_id=asha_kavita.id,
            follow_up_id=fup_sunita.id,
            task_type="MISSED_FOLLOW_UP",
            description="Sunita Devi missed scheduled diabetes review. Conduct home visit, verify compliance and re-schedule.",
            priority="HIGH",
            due_date=(utcnow() + datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
            status="OPEN",
            created_at=utcnow() - datetime.timedelta(days=2)
        )
        db.add(task_sunita)
        db.commit()

        fup_csv = os.path.join(DATA_DIR, "followups.csv")
        fup_map = {}
        if os.path.exists(fup_csv):
            df_fup = pd.read_csv(fup_csv)
            for idx, row in df_fup.iterrows():
                total_processed += 1
                f_ext = str(row["followup_id"]).strip()
                p_ext = str(row["patient_id"]).strip()
                patient_id = pat_map.get(p_ext)
                if not patient_id:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="followups.csv", row_identifier=f_ext,
                        error_type="ORPHAN_PATIENT", details=f"Unknown patient {p_ext}",
                        raw_data_json=json.dumps(dict(row))
                    ))
                    continue

                existing = db.query(models.FollowUpPlan).filter(models.FollowUpPlan.external_id == f_ext).first()
                if existing:
                    fup_map[f_ext] = existing.id
                    total_imported += 1
                    continue

                status_raw = str(row["status"]).strip()
                status = "SCHEDULED"
                if status_raw.lower() in ["due", "pending"]:
                    status = "DUE"
                elif status_raw.lower() in ["missed", "overdue"]:
                    status = "MISSED"
                elif status_raw.lower() in ["completed", "done"]:
                    status = "COMPLETED"

                fup = models.FollowUpPlan(
                    external_id=f_ext,
                    patient_id=patient_id,
                    doctor_id=dr_deshmukh.id,
                    facility_id=chc_paud.id,
                    due_date=str(row["due_date"]),
                    care_type=str(row.get("care_type", "Routine consultation")),
                    instructions=f"{row.get('care_type', 'Consultation')} follow-up care plan.",
                    next_action=str(row.get("next_action", "Scheduled follow-up check")),
                    status=status,
                    created_at=utcnow()
                )
                db.add(fup)
                db.flush()
                fup_map[f_ext] = fup.id
                total_imported += 1
            db.commit()

        # ---------------------------------------------------------
        # K. Health Worker Tasks (health_worker_tasks.csv - 500 rows)
        # ---------------------------------------------------------
        hwt_csv = os.path.join(DATA_DIR, "health_worker_tasks.csv")
        if os.path.exists(hwt_csv):
            df_hwt = pd.read_csv(hwt_csv)
            for idx, row in df_hwt.iterrows():
                total_processed += 1
                w_ext = str(row["task_id"]).strip()
                p_ext = str(row["patient_id"]).strip()
                patient_id = pat_map.get(p_ext)
                if not patient_id:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="health_worker_tasks.csv", row_identifier=w_ext,
                        error_type="ORPHAN_PATIENT", details=f"Unknown patient {p_ext}",
                        raw_data_json=json.dumps(dict(row))
                    ))
                    continue

                existing = db.query(models.HealthWorkerTask).filter(models.HealthWorkerTask.external_id == w_ext).first()
                if existing:
                    total_imported += 1
                    continue

                status_raw = str(row["status"]).strip()
                # Keep consistent statuses for ASHA portal
                task_status = "OPEN"
                if status_raw.lower() == "completed":
                    task_status = "RESOLVED"
                elif status_raw.lower() in ["assigned", "in progress"]:
                    task_status = "IN_PROGRESS"

                task = models.HealthWorkerTask(
                    external_id=w_ext,
                    patient_id=patient_id,
                    asha_worker_id=asha_kavita.id,
                    task_type=str(row["task_type"]),
                    description=str(row.get("description", "Home visit / patient confirmation")),
                    priority=str(row["priority"]).upper(),
                    due_date="2026-11-05",
                    status=task_status,
                    visit_notes=f"Initial record imported." if task_status == "RESOLVED" else None,
                    outcome="HOME_CHECK_COMPLETED" if task_status == "RESOLVED" else None,
                    created_at=utcnow()
                )
                db.add(task)
                total_imported += 1
            db.commit()

        # ---------------------------------------------------------
        # L. Sample Reports (sample_reports.csv - 500 rows)
        # ---------------------------------------------------------
        rep_csv = os.path.join(DATA_DIR, "sample_reports.csv")
        if os.path.exists(rep_csv):
            df_rep = pd.read_csv(rep_csv)
            for idx, row in df_rep.iterrows():
                total_processed += 1
                r_ext = str(row["report_id"]).strip()
                p_ext = str(row["patient_id"]).strip()
                patient_id = pat_map.get(p_ext)
                if not patient_id:
                    total_rejected += 1
                    validation_errors.append(models.IngestionValidationError(
                        job_id=job.id, file_name="sample_reports.csv", row_identifier=r_ext,
                        error_type="ORPHAN_PATIENT", details=f"Unknown patient {p_ext}",
                        raw_data_json=json.dumps(dict(row))
                    ))
                    continue

                existing = db.query(models.PatientReport).filter(models.PatientReport.external_id == r_ext).first()
                if existing:
                    total_imported += 1
                    continue

                findings_str = str(row["findings"])
                ai_note = str(row.get("ai_action_note", "Doctor review recommended"))
                is_abnormal = ("high" in findings_str.lower() or "elevated" in findings_str.lower() or
                               "abnormal" in findings_str.lower() or "256" in findings_str or "218" in findings_str)

                rep = models.PatientReport(
                    external_id=r_ext,
                    patient_id=patient_id,
                    report_type=str(row["report_type"]),
                    report_date=str(row["report_date"]),
                    findings=findings_str,
                    ai_action_note=ai_note,
                    ai_extracted_values=json.dumps({"findings": findings_str, "extracted_at": utcnow().isoformat()}),
                    is_abnormal=is_abnormal,
                    doctor_reviewed=False,
                    created_at=utcnow()
                )
                db.add(rep)
                total_imported += 1
            db.commit()

        # Update Job completion
        job.total_records_processed = total_processed
        job.valid_records_imported = total_imported
        job.rejected_records_count = total_rejected
        job.status = "COMPLETED"
        job.completed_at = utcnow()
        job.summary_json = json.dumps({
            "hospitals": len(hosp_map),
            "doctors": len(doc_map),
            "patients": len(pat_map),
            "medicines": len(med_map),
            "total_processed": total_processed,
            "total_imported": total_imported,
            "total_rejected": total_rejected
        })

        if validation_errors:
            db.add_all(validation_errors)
        db.commit()

        print(f"[INGESTION SUCCESS] Processed {total_processed} records. Imported {total_imported}, Rejected {total_rejected}.")
        return {
            "status": "COMPLETED",
            "job_id": job.id,
            "total_processed": total_processed,
            "total_imported": total_imported,
            "total_rejected": total_rejected
        }

    except Exception as e:
        db.rollback()
        job.status = "FAILED"
        job.completed_at = utcnow()
        job.summary_json = json.dumps({"error": str(e)})
        db.commit()
        print(f"[INGESTION FAILED] Error: {e}")
        raise e
    finally:
        if should_close:
            db.close()

if __name__ == "__main__":
    ingest_dataset(reset_db=True)
