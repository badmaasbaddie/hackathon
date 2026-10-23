"""
Approved healthcare reference material for the SwasthyaSetu AI assistant.

These are short, conservative self-care and navigation notes written for the
demo, summarising widely published public-health guidance (MoHFW / NHM
programme material, WHO patient leaflets). They are the ONLY medical content
the assistant is allowed to ground its answers in. Before a real deployment
each entry must be reviewed and signed off by a qualified clinician.

Retrieval is a simple keyword-overlap scorer: small, deterministic and easy to
audit, which suits an MVP. It can be swapped for embeddings later without
changing the assistant interface.
"""

import re
from typing import List, Dict

REFERENCE_DOCS: List[Dict] = [
    {
        "id": "REF-EMERGENCY-01",
        "title": "Emergency warning signs - when to call 112 / 108",
        "source": "Adapted from MoHFW emergency care guidance (demo summary)",
        "keywords": ["emergency", "chest", "breath", "saans", "unconscious", "behosh", "stroke", "lakwa", "bleeding", "khoon", "fits", "seizure", "112", "108", "ambulance"],
        "text": "Chest pain or pressure, severe breathlessness, sudden weakness of one side of the body, slurred speech, fits, fainting, heavy bleeding, vomiting blood, poisoning or snake bite are emergencies. Call 112 (or 108 for ambulance) immediately and go to the nearest 24x7 CHC or District Hospital. Do not wait for an OPD appointment and do not drive yourself if you feel faint.",
    },
    {
        "id": "REF-FEVER-01",
        "title": "Fever: home care and when to see a doctor",
        "source": "Adapted from NHM fever / vector-borne disease patient guidance (demo summary)",
        "keywords": ["fever", "bukhar", "temperature", "badan dard", "body pain", "chills", "thand", "malaria", "dengue", "बुखार"],
        "text": "Rest, drink plenty of fluids (water, ORS, soups) and use paracetamol only as advised on the pack or by a health worker. See a doctor the same day if fever is above 102°F (39°C), lasts more than 2 days, comes with rash, bleeding gums, severe headache, stiff neck, confusion, or in a child under 5, a pregnant woman or an elderly person. Fever in malaria/dengue areas needs a blood test at the PHC/CHC.",
    },
    {
        "id": "REF-DIARRHOEA-01",
        "title": "Diarrhoea and dehydration: ORS and zinc",
        "source": "Adapted from NHM Intensified Diarrhoea Control guidance (demo summary)",
        "keywords": ["diarrhoea", "diarrhea", "dast", "loose motion", "vomiting", "ulti", "dehydration", "ors", "दस्त", "उल्टी"],
        "text": "Start ORS early: one packet in one litre of clean drinking water, sip frequently after every loose stool. Children with diarrhoea should also get zinc for 14 days as advised by the ASHA/ANM. Continue feeding and breastfeeding. Go to the PHC/CHC the same day if there is blood in stool, very little urine, sunken eyes, unable to drink, or continuous vomiting.",
    },
    {
        "id": "REF-HTN-01",
        "title": "High blood pressure (hypertension): routine care",
        "source": "Adapted from NPCDCS / NP-NCD hypertension guidance (demo summary)",
        "keywords": ["bp", "blood pressure", "hypertension", "amlodipine", "telmisartan", "headache", "sar dard", "namak", "salt"],
        "text": "Take BP medicines every day at the same time, even when you feel well; do not stop them without asking your doctor. Reduce salt, avoid tobacco and alcohol, walk 30 minutes a day. Get BP checked at least monthly at the sub-centre/PHC or by the ASHA. Severe headache with blurred vision, chest pain or weakness is an emergency.",
    },
    {
        "id": "REF-DM-01",
        "title": "Diabetes: daily care and follow-up",
        "source": "Adapted from NP-NCD diabetes guidance (demo summary)",
        "keywords": ["diabetes", "sugar", "madhumeh", "metformin", "insulin", "glucose", "शुगर", "मधुमेह"],
        "text": "Take diabetes medicines as prescribed and keep follow-up visits to check blood sugar and HbA1c. Eat regular meals with less sugar and refined flour, stay active and check your feet daily for cuts. Very high thirst with drowsiness, or sweating, shaking and confusion (low sugar) need urgent medical help.",
    },
    {
        "id": "REF-ANC-01",
        "title": "Pregnancy care (ANC) and danger signs",
        "source": "Adapted from MoHFW Mother & Child Protection guidance (demo summary)",
        "keywords": ["pregnant", "pregnancy", "garbh", "anc", "maternal", "delivery", "iron", "ifa", "anaemia", "anemia", "khoon ki kami", "गर्भ"],
        "text": "A pregnant woman should have at least four antenatal check-ups, take iron-folic acid and calcium as advised, and plan an institutional delivery. Danger signs - bleeding, severe headache, blurred vision, fits, swelling of face/hands, high fever, reduced baby movement or water leaking - need immediate travel to a facility with obstetric care (call 108/102).",
    },
    {
        "id": "REF-CHILD-01",
        "title": "Child health and immunisation",
        "source": "Adapted from Universal Immunisation Programme guidance (demo summary)",
        "keywords": ["child", "baby", "bachcha", "vaccine", "teeka", "immunisation", "immunization", "बच्चा", "टीका"],
        "text": "Follow the immunisation card and ask the ASHA/ANM about the next due vaccine; vaccines are free at government facilities. A child who cannot drink or breastfeed, vomits everything, has fits, is very sleepy, or has fast or difficult breathing needs a doctor immediately.",
    },
    {
        "id": "REF-COUGH-01",
        "title": "Cough, cold and TB screening",
        "source": "Adapted from National TB Elimination Programme guidance (demo summary)",
        "keywords": ["cough", "khansi", "cold", "sardi", "zukam", "tb", "tuberculosis", "balgam", "खांसी", "सर्दी"],
        "text": "Common cold usually improves in a week with rest, warm fluids and steam. A cough lasting more than 2 weeks, cough with blood, weight loss, night sweats or evening fever should be tested for TB at the PHC/CHC - testing and treatment are free. Breathlessness at rest is an emergency.",
    },
    {
        "id": "REF-FOLLOWUP-01",
        "title": "Why follow-up visits matter",
        "source": "SwasthyaSetu continuity-of-care protocol (demo)",
        "keywords": ["follow", "follow-up", "review", "reminder", "missed", "appointment", "checkup", "dobara"],
        "text": "Follow-up visits let the doctor check whether treatment is working and adjust medicines. If you cannot travel on the due date, tell your ASHA worker - she can arrange a home check or help you reach the CHC. SwasthyaSetu sends SMS reminders before each follow-up.",
    },
    {
        "id": "REF-MEDS-01",
        "title": "Using medicines safely",
        "source": "Adapted from MoHFW rational drug use guidance (demo summary)",
        "keywords": ["medicine", "dawai", "dawa", "tablet", "dose", "antibiotic", "painkiller", "side effect", "दवा"],
        "text": "Take medicines only as prescribed and finish the full course of antibiotics. Do not share prescription medicines or buy antibiotics without a prescription. If a medicine is out of stock at your facility, ask the doctor or pharmacist for the nearest facility that has it - do not substitute on your own.",
    },
]


