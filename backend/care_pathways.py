"""
Care pathways learned from the 100 synthetic case reviews
(data/case_reviews_synthetic.json, from SwasthyaSetu_AI_100_Synthetic_Deceased_Patient_Reports.pdf).

What is taken from the reports: for each of the 10 conditions, the facility, specialist and
test it needed, plus the distances, delays and access barriers in the reviews.
What is NOT used: the medicine column (random per record, e.g. insulin for heart attack)
and the patient demographics (inconsistent). No statistical model is trained: every
condition has a single templated symptom sentence, so a classifier would only memorise it.

At runtime the module recognises which condition pattern a patient's description fits,
and checks which nearby facility actually has the required services and a matching
specialist on duty - the gap behind the "delayed referral / imaging / specialist
unavailable" barriers in the reviews.
"""

import json
import os
import statistics
from collections import Counter
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

import models
from triage_engine import _matches

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "case_reviews_synthetic.json")

FEVER = ["fever", "bukhar", "बुखार", "ताप"]
COUGH = ["cough", "khansi", "खांसी", "खोकला"]
BREATHING = ["respiratory distress", "difficulty breathing", "breathing difficulty", "breathless", "breathlessness",
             "shortness of breath", "saans", "सांस", "साँस", "श्वास", "दम लागत", "धाप"]

