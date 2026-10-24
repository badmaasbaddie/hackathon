"""
Deterministic Clinical Safety Screening & Care Triage Engine
Complies with clinical protocols: conservative emergency escalation,
immediate 112 emergency advice, multi-language detection (Hindi + English).

Runs BEFORE any language model is consulted, so an emergency is never delayed
or softened by generated text. Matching is word-boundary based and covers
English, romanised Hindi (Hinglish), Hindi and Marathi in Devanagari script
(voice input in hi-IN / mr-IN returns Devanagari).
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
        "छातीत दुखत", "छातीत दुखणे", "छातीत वेदना", "छातीत कळ", "हृदयविकाराचा झटका", "chhatit dukhat",
    ],
    "BREATHING": [
        "difficulty breathing", "severe breathlessness", "shortness of breath", "unable to breathe", "gasping",
        "saans phool rahi", "saans lene mein dikkat", "saans lene me dikkat", "saans nahi aa rahi",
        "सांस फूल रही", "साँस फूल रही", "सांस लेने में दिक्कत", "सांस लेने में तकलीफ", "साँस लेने में तकलीफ",
        "सांस नहीं आ रही", "सांस नहीं ले पा",
        "श्वास घ्यायला त्रास", "श्वास घेण्यास त्रास", "श्वास घेता येत नाही", "दम लागत", "धाप लागत", "dam lagat",
    ],
    "NEURO": [
        "stroke", "face drooping", "slurred speech", "paralysis", "sudden loss of vision", "unconscious",
        "seizure", "fits", "lakwa", "ek taraf kamzori", "behosh", "mirgi",
        "लकवा", "बेहोश", "दौरा पड़", "मिर्गी", "एक तरफ कमजोरी", "चेहरा टेढ़ा",
        "अर्धांगवायू", "पक्षाघात", "फिट येत", "फिट आली", "आकडी", "बोलताना अडखळ", "beshuddh",
    ],
    "BLEEDING": [
        "severe bleeding", "uncontrolled bleeding", "blood vomiting", "vomiting blood",
        "khoon ki ulti", "bhaari khoon", "bahut khoon",
        "खून की उल्टी", "बहुत खून", "तेज खून",
        "रक्ताची उलटी", "खूप रक्तस्राव", "खूप रक्तस्त्राव", "रक्त थांबत नाही",
    ],
    "OBSTETRIC": [
        "pregnancy bleeding", "bleeding in pregnancy", "severe labor pain before term", "garbh me dard",
        "garbhavastha me khoon", "गर्भावस्था में खून", "गर्भ में दर्द",
        "गरोदरपणात रक्तस्राव", "गरोदरपणात रक्त", "गर्भारपणात रक्त",
    ],
    "POISONING": [
        "poison", "snake bite", "saanp ne kaata", "zeher", "जहर", "सांप ने काटा", "साँप ने काटा",
        "साप चावला", "सर्पदंश", "विषबाधा", "विष प्या", "विष घेतले",
    ],
}

URGENT_KEYWORDS = [
    "high fever", "tez bukhar", "severe stomach pain", "pet me tez dard", "pet mein tez dard",
    "continuous vomiting", "lagatar ulti", "severe dehydration", "dast", "diarrhoea", "diarrhea",
    "fracture", "haddi toot", "deep cut", "infection", "burn", "jal gaya",
    "तेज बुखार", "पेट में तेज दर्द", "लगातार उल्टी", "दस्त", "हड्डी टूट", "गहरा घाव", "जल गया",
    "खूप ताप", "जास्त ताप", "पोटात खूप दुख", "सतत उलट्या", "जुलाब", "हाड मोडले", "भाजले",
]

EMERGENCY_TEXT = {
    "CARDIAC": {
        "en": ("Chest pain or pressure can be a heart emergency.", "Possible acute coronary syndrome", "Immediate ECG and vitals stabilisation recommended."),
        "hi": ("सीने में दर्द या भारीपन दिल की आपात स्थिति हो सकती है।", "Possible acute coronary syndrome", "Immediate ECG and vitals stabilisation recommended."),
        "mr": ("छातीत दुखणे किंवा दाब जाणवणे ही हृदयाची आपत्कालीन स्थिती असू शकते.", "Possible acute coronary syndrome", "Immediate ECG and vitals stabilisation recommended."),
    },
    "BREATHING": {
        "en": ("Severe breathing difficulty needs urgent oxygen and assessment.", "Acute respiratory distress", "Check SpO2, give oxygen, assess airway."),
        "hi": ("सांस लेने में गंभीर तकलीफ में तुरंत ऑक्सीजन और जांच ज़रूरी है।", "Acute respiratory distress", "Check SpO2, give oxygen, assess airway."),
        "mr": ("श्वास घेण्यास तीव्र त्रास होत असल्यास त्वरित ऑक्सिजन आणि तपासणी आवश्यक आहे.", "Acute respiratory distress", "Check SpO2, give oxygen, assess airway."),
    },
    "NEURO": {
        "en": ("Signs like sudden weakness, slurred speech, fits or fainting may mean a stroke or seizure. Every minute matters.", "Possible stroke / seizure / altered consciousness", "Note time of onset; urgent neuro assessment and glucose check."),
        "hi": ("अचानक कमजोरी, बोलने में दिक्कत, दौरा या बेहोशी लकवा या मिर्गी का संकेत हो सकता है। हर मिनट कीमती है।", "Possible stroke / seizure / altered consciousness", "Note time of onset; urgent neuro assessment and glucose check."),
        "mr": ("अचानक अशक्तपणा, बोलताना अडखळणे, फिट येणे किंवा बेशुद्ध होणे हे पक्षाघात किंवा फिटचे लक्षण असू शकते. प्रत्येक मिनिट महत्त्वाचा आहे.", "Possible stroke / seizure / altered consciousness", "Note time of onset; urgent neuro assessment and glucose check."),
    },
    "BLEEDING": {
        "en": ("Heavy bleeding or vomiting blood is a medical emergency.", "Significant haemorrhage", "Control bleeding, IV access, assess haemodynamics."),
        "hi": ("बहुत खून बहना या खून की उल्टी आपात स्थिति है।", "Significant haemorrhage", "Control bleeding, IV access, assess haemodynamics."),
        "mr": ("जास्त रक्तस्राव किंवा रक्ताची उलटी ही आपत्कालीन स्थिती आहे.", "Significant haemorrhage", "Control bleeding, IV access, assess haemodynamics."),
    },
    "OBSTETRIC": {
        "en": ("Bleeding or severe pain in pregnancy needs immediate care at a facility with obstetric services.", "Obstetric emergency", "Refer to facility with emergency obstetric care."),
        "hi": ("गर्भावस्था में खून आना या तेज दर्द होने पर तुरंत प्रसूति सुविधा वाले अस्पताल जाएं।", "Obstetric emergency", "Refer to facility with emergency obstetric care."),
        "mr": ("गरोदरपणात रक्तस्राव किंवा तीव्र वेदना झाल्यास त्वरित प्रसूती सुविधा असलेल्या रुग्णालयात जा.", "Obstetric emergency", "Refer to facility with emergency obstetric care."),
    },
    "POISONING": {
        "en": ("Poisoning or snake bite needs emergency treatment immediately. Keep the person still and calm.", "Poisoning / envenomation", "Urgent antidote / anti-snake venom assessment."),
        "hi": ("जहर या सांप के काटने पर तुरंत आपातकालीन इलाज ज़रूरी है। व्यक्ति को शांत और स्थिर रखें।", "Poisoning / envenomation", "Urgent antidote / anti-snake venom assessment."),
        "mr": ("विषबाधा किंवा साप चावल्यास त्वरित आपत्कालीन उपचार आवश्यक आहेत. व्यक्तीला शांत आणि स्थिर ठेवा.", "Poisoning / envenomation", "Urgent antidote / anti-snake venom assessment."),
    },
}


# Speech recognition often confuses similar Devanagari sounds (छ/च, घ/ग, vowel signs,
# doubled letters). For multi-word Devanagari phrases we therefore also compare a
# consonant "skeleton". Single words are matched exactly, so a short word like "दस्त"
# (diarrhoea) cannot match "दोस्त" (friend).
_ASPIRATE = str.maketrans({
    "ख": "क", "घ": "ग", "छ": "च", "झ": "ज", "ठ": "ट", "ढ": "ड",
    "थ": "त", "ध": "द", "फ": "प", "भ": "ब", "ण": "न", "ष": "श", "ऴ": "ळ",
})
_DROP = re.compile("[\u093c\u0901\u0902\u0903\u093e-\u094d\u0962\u0963\u0905-\u0914.,!?।]")


def _skeleton(text: str) -> str:
    out = _DROP.sub("", text.translate(_ASPIRATE))
    out = re.sub(r"(.)\1+", r"\1", out)  # collapse doubled letters
    return re.sub(r"\s+", " ", out).strip()


def _is_devanagari(text: str) -> bool:
    return re.search("[\u0900-\u097f]", text) is not None


def _matches(text: str, keyword: str) -> bool:
    # Devanagari has no reliable \b semantics, so use plain containment there.
    if _is_devanagari(keyword):
        if keyword in text:
            return True
        return " " in keyword.strip() and _skeleton(keyword) in _skeleton(text)
    return re.search(r"(?<![a-z])" + re.escape(keyword) + r"(?![a-z])", text) is not None


def find_red_flags(text: str) -> List[Tuple[str, str]]:
    text_lower = text.lower()
    return [
        (category, kw)
        for category, kws in EMERGENCY_KEYWORDS.items()
        for kw in kws
        if _matches(text_lower, kw)
    ]


PATIENT_TEXT = {
    "en": {
        "emergency_advice": "WARNING: Your symptoms may indicate a medical emergency. Call 112 (ambulance 108) now or go to the nearest emergency-ready hospital without delay. ",
        "emergency_complaint": "Emergency symptoms - seek immediate care",
        "urgent_advice": "Please see a doctor today. If symptoms get worse, call 112.",
        "urgent_explanation": "These acute symptoms should be examined by a doctor today to prevent complications.",
        "urgent_complaint": "Acute symptoms - same-day consultation advised",
        "routine_explanation": "Your symptoms can be addressed at your local Primary Health Centre (PHC/CHC). You may book a routine consultation.",
        "routine_complaint": "Routine General Health Consultation",
    },
    "hi": {
        "emergency_advice": "चेतावनी: आपके लक्षण गंभीर हो सकते हैं। कृपया तुरंत 112 (या एम्बुलेंस 108) डायल करें या बिना देरी किए निकटतम आपातकालीन अस्पताल पहुंचें। ",
        "emergency_complaint": "आपातकालीन लक्षण - तुरंत चिकित्सा सहायता लें",
        "urgent_advice": "कृपया आज ही डॉक्टर से परामर्श लें। लक्षण बढ़ें तो 112 पर कॉल करें।",
        "urgent_explanation": "लक्षण तीव्र हैं और आज ही डॉक्टर द्वारा जांच आवश्यक है ताकि स्थिति बिगड़े नहीं।",
        "urgent_complaint": "तीव्र लक्षण - आज ही डॉक्टर को दिखाएं",
        "routine_explanation": "आपके लक्षण प्राथमिक स्वास्थ्य केंद्र (PHC/CHC) में डॉक्टर को दिखाने योग्य हैं। नियमित ओपीडी अपॉइंटमेंट बुक करें।",
        "routine_complaint": "सामान्य स्वास्थ्य समस्या / परामर्श",
    },
    "mr": {
        "emergency_advice": "इशारा: तुमची लक्षणे गंभीर असू शकतात. कृपया त्वरित 112 (किंवा रुग्णवाहिका 108) वर कॉल करा किंवा उशीर न करता जवळच्या आपत्कालीन रुग्णालयात जा. ",
        "emergency_complaint": "आपत्कालीन लक्षणे - त्वरित वैद्यकीय मदत घ्या",
        "urgent_advice": "कृपया आजच डॉक्टरांना दाखवा. लक्षणे वाढल्यास 112 वर कॉल करा.",
        "urgent_explanation": "लक्षणे तीव्र आहेत आणि स्थिती बिघडू नये म्हणून आजच डॉक्टरांकडून तपासणी आवश्यक आहे.",
        "urgent_complaint": "तीव्र लक्षणे - आजच डॉक्टरांना दाखवा",
        "routine_explanation": "तुमची लक्षणे प्राथमिक आरोग्य केंद्रात (PHC/CHC) डॉक्टरांना दाखवता येतील. नियमित ओपीडी अपॉइंटमेंट बुक करा.",
        "routine_complaint": "सामान्य आरोग्य समस्या / सल्ला",
    },
}


def analyze_symptoms(text: str, language: str = "hi", duration_days: int = 2) -> Dict[str, Any]:
    lang = language if language in PATIENT_TEXT else "en"
    t = PATIENT_TEXT[lang]
    text_lower = text.lower()

    flag_hits = find_red_flags(text)
    red_flags = list(dict.fromkeys(kw for _, kw in flag_hits))
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
        impressions = [EMERGENCY_TEXT[c]["en"][1] for c in categories]
        actions = [EMERGENCY_TEXT[c]["en"][2] for c in categories]
        emergency_advice = t["emergency_advice"] + " ".join(explanations)
        primary_complaint = t["emergency_complaint"]
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
        emergency_advice = t["urgent_advice"]
        patient_exp = t["urgent_explanation"]
        primary_complaint = t["urgent_complaint"]
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
        patient_exp = t["routine_explanation"]
        primary_complaint = t["routine_complaint"]
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