STOPWORDS = {"a", "an", "and", "the", "to", "of", "in", "on", "for", "is", "it", "i", "my", "me", "what", "when",
             "how", "do", "should", "can", "with", "from", "since", "have", "has", "hai", "ho", "se", "ka", "ki", "ke",
             "mein", "me", "aur", "kya", "care", "see", "doctor"}


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+|[ऀ-ॿ]+", text.lower())) - STOPWORDS


def retrieve(query: str, k: int = 3) -> List[Dict]:
    """Return the k most relevant reference documents for the query."""
    q = query.lower()
    q_tokens = _tokens(query)
    scored = []
    for doc in REFERENCE_DOCS:
        score = 0
        for kw in doc["keywords"]:
            if " " in kw or "-" in kw:
                score += 2 if kw in q else 0
            elif kw in q_tokens or (re.search(r"[ऀ-ॿ]", kw) and kw in q):
                score += 2
        if score > 0:
            score += len(q_tokens & _tokens(doc["title"]))
            scored.append((score, doc))
    scored.sort(key=lambda s: -s[0])
    return [d for _, d in scored[:k]]


# Marathi search terms and short patient-language summaries. The summaries are
# used for the deterministic demo answer when no LLM is configured; like the
# English entries they must be clinically reviewed before real use.
LOCALIZED: Dict[str, Dict] = {
    "REF-EMERGENCY-01": {
        "keywords": ["छातीत", "श्वास", "बेशुद्ध", "अर्धांगवायू", "रक्तस्राव", "रुग्णवाहिका", "आपत्कालीन"],
        "hi": "सीने में दर्द, सांस की गंभीर तकलीफ, अचानक कमजोरी, बोलने में दिक्कत, दौरा, बेहोशी या बहुत खून बहना आपात स्थिति है। तुरंत 112 या 108 पर कॉल करें और नज़दीकी 24x7 अस्पताल जाएं।",
        "mr": "छातीत दुखणे, श्वास घेण्यास तीव्र त्रास, अचानक अशक्तपणा, बोलताना अडखळणे, फिट, बेशुद्धी किंवा जास्त रक्तस्राव ही आपत्कालीन स्थिती आहे. त्वरित 112 किंवा 108 वर कॉल करा आणि जवळच्या 24x7 रुग्णालयात जा.",
    },
    "REF-FEVER-01": {
        "keywords": ["ताप", "अंगदुखी", "थंडी", "हिवताप", "डेंग्यू"],
        "hi": "आराम करें, खूब पानी और ORS पिएं। पैरासिटामोल केवल पैकेट या स्वास्थ्य कार्यकर्ता की सलाह के अनुसार लें। बुखार 2 दिन से ज़्यादा रहे, बहुत तेज़ हो, या चकत्ते, खून आना, तेज़ सिरदर्द हो तो उसी दिन डॉक्टर को दिखाएं।",
        "mr": "विश्रांती घ्या, भरपूर पाणी आणि ORS प्या. पॅरासिटामॉल फक्त पाकिटावरील किंवा आरोग्य कर्मचाऱ्याच्या सल्ल्यानुसार घ्या. ताप 2 दिवसांपेक्षा जास्त राहिल्यास, खूप जास्त असल्यास, किंवा पुरळ, रक्तस्राव, तीव्र डोकेदुखी असल्यास त्याच दिवशी डॉक्टरांना दाखवा.",
    },
    "REF-DIARRHOEA-01": {
        "keywords": ["जुलाब", "अतिसार", "उलटी", "उलट्या", "निर्जलीकरण"],
        "hi": "जल्दी ORS शुरू करें: एक पैकेट एक लीटर साफ़ पानी में घोलें और हर दस्त के बाद घूंट-घूंट पिलाएं। बच्चों को ज़िंक भी दें। मल में खून, पेशाब बहुत कम, या लगातार उल्टी हो तो उसी दिन PHC/CHC जाएं।",
        "mr": "लवकर ORS सुरू करा: एक पाकीट एक लिटर स्वच्छ पाण्यात मिसळा आणि प्रत्येक जुलाबानंतर थोडे थोडे प्या. मुलांना झिंकही द्या. शौचात रक्त, लघवी खूप कमी, किंवा सतत उलट्या होत असल्यास त्याच दिवशी PHC/CHC मध्ये जा.",
    },
    "REF-HTN-01": {
        "keywords": ["रक्तदाब", "बीपी", "मीठ", "डोकेदुखी"],
        "hi": "बीपी की दवा रोज़ एक ही समय पर लें, ठीक लगने पर भी डॉक्टर से पूछे बिना बंद न करें। नमक कम करें, तंबाकू-शराब छोड़ें और रोज़ 30 मिनट चलें। हर महीने बीपी जांच कराएं।",
        "mr": "रक्तदाबाचे औषध रोज एकाच वेळी घ्या, बरे वाटत असले तरी डॉक्टरांना विचारल्याशिवाय बंद करू नका. मीठ कमी करा, तंबाखू व दारू टाळा आणि रोज 30 मिनिटे चाला. दर महिन्याला रक्तदाब तपासा.",
    },
    "REF-DM-01": {
        "keywords": ["मधुमेह", "साखर", "शुगर"],
        "hi": "शुगर की दवा डॉक्टर के बताए अनुसार लें और फॉलो-अप पर जांच कराते रहें। मीठा और मैदा कम खाएं, सक्रिय रहें और रोज़ पैरों में घाव देखें।",
        "mr": "मधुमेहाचे औषध डॉक्टरांनी सांगितल्याप्रमाणे घ्या आणि फॉलो-अपला तपासणी करत रहा. गोड आणि मैदा कमी खा, सक्रिय रहा आणि रोज पायांवर जखमा तपासा.",
    },
    "REF-ANC-01": {
        "keywords": ["गरोदर", "गर्भवती", "बाळंतपण", "प्रसूती", "लोह"],
        "hi": "गर्भावस्था में कम से कम चार जांच कराएं, आयरन-फोलिक एसिड लें और अस्पताल में प्रसव की योजना बनाएं। खून आना, तेज़ सिरदर्द, धुंधला दिखना, दौरा या बच्चे की हलचल कम होना खतरे के संकेत हैं।",
        "mr": "गरोदरपणात किमान चार तपासण्या करा, लोह-फॉलिक ॲसिड घ्या आणि रुग्णालयात प्रसूतीचे नियोजन करा. रक्तस्राव, तीव्र डोकेदुखी, धूसर दिसणे, फिट किंवा बाळाची हालचाल कमी होणे ही धोक्याची लक्षणे आहेत.",
    },
    "REF-CHILD-01": {
        "keywords": ["बाळ", "मूल", "लस", "लसीकरण"],
        "hi": "टीकाकरण कार्ड के अनुसार टीके लगवाएं; सरकारी केंद्रों पर टीके मुफ्त हैं। बच्चा पी न सके, सब उल्टी कर दे, दौरा पड़े या सांस तेज़ चले तो तुरंत डॉक्टर को दिखाएं।",
        "mr": "लसीकरण कार्डप्रमाणे लसी द्या; सरकारी केंद्रांवर लसी मोफत आहेत. बाळ पिऊ शकत नसेल, सगळे उलटून टाकत असेल, फिट आली किंवा श्वास जलद चालत असेल तर त्वरित डॉक्टरांना दाखवा.",
    },
    "REF-COUGH-01": {
        "keywords": ["खोकला", "सर्दी", "क्षयरोग", "टीबी", "कफ"],
        "hi": "सामान्य सर्दी आराम, गर्म पानी और भाप से एक हफ्ते में ठीक होती है। 2 हफ्ते से ज़्यादा खांसी, खांसी में खून या वज़न कम होना हो तो PHC/CHC में मुफ्त टीबी जांच कराएं।",
        "mr": "साधी सर्दी विश्रांती, गरम पाणी आणि वाफ घेतल्याने आठवड्यात बरी होते. 2 आठवड्यांपेक्षा जास्त खोकला, खोकल्यात रक्त किंवा वजन कमी होत असल्यास PHC/CHC मध्ये मोफत टीबी तपासणी करा.",
    },
    "REF-FOLLOWUP-01": {
        "keywords": ["फॉलो", "पुन्हा", "तपासणी", "भेट", "आठवण"],
        "hi": "फॉलो-अप से डॉक्टर देखते हैं कि इलाज काम कर रहा है या नहीं। तय तारीख पर न आ सकें तो अपनी आशा कार्यकर्ता को बताएं, वे घर पर जांच या केंद्र तक पहुंचने में मदद करेंगी।",
        "mr": "फॉलो-अपमुळे डॉक्टर उपचार काम करत आहेत का ते पाहतात. ठरलेल्या दिवशी येऊ शकत नसल्यास तुमच्या आशा सेविकेला सांगा, त्या घरी तपासणी किंवा केंद्रापर्यंत पोहोचण्यास मदत करतील.",
    },
    "REF-MEDS-01": {
        "keywords": ["औषध", "गोळी", "डोस", "दवाई"],
        "hi": "दवा केवल डॉक्टर के बताए अनुसार लें और एंटीबायोटिक का पूरा कोर्स करें। दवा केंद्र पर न हो तो डॉक्टर या फार्मासिस्ट से पूछें कि कहां मिलेगी - खुद से दवा न बदलें।",
        "mr": "औषध फक्त डॉक्टरांनी सांगितल्याप्रमाणे घ्या आणि अँटिबायोटिकचा पूर्ण कोर्स करा. केंद्रात औषध नसल्यास डॉक्टर किंवा फार्मासिस्टला विचारा ते कुठे मिळेल - स्वतःहून औषध बदलू नका.",
    },
}

for _doc in REFERENCE_DOCS:
    _loc = LOCALIZED.get(_doc["id"], {})
    _doc["keywords"] = _doc["keywords"] + _loc.get("keywords", [])
    _doc["summary"] = {"hi": _loc.get("hi"), "mr": _loc.get("mr")}
