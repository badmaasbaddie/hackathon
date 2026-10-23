"""
SwasthyaSetu AI - Machine Learning Model Training & Inference Engine
Trained on 1,000 Indian Patient Monitoring Records (Hub Hospitals, Doctors, ASHA Workers, Vitals)
"""

import os
import re
import json
import datetime
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, accuracy_score

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models_trained")
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "patients_dataset.csv")
MODEL_FILE = os.path.join(MODEL_DIR, "triage_classifier.joblib")
INFO_FILE = os.path.join(MODEL_DIR, "dataset_summary.json")

def parse_patient_demographics(val: str):
    """Parses 'Ram Sharma (33/M)' -> Name: Ram Sharma, Age: 33, Gender: M"""
    m = re.search(r"^(.*?)\s*\(\s*(\d+)\s*/\s*([MFmf])\s*\)", str(val).strip())
    if m:
        return m.group(1).strip(), int(m.group(2)), m.group(3).upper()
    return str(val).strip(), 40, "M"

def parse_vitals(vitals_str: str):
    """
    Parses varied vitals strings:
    - 'BP: 128/83, HR: 66' -> bp_sys=128, bp_dia=83, hr=66
    - 'Hb: 11.8, Wt: 67kg' -> hb=11.8, wt=67
    - 'SpO2: 99%, Temp: 98.2' -> spo2=99, temp=98.2
    """
    res = {
        "bp_sys": 120.0,
        "bp_dia": 80.0,
        "hr": 76.0,
        "hb": 11.5,
        "wt": 62.0,
        "spo2": 98.0,
        "temp": 98.4
    }
    s = str(vitals_str)
    
    bp_m = re.search(r"BP:\s*(\d+)\s*/\s*(\d+)", s, re.IGNORECASE)
    if bp_m:
        res["bp_sys"] = float(bp_m.group(1))
        res["bp_dia"] = float(bp_m.group(2))
        
    hr_m = re.search(r"HR:\s*(\d+)", s, re.IGNORECASE)
    if hr_m:
        res["hr"] = float(hr_m.group(1))
        
    hb_m = re.search(r"Hb:\s*([\d\.]+)", s, re.IGNORECASE)
    if hb_m:
        res["hb"] = float(hb_m.group(1))
        
    wt_m = re.search(r"Wt:\s*([\d\.]+)", s, re.IGNORECASE)
    if wt_m:
        res["wt"] = float(wt_m.group(1))
        
    spo2_m = re.search(r"SpO2:\s*([\d\.]+)", s, re.IGNORECASE)
    if spo2_m:
        res["spo2"] = float(spo2_m.group(1))
        
    temp_m = re.search(r"Temp:\s*([\d\.]+)", s, re.IGNORECASE)
    if temp_m:
        res["temp"] = float(temp_m.group(1))
        
    return res

