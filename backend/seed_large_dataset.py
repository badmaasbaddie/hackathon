"""
Large-Scale Synthetic Seed Generator for SwasthyaSetu AI
Populates:
- 10 Jila Prashashan (District Administration) Authorities
- 25 Regional Facilities across 10 Districts
- 100 ASHA Workers across rural catchments
- 200 Doctors across specialties & regional hospitals
- 1,000 Diverse Patients with varied disease profiles, ABHA IDs, follow-ups & appointments
"""

import random
import datetime
from database import engine, SessionLocal, Base
import models

def seed_large_dataset():
    print("Initializing large-scale Indian health workforce and patient dataset...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.datetime.now(datetime.timezone.utc)

    # ---------------- 1. DISTRICTS & JILA PRASHASHAN (10 AUTHORITIES) ----------------
    districts_data = [
        {"name": "Pune", "dho": "Dr. Rajesh Kulkarni", "title": "District Health Officer (DHO Pune)"},
        {"name": "Nagpur", "dho": "Dr. Sanjay Deshmukh", "title": "Civil Surgeon & DHO Nagpur"},
        {"name": "Nashik", "dho": "Dr. Kavita Gavit", "title": "Chief Medical Officer (CMO Nashik)"},
        {"name": "Thane", "dho": "Dr. Pradeep Sharma", "title": "District Health Administrator Thane"},
        {"name": "Satara", "dho": "Dr. Anand Shinde", "title": "District Health Officer (DHO Satara)"},
        {"name": "Chhatrapati Sambhajinagar", "dho": "Dr. Fatima Sheikh", "title": "DHO Sambhajinagar"},
        {"name": "Kolhapur", "dho": "Dr. Vikram Patil", "title": "Civil Surgeon Kolhapur"},
        {"name": "Solapur", "dho": "Dr. Rameshwar Waghmare", "title": "District Health Officer Solapur"},
        {"name": "Amravati", "dho": "Dr. Sunita Meshram", "title": "DHO Amravati Rural Division"},
        {"name": "Nanded", "dho": "Dr. Harpreet Singh", "title": "District Health Officer Nanded"}
    ]

    jila_users = []
    # Always include baseline admin_district for demo login
    admin_main = models.User(
        username="admin_district",
        email="dho.pune@gov.in",
        full_name="District Health Officer (DHO Pune)",
        role="SUPER_ADMIN",
        phone="020-26123456",
        village="Pune Headquarter"
    )
    jila_users.append(admin_main)

    for i, dist in enumerate(districts_data):
        uname = f"jila_prashashan_{i+1:02d}"
        if i == 0:
            user = admin_main
        else:
            user = models.User(
                username=uname,
                email=f"dho.{dist['name'].lower().replace(' ', '')}@swasthyasetu.gov.in",
                full_name=f"{dist['dho']} - {dist['title']}",
                role="SUPER_ADMIN",
                phone=f"98220{i:02d}1234",
                village=f"{dist['name']} Zilla Parishad"
            )
            jila_users.append(user)
    db.add_all(jila_users)
    db.commit()
    print(f"[OK] Added {len(jila_users)} Jila Prashashan Authorities.")

    # ---------------- 2. FACILITIES (25 ACROSS REGIONS) ----------------
    facilities = []
    facility_types = ["PHC", "CHC", "SUB_DISTRICT", "DISTRICT_HOSPITAL"]

    # Add core baseline facilities first
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
        last_verified_at=now - datetime.timedelta(minutes=15)
    )
    facilities.append(chc_paud)

    phc_pirangut = models.Facility(
        name="Pirangut Primary Health Centre (PHC)",
        facility_type="PHC",
        address="Ghotawade Phata, Pirangut",
        village_block="Mulshi",
        district="Pune",
        phone="020-22921122",
        emergency_contact="112",
        latitude=18.5110,
        longitude=73.6820,
        distance_km=11.8,
        travel_time_mins=24,
        operating_hours="OPD: 09:00 AM - 03:00 PM",
        is_open_now=True,
        is_simulated=True,
        last_verified_at=now - datetime.timedelta(hours=1)
    )
    facilities.append(phc_pirangut)

    dh_pune = models.Facility(
        name="Aundh District Hospital (DH), Pune",
        facility_type="DISTRICT_HOSPITAL",
        address="Sangvi-Aundh Link Road, Pune",
        village_block="Pune Urban",
        district="Pune",
        phone="020-27271234",
        emergency_contact="112",
        latitude=18.5793,
        longitude=73.8054,
        distance_km=26.5,
        travel_time_mins=48,
        operating_hours="24x7 Multi-Specialty Care",
        is_open_now=True,
        is_simulated=True,
        last_verified_at=now - datetime.timedelta(minutes=10)
    )
    facilities.append(dh_pune)

    # 22 more facilities across 10 districts
    district_names = [d["name"] for d in districts_data]
    blocks = ["Mulshi", "Haveli", "Baramati", "Shirur", "Hingna", "Katol", "Sinnar", "Niphad", "Kalyan", "Murbad", "Karad", "Wai", "Vaijapur", "Gangapur", "Karveer", "Panhala", "Pandharpur", "Barshi", "Achalpur", "Chandur", "Loha", "Degloor"]

    for idx in range(4, 26):
        dist_name = district_names[(idx - 4) % len(district_names)]
        f_type = facility_types[(idx - 4) % len(facility_types)]
        blk = blocks[(idx - 4) % len(blocks)]
        fac = models.Facility(
            name=f"{blk} {f_type} - {dist_name}",
            facility_type=f_type,
            address=f"Main Road, {blk}, District {dist_name}",
            village_block=blk,
            district=dist_name,
            phone=f"0{random.randint(20, 79)}-{random.randint(2200000, 2999999)}",
            emergency_contact="112",
            latitude=18.5 + (random.random() * 2.5),
            longitude=73.5 + (random.random() * 3.5),
            distance_km=round(random.uniform(5.0, 35.0), 1),
            travel_time_mins=random.randint(15, 60),
            operating_hours="24x7 Emergency / OPD 9am-3pm" if f_type in ["CHC", "DISTRICT_HOSPITAL"] else "OPD 9am-2pm",
            is_open_now=True,
            is_simulated=True,
            last_verified_at=now - datetime.timedelta(minutes=random.randint(5, 120))
        )
        facilities.append(fac)

    db.add_all(facilities)
    db.commit()
    print(f"[OK] Added {len(facilities)} Regional Healthcare Facilities.")

    # ---------------- 3. 100 ASHA WORKERS ----------------
    asha_first_names = [
        "Kavita", "Rekha", "Sunita", "Shobha", "Meena", "Savita", "Anita", "Geeta", "Urmila", "Lata",
        "Mangal", "Ranjana", "Usha", "Surekha", "Asha", "Pushpa", "Chhaya", "Suman", "Vandana", "Jyoti",
        "Pooja", "Seema", "Vidya", "Kiran", "Sheetal", "Sharda", "Kalpana", "Archana", "Manjula", "Sushila"
    ]
    asha_last_names = [
        "Patil", "Shinde", "Deshmukh", "Jadhav", "Pawar", "Kadam", "Chavan", "Bhosale", "Gaikwad", "More",
        "Wagh", "Kamble", "Sawant", "Thorat", "Salunkhe", "Mane", "Jagtap", "Mohite", "Ghate", "Kale"
    ]
    villages = [
        "Paud", "Pirangut", "Lavale", "Kamshet", "Khadakwasla", "Uruli Kanchan", "Wagholi", "Manchar",
        "Bhor", "Saswad", "Narayangaon", "Chakan", "Rajgurunagar", "Talegaon", "Lonavala", "Daund",
        "Indapur", "Walchandnagar", "Alandi", "Shirwal", "Khandala", "Panchgani", "Mahabaleshwar", "Satara Rural",
        "Baramati Rural", "Supa", "Morgaon", "Someshwar", "Malegaon Khurd", "Koregaon Bhima"
    ]

    asha_users = []
    # Primary ASHA worker for demo
    asha_main = models.User(
        username="asha_kavita",
        email="kavita.patil@asha.swasthyasetu.gov.in",
        full_name="Kavita Tai Patil (ASHA Worker)",
        role="ASHA",
        phone="9123456780",
        village="Paud"
    )
    asha_users.append(asha_main)

    for i in range(2, 101):
        first = asha_first_names[(i - 2) % len(asha_first_names)]
        last = asha_last_names[(i * 3) % len(asha_last_names)]
        vil = villages[(i - 2) % len(villages)]
        uname = f"asha_{i:03d}"
        user = models.User(
            username=uname,
            email=f"{first.lower()}.{last.lower()}{i}@asha.swasthyasetu.gov.in",
            full_name=f"{first} Tai {last} (ASHA-{i:03d})",
            role="ASHA",
            phone=f"91{random.randint(70000000, 99999999)}",
            village=vil
        )
        asha_users.append(user)

    db.add_all(asha_users)
    db.commit()
    print(f"[OK] Added {len(asha_users)} ASHA Health Workers with Indian rural credentials.")

    # ---------------- 4. 200 DOCTORS IN DIFFERENT REGIONS ----------------
    doc_first_names = [
        "Anand", "Sunita", "Ramesh", "Priya", "Santosh", "Ashok", "Manisha", "Deepak", "Rajendra", "Neha",
        "Suresh", "Pooja", "Vikram", "Sneha", "Manoj", "Prashant", "Anjali", "Milind", "Ganesh", "Archana",
        "Nitin", "Swati", "Mahesh", "Sheetal", "Kishore", "Pallavi", "Sachin", "Smita", "Ajit", "Shalini"
    ]
    doc_last_names = [
        "Deshmukh", "Joshi", "Kulkarni", "Patil", "Shinde", "Agarwal", "Bhatnagar", "Sen", "Nair", "Iyer",
        "Chakraborty", "Reddy", "Rao", "Gupta", "Verma", "Pandey", "Mishra", "Choudhury", "Yadav", "Malhotra"
    ]
    specialties = [
        "General Medicine", "Cardiology", "Obstetrics & Gynaecology", "Pediatrics", "Orthopedics",
        "Pulmonology", "Dermatology", "Ophthalmology", "ENT", "Psychiatry",
        "Endocrinology", "Nephrology", "General Surgery", "Emergency Medicine", "Community Medicine"
    ]
    qualifications = [
        "MBBS, MD (Medicine)", "MBBS, MS (General Surgery)", "MBBS, DGO", "MBBS, MD (Cardiology)",
        "MBBS, DCH (Pediatrics)", "MBBS, MS (Orthopedics)", "MBBS", "MBBS, MD (Pulmonary Medicine)",
        "MBBS, DNB (Internal Medicine)", "MBBS, MD (Community Medicine)"
    ]

    doctor_users = []
    doctor_records = []

    # Primary demo doctor
    doc_main_user = models.User(
        username="dr_deshmukh",
        email="dr.anand@gov.in",
        full_name="Dr. Anand Deshmukh",
        role="DOCTOR",
        phone="9822012345",
        village="Paud",
        facility_id=1
    )
    doctor_users.append(doc_main_user)

    doc_main = models.Doctor(
        user_id=None, # Will link
        facility_id=1,
        name="Dr. Anand Deshmukh",
        specialty="General Medicine",
        qualification="MBBS, MD (Internal Medicine)",
        experience_years=12,
        phone="9822012345",
        is_available_today=True,
        last_roster_update=now - datetime.timedelta(hours=1)
    )
    doctor_records.append(doc_main)

    for i in range(2, 201):
        first = doc_first_names[(i - 2) % len(doc_first_names)]
        last = doc_last_names[(i * 7) % len(doc_last_names)]
        spec = specialties[(i - 2) % len(specialties)]
        qual = qualifications[(i - 2) % len(qualifications)]
        fac = facilities[(i - 2) % len(facilities)]
        uname = f"dr_{i:03d}"

        u = models.User(
            username=uname,
            email=f"dr.{first.lower()}.{last.lower()}{i}@gov.in",
            full_name=f"Dr. {first} {last}",
            role="DOCTOR",
            phone=f"98{random.randint(10000000, 99999999)}",
            village=fac.village_block,
            facility_id=fac.id
        )
        doctor_users.append(u)

        d_record = models.Doctor(
            user_id=None,
            facility_id=fac.id,
            name=f"Dr. {first} {last}",
            specialty=spec,
            qualification=qual,
            experience_years=random.randint(3, 28),
            phone=u.phone,
            is_available_today=random.choice([True, True, True, False]),
            last_roster_update=now - datetime.timedelta(minutes=random.randint(10, 180))
        )
        doctor_records.append(d_record)

    db.add_all(doctor_users)
    db.commit()

    # Link user ids
    for u, d in zip(doctor_users, doctor_records):
        d.user_id = u.id
    db.add_all(doctor_records)
    db.commit()
    print(f"[OK] Added {len(doctor_records)} Doctors across diverse Indian regions and clinical specialties.")

    # ---------------- 5. STANDARD MEDICINES & INVENTORY ----------------
    med_para = models.Medicine(code="MED-PARA", generic_name="Paracetamol", brand_name="Crocin / Dolo", category="ANALGESIC", strength="500mg", dosage_form="TABLET")
    med_amlo = models.Medicine(code="MED-AMLO", generic_name="Amlodipine", brand_name="Amlip", category="ANTIHYPERTENSIVE", strength="5mg", dosage_form="TABLET")
    med_met = models.Medicine(code="MED-MET", generic_name="Metformin", brand_name="Glycomet", category="ANTIDIABETIC", strength="500mg", dosage_form="TABLET")
    med_amox = models.Medicine(code="MED-AMOX", generic_name="Amoxicillin", brand_name="Mox", category="ANTIBIOTIC", strength="500mg", dosage_form="CAPSULE")
    med_telm = models.Medicine(code="MED-TELM", generic_name="Telmisartan", brand_name="Telma", category="ANTIHYPERTENSIVE", strength="40mg", dosage_form="TABLET")
    med_ors = models.Medicine(code="MED-ORS", generic_name="Oral Rehydration Salts (ORS)", brand_name="Electral", category="ELECTROLYTE", strength="21.8g", dosage_form="SACHET")
    med_ator = models.Medicine(code="MED-ATOR", generic_name="Atorvastatin", brand_name="Atorva", category="LIPID_LOWERING", strength="10mg", dosage_form="TABLET")
    med_ifa = models.Medicine(code="MED-IFA", generic_name="Iron & Folic Acid", brand_name="IFA Red", category="NUTRITIONAL", strength="100mg+500mcg", dosage_form="TABLET")
    db.add_all([med_para, med_amlo, med_met, med_amox, med_telm, med_ors, med_ator, med_ifa])
    db.commit()

    # Seed inventories across all facilities
    inventories = []
    for fac in facilities:
        inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_para.id, medicine_name="Paracetamol 500mg", quantity_in_stock=random.randint(150, 1500), stock_status="IN_STOCK", last_verified_at=now))
        inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_met.id, medicine_name="Metformin 500mg", quantity_in_stock=random.randint(80, 800), stock_status="IN_STOCK", last_verified_at=now))
        inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_ors.id, medicine_name="Oral Rehydration Salts (ORS)", quantity_in_stock=random.randint(50, 500), stock_status="IN_STOCK", last_verified_at=now))
        
        # Amlodipine stockout at Paud CHC for Scenario C, in-stock elsewhere
        if fac.id == 1:
            inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_amlo.id, medicine_name="Amlodipine 5mg", quantity_in_stock=0, stock_status="OUT_OF_STOCK", last_verified_at=now))
        else:
            inventories.append(models.InventorySnapshot(facility_id=fac.id, medicine_id=med_amlo.id, medicine_name="Amlodipine 5mg", quantity_in_stock=random.randint(200, 1200), stock_status="IN_STOCK", last_verified_at=now))
    db.add_all(inventories)
    db.commit()
    print("[OK] Seeded verified regional dispensary inventories.")

    # ---------------- 6. 1,000 PATIENTS WITH DIVERSE DISEASES ----------------
    patient_first_names_m = [
        "Ramesh", "Rahul", "Suresh", "Santosh", "Vijay", "Anil", "Ganesh", "Mahesh", "Sachin", "Dattatray",
        "Ajay", "Sunil", "Prakash", "Rajesh", "Nitin", "Vikas", "Sanjay", "Deepak", "Manoj", "Pradeep",
        "Avinash", "Balasaheb", "Chandrakant", "Gorakh", "Jitendra", "Kailas", "Lakshman", "Pandurang", "Ramdas", "Tukaram"
    ]
    patient_first_names_f = [
        "Sunita", "Anita", "Meena", "Sangita", "Shobha", "Savita", "Rekha", "Usha", "Mangal", "Ranjana",
        "Asha", "Pushpa", "Chhaya", "Suman", "Vandana", "Jyoti", "Pooja", "Seema", "Vidya", "Kiran",
        "Sheetal", "Sharda", "Kalpana", "Archana", "Manjula", "Sushila", "Lata", "Rukmini", "Draupadi", "Radhabai"
    ]
    patient_last_names = [
        "Kumar", "Devi", "Shinde", "More", "Patil", "Jadhav", "Pawar", "Bhosale", "Kadam", "Chavan",
        "Gaikwad", "Wagh", "Kamble", "Sawant", "Thorat", "Salunkhe", "Mane", "Jagtap", "Mohite", "Ghate",
        "Kale", "Kulkarni", "Deshmukh", "Tambe", "Gawade", "Dumbre", "Bhegade", "Marathe", "Khanna", "Chauhan"
    ]

    disease_profiles = [
        {"cond": "Type 2 Diabetes Mellitus", "spec": "General Medicine", "urg": "ROUTINE", "test": "Fasting Blood Sugar (FBS)"},
        {"cond": "Essential Hypertension", "spec": "Cardiology", "urg": "ROUTINE", "test": "Electrocardiogram (ECG)"},
        {"cond": "Chronic Bronchial Asthma", "spec": "Pulmonology", "urg": "MODERATE", "test": "Chest X-Ray Digital"},
        {"cond": "Pulmonary Tuberculosis (DOTS Category 1)", "spec": "Pulmonology", "urg": "HIGH", "test": "Complete Blood Count (CBC)"},
        {"cond": "High Risk Antenatal Care (3rd Trimester)", "spec": "Obstetrics & Gynaecology", "urg": "HIGH", "test": "Ultrasound Abdomen (USG)"},
        {"cond": "Severe Iron Deficiency Anemia", "spec": "General Medicine", "urg": "MODERATE", "test": "Complete Blood Count (CBC)"},
        {"cond": "Bilateral Knee Osteoarthritis", "spec": "Orthopedics", "urg": "ROUTINE", "test": "X-Ray Knee"},
        {"cond": "Coronary Artery Disease (Post-PCI)", "spec": "Cardiology", "urg": "CRITICAL", "test": "Electrocardiogram (ECG)"},
        {"cond": "Chronic Kidney Disease Stage 3", "spec": "Nephrology", "urg": "HIGH", "test": "Serum Creatinine"},
        {"cond": "Primary Hypothyroidism", "spec": "Endocrinology", "urg": "ROUTINE", "test": "TSH Profile"},
        {"cond": "Acute Viral Dengue with Thrombocytopenia", "spec": "Emergency Medicine", "urg": "CRITICAL", "test": "Complete Blood Count (CBC)"},
        {"cond": "Gastroesophageal Reflux & Peptic Ulcer", "spec": "General Medicine", "urg": "ROUTINE", "test": "Ultrasound Abdomen (USG)"},
        {"cond": "Cerebrovascular Accident (Post-Stroke Rehabilitation)", "spec": "General Medicine", "urg": "HIGH", "test": "Routine Review"},
        {"cond": "Pediatric Severe Acute Malnutrition (SAM)", "spec": "Pediatrics", "urg": "HIGH", "test": "Growth Monitoring"},
        {"cond": "Senile Cataract (Bilateral)", "spec": "Ophthalmology", "urg": "ROUTINE", "test": "Visual Acuity Examination"}
    ]

    patients = []
    patient_users = []
    follow_up_plans = []
    health_worker_tasks = []
    appointments = []

    # 1. Ramesh Kumar (Patient #1, Baseline Demo)
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
        emergency_contact="9876543211 (Brother)",
        chronic_conditions="Hypertension (Mild)",
        assigned_asha_id=1,
        created_at=now - datetime.timedelta(days=45)
    )
    patients.append(p_ramesh)

    # 2. Sunita Devi (Patient #2, Scenario D Overdue Follow-up)
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
        emergency_contact="9823456780 (Son)",
        chronic_conditions="Type 2 Diabetes Mellitus, Hypertension",
        assigned_asha_id=1,
        created_at=now - datetime.timedelta(days=90)
    )
    patients.append(p_sunita)

    # 3. Rahul Shinde (Patient #3, Routine Flow)
    u_rahul = models.User(username="rahul", email="rahul.shinde@demo.swasthyasetu.gov.in", full_name="Rahul Shinde", role="PATIENT", phone="9765432109", village="Lavale")
    patient_users.append(u_rahul)
    p_rahul = models.Patient(
        user_id=None,
        abha_id="91-7721-3990-1123",
        name="Rahul Shinde",
        age=28,
        gender="Male",
        village="Lavale",
        block="Mulshi",
        district="Pune",
        phone="9765432109",
        blood_group="A+",
        emergency_contact="9765432100 (Father)",
        chronic_conditions="None",
        assigned_asha_id=1,
        created_at=now - datetime.timedelta(days=10)
    )
    patients.append(p_rahul)

    # 4. Anita More (Patient #4, Scenario G Unauthorized Catchment)
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
        assigned_asha_id=2, # Assigned to asha_002
        created_at=now - datetime.timedelta(days=20)
    )
    patients.append(p_anita)

    # Generate remaining 996 patients to reach total 1,000 patients!
    blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

    for i in range(5, 1001):
        is_female = (i % 2 == 0)
        first = patient_first_names_f[(i - 5) % len(patient_first_names_f)] if is_female else patient_first_names_m[(i - 5) % len(patient_first_names_m)]
        last = patient_last_names[(i * 11) % len(patient_last_names)]
        full_name = f"{first} {last}"
        age = random.randint(12, 82)
        gender = "Female" if is_female else "Male"
        vil = villages[(i - 5) % len(villages)]
        dist = district_names[(i - 5) % len(district_names)]
        cond_info = disease_profiles[(i - 5) % len(disease_profiles)]
        asha_idx = ((i - 5) % len(asha_users)) + 1
        
        # 14-digit ABHA ID formatted
        part1 = random.randint(10, 99)
        part2 = random.randint(1000, 9999)
        part3 = random.randint(1000, 9999)
        part4 = random.randint(1000, 9999)
        abha = f"{part1}-{part2}-{part3}-{part4}"

        uname = f"pat_{i:04d}"
        u = models.User(
            username=uname,
            email=f"{first.lower()}.{last.lower()}{i}@patient.swasthyasetu.gov.in",
            full_name=full_name,
            role="PATIENT",
            phone=f"9{random.randint(100000000, 999999999)}",
            village=vil
        )
        patient_users.append(u)

        p = models.Patient(
            user_id=None,
            abha_id=abha,
            name=full_name,
            age=age,
            gender=gender,
            village=vil,
            block="Rural Taluka",
            district=dist,
            phone=u.phone,
            blood_group=random.choice(blood_groups),
            emergency_contact=f"9{random.randint(100000000, 999999999)} (Kin)",
            chronic_conditions=cond_info["cond"],
            assigned_asha_id=asha_idx,
            created_at=now - datetime.timedelta(days=random.randint(5, 180))
        )
        patients.append(p)

    db.add_all(patient_users)
    db.commit()

    # Link patient user_ids
    for u, p in zip(patient_users, patients):
        p.user_id = u.id
    db.add_all(patients)
    db.commit()
    print(f"[OK] Added {len(patients)} Patients with unique ABHA IDs & clinical disease categories.")

    # ---------------- 7. SEED OVERDUE FOLLOW-UPS & ASHA TASKS ----------------
    # Sunita Devi overdue follow-up (Scenario D baseline)
    past_due_date = (now - datetime.timedelta(days=4)).strftime("%Y-%m-%d")
    overdue_sunita = models.FollowUpPlan(
        patient_id=p_sunita.id,
        doctor_id=1,
        facility_id=1,
        due_date=past_due_date,
        instructions="Diabetic glycemic monitoring & blood pressure check (30-day review).",
        status="OVERDUE",
        created_at=now - datetime.timedelta(days=34)
    )
    db.add(overdue_sunita)
    db.commit()

    task_sunita = models.HealthWorkerTask(
        patient_id=p_sunita.id,
        asha_worker_id=1,
        follow_up_id=overdue_sunita.id,
        task_type="MISSED_FOLLOW_UP",
        priority="HIGH",
        due_date=past_due_date,
        status="OPEN",
        visit_notes=None,
        outcome=None,
        created_at=now - datetime.timedelta(days=3)
    )
    db.add(task_sunita)

    # Generate additional realistic active & overdue follow-ups and tasks for ASHA workers
    for idx in range(10, 120, 5):
        pat = patients[idx]
        is_overdue = (idx % 2 == 0)
        due_d = (now - datetime.timedelta(days=random.randint(2, 10))).strftime("%Y-%m-%d") if is_overdue else (now + datetime.timedelta(days=random.randint(3, 14))).strftime("%Y-%m-%d")
        
        fup = models.FollowUpPlan(
            patient_id=pat.id,
            doctor_id=random.randint(1, min(50, len(doctor_records))),
            facility_id=random.randint(1, len(facilities)),
            due_date=due_d,
            instructions=f"Review for {pat.chronic_conditions}",
            status="OVERDUE" if is_overdue else "SCHEDULED",
            created_at=now - datetime.timedelta(days=25)
        )
        follow_up_plans.append(fup)

    db.add_all(follow_up_plans)
    db.commit()

    for fup in follow_up_plans:
        if fup.status == "OVERDUE":
            pat = db.query(models.Patient).filter(models.Patient.id == fup.patient_id).first()
            t = models.HealthWorkerTask(
                patient_id=fup.patient_id,
                asha_worker_id=pat.assigned_asha_id if pat else 1,
                follow_up_id=fup.id,
                task_type="MISSED_FOLLOW_UP",
                priority="HIGH",
                due_date=fup.due_date,
                status="OPEN",
                created_at=now - datetime.timedelta(days=2)
            )
            health_worker_tasks.append(t)

    db.add_all(health_worker_tasks)
    db.commit()
    print(f"[OK] Generated {len(follow_up_plans)} Follow-Up Plans and {len(health_worker_tasks) + 1} ASHA Field Tasks.")

    # ---------------- 8. INITIAL CARE TIMELINE & AUDIT LOG ----------------
    tl1 = models.CareTimelineEvent(
        patient_id=p_sunita.id,
        event_type="FOLLOW_UP",
        title="Scheduled Follow-up Review Missed",
        description=f"Patient Sunita Devi missed scheduled review on {past_due_date}. Automated missed-care trigger created task for ASHA worker Kavita Tai Patil.",
        facility_id=1,
        doctor_id=1,
        actor_name="SwasthyaSetu Continuity Engine",
        actor_role="SYSTEM",
        metadata_json='{"status": "OVERDUE", "triggered_escalation": true}',
        created_at=now - datetime.timedelta(days=3)
    )
    tl2 = models.CareTimelineEvent(
        patient_id=p_ramesh.id,
        event_type="APPOINTMENT",
        title="Routine Registration Completed",
        description="Patient Ramesh Kumar verified with ABHA 91-4829-1029-3849 under Paud sub-centre.",
        facility_id=1,
        actor_name="Kavita Tai Patil",
        actor_role="ASHA",
        metadata_json='{"verified": true}',
        created_at=now - datetime.timedelta(days=15)
    )
    db.add_all([tl1, tl2])

    audit1 = models.AuditEvent(
        user_id=admin_main.id,
        user_name="District Health Officer",
        role="SUPER_ADMIN",
        action="LARGE_DATABASE_SEEDED",
        resource_type="SYSTEM",
        resource_id="ALL_REGIONS",
        outcome="SUCCESS",
        ip_address="127.0.0.1",
        details_json=f'{{"total_asha": {len(asha_users)}, "total_doctors": {len(doctor_records)}, "total_jila_prashashan": {len(jila_users)}, "total_patients": {len(patients)}}}'
    )
    db.add(audit1)
    db.commit()
    db.close()
    print("\n=======================================================")
    print("SUCCESSFULLY SEEDED LARGE-SCALE HEALTH WORKFORCE & PATIENTS:")
    print(f"• 10 Jila Prashashan Authorities")
    print(f"• 25 Regional Healthcare Facilities (PHCs, CHCs, DH)")
    print(f"• 100 ASHA Community Health Workers")
    print(f"• 200 Doctors Across Specialties & Regions")
    print(f"• 1,000 Patients with Clinical Disease Profiles & ABHA IDs")
    print("=======================================================")

if __name__ == "__main__":
    seed_large_dataset()