# Patient-language patterns. A condition matches if ANY pattern matches; a pattern matches
# if EVERY group in it has at least one keyword present.
CONDITIONS: Dict[str, Dict] = {
    "Acute myocardial infarction": {
        "key": "AMI", "name": {"en": "Possible heart attack", "hi": "संभावित दिल का दौरा", "mr": "संभाव्य हृदयविकाराचा झटका"},
        "patterns": [[["chest pain", "chest discomfort", "pressure in chest", "seene mein dard", "chest mein", "सीने में दर्द",
                       "सीने में भारीपन", "छाती में दर्द", "छातीत दुखत", "छातीत वेदना", "heart attack", "दिल का दौरा"]]],
        "services": ["Electrocardiogram (ECG)", "Troponin test"], "specialists": ["cardio"],
    },
    "Stroke": {
        "key": "STROKE", "name": {"en": "Possible stroke", "hi": "संभावित लकवा (स्ट्रोक)", "mr": "संभाव्य पक्षाघात (स्ट्रोक)"},
        "patterns": [[["sudden weakness", "speech difficulty", "difficulty speaking", "slurred speech", "face drooping",
                       "weakness on one side", "paralysis", "stroke", "lakwa", "achanak kamzori", "bolne mein dikkat",
                       "लकवा", "अचानक कमजोरी", "बोलने में दिक्कत", "एक तरफ कमजोरी", "अर्धांगवायू", "पक्षाघात",
                       "अचानक अशक्तपणा", "बोलता येत नाही", "बोलण्यास त्रास"]]],
        "services": ["CT Brain"], "specialists": ["neuro"],
    },
    "Severe pneumonia": {
        "key": "PNEUMONIA", "name": {"en": "Possible severe pneumonia", "hi": "संभावित गंभीर निमोनिया", "mr": "संभाव्य गंभीर न्यूमोनिया"},
        "patterns": [[FEVER + COUGH, BREATHING]],
        "services": ["Chest X-Ray Digital"], "specialists": [],
    },
    "Severe anemia": {
        "key": "ANEMIA", "name": {"en": "Possible severe anaemia", "hi": "संभावित गंभीर खून की कमी", "mr": "संभाव्य तीव्र रक्तक्षय"},
        "patterns": [[["anemia", "anaemia", "khoon ki kami", "खून की कमी", "रक्त कमी", "रक्तक्षय"]],
                     [["weakness", "kamzori", "कमजोरी", "अशक्तपणा"], ["dizziness", "chakkar", "चक्कर"] + BREATHING]],
        "services": ["Complete Blood Count (CBC)", "Blood bank / transfusion"], "specialists": [],
    },
    "Severe sepsis": {
        "key": "SEPSIS", "name": {"en": "Possible sepsis", "hi": "संभावित सेप्सिस (गंभीर संक्रमण)", "mr": "संभाव्य सेप्सिस (गंभीर संसर्ग)"},
        "patterns": [[FEVER, ["confusion", "confused", "low blood pressure", "low bp", "very low bp", "cold and clammy", "behosh",
                              "बेहोश", "भ्रम", "बीपी बहुत कम", "गोंधळलेले", "गोंधळलेला", "गोंधळलेली", "रक्तदाब खूप कमी"]],
                     [["sepsis"]]],
        "services": ["Complete Blood Count (CBC)", "Lactate test", "ICU beds"], "specialists": ["critical", "emergency"],
    },
    "Eclampsia": {
        "key": "ECLAMPSIA", "name": {"en": "Possible eclampsia (pregnancy emergency)", "hi": "संभावित एक्लेम्पसिया (गर्भावस्था आपात)", "mr": "संभाव्य एक्लॅम्पसिया (गरोदरपणातील आपत्काल)"},
        "patterns": [[["pregnant", "pregnancy", "garbh", "गर्भवती", "गर्भावस्था", "गरोदर"],
                      ["seizure", "seizures", "fits", "convulsion", "very high bp", "high bp", "दौरे", "दौरा", "झटके", "फिट",
                       "बीपी", "रक्तदाब", "blurred vision", "धुंधला"]]],
        "services": ["Emergency obstetric care (EmOC)"], "specialists": ["obstetric", "maternal", "gynae"],
    },
    "Postpartum hemorrhage": {
        "key": "PPH", "name": {"en": "Possible bleeding after delivery (PPH)", "hi": "संभावित प्रसव के बाद रक्तस्राव", "mr": "संभाव्य प्रसूतीनंतर रक्तस्राव"},
        "patterns": [[["delivery", "after birth", "postpartum", "डिलीवरी", "प्रसव", "प्रसूती", "बाळंतपण"],
                      ["bleeding", "khoon", "खून", "रक्तस्राव", "रक्त"]]],
        "services": ["Emergency obstetric care (EmOC)", "Blood bank / transfusion"], "specialists": ["obstetric", "maternal", "gynae"],
    },
    "Severe malaria": {
        "key": "MALARIA", "name": {"en": "Possible severe malaria", "hi": "संभावित गंभीर मलेरिया", "mr": "संभाव्य गंभीर मलेरिया"},
        "patterns": [[FEVER, ["chills", "shivering", "thand", "ठंड", "कंपकंपी", "थंडी", "हुडहुडी"]], [["malaria", "मलेरिया"]]],
        "services": ["Malaria test", "Complete Blood Count (CBC)"], "specialists": [],
    },
    "TB complication": {
        "key": "TB", "name": {"en": "Possible tuberculosis (TB)", "hi": "संभावित टीबी", "mr": "संभाव्य क्षयरोग (टीबी)"},
        "patterns": [[COUGH, ["weight loss", "wajan kam", "वजन कम", "वजन कमी", "two weeks", "2 weeks", "do hafte", "दो हफ्ते",
                              "night sweats", "blood in cough", "खांसी में खून", "persistent", "लगातार", "सतत"]],
                     [["tuberculosis", "टीबी", "क्षयरोग"]]],
        "services": ["Chest X-Ray Digital", "TB sputum test"], "specialists": [],
    },
    "Diabetic emergency": {
        "key": "DKA", "name": {"en": "Possible diabetic emergency", "hi": "संभावित मधुमेह आपात स्थिति", "mr": "संभाव्य मधुमेह आपत्कालीन स्थिती"},
        "patterns": [[["sugar", "शुगर", "साखर", "diabetes", "diabetic", "madhumeh", "मधुमेह"],
                      ["very high", "bahut zyada", "bahut badh", "बहुत ज़्यादा", "बहुत बढ़", "खूप वाढ", "खूप जास्त",
                       "vomiting", "ulti", "उल्टी", "उलट्या", "drowsy", "सुस्ती"]]],
        "services": ["Fasting Blood Sugar (FBS)", "Electrolyte panel"], "specialists": [],
    },
}


def _load_reviews() -> Dict[str, Dict]:
    data = json.load(open(DATA_FILE, encoding="utf-8"))
    by_disease: Dict[str, List[Dict]] = {}
    for case in data["cases"]:
        by_disease.setdefault(case["disease"], []).append(case)
    out = {}
    for disease, cases in by_disease.items():
        first = cases[0]
        barriers = Counter(c["barrier"] for c in cases).most_common()
        out[disease] = {
            "cases": len(cases),
            "needs_facility": first["facility"],
            "needs_specialist": first["specialist"],
            "needs_tests": first["test"],
            "median_distance_km": statistics.median(c["distance_km"] for c in cases),
            "median_delay_hrs": statistics.median(c["delay_hrs"] for c in cases),
            "main_barrier": barriers[0][0],
        }
    return out


REVIEWS = _load_reviews()
NOTICE = json.load(open(DATA_FILE, encoding="utf-8"))["notice"]


def match_conditions(text: str) -> List[str]:
    t = text.lower()
    found = []
    for disease, cond in CONDITIONS.items():
        for pattern in cond["patterns"]:
            if all(any(_matches(t, kw) for kw in group) for group in pattern):
                found.append(disease)
                break
    return found