def train_model():
    """Trains the Care Pathway & Risk Prediction Model on the 1000 Patient Dataset."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} records from {DATA_PATH}")

    # Extract clean columns
    names, ages, genders = [], [], []
    vitals_list = []

    for _, row in df.iterrows():
        name, age, gender = parse_patient_demographics(row["Name / Age / Gender"])
        names.append(name)
        ages.append(age)
        genders.append(gender)
        vitals_list.append(parse_vitals(row["Last Update Vitals"]))

    df["Clean_Name"] = names
    df["Age"] = ages
    df["Gender"] = genders

    vitals_df = pd.DataFrame(vitals_list)
    for col in vitals_df.columns:
        df[col] = vitals_df[col]

    # Target variable: Monitoring Type
    # Values: 'Daily SMS / Weekly Visit', 'High-Risk Maternal Care', 'Chronic Disease Mgmt', 'Post-Op Connected Care'
    X = df[[
        "Age", "Gender", "Village Name", "Registered Hub Hospital",
        "bp_sys", "bp_dia", "hr", "hb", "wt", "spo2", "temp"
    ]]
    y = df["Monitoring Type"]

    categorical_features = ["Gender", "Village Name", "Registered Hub Hospital"]
    numeric_features = ["Age", "bp_sys", "bp_dia", "hr", "hb", "wt", "spo2", "temp"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )

    clf = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    # Save model and summary
    joblib.dump(clf, MODEL_FILE)

    summary = {
        "status": "TRAINED",
        "dataset_size": len(df),
        "test_accuracy": round(float(acc) * 100, 2),
        "classes": list(clf.classes_),
        "hospitals_count": int(df["Registered Hub Hospital"].nunique()),
        "hospitals": list(df["Registered Hub Hospital"].unique()),
        "doctors_count": int(df["Primary Care Doctor"].nunique()),
        "doctors": list(df["Primary Care Doctor"].unique()),
        "asha_workers_count": int(df["Assigned ASHA Worker"].nunique()),
        "villages_count": int(df["Village Name"].nunique()),
        "villages": list(df["Village Name"].unique()),
        "metrics": {
            "accuracy": round(float(acc), 4),
            "macro_avg_f1": round(float(report["macro avg"]["f1-score"]), 4)
        },
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    with open(INFO_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Model trained successfully! Accuracy: {summary['test_accuracy']}%")
    return summary

def predict_care_pathway(data: dict):
    """
    Inference endpoint: takes patient features and returns:
    - Predicted Monitoring Type
    - Confidence score
    - Clinical Risk Assessment
    - Recommended Hospital & Doctor
    """
    if not os.path.exists(MODEL_FILE):
        train_model()

    clf = joblib.load(MODEL_FILE)

    # Prepare single-row DataFrame
    vitals = parse_vitals(data.get("vitals", ""))
    row = {
        "Age": int(data.get("age", 35)),
        "Gender": str(data.get("gender", "F")).upper(),
        "Village Name": str(data.get("village", "Mohanlalganj")),
        "Registered Hub Hospital": str(data.get("hub_hospital", "Apollo Medics Lucknow")),
        "bp_sys": float(data.get("bp_sys", vitals["bp_sys"])),
        "bp_dia": float(data.get("bp_dia", vitals["bp_dia"])),
        "hr": float(data.get("hr", vitals["hr"])),
        "hb": float(data.get("hb", vitals["hb"])),
        "wt": float(data.get("wt", vitals["wt"])),
        "spo2": float(data.get("spo2", vitals["spo2"])),
        "temp": float(data.get("temp", vitals["temp"]))
    }
    sample_df = pd.DataFrame([row])
    pred = clf.predict(sample_df)[0]
    probs = clf.predict_proba(sample_df)[0]
    confidence = float(np.max(probs))

    # Risk Scoring Rule
    risk_level = "LOW"
    risk_flags = []
    if row["spo2"] < 96:
        risk_level = "HIGH"
        risk_flags.append(f"Low oxygen saturation: {row['spo2']}%")
    if row["temp"] > 99.0:
        risk_level = "HIGH"
        risk_flags.append(f"Elevated temperature: {row['temp']}°F")
    if row["hb"] < 10.0 and pred == "High-Risk Maternal Care":
        risk_level = "CRITICAL"
        risk_flags.append(f"Severe gestational anemia: Hb {row['hb']} g/dL")
    if row["bp_sys"] > 135 or row["bp_dia"] > 88:
        risk_flags.append(f"Hypertensive range BP: {int(row['bp_sys'])}/{int(row['bp_dia'])}")
        if risk_level != "CRITICAL":
            risk_level = "MODERATE"

    return {
        "predicted_monitoring_type": pred,
        "confidence_pct": round(confidence * 100, 1),
        "clinical_risk_level": risk_level,
        "risk_flags": risk_flags,
        "recommended_doctor": data.get("doctor", "Dr. Meera Jha"),
        "recommended_hospital": row["Registered Hub Hospital"],
        "assigned_village": row["Village Name"],
        "model_version": "RandomForest-v1.0 (Trained on 1,000 Indian Patient Records)"
    }

if __name__ == "__main__":
    train_model()
