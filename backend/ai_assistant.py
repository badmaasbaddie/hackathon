"""
SwasthyaSetu AI Health Assistant (Hindi / English).

Pipeline for every patient message:
  1. Deterministic safety screen (triage_engine) on everything the patient has
     said. Emergencies are answered immediately with fixed 112/108 advice - the
     language model is never consulted, so it cannot delay or soften them.
  2. Retrieve approved reference material (knowledge_base) relevant to the
     message.
  3. Retrieve the patient's own record (conditions, recent consultations,
     active prescriptions, upcoming follow-ups) from the database. Only records
     the caller is already authorised to see are passed in by the API layer.
  4. If an Anthropic API key is configured, ask Claude (an existing LLM - no
     model is trained here) to write safe next-step guidance grounded ONLY in
     (2) and (3). Otherwise a deterministic, clearly-labelled demo answer is
     composed from the same retrieved material.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

import models
from triage_engine import analyze_symptoms
from knowledge_base import retrieve

logger = logging.getLogger("swasthyasetu.ai")

MODEL_ID = os.getenv("AI_MODEL_NAME", "claude-opus-5-5")

SYSTEM_PROMPT = """You are SwasthyaSetu AI, a health navigation assistant for patients in rural India, used inside a government-style demo platform.

Your job is to help the patient understand safe next steps - self-care that is clearly low-risk, which kind of facility to visit and how soon, and how to use their existing prescriptions and follow-up plan. You are not a doctor: do not diagnose, do not prescribe or change medicines or doses, and do not interpret test results beyond what the record already states.

Ground every medical statement only in the APPROVED REFERENCE MATERIAL and the PATIENT RECORD provided in the conversation. If they do not cover the question, say so plainly and suggest asking the doctor at the PHC/CHC or the ASHA worker. If anything the patient says could be an emergency, tell them to call 112 (ambulance 108) now.

