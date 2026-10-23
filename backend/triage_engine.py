"""
Deterministic Clinical Safety Screening & Care Triage Engine
Complies with clinical protocols: conservative emergency escalation,
immediate 112 emergency advice, multi-language detection (Hindi + English).

Runs BEFORE any language model is consulted, so an emergency is never delayed
or softened by generated text. Matching is word-boundary based and covers
English, romanised Hindi (Hinglish) and Devanagari script (voice input in
hi-IN returns Devanagari).
"""

import re
from typing import Dict, Any, List, Tuple

# Each emergency keyword maps to a category so advice matches the actual red flag.
EMERGENCY_KEYWORDS: Dict[str, List[str]] = {
    "CARDIAC": [
        "chest pain", "chest discomfort", "chest mein dard", "chest me dard", "chest mein severe pain",
        "seene mein dard", "seene me dard", "chhati me dard", "chhati mein dard", "pressure in chest",
        "heart attack", "dil ka daura",
        "सीने में दर्द", "सीने मे दर्द", "छाती में दर्द", "छाती मे दर्द", "सीने में भारीपन", "दिल का दौरा",
    ],
    "BREATHING": [
        "difficulty breathing", "severe breathlessness", "shortness of breath", "unable to breathe", "gasping",
        "saans phool rahi", "saans lene mein dikkat", "saans lene me dikkat", "saans nahi aa rahi",
        "सांस फूल रही", "साँस फूल रही", "सांस लेने में दिक्कत", "सांस लेने में तकलीफ", "साँस लेने में तकलीफ",
        "सांस नहीं आ रही", "सांस नहीं ले पा",
    ],
    "NEURO": [
        "stroke", "face drooping", "slurred speech", "paralysis", "sudden loss of vision", "unconscious",
        "seizure", "fits", "lakwa", "ek taraf kamzori", "behosh", "mirgi",
        "लकवा", "बेहोश", "दौरा पड़", "मिर्गी", "एक तरफ कमजोरी", "चेहरा टेढ़ा",
    ],
    "BLEEDING": [
        "severe bleeding", "uncontrolled bleeding", "blood vomiting", "vomiting blood",
        "khoon ki ulti", "bhaari khoon", "bahut khoon",
        "खून की उल्टी", "बहुत खून", "तेज खून",
    ],
    "OBSTETRIC": [
        "pregnancy bleeding", "bleeding in pregnancy", "severe labor pain before term", "garbh me dard",
        "garbhavastha me khoon", "गर्भावस्था में खून", "गर्भ में दर्द",
    ],
    "POISONING": [
        "poison", "snake bite", "saanp ne kaata", "zeher", "जहर", "सांप ने काटा", "साँप ने काटा",
    ],
}

URGENT_KEYWORDS = [
    "high fever", "tez bukhar", "severe stomach pain", "pet me tez dard", "pet mein tez dard",
    "continuous vomiting", "lagatar ulti", "severe dehydration", "dast", "diarrhoea", "diarrhea",
    "fracture", "haddi toot", "deep cut", "infection", "burn", "jal gaya",
    "तेज बुखार", "पेट में तेज दर्द", "लगातार उल्टी", "दस्त", "हड्डी टूट", "गहरा घाव", "जल गया",
]

EMERGENCY_TEXT = {
    "CARDIAC": {
        "en": ("Chest pain or pressure can be a heart emergency.", "Possible acute coronary syndrome", "Immediate ECG and vitals stabilisation recommended."),
        "hi": ("सीने में दर्द या भारीपन दिल की आपात स्थिति हो सकती है।", "Possible acute coronary syndrome", "Immediate ECG and vitals stabilisation recommended."),
    },
    "BREATHING": {
        "en": ("Severe breathing difficulty needs urgent oxygen and assessment.", "Acute respiratory distress", "Check SpO2, give oxygen, assess airway."),
        "hi": ("सांस लेने में गंभीर तकलीफ में तुरंत ऑक्सीजन और जांच ज़रूरी है।", "Acute respiratory distress", "Check SpO2, give oxygen, assess airway."),
    },
    "NEURO": {
        "en": ("Signs like sudden weakness, slurred speech, fits or fainting may mean a stroke or seizure. Every minute matters.", "Possible stroke / seizure / altered consciousness", "Note time of onset; urgent neuro assessment and glucose check."),
        "hi": ("अचानक कमजोरी, बोलने में दिक्कत, दौरा या बेहोशी लकवा या मिर्गी का संकेत हो सकता है। हर मिनट कीमती है।", "Possible stroke / seizure / altered consciousness", "Note time of onset; urgent neuro assessment and glucose check."),
    },
    "BLEEDING": {
        "en": ("Heavy bleeding or vomiting blood is a medical emergency.", "Significant haemorrhage", "Control bleeding, IV access, assess haemodynamics."),
        "hi": ("बहुत खून बहना या खून की उल्टी आपात स्थिति है।", "Significant haemorrhage", "Control bleeding, IV access, assess haemodynamics."),
    },
    "OBSTETRIC": {
        "en": ("Bleeding or severe pain in pregnancy needs immediate care at a facility with obstetric services.", "Obstetric emergency", "Refer to facility with emergency obstetric care."),
        "hi": ("गर्भावस्था में खून आना या तेज दर्द होने पर तुरंत प्रसूति सुविधा वाले अस्पताल जाएं।", "Obstetric emergency", "Refer to facility with emergency obstetric care."),
    },
    "POISONING": {
        "en": ("Poisoning or snake bite needs emergency treatment immediately. Keep the person still and calm.", "Poisoning / envenomation", "Urgent antidote / anti-snake venom assessment."),
        "hi": ("जहर या सांप के काटने पर तुरंत आपातकालीन इलाज ज़रूरी है। व्यक्ति को शांत और स्थिर रखें।", "Poisoning / envenomation", "Urgent antidote / anti-snake venom assessment."),
    },
}


