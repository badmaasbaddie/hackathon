"""
Seed database with the exact 1,000 Patient Dataset trained by SwasthyaSetu AI:
- 10 Jila Prashashan Authorities
- 10 Registered Hub Hospitals
- Primary Care Doctors
- ASHA Workers (ASHA-LKO-xxx)
- 1,000 Patients (P-0001 to P-1000) with vitals and monitoring pathways
"""

import os
import re
import random
import datetime
import pandas as pd
from database import engine, SessionLocal, Base
import models
from ml_model import parse_patient_demographics, parse_vitals

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "patients_dataset.csv")

def seed_trained_dataset():
    print("Seeding database with exact 1,000 patient dataset and health infrastructure...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.datetime.now(datetime.timezone.utc)

    # 1. 10 Jila Prashashan Authorities
    jila_authorities = [
        {"name": "Dr. Rajesh Kulkarni", "title": "District Health Officer (DHO Lucknow Central)", "district": "Lucknow"},
        {"name": "Dr. Sanjay Deshmukh", "title": "Civil Surgeon & DHO Lucknow Rural", "district": "Lucknow Rural"},
        {"name": "Dr. Kavita Gavit", "title": "Chief Medical Officer (CMO Mohanlalganj)", "district": "Mohanlalganj"},
        {"name": "Dr. Pradeep Sharma", "title": "District Health Administrator Malihabad", "district": "Malihabad"},
        {"name": "Dr. Anand Shinde", "title": "DHO Bakshi Ka Talab Division", "district": "Bakshi Ka Talab"},
        {"name": "Dr. Fatima Sheikh", "title": "DHO Kakori & Chinhat Division", "district": "Kakori"},
        {"name": "Dr. Vikram Patil", "title": "Civil Surgeon Gosainganj Division", "district": "Gosainganj"},
        {"name": "Dr. Rameshwar Waghmare", "title": "District Health Officer Itaunja", "district": "Itaunja"},
        {"name": "Dr. Sunita Meshram", "title": "DHO Amethi Rural Healthcare", "district": "Amethi"},
        {"name": "Dr. Harpreet Singh", "title": "State Health Quality Inspector", "district": "State HQ"}
    ]

    jila_users = []
    # Primary admin login
    admin_main = models.User(
        username="admin_district",
        email="dho.lucknow@gov.in",
        full_name="District Health Officer (DHO Lucknow)",
        role="SUPER_ADMIN",
        phone="0522-2612345",
        village="Lucknow Headquarter"
    )
    jila_users.append(admin_main)

    for i, j in enumerate(jila_authorities):
        uname = f"jila_prashashan_{i+1:02d}"
        if i > 0:
            u = models.User(
                username=uname,
                email=f"dho.{j['district'].lower().replace(' ', '')}@swasthyasetu.gov.in",
                full_name=f"{j['name']} - {j['title']}",
                role="SUPER_ADMIN",
                phone=f"98390{i:02d}123",
                village=f"{j['district']} Zilla Parishad"
            )
            jila_users.append(u)
    db.add_all(jila_users)
    db.commit()

    # 2. Facilities: 10 Hub Hospitals + Baseline CHC Paud / PHC Pirangut
    df = pd.read_csv(DATA_PATH)
    unique_hospitals = list(df["Registered Hub Hospital"].unique())
    
    facility_records = []
    # Always include baseline Paud CHC for baseline demonstration
    chc_paud = models.Facility(
        name="Paud Community Health Centre (CHC)",
        facility_type="CHC",
        address="Near ST Bus Stand, Paud, Taluka Mulshi",
        village_block="Mulshi",
        district="Pune",
        phone="020-22923450",
        emergency_contact="112",
        latitude=18.5332,
        longitude=73.6154,
        distance_km=4.2,
        travel_time_mins=12,
        operating_hours="24x7 Emergency / OPD: 08:30 AM - 02:00 PM",
        is_open_now=True,
        is_simulated=True,
        last_verified_at=now - datetime.timedelta(minutes=10)
    )
    facility_records.append(chc_paud)

    hospital_map = {}
    for i, h_name in enumerate(unique_hospitals):
        f_type = "DISTRICT_HOSPITAL" if "Hospital" in h_name else "CHC"
        dist_km = round(3.5 + (i * 2.8), 1)
        mins = int(dist_km * 2.2)
        fac = models.Facility(
            name=h_name,
            facility_type=f_type,
            address=f"Main Healthcare Corridor, {h_name.split()[0]} Area, Lucknow",
            village_block="Lucknow Metropolitan & Rural Catchment",
            district="Lucknow",
            phone=f"0522-{random.randint(2200000, 2999999)}",
            emergency_contact="112",
            latitude=26.8467 + (random.random() * 0.15),
            longitude=80.9462 + (random.random() * 0.15),
            distance_km=dist_km,
            travel_time_mins=mins,
            operating_hours="24x7 Emergency & Inpatient Care",
            is_open_now=True,
            is_simulated=True,
            last_verified_at=now - datetime.timedelta(minutes=random.randint(5, 60))
        )
        facility_records.append(fac)

    # Rest of the Mulshi (Pune) demo cluster, so Paud patients have a PHC and a District Hospital to compare
    facility_records.append(models.Facility(
        name="Pirangut Primary Health Centre (PHC)", facility_type="PHC",
        address="Ghotawade Phata Road, Pirangut, Taluka Mulshi", village_block="Mulshi", district="Pune",
        phone="020-22950110", emergency_contact="112", latitude=18.5112, longitude=73.6812,
        distance_km=8.6, travel_time_mins=22, operating_hours="OPD: 09:00 AM - 04:00 PM (Mon-Sat)",
        is_open_now=True, is_simulated=True, last_verified_at=now - datetime.timedelta(minutes=35)
    ))
    facility_records.append(models.Facility(
        name="Aundh District Hospital (Demo)", facility_type="DISTRICT_HOSPITAL",
        address="Aundh Camp Road, Aundh, Pune", village_block="Haveli", district="Pune",
        phone="020-25801234", emergency_contact="112", latitude=18.5590, longitude=73.8070,
        distance_km=26.0, travel_time_mins=55, operating_hours="24x7 Emergency & Inpatient Care",
        is_open_now=True, is_simulated=True, last_verified_at=now - datetime.timedelta(minutes=20)
    ))

    db.add_all(facility_records)
    db.commit()

    for fac in facility_records:
        hospital_map[fac.name] = fac.id

    # 3. Doctors: 10 Primary Care Doctors from Dataset + 190 regional specialists
    unique_doctors = list(df["Primary Care Doctor"].unique())
    doctor_users = []
    doctor_records = []

    # Include Dr. Deshmukh for baseline demo
    u_deshmukh = models.User(username="dr_deshmukh", email="dr.anand@gov.in", full_name="Dr. Anand Deshmukh", role="DOCTOR", phone="9822012345", village="Paud", facility_id=1)
    doctor_users.append(u_deshmukh)
    doc_deshmukh = models.Doctor(user_id=None, facility_id=1, name="Dr. Anand Deshmukh", specialty="General Medicine", qualification="MBBS, MD (Internal Medicine)", experience_years=12, phone="9822012345", is_available_today=True, last_roster_update=now)
    doctor_records.append(doc_deshmukh)

    doc_map = {}
    doc_map["Dr. Anand Deshmukh"] = 1

    doctor_specs = {
        "Dr. Meera Jha": "General Medicine & Internal Care",
        "Dr. A. K. Srivastava": "Cardiology & Chronic Care",
        "Dr. Sanjay Verma": "Pulmonology & Critical Care",
        "Dr. Ritu Anand": "Obstetrics & High-Risk Maternal Health",
        "Dr. Shalini Rai": "Endocrinology & Diabetic Care",
        "Dr. Sunita Kapoor": "Post-Operative Surgery & Rehab",
        "Dr. Alok Pandey": "Community & Preventive Medicine",
        "Dr. Rajesh Mishra": "Emergency Medicine",
        "Dr. Neha Tripathi": "Pediatrics & Maternal Health",
        "Dr. Vikas Gupta": "Orthopedics & Chronic Care"
    }

    for i, d_name in enumerate(unique_doctors):
        uname = f"dr_{d_name.lower().replace(' ', '_').replace('.', '')}"
        u = models.User(
            username=uname,
            email=f"{uname}@gov.in",
            full_name=d_name,
            role="DOCTOR",
            phone=f"9839{random.randint(100000, 999999)}",
            village="Lucknow Central",
            facility_id=facility_records[(i % len(unique_hospitals)) + 1].id
        )
        doctor_users.append(u)

        d = models.Doctor(
            user_id=None,
            facility_id=facility_records[(i % len(unique_hospitals)) + 1].id,
            name=d_name,
            specialty=doctor_specs.get(d_name, "General Medicine"),
            qualification="MBBS, MD / MS (Certified)",
            experience_years=random.randint(8, 26),
            phone=u.phone,
            is_available_today=True,
            last_roster_update=now - datetime.timedelta(minutes=random.randint(10, 120))
        )
        doctor_records.append(d)

    # Add remaining to reach 200 doctors
    first_names = ["Arun", "Bhavna", "Chirag", "Divya", "Girish", "Harish", "Ila", "Kamal", "Lokesh", "Mohit"]
    last_names = ["Bajpai", "Tiwari", "Shukla", "Awasthi", "Dixit", "Chaturvedi", "Dubey", "Dwivedi", "Upadhyay", "Pathak"]
    specs = ["Cardiology", "Nephrology", "Dermatology", "Ophthalmology", "ENT", "Psychiatry", "Neurology", "Pediatrics"]
    
    for i in range(len(doctor_records) + 1, 201):
        fn = first_names[i % len(first_names)]
        ln = last_names[(i * 3) % len(last_names)]
        full_d = f"Dr. {fn} {ln}"
        u = models.User(
            username=f"dr_{i:03d}",
            email=f"dr.{fn.lower()}.{ln.lower()}{i}@gov.in",
            full_name=full_d,
            role="DOCTOR",
            phone=f"98{random.randint(10000000, 99999999)}",
            village="Regional Center",
            facility_id=facility_records[i % len(facility_records)].id
        )
        doctor_users.append(u)
        d = models.Doctor(
            user_id=None,
            facility_id=facility_records[i % len(facility_records)].id,
            name=full_d,
            specialty=specs[i % len(specs)],
            qualification="MBBS, MD",
            experience_years=random.randint(4, 25),
            phone=u.phone,
            is_available_today=random.choice([True, True, True, False]),
            last_roster_update=now - datetime.timedelta(minutes=30)
        )
        doctor_records.append(d)

    db.add_all(doctor_users)
    db.commit()

    for u, d in zip(doctor_users, doctor_records):
        d.user_id = u.id
    db.add_all(doctor_records)
    db.commit()

    for d in doctor_records:
        doc_map[d.name] = d.id

    # 4. ASHA Workers (all unique ASHA-LKO-xxx from dataset + Kavita Tai)
    unique_ashas = list(df["Assigned ASHA Worker"].unique())
    asha_users = []
    
    # Always include asha_kavita for baseline demo
    asha_kavita = models.User(
        username="asha_kavita",
        email="kavita.patil@asha.swasthyasetu.gov.in",
        full_name="Kavita Tai Patil (ASHA Worker)",
        role="ASHA",
        phone="9123456780",
        village="Paud"
    )
    asha_users.append(asha_kavita)

    asha_map = {}

    for a_code in unique_ashas:
        uname = a_code.lower().replace("-", "_")
        u = models.User(
            username=uname,
            email=f"{uname}@asha.swasthyasetu.gov.in",
            full_name=f"Community Health Worker ({a_code})",
            role="ASHA",
            phone=f"91{random.randint(70000000, 99999999)}",
            village="Lucknow Catchment Area"
        )
        asha_users.append(u)

    db.add_all(asha_users)
    db.commit()

    for u in asha_users:
        code_part = u.username.upper().replace("_", "-")
        asha_map[code_part] = u.id
        asha_map[u.username] = u.id
    kavita_id = asha_kavita.id
    other_asha_id = asha_users[1].id  # a different ASHA, used for the cross-catchment access check

    # 4b. Facility administrators (hospital staff who maintain rosters, services and stock)
    facility_admins = [models.User(
        username="admin_paud",
        email="admin.paud@swasthyasetu.gov.in",
        full_name="Paud CHC Facility Manager",
        role="FACILITY_ADMIN",
        phone="020-22923451",
        village="Paud",
        facility_id=chc_paud.id
    )]
    for fac in facility_records[1:]:
        facility_admins.append(models.User(
            username=f"facility_admin_{fac.id:02d}",
            email=f"facility.admin{fac.id:02d}@swasthyasetu.gov.in",
            full_name=f"{fac.name} Facility Manager",
            role="FACILITY_ADMIN",
            phone=fac.phone,
            village=fac.village_block,
            facility_id=fac.id
        ))
    db.add_all(facility_admins)
    db.commit()

    # 4c. Diagnostic services per facility (editable by facility admins)
    tier_tests = {
        "DISTRICT_HOSPITAL": {"Electrocardiogram (ECG)": True, "Complete Blood Count (CBC)": True, "Ultrasound Abdomen (USG)": True, "Fasting Blood Sugar (FBS)": True, "Chest X-Ray Digital": True},
        "CHC": {"Electrocardiogram (ECG)": True, "Complete Blood Count (CBC)": True, "Fasting Blood Sugar (FBS)": True, "Chest X-Ray Digital": True, "Ultrasound Abdomen (USG)": False},
        "PHC": {"Fasting Blood Sugar (FBS)": True, "Urine Albumin": True, "Electrocardiogram (ECG)": False, "Complete Blood Count (CBC)": False, "Ultrasound Abdomen (USG)": False, "Chest X-Ray Digital": False},
    }
    services = []
    for fac in facility_records:
        for test_name, avail in tier_tests.get(fac.facility_type, tier_tests["PHC"]).items():
            services.append(models.FacilityService(
                facility_id=fac.id, name=test_name, category="DIAGNOSTIC", is_available=avail,
                notes=None if avail else "Equipment not installed at this tier - refer to District Hospital",
                updated_at=now
            ))
    db.add_all(services)

    # 4d. Weekly OPD schedules for every doctor
    schedules = []
    for d in doctor_records:
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            schedules.append(models.DoctorAvailability(doctor_id=d.id, day_of_week=day, start_time="09:00", end_time="14:00", slot_duration_minutes=15))
    db.add_all(schedules)
    db.commit()

    # 5. Seed standard medicines & inventory
    med_para = models.Medicine(code="MED-PARA", generic_name="Paracetamol", brand_name="Crocin / Dolo", category="ANALGESIC", strength="500mg", dosage_form="TABLET")
    med_amlo = models.Medicine(code="MED-AMLO", generic_name="Amlodipine", brand_name="Amlip", category="ANTIHYPERTENSIVE", strength="5mg", dosage_form="TABLET")
    med_met = models.Medicine(code="MED-MET", generic_name="Metformin", brand_name="Glycomet", category="ANTIDIABETIC", strength="500mg", dosage_form="TABLET")
    med_amox = models.Medicine(code="MED-AMOX", generic_name="Amoxicillin", brand_name="Mox", category="ANTIBIOTIC", strength="500mg", dosage_form="CAPSULE")
    med_telm = models.Medicine(code="MED-TELM", generic_name="Telmisartan", brand_name="Telma", category="ANTIHYPERTENSIVE", strength="40mg", dosage_form="TABLET")
    med_ors = models.Medicine(code="MED-ORS", generic_name="Oral Rehydration Salts (ORS)", brand_name="Electral", category="ELECTROLYTE", strength="21.8g", dosage_form="SACHET")
    db.add_all([med_para, med_amlo, med_met, med_amox, med_telm, med_ors])
    db.commit()

    inventories = []
    for fac in facility_records:
        inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_para.id, medicine_name="Paracetamol 500mg", quantity_in_stock=random.randint(200, 2000), stock_status="IN_STOCK", last_verified_at=now))
        inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_met.id, medicine_name="Metformin 500mg", quantity_in_stock=random.randint(100, 1000), stock_status="IN_STOCK", last_verified_at=now))
        inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_ors.id, medicine_name="Oral Rehydration Salts (ORS)", quantity_in_stock=random.randint(80, 800), stock_status="IN_STOCK", last_verified_at=now))
        if fac.id == 1:
            inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_amlo.id, medicine_name="Amlodipine 5mg", quantity_in_stock=0, stock_status="OUT_OF_STOCK", last_verified_at=now))
        else:
            inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_amlo.id, medicine_name="Amlodipine 5mg", quantity_in_stock=random.randint(300, 1500), stock_status="IN_STOCK", last_verified_at=now))
    db.add_all(inventories)
    db.commit()

    # 6. Seed 1,000 Patients from Dataset
    patient_users = []
    patient_records = []
    encounters = []
    follow_ups = []
    tasks = []

    # Add baseline demo patients
    # Ramesh Kumar
    u_ramesh = models.User(username="ramesh", email="ramesh.kumar@demo.swasthyasetu.gov.in", full_name="Ramesh Kumar", role="PATIENT", phone="9876543210", village="Paud")
    patient_users.append(u_ramesh)
    p_ramesh = models.Patient(
        user_id=None,
        abha_id="91-4829-1029-3849",
        name="Ramesh Kumar",
        age=48,
        gender="Male",
        village="Paud",
        block="Mulshi",
        district="Pune",
        phone="9876543210",
        blood_group="B+",
        emergency_contact="9876543211",
        chronic_conditions="Hypertension (Mild)",
        assigned_asha_id=kavita_id,
        created_at=now - datetime.timedelta(days=45)
    )
    patient_records.append(p_ramesh)

    # Sunita Devi (Scenario D baseline)
    u_sunita = models.User(username="sunita", email="sunita.devi@demo.swasthyasetu.gov.in", full_name="Sunita Devi", role="PATIENT", phone="9823456789", village="Pirangut")
    patient_users.append(u_sunita)
    p_sunita = models.Patient(
        user_id=None,
        abha_id="91-5829-4411-9022",
        name="Sunita Devi",
        age=56,
        gender="Female",
        village="Pirangut",
        block="Mulshi",
        district="Pune",
        phone="9823456789",
        blood_group="O+",
        emergency_contact="9823456780",
        chronic_conditions="Type 2 Diabetes Mellitus, Hypertension",
        assigned_asha_id=kavita_id,
        created_at=now - datetime.timedelta(days=90)
    )
    patient_records.append(p_sunita)

    # Anita More (Scenario G unauthorized access check - assigned to ASHA #2, NOT Kavita #1)
    u_anita = models.User(username="anita", email="anita.more@demo.swasthyasetu.gov.in", full_name="Anita More", role="PATIENT", phone="9988776655", village="Kamshet")
    patient_users.append(u_anita)
    p_anita = models.Patient(
        user_id=None,
        abha_id="91-9988-7766-5544",
        name="Anita More",
        age=34,
        gender="Female",
        village="Kamshet",
        block="Maval",
        district="Pune",
        phone="9988776655",
        blood_group="AB+",
        emergency_contact="9988776650",
        chronic_conditions="Hypothyroidism",
        assigned_asha_id=other_asha_id, # Outside Kavita's catchment
        created_at=now - datetime.timedelta(days=20)
    )
    patient_records.append(p_anita)

    # Add 1,000 patients from CSV
    for idx, row in df.iterrows():
        p_id = row["Patient ID"]
        name, age, gender = parse_patient_demographics(row["Name / Age / Gender"])
        village = row["Village Name"]
        hub_hosp = row["Registered Hub Hospital"]
        doctor_name = row["Primary Care Doctor"]
        asha_code = row["Assigned ASHA Worker"]
        m_type = row["Monitoring Type"]
        vitals_raw = row["Last Update Vitals"]
        vitals = parse_vitals(vitals_raw)

        u_uname = f"pat_{p_id.lower().replace('-', '_')}"
        u = models.User(
            username=u_uname,
            email=f"{u_uname}@patient.swasthyasetu.gov.in",
            full_name=name,
            role="PATIENT",
            phone=f"98{random.randint(10000000, 99999999)}",
            village=village
        )
        patient_users.append(u)

        # 14-digit ABHA ID formatted e.g. 91-1234-5678-0001
        seq_num = int(p_id.replace("P-", ""))
        abha = f"91-{age:02d}{random.randint(10,99)}-{random.randint(1000,9999)}-{seq_num:04d}"

        # Assign ASHA id
        assigned_asha_id = asha_map.get(asha_code, asha_map.get(asha_code.lower().replace("-", "_"), kavita_id))

        p = models.Patient(
            user_id=None,
            abha_id=abha,
            name=name,
            age=age,
            gender="Female" if gender == "F" else "Male",
            village=village,
            block="Lucknow Catchment",
            district="Lucknow",
            phone=u.phone,
            blood_group=random.choice(["A+", "B+", "O+", "AB+", "A-", "B-"]),
            emergency_contact=f"98{random.randint(10000000, 99999999)} (Kin)",
            chronic_conditions=m_type,
            assigned_asha_id=assigned_asha_id,
            created_at=now - datetime.timedelta(days=random.randint(10, 180))
        )
        patient_records.append(p)

    db.add_all(patient_users)
    db.commit()

    for u, p in zip(patient_users, patient_records):
        p.user_id = u.id
    db.add_all(patient_records)
    db.commit()

    # Pre-seed clinical encounters with exact vitals from dataset for each patient
    for idx, row in df.iterrows():
        p = patient_records[idx + 3] # Skip the three baseline demo patients (Ramesh, Sunita, Anita)
        doctor_name = row["Primary Care Doctor"]
        hub_hosp = row["Registered Hub Hospital"]
        vitals_raw = row["Last Update Vitals"]
        vitals = parse_vitals(vitals_raw)
        m_type = row["Monitoring Type"]

        doc_id = doc_map.get(doctor_name, 1)
        fac_id = hospital_map.get(hub_hosp, 1)

        enc = models.ClinicalEncounter(
            appointment_id=None,
            patient_id=p.id,
            doctor_id=doc_id,
            facility_id=fac_id,
            encounter_date=now - datetime.timedelta(days=random.randint(1, 14)),
            chief_complaints=f"Enrolled in {m_type}. Recent vitals: {vitals_raw}",
            clinical_notes=f"Clinical observation under {doctor_name} at {hub_hosp}. Protocol: {m_type}.",
            diagnosis=m_type,
            vital_bp=f"{int(vitals['bp_sys'])}/{int(vitals['bp_dia'])}",
            vital_pulse=int(vitals["hr"]),
            vital_temp=vitals["temp"],
            vital_spo2=int(vitals["spo2"]),
            clinician_risk_flag="HIGH_RISK" if (vitals["spo2"] < 96 or vitals["hb"] < 10.0) else "NORMAL"
        )
        encounters.append(enc)

        # Overdue check for High-Risk or Chronic Disease Mgmt
        if idx % 15 == 0:
            past_due = (now - datetime.timedelta(days=random.randint(2, 8))).strftime("%Y-%m-%d")
            fup = models.FollowUpPlan(
                encounter_id=None,
                patient_id=p.id,
                doctor_id=doc_id,
                facility_id=fac_id,
                due_date=past_due,
                instructions=f"Review vitals and adherence under {m_type}",
                status="OVERDUE",
                created_at=now - datetime.timedelta(days=30)
            )
            follow_ups.append(fup)

    db.add_all(encounters)
    db.commit()

    db.add_all(follow_ups)
    db.commit()

    for fup in follow_ups:
        pat = db.query(models.Patient).filter(models.Patient.id == fup.patient_id).first()
        t = models.HealthWorkerTask(
            patient_id=fup.patient_id,
            asha_worker_id=pat.assigned_asha_id if pat else kavita_id,
            follow_up_id=fup.id,
            task_type="MISSED_FOLLOW_UP",
            priority="HIGH",
            due_date=fup.due_date,
            status="OPEN",
            visit_notes=None,
            outcome=None,
            created_at=now - datetime.timedelta(days=2)
        )
        tasks.append(t)

    # Also seed Sunita Devi's overdue follow-up & task for Scenario D
    past_due_sunita = (now - datetime.timedelta(days=4)).strftime("%Y-%m-%d")
    overdue_sunita = models.FollowUpPlan(
        patient_id=p_sunita.id,
        doctor_id=1,
        facility_id=1,
        due_date=past_due_sunita,
        instructions="Diabetic glycemic monitoring & blood pressure check (30-day review).",
        status="OVERDUE",
        created_at=now - datetime.timedelta(days=34)
    )
    db.add(overdue_sunita)
    db.commit()

    task_sunita = models.HealthWorkerTask(
        patient_id=p_sunita.id,
        asha_worker_id=kavita_id,
        follow_up_id=overdue_sunita.id,
        task_type="MISSED_FOLLOW_UP",
        priority="HIGH",
        due_date=past_due_sunita,
        status="OPEN",
        visit_notes=None,
        outcome=None,
        created_at=now - datetime.timedelta(days=3)
    )
    db.add(task_sunita)
    db.add_all(tasks)
    db.commit()

    # Timeline event
    tl1 = models.CareTimelineEvent(
        patient_id=p_sunita.id,
        event_type="FOLLOW_UP",
        title="Scheduled Follow-up Review Missed",
        description=f"Patient Sunita Devi missed scheduled review on {past_due_sunita}. Automated missed-care trigger created task for ASHA worker Kavita Tai Patil.",
        facility_id=1,
        doctor_id=1,
        actor_name="SwasthyaSetu Continuity Engine",
        actor_role="SYSTEM",
        metadata_json='{"status": "OVERDUE", "triggered_escalation": true}',
        created_at=now - datetime.timedelta(days=3)
    )
    db.add(tl1)

    # Ramesh's household, consents, and a booked OPD visit so the doctor queue has a live case
    db.add_all([
        models.FamilyMember(patient_id=p_ramesh.id, full_name="Meena Kumar", relationship_type="SPOUSE", age=44, gender="Female", chronic_conditions="None"),
        models.FamilyMember(patient_id=p_ramesh.id, full_name="Aakash Kumar", relationship_type="CHILD", age=19, gender="Male", chronic_conditions="Asthma (Mild)"),
        models.ConsentRecord(patient_id=p_ramesh.id, granted_to_role="DOCTOR", granted_to_user_id=u_deshmukh.id, purpose="Consultation at Paud CHC (Dr. Anand Deshmukh)", status="GRANTED", valid_until=now + datetime.timedelta(days=180)),
        models.ConsentRecord(patient_id=p_ramesh.id, granted_to_role="ASHA", granted_to_user_id=kavita_id, purpose="Follow-up home visits (Kavita Tai Patil)", status="GRANTED", valid_until=now + datetime.timedelta(days=365)),
    ])
    db.add(models.SymptomIntake(
        patient_id=p_ramesh.id,
        raw_input="Chalne par seene mein halka bhaaripan aur thakaan, 2 din se.",
        language="hi",
        primary_complaint="Exertional chest heaviness and fatigue",
        duration_days=2,
        severity="MODERATE",
        red_flags_detected="None",
        emergency_triaged=False,
        triage_level="URGENT",
        ai_summary_for_doctor="TRIAGE [URGENT]: 48y male, known mild hypertension, reports chest heaviness on walking with fatigue for 2 days; no rest pain reported. ECG evaluation recommended at OPD today.",
        recommended_specialty="General Medicine",
        recommended_facility_type="Community Health Centre (CHC)",
        created_at=now - datetime.timedelta(hours=3)
    ))
    db.add(models.Appointment(
        appointment_code="APT-DEMO01",
        patient_id=p_ramesh.id,
        doctor_id=doc_deshmukh.id,
        facility_id=chc_paud.id,
        scheduled_date=datetime.date.today().isoformat(),
        scheduled_time="10:30 AM",
        consultation_type="IN_PERSON",
        status="BOOKED",
        reason="Exertional chest heaviness and fatigue",
        queue_token="T-1",
        is_simulated=True,
        created_at=now - datetime.timedelta(hours=2)
    ))
    db.add(models.CareTimelineEvent(
        patient_id=p_ramesh.id,
        event_type="APPOINTMENT",
        title="Appointment Confirmed (APT-DEMO01)",
        description=f"Token T-1 booked at Paud CHC with Dr. Anand Deshmukh for {datetime.date.today().isoformat()} 10:30 AM.",
        facility_id=chc_paud.id,
        doctor_id=doc_deshmukh.id,
        actor_name="Ramesh Kumar",
        actor_role="PATIENT",
        metadata_json='{"appointment_code": "APT-DEMO01", "token": "T-1"}',
        created_at=now - datetime.timedelta(hours=2)
    ))
    db.commit()

    # Initial audit
    audit = models.AuditEvent(
        user_id=admin_main.id,
        user_name="District Health Officer",
        role="SUPER_ADMIN",
        action="TRAINED_DATASET_SEEDED",
        resource_type="SYSTEM",
        resource_id="1000_PATIENTS",
        outcome="SUCCESS",
        ip_address="127.0.0.1",
        details_json=f'{{"total_patients": {len(patient_records)}, "total_facilities": {len(facility_records)}, "total_doctors": {len(doctor_records)}, "total_asha": {len(asha_users)}}}'
    )
    db.add(audit)
    db.commit()
    db.close()

    print(f"[OK] Database Seeded Successfully with {len(patient_records)} Patients, {len(facility_records)} Facilities, {len(doctor_records)} Doctors, and {len(asha_users)} ASHA Workers!")

if __name__ == "__main__":
    seed_trained_dataset()