Reply in the requested language: Hindi or Marathi in Devanagari script, or English. If the patient writes in another of these languages, still answer in the requested one. Use short sentences and plain words a person with limited schooling can follow. Keep replies under about 150 words, end with one clear next step, and mention the reference title(s) you relied on in a final line starting with "Sources:"."""


LANGUAGE_NAMES = {"hi": "Hindi", "mr": "Marathi", "en": "English"}


def _llm_enabled() -> bool:
    if os.getenv("AI_ASSISTANT_MODE", "").lower() == "fallback":
        return False
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def build_patient_context(db: Session, patient: models.Patient) -> Dict[str, Any]:
    encounters = (
        db.query(models.ClinicalEncounter)
        .filter(models.ClinicalEncounter.patient_id == patient.id)
        .order_by(desc(models.ClinicalEncounter.encounter_date))
        .limit(3).all()
    )
    rx_items = (
        db.query(models.PrescriptionItem)
        .join(models.Prescription, models.PrescriptionItem.prescription_id == models.Prescription.id)
        .filter(models.Prescription.patient_id == patient.id)
        .order_by(desc(models.Prescription.created_at))
        .limit(5).all()
    )
    follow_ups = (
        db.query(models.FollowUpPlan)
        .filter(models.FollowUpPlan.patient_id == patient.id, models.FollowUpPlan.status.in_(["SCHEDULED", "OVERDUE"]))
        .order_by(models.FollowUpPlan.due_date).all()
    )
    return {
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "village": patient.village,
        "chronic_conditions": patient.chronic_conditions or "None",
        "recent_consultations": [
            f"{e.encounter_date:%Y-%m-%d}: {e.diagnosis} (BP {e.vital_bp}, SpO2 {e.vital_spo2}%)" for e in encounters
        ],
        "medicines": [f"{i.medicine_name} {i.dosage}, {i.frequency}" for i in rx_items],
        "follow_ups": [f"{f.status}: due {f.due_date} - {f.instructions}" for f in follow_ups],
    }


def _format_context(ctx: Dict[str, Any], refs: List[Dict]) -> str:
    lines = [
        "PATIENT RECORD (retrieved securely for this patient only):",
        f"- {ctx['name']}, {ctx['age']}y {ctx['gender']}, village {ctx['village']}",
        f"- Known conditions: {ctx['chronic_conditions']}",
        f"- Recent consultations: {'; '.join(ctx['recent_consultations']) or 'none on record'}",
        f"- Current medicines: {'; '.join(ctx['medicines']) or 'none on record'}",
        f"- Follow-ups: {'; '.join(ctx['follow_ups']) or 'none pending'}",
        "",
        "APPROVED REFERENCE MATERIAL:",
    ]
    if refs:
        for r in refs:
            lines.append(f"[{r['title']}] {r['text']}")
    else:
        lines.append("(No reference entry matched this question.)")
    return "\n".join(lines)


FALLBACK_LABELS = {
    "en": {"guidance": "Guidance", "follow_up": "Your follow-up: ", "medicines": "Your current medicines: ",
           "dont_change": " - do not change these without your doctor's advice.",
           "next": "Next step: book an appointment on the Facilities tab, or contact your ASHA worker.",
           "sources": "Sources: "},
    "hi": {"guidance": "मार्गदर्शन", "follow_up": "आपका फॉलो-अप: ", "medicines": "आपकी चालू दवाएं: ",
           "dont_change": " - इन्हें डॉक्टर की सलाह के बिना न बदलें।",
           "next": "अगला कदम: अस्पताल टैब में अपॉइंटमेंट बुक करें या अपनी आशा कार्यकर्ता से संपर्क करें।",
           "sources": "स्रोत: "},
    "mr": {"guidance": "मार्गदर्शन", "follow_up": "तुमचा फॉलो-अप: ", "medicines": "तुमची सध्याची औषधे: ",
           "dont_change": " - डॉक्टरांच्या सल्ल्याशिवाय ही बदलू नका.",
           "next": "पुढील पाऊल: रुग्णालय टॅबमध्ये अपॉइंटमेंट बुक करा किंवा तुमच्या आशा सेविकेशी संपर्क साधा.",
           "sources": "स्रोत: "},
}


def _fallback_reply(language: str, triage: Dict[str, Any], ctx: Dict[str, Any], refs: List[Dict]) -> str:
    lbl = FALLBACK_LABELS.get(language, FALLBACK_LABELS["en"])
    parts = [triage["explanation_patient"]]
    if triage["triage_level"] == "URGENT" and triage.get("emergency_advice"):
        parts.append(triage["emergency_advice"])
    if refs:
        guidance = refs[0].get("summary", {}).get(language) or refs[0]["text"]
        parts.append(f"{lbl['guidance']} ({refs[0]['title']}): {guidance}")
    if ctx["follow_ups"]:
        parts.append(lbl["follow_up"] + ctx["follow_ups"][0])
    if ctx["medicines"]:
        parts.append(lbl["medicines"] + "; ".join(ctx["medicines"][:3]) + lbl["dont_change"])
    parts.append(lbl["next"])
    if refs:
        parts.append(lbl["sources"] + ", ".join(r["title"] for r in refs))
    return "\n\n".join(parts)


def _call_llm(history: List[Dict[str, str]], context_block: str, language: str) -> Optional[str]:
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed; using demo fallback")
        return None

    client = anthropic.Anthropic(timeout=45.0, max_retries=1)
    messages = []
    for i, m in enumerate(history):
        content = m["content"]
        if i == len(history) - 1:
            content = (
                f"{context_block}\n\nRequested reply language: {LANGUAGE_NAMES.get(language, 'English')}\n\n"
                f"PATIENT MESSAGE:\n{content}"
            )
        messages.append({"role": m["role"], "content": content})

    try:
        response = client.beta.messages.create(
            model=MODEL_ID,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=messages,
        )
    except anthropic.APIConnectionError:
        logger.warning("Claude API unreachable; using demo fallback")
        return None
    except anthropic.APIStatusError as e:
        logger.warning("Claude API error %s; using demo fallback", e.status_code)
        return None

    if response.stop_reason == "refusal":
        return None
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    return text or None


def respond(db: Session, patient: models.Patient, history: List[Dict[str, str]], language: str) -> Dict[str, Any]:
    """history: list of {"role": "user"|"assistant", "content": str}, last item is the new user message."""
    user_text = " \n".join(m["content"] for m in history if m["role"] == "user")
    latest = history[-1]["content"]

    # Screen the whole conversation so a red flag mentioned earlier is never lost.
    triage = analyze_symptoms(user_text, language=language)
    refs = retrieve(latest) or retrieve(user_text)
    ctx = build_patient_context(db, patient)

    mode = "SAFETY_RULES"
    if triage["is_emergency"]:
        reply = triage["emergency_advice"]
    else:
        reply = None
        if _llm_enabled():
            reply = _call_llm(history, _format_context(ctx, refs), language)
            if reply:
                mode = "LLM"
        if not reply:
            reply = _fallback_reply(language, triage, ctx, refs)
            mode = "DEMO_FALLBACK"

    return {
        "reply": reply,
        "mode": mode,
        "model": MODEL_ID if mode == "LLM" else None,
        "triage": triage,
        "sources": [{"id": r["id"], "title": r["title"], "source": r["source"]} for r in refs],
        "patient_context_used": True,
    }