def _facility_gaps(db: Session, facility: models.Facility, cond: Dict) -> List[str]:
    services = {s.name: s.is_available for s in db.query(models.FacilityService).filter(models.FacilityService.facility_id == facility.id)}
    missing = [name for name in cond["services"] if not services.get(name)]
    if cond["specialists"]:
        doctors = db.query(models.Doctor).filter(models.Doctor.facility_id == facility.id, models.Doctor.is_available_today == True).all()
        if not any(any(sp in d.specialty.lower() for sp in cond["specialists"]) for d in doctors):
            missing.append("Specialist on duty: " + "/".join(s.capitalize() for s in cond["specialists"]))
    return missing


def pathways_for(db: Session, text: str, district: Optional[str], language: str) -> List[Dict]:
    """Which condition patterns fit, what they need, and where to go."""
    lang = language if language in ("hi", "mr", "en") else "en"
    facilities = db.query(models.Facility).filter(models.Facility.district == district).order_by(models.Facility.distance_km).all() if district else []
    if not facilities:
        facilities = db.query(models.Facility).order_by(models.Facility.distance_km).all()

    results = []
    for disease in match_conditions(text):
        cond = CONDITIONS[disease]
        review = REVIEWS.get(disease, {})
        gaps = [(f, _facility_gaps(db, f, cond)) for f in facilities]
        nearest, nearest_missing = gaps[0] if gaps else (None, [])
        ready = next(((f, m) for f, m in gaps if not m), None)

        def fac_out(f):
            return {"id": f.id, "name": f.name, "facility_type": f.facility_type, "distance_km": f.distance_km,
                    "travel_time_mins": f.travel_time_mins, "phone": f.phone} if f else None

        results.append({
            "condition": disease,
            "condition_key": cond["key"],
            "label": cond["name"][lang],
            "needs_facility": review.get("needs_facility"),
            "needs_specialist": review.get("needs_specialist"),
            "needs_tests": review.get("needs_tests"),
            "required_services": cond["services"],
            "recommended_facility": fac_out(ready[0]) if ready else None,
            "nearest_facility": fac_out(nearest),
            "nearest_facility_missing": nearest_missing,
            "case_reviews": {
                "cases": review.get("cases", 0),
                "median_distance_km": review.get("median_distance_km"),
                "median_delay_hrs": review.get("median_delay_hrs"),
                "main_barrier": review.get("main_barrier"),
            },
        })
    return results


BARRIER_RESPONSES = [
    ("blood service", "Blood bank availability is listed per facility, so patients are sent where blood is available."),
    ("icu", "ICU beds are listed per facility (live bed counts are a later phase)."),
    ("bed unavailable", "Facilities update their services; emergency routing prefers facilities that can admit."),
    ("imaging", "Each facility's tests (CT, X-ray, ultrasound) are visible before the patient travels."),
    ("specialist", "The live doctor roster shows where the needed specialist is on duty today."),
    ("diagnostic delay", "Danger signs are screened at the first message; required tests are named up front."),
    ("medicine access", "Medicine stock is tracked per facility and prescriptions warn when it is out of stock."),
    ("referral", "Emergency signs trigger 112/108 advice at once and point to the nearest facility that can treat the condition."),
]


def review_summary(db: Session) -> Dict:
    """District view: what the 100 synthetic reviews show, and how ready our facilities are."""
    data = json.load(open(DATA_FILE, encoding="utf-8"))
    cases = data["cases"]
    facilities = db.query(models.Facility).all()
    conditions = []
    for disease, review in REVIEWS.items():
        cond = CONDITIONS[disease]
        ready = [f for f in facilities if not _facility_gaps(db, f, cond)]
        conditions.append({
            "condition": disease,
            "label": cond["name"]["en"],
            **review,
            "facilities_ready": len(ready),
            "facilities_total": len(facilities),
            "ready_facility_names": [f.name for f in ready][:4],
        })
    barrier_parts = Counter()
    for c in cases:
        for part in c["barrier"].split("/"):
            barrier_parts[part.strip().lower()] += 1
    barriers = []
    for part, count in barrier_parts.most_common():
        response = next((r for key, r in BARRIER_RESPONSES if key in part), None)
        barriers.append({"barrier": part, "cases": count, "how_swasthyasetu_helps": response})
    return {
        "notice": data["notice"],
        "excluded_fields": data["excluded_fields"],
        "total_cases": len(cases),
        "median_distance_km": statistics.median(c["distance_km"] for c in cases),
        "median_delay_hrs": statistics.median(c["delay_hrs"] for c in cases),
        "conditions": conditions,
        "barriers": barriers,
    }
