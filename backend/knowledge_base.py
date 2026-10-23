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
