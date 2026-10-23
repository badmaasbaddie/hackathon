"""
Deterministic Clinical Safety Screening & Care Triage Engine
Complies with clinical protocols: conservative emergency escalation,
immediate 112 emergency advice, multi-language detection (Hindi + English).
"""

from typing import Dict, Any, List

EMERGENCY_KEYWORDS = [
    # Cardiac / Chest pain
    "chest pain", "chest discomfort", "seene mein dard", "seene me dard", "chhati me dard", 
    "chhati mein dard", "pressure in chest", "heart attack", "dil ka daura",
    # Breathing / Respiratory distress
    "difficulty breathing", "severe breathlessness", "saans phool rahi hai", 
    "saans lene mein dikkat", "saans nahi aa rahi", "gasping", "unable to breathe",
    # Neurological / Stroke
    "stroke", "face drooping", "slurred speech", "paralysis", "lakwa", 
    "ek taraf kamzori", "sudden loss of vision", "behosh", "unconscious", "fits", "daura",
    # Severe hemorrhage / Trauma
    "severe bleeding", "blood vomiting", "khoon ki ulti", "bhaari khoon", "uncontrolled bleeding",
    # Obstetric emergency
    "pregnancy bleeding", "garbh me dard", "severe labor pain before term"
]

URGENT_KEYWORDS = [
    "high fever", "tez bukhar", "severe stomach pain", "pet me tez dard",
    "continuous vomiting", "lagatar ulti", "severe dehydration", "dast",
    "fracture", "haddi toot gayi", "deep cut", "infection"
]

def analyze_symptoms(text: str, language: str = "hi", duration_days: int = 2) -> Dict[str, Any]:
    text_lower = text.lower()
    
    red_flags = []
    for kw in EMERGENCY_KEYWORDS:
        if kw in text_lower:
            red_flags.append(kw)
            
    is_emergency = len(red_flags) > 0
    
    urgent_flags = []
    if not is_emergency:
        for kw in URGENT_KEYWORDS:
            if kw in text_lower:
                urgent_flags.append(kw)
    
    is_urgent = len(urgent_flags) > 0
    
    if is_emergency:
        triage_level = "EMERGENCY"
        severity = "CRITICAL"
        rec_specialty = "Emergency Medicine / Cardiology"
        rec_facility = "District Hospital or 24x7 CHC"
        
        if language == "hi":
            emergency_advice = (
                "चेतावनी: आपके लक्षण गंभीर हो सकते हैं। कृपया तुरंत 112 डायल करें या बिना देरी किए निकटतम आपातकालीन अस्पताल पहुंचें। "
                "यह लक्षण संभावित हृदय या सांस की आपातकालीन स्थिति का संकेत हो सकते हैं।"
            )
            patient_exp = (
                "सीने में असहजता या सांस लेने में भारीपन एक आपातकालीन संकेत हो सकता है। तुरंत चिकित्सा सहायता लें।"
            )
            primary_complaint = "गंभीर सीने में बेचैनी / सांस लेने में तकलीफ (आपातकालीन)"
        else:
            emergency_advice = (
                "WARNING: Your reported symptoms indicate a potential medical emergency. "
                "Please call 112 immediately or proceed to the nearest emergency-ready hospital (CHC / District Hospital) without delay."
            )
            patient_exp = (
                "Chest discomfort or severe breathing difficulty requires immediate in-person clinical assessment with ECG."
            )
            primary_complaint = "Severe Chest Discomfort / Acute Respiratory Distress (Emergency)"
            
        doctor_summary = (
            f"TRIAGE ALERT [EMERGENCY]: Patient presented with acute concerning symptoms ({', '.join(red_flags)}). "
            f"Duration: {duration_days} days. High suspicion of acute coronary syndrome or critical cardiopulmonary compromise. "
            f"Immediate ECG and vitals stabilization recommended."
        )

    elif is_urgent:
        triage_level = "URGENT"
        severity = "MODERATE_HIGH"
        rec_specialty = "General Medicine"
        rec_facility = "Community Health Centre (CHC)"
        
        if language == "hi":
            emergency_advice = "कृपया आज ही डॉक्टर से परामर्श लें।"
            patient_exp = "लक्षण तीव्र हैं और समय पर डॉक्टर द्वारा जांच आवश्यक है ताकि स्थिति बिगड़े नहीं।"
            primary_complaint = "तीव्र लक्षण / बुखार या पेट दर्द"
        else:
            emergency_advice = "Please visit a doctor today for clinical examination."
            patient_exp = "These acute symptoms warrant clinical evaluation today to prevent complications."
            primary_complaint = "Acute High Fever / Severe Abdominal Distress"
            
        doctor_summary = (
            f"TRIAGE ALERT [URGENT]: Patient presented with acute moderate-high symptoms ({', '.join(urgent_flags)}). "
            f"Duration: {duration_days} days. Recommended OPD consult today."
        )

    else:
        triage_level = "ROUTINE"
        severity = "MILD_MODERATE"
        rec_specialty = "General Medicine / Family Medicine"
        rec_facility = "Primary Health Centre (PHC) / Sub-Centre"
        
        if language == "hi":
            emergency_advice = None
            patient_exp = "आपके लक्षण सामान्य प्राथमिक स्वास्थ्य केंद्र (PHC) में डॉक्टर को दिखाने योग्य हैं। नियमित ओपीडी अपॉइंटमेंट बुक करें।"
            primary_complaint = "सामान्य स्वास्थ्य समस्या / परामर्श"
        else:
            emergency_advice = None
            patient_exp = "Your symptoms can be addressed at your local Primary Health Centre (PHC). You may book a routine consultation."
            primary_complaint = "Routine General Health Consultation"
            
        doctor_summary = (
            f"TRIAGE [ROUTINE]: Patient reports non-critical complaints. Duration: {duration_days} days. "
            f"Chief concern: {text[:100]}. Recommended standard outpatient consultation."
        )

    return {
        "primary_complaint": primary_complaint,
        "severity": severity,
        "is_emergency": is_emergency,
        "triage_level": triage_level,
        "red_flags": red_flags if is_emergency else urgent_flags,
        "emergency_advice": emergency_advice,
        "emergency_number": "112",
        "recommended_specialty": rec_specialty,
        "recommended_facility_type": rec_facility,
        "ai_doctor_summary": doctor_summary,
        "explanation_patient": patient_exp,
        "is_simulated_ai": True
    }