def _matches(text: str, keyword: str) -> bool:
    # Devanagari has no reliable \b semantics, so use plain containment there.
    if re.search(r"[ऀ-ॿ]", keyword):
        return keyword in text
    return re.search(r"(?<![a-z])" + re.escape(keyword) + r"(?![a-z])", text) is not None


def find_red_flags(text: str) -> List[Tuple[str, str]]:
    text_lower = text.lower()
    return [
        (category, kw)
        for category, kws in EMERGENCY_KEYWORDS.items()
        for kw in kws
        if _matches(text_lower, kw)
    ]


def analyze_symptoms(text: str, language: str = "hi", duration_days: int = 2) -> Dict[str, Any]:
    lang = "hi" if language == "hi" else "en"
    text_lower = text.lower()

    flag_hits = find_red_flags(text)
    red_flags = [kw for _, kw in flag_hits]
    categories = list(dict.fromkeys(cat for cat, _ in flag_hits))
    is_emergency = len(red_flags) > 0

    urgent_flags = [] if is_emergency else [kw for kw in URGENT_KEYWORDS if _matches(text_lower, kw)]
    is_urgent = len(urgent_flags) > 0

    if is_emergency:
        triage_level = "EMERGENCY"
        severity = "CRITICAL"
        rec_specialty = "Emergency Medicine"
        rec_facility = "District Hospital or 24x7 CHC"
        explanations = [EMERGENCY_TEXT[c][lang][0] for c in categories]
        impressions = [EMERGENCY_TEXT[c][lang][1] for c in categories]
        actions = [EMERGENCY_TEXT[c][lang][2] for c in categories]

        if lang == "hi":
            emergency_advice = (
                "चेतावनी: आपके लक्षण गंभीर हो सकते हैं। कृपया तुरंत 112 (या एम्बुलेंस 108) डायल करें या बिना देरी किए "
                "निकटतम आपातकालीन अस्पताल पहुंचें। " + " ".join(explanations)
            )
            primary_complaint = "आपातकालीन लक्षण - तुरंत चिकित्सा सहायता लें"
        else:
            emergency_advice = (
                "WARNING: Your symptoms may indicate a medical emergency. Call 112 (ambulance 108) now or go to the "
                "nearest emergency-ready hospital without delay. " + " ".join(explanations)
            )
            primary_complaint = "Emergency symptoms - seek immediate care"
        patient_exp = " ".join(explanations)

        doctor_summary = (
            f"TRIAGE ALERT [EMERGENCY]: Red flags detected ({', '.join(red_flags)}). "
            f"Reported duration: {duration_days} day(s). Working concern: {'; '.join(impressions)}. "
            f"{' '.join(actions)}"
        )

    elif is_urgent:
        triage_level = "URGENT"
        severity = "MODERATE_HIGH"
        rec_specialty = "General Medicine"
        rec_facility = "Community Health Centre (CHC)"

        if lang == "hi":
            emergency_advice = "कृपया आज ही डॉक्टर से परामर्श लें। लक्षण बढ़ें तो 112 पर कॉल करें।"
            patient_exp = "लक्षण तीव्र हैं और आज ही डॉक्टर द्वारा जांच आवश्यक है ताकि स्थिति बिगड़े नहीं।"
            primary_complaint = "तीव्र लक्षण - आज ही डॉक्टर को दिखाएं"
        else:
            emergency_advice = "Please see a doctor today. If symptoms get worse, call 112."
            patient_exp = "These acute symptoms should be examined by a doctor today to prevent complications."
            primary_complaint = "Acute symptoms - same-day consultation advised"

        doctor_summary = (
            f"TRIAGE ALERT [URGENT]: Moderate-high symptoms reported ({', '.join(urgent_flags)}). "
            f"Duration: {duration_days} day(s). Recommended OPD consult today."
        )

    else:
        triage_level = "ROUTINE"
        severity = "MILD_MODERATE"
        rec_specialty = "General Medicine / Family Medicine"
        rec_facility = "Primary Health Centre (PHC) / Sub-Centre"
        emergency_advice = None

        if lang == "hi":
            patient_exp = "आपके लक्षण प्राथमिक स्वास्थ्य केंद्र (PHC/CHC) में डॉक्टर को दिखाने योग्य हैं। नियमित ओपीडी अपॉइंटमेंट बुक करें।"
            primary_complaint = "सामान्य स्वास्थ्य समस्या / परामर्श"
        else:
            patient_exp = "Your symptoms can be addressed at your local Primary Health Centre (PHC/CHC). You may book a routine consultation."
            primary_complaint = "Routine General Health Consultation"

        doctor_summary = (
            f"TRIAGE [ROUTINE]: Non-critical complaints. Duration: {duration_days} day(s). "
            f"Chief concern: {text[:160]}. Standard outpatient consultation recommended."
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
