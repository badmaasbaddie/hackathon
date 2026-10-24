"""
Patient report analysis: lab reports, imaging/ECG reports and prescriptions.

Pipeline
  1. Read the upload: typed text, digital PDF (pypdf), or - when ANTHROPIC_API_KEY is set -
     photos, scanned PDFs and handwriting via Claude vision.
  2. Work out the document type and pull out lab values (with aliases from the dataset fields,
     common Indian lab abbreviations and the Russian/English glossary), imaging impressions,
     or prescription lines (checked against the medicine vocabulary from the 1,000
     handwritten prescriptions).
  3. Flag each value against adult reference ranges; critical values and alarming imaging
     words raise the urgency. A normal report is reported as normal.
  4. Only if something is abnormal, ask the trained router (report_model.py) which pattern
     and specialty it fits, then find a facility nearby with that specialist on duty.
  5. Add the dataset's non-prescriptive next steps and labelled time/cost estimates.

Decision support only: it never diagnoses or prescribes.
"""

import base64
import difflib
import io
import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

import models
import report_model
from triage_engine import analyze_symptoms

logger = logging.getLogger("swasthyasetu.reports")
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
VISION_MODEL = os.getenv("AI_MODEL_NAME", "claude-opus-5-5")

ESTIMATES = json.load(open(os.path.join(HERE, "data", "report_estimates.json"), encoding="utf-8"))
MEDICINES = [m["name"] for m in json.load(open(os.path.join(HERE, "data", "medicine_vocabulary.json"), encoding="utf-8"))["medicines"]]
_MED_LOWER = {m.lower(): m for m in MEDICINES}


class ReportError(Exception):
    pass


# ----------------------------------------------------------------- lab value aliases
# Canonical names are the model's fields (from the synthetic lab dataset).
ALIASES: Dict[str, List[str]] = {
    "Hemoglobin (g/dL)": ["haemoglobin", "hemoglobin", "hgb", "hb"],
    "Hematocrit (%)": ["haematocrit", "hematocrit", "hct", "pcv", "packed cell volume"],
    "MCV (fL)": ["mean corpuscular volume", "mcv"],
    "Platelets (/uL)": ["platelet count", "platelets", "plt"],
    "WBC (/uL)": ["total leucocyte count", "total leukocyte count", "white blood cells", "wbc count", "tlc", "wbc"],
    "Fasting glucose (mg/dL)": ["fasting blood sugar", "fasting plasma glucose", "fasting glucose", "glucose fasting", "fbs", "fpg"],
    "Random glucose (mg/dL)": ["random blood sugar", "random glucose", "glucose random", "rbs", "blood sugar", "glucose"],
    "HbA1c (%)": ["glycated haemoglobin", "glycated hemoglobin", "glycosylated hemoglobin", "hba1c", "a1c"],
    "LDL (mg/dL)": ["ldl cholesterol", "cholesterol - ldl", "ldl-c", "ldl"],
    "HDL (mg/dL)": ["hdl cholesterol", "hdl-c", "hdl"],
    "Triglycerides (mg/dL)": ["triglycerides", "triglyceride", "tg"],
    "Creatinine (mg/dL)": ["serum creatinine", "creatinine in blood", "s. creatinine", "creatinine"],
    "Urea (mg/dL)": ["blood urea", "serum urea", "urea"],
    "eGFR (mL/min/1.73m2)": ["egfr", "estimated gfr"],
    "ALT (U/L)": ["alanine aminotransferase", "sgpt", "alt"],
    "AST (U/L)": ["aspartate aminotransferase", "sgot", "ast"],
    "Total bilirubin (mg/dL)": ["total bilirubin", "bilirubin total", "s. bilirubin", "bilirubin"],
    "TSH (mIU/L)": ["thyroid stimulating hormone", "tsh"],
    "Free T4 (ng/dL)": ["free t4", "free thyroxine", "ft4"],
    "Ferritin (ng/mL)": ["serum ferritin", "ferritin"],
    "Serum iron (mcg/dL)": ["serum iron", "iron (fe)", "s. iron"],
    "TIBC (mcg/dL)": ["total iron binding capacity", "tibc"],
    "25-OH Vitamin D (ng/mL)": ["25-oh vitamin d", "25 oh vitamin d", "25-hydroxy vitamin d", "vitamin d (25-oh)", "vitamin d3 (25-oh)", "vitamin d", "vit d"],
    "Vitamin B12 (pg/mL)": ["vitamin b12", "vit b12", "cobalamin", "b12"],
    "CRP (mg/L)": ["c-reactive protein", "c reactive protein", "crp"],
    "ESR (mm/hr)": ["erythrocyte sedimentation rate", "esr"],
    "PSA (ng/mL)": ["prostate specific antigen", "total psa", "psa"],
    "CA-125 (U/mL)": ["ca-125", "ca 125", "ca125"],
    "Beta hCG (mIU/mL)": ["beta hcg", "beta-hcg", "b-hcg", "hcg"],
    "LH (mIU/mL)": ["luteinizing hormone", "lh"],
    "FSH (mIU/mL)": ["follicle stimulating hormone", "fsh"],
    "AMH (ng/mL)": ["anti mullerian hormone", "anti-mullerian hormone", "antimueller hormone", "amh"],
    "Total testosterone (ng/dL)": ["total testosterone", "testosterone"],
    "Ejection fraction (%)": ["ejection fraction", "lvef", "ef"],
    "WBC (/hpf)": ["pus cells", "urine wbc", "wbc/hpf"],
}
QUALITATIVE: Dict[str, List[str]] = {
    "Malaria parasite test": ["malaria parasite", "malaria antigen", "mp test", "malaria"],
    "Dengue NS1 antigen": ["dengue ns1", "ns1 antigen", "ns1"],
    "Typhoid IgM": ["typhoid igm", "typhidot", "salmonella typhi igm"],
    "HBsAg": ["hbsag", "hepatitis b surface antigen"],
    "Urine pregnancy test": ["urine pregnancy test", "upt"],
    "Nitrite": ["nitrite"],
    "Leukocyte esterase": ["leukocyte esterase", "leucocyte esterase"],
    "ANA": ["antinuclear antibody", "ana"],
}


def _load_glossary_aliases():
    """Russian lab names from Glossary.xlsx (provided as a small JSON copy) mapped onto our fields."""
    path = os.path.join(HERE, "data", "lab_glossary_ru_en.json")
    if not os.path.exists(path):
        return
    for ru, en in json.load(open(path, encoding="utf-8")):
        en_l = en.lower()
        for field, names in ALIASES.items():
            if any(re.search(r"(?<![a-z])" + re.escape(n) + r"(?![a-z])", en_l) for n in names if len(n) > 3):
                names.append(ru.lower())
                break


_load_glossary_aliases()

# Adult reference ranges (low, high) plus critical limits that raise urgency.
REFERENCE = {
    "Hemoglobin (g/dL)": {"male": (13.0, 17.0), "female": (12.0, 15.5), "crit_low": 7.0, "emerg_low": 5.0},
    "Hematocrit (%)": {"male": (40, 50), "female": (36, 46)},
    "MCV (fL)": {"range": (80, 100)},
    "Platelets (/uL)": {"range": (150000, 450000), "crit_low": 50000, "emerg_low": 20000},
    "WBC (/uL)": {"range": (4000, 11000), "crit_low": 2000, "crit_high": 30000},
    "WBC (/hpf)": {"range": (0, 5)},
    "Fasting glucose (mg/dL)": {"range": (70, 99), "crit_high": 300, "emerg_high": 400, "emerg_low": 54},
    "Random glucose (mg/dL)": {"range": (70, 139), "crit_high": 300, "emerg_high": 400, "emerg_low": 54},
    "HbA1c (%)": {"range": (4.0, 5.6), "crit_high": 10.0},
    "LDL (mg/dL)": {"range": (0, 129)},
    "HDL (mg/dL)": {"male": (40, 200), "female": (50, 200)},
    "Triglycerides (mg/dL)": {"range": (0, 149), "crit_high": 500},
    "Creatinine (mg/dL)": {"male": (0.7, 1.3), "female": (0.6, 1.1), "crit_high": 3.0},
    "Urea (mg/dL)": {"range": (15, 45), "crit_high": 100},
    "eGFR (mL/min/1.73m2)": {"range": (60, 200), "crit_low": 15},
    "ALT (U/L)": {"range": (7, 56), "crit_high": 300},
    "AST (U/L)": {"range": (10, 40), "crit_high": 300},
    "Total bilirubin (mg/dL)": {"range": (0.2, 1.2), "crit_high": 5.0},
    "TSH (mIU/L)": {"range": (0.4, 4.0)},
    "Free T4 (ng/dL)": {"range": (0.8, 1.8)},
    "Ferritin (ng/mL)": {"male": (30, 400), "female": (15, 150)},
    "Serum iron (mcg/dL)": {"range": (60, 170)},
    "TIBC (mcg/dL)": {"range": (250, 450)},
    "25-OH Vitamin D (ng/mL)": {"range": (30, 100)},
    "Vitamin D (ng/mL)": {"range": (30, 100)},
    "Vitamin B12 (pg/mL)": {"range": (200, 900)},
    "CRP (mg/L)": {"range": (0, 10), "crit_high": 100},
    "ESR (mm/hr)": {"male": (0, 15), "female": (0, 20)},
    "PSA (ng/mL)": {"range": (0, 4.0)},
    "CA-125 (U/mL)": {"range": (0, 35)},
    "LH (mIU/mL)": {"range": (2, 15)},
    "FSH (mIU/mL)": {"range": (2, 12)},
    "AMH (ng/mL)": {"range": (1.0, 4.5)},
    "Total testosterone (ng/dL)": {"male": (300, 1000), "female": (15, 70)},
    "Ejection fraction (%)": {"range": (55, 75), "crit_low": 35},
}
URGENT_POSITIVES = {"Malaria parasite test", "Dengue NS1 antigen", "Typhoid IgM"}
INFO_POSITIVES = {"Urine pregnancy test", "Beta hCG (mIU/mL)"}

IMAGING_STUDIES = [("mri", "MRI brain"), ("ct ", "CT"), ("computed tomography", "CT"), ("x-ray", "Chest X-ray"), ("xray", "Chest X-ray"),
                   ("radiograph", "Chest X-ray"), ("ultrasound", "Ultrasound abdomen"), ("usg", "Ultrasound abdomen"), ("sonography", "Ultrasound abdomen"),
                   ("echocardiograph", "2D Echo"), ("2d echo", "2D Echo"), ("tmt", "TMT"), ("treadmill", "TMT"), ("ecg", "ECG"), ("ekg", "ECG"),
                   ("electrocardiogram", "ECG"), ("eeg", "EEG"), ("electroencephalogram", "EEG")]
EMERGENCY_IMAGING = ["st elevation", "st-elevation", "stemi", "haemorrhage", "hemorrhage", "bleed", "acute infarct", "pneumothorax",
                     "ventricular tachycardia", "complete heart block", "aortic dissection", "midline shift"]
URGENT_IMAGING = ["st-segment", "st segment", "st depression", "infarct", "mass", "lesion", "consolidation", "effusion", "fracture",
                  "obstruction", "ischemi", "ischaemi", "reduced ejection", "positive for inducible", "epileptiform", "seizure", "calculus", "stone"]


# ----------------------------------------------------------------- reading the upload
def _anthropic_client():
    if os.getenv("AI_ASSISTANT_MODE", "").lower() == "fallback" or not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        return None
    try:
        import anthropic
        return anthropic.Anthropic(timeout=90.0, max_retries=1)
    except ImportError:
        return None


def vision_available() -> bool:
    return _anthropic_client() is not None


VISION_PROMPT = (
    "Transcribe this medical document for a patient-facing decision-support tool. "
    "Copy test names, values, units and reference ranges exactly; for imaging/ECG/EEG reports copy the study name, findings and impression; "
    "for prescriptions write one line per medicine as on the page (form, name, strength, dose pattern such as 1+0+1, duration) and the complaints/advice. "
    "Write illegible words as [illegible] - never guess medicine names. Leave out names, phone numbers, addresses and ID numbers of the patient. "
    'Reply with JSON only: {"document_type": "lab_report" | "imaging_report" | "prescription" | "other", "text": "..."}'
)


def _shrink_image(data: bytes) -> Tuple[bytes, str]:
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img = img.convert("RGB")
        img.thumbnail((2000, 2000))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=85)
        return out.getvalue(), "image/jpeg"
    except Exception as e:
        raise ReportError(f"Could not open the image: {e}")


def _read_with_vision(data: bytes, content_type: str) -> Tuple[str, Optional[str]]:
    client = _anthropic_client()
    if client is None:
        raise ReportError("Reading photos and scanned documents needs the AI vision service (ANTHROPIC_API_KEY). "
                          "Upload a digital PDF or type the report text instead.")
    if content_type == "application/pdf":
        block = {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": base64.standard_b64encode(data).decode()}}
    else:
        data, content_type = _shrink_image(data)
        block = {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": base64.standard_b64encode(data).decode()}}
    import anthropic
    try:
        response = client.beta.messages.create(
            model=VISION_MODEL, max_tokens=4000, output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            messages=[{"role": "user", "content": [block, {"type": "text", "text": VISION_PROMPT}]}],
        )
    except anthropic.APIStatusError as e:
        raise ReportError(f"The AI vision service returned an error ({e.status_code}).")
    except anthropic.APIConnectionError:
        raise ReportError("Could not reach the AI vision service.")
    if response.stop_reason == "refusal":
        raise ReportError("The AI vision service declined to read this document.")
    raw = "".join(b.text for b in response.content if b.type == "text").strip()
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if m:
        try:
            parsed = json.loads(m.group())
            return str(parsed.get("text", "")), parsed.get("document_type")
        except json.JSONDecodeError:
            pass
    return raw, None


def read_document(data: bytes, content_type: str) -> Dict:
    if not data:
        raise ReportError("The file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ReportError("The file is larger than 10 MB.")
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct.startswith("text/") or ct == "application/json":
        return {"text": data.decode("utf-8", errors="replace"), "method": "typed", "doc_hint": None}
    if ct == "application/pdf" or data[:4] == b"%PDF":
        try:
            import pypdf
            text = "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(io.BytesIO(data)).pages)
        except Exception:
            text = ""
        if len(text.strip()) >= 40:
            return {"text": text, "method": "pdf_text", "doc_hint": None}
        text, hint = _read_with_vision(data, "application/pdf")
        return {"text": text, "method": "ai_vision", "doc_hint": hint}
    if ct.startswith("image/"):
        text, hint = _read_with_vision(data, ct)
        return {"text": text, "method": "ai_vision", "doc_hint": hint}
    raise ReportError("Unsupported file type. Upload a PDF, a photo (JPG/PNG) or paste the text.")


# ----------------------------------------------------------------- parsing
_NUM = r"(-?\d+(?:[.,]\d+)?)"
_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯०१२३४५६७८९", "01234567890123456789")


def _alias_regex(alias: str) -> str:
    return r"(?<![a-zа-я0-9])" + re.escape(alias) + r"(?![a-zа-я0-9])"


def _convert_units(field: str, value: float) -> float:
    if field == "Platelets (/uL)":
        if value < 10:        # lakh/cumm
            return value * 100000
        if value < 2000:      # x10^3/uL
            return value * 1000
    if field == "WBC (/uL)" and value < 200:   # x10^3/uL
        return value * 1000
    if field == "Hemoglobin (g/dL)" and value > 30:   # g/L
        return value / 10
    if field in ("Fasting glucose (mg/dL)", "Random glucose (mg/dL)") and value < 35:   # mmol/L
        return round(value * 18, 1)
    if field == "Creatinine (mg/dL)" and value > 20:   # umol/L
        return round(value / 88.4, 2)
    if field in ("LDL (mg/dL)", "HDL (mg/dL)") and value < 15:   # mmol/L
        return round(value * 38.67, 1)
    if field == "Triglycerides (mg/dL)" and value < 20:   # mmol/L
        return round(value * 88.57, 1)
    return value


def parse_lab_values(text: str) -> Tuple[Dict, List[str]]:
    """Return {field: value} and any imaging/study lines found."""
    values: Dict = {}
    lines = [l.strip() for l in text.translate(_BN_DIGITS).splitlines() if l.strip()]
    all_aliases = sorted([(a, f, False) for f, names in ALIASES.items() for a in names] +
                         [(a, f, True) for f, names in QUALITATIVE.items() for a in names], key=lambda x: -len(x[0]))
    for line in lines:
        low = line.lower()
        for alias, field, qualitative in all_aliases:
            if field in values:
                continue
            m = re.search(_alias_regex(alias), low)
            if not m:
                continue
            rest = low[m.end():]
            if qualitative:
                q = re.search(r"\b(positive|negative|reactive|non[- ]?reactive|detected|not detected|present|absent|nil|large|trace)\b", rest)
                if q:
                    values[field] = q.group(1).capitalize()
                    break
                continue
            num = re.search(_NUM, rest)
            if num:
                try:
                    values[field] = _convert_units(field, float(num.group(1).replace(",", ".")))
                except ValueError:
                    continue
                break
    # A random "glucose"/"blood sugar" line should not duplicate an explicit fasting value.
    if "Fasting glucose (mg/dL)" in values and values.get("Random glucose (mg/dL)") == values["Fasting glucose (mg/dL)"]:
        values.pop("Random glucose (mg/dL)")
    return values, lines


def detect_imaging(text: str) -> Optional[Dict]:
    low = text.lower()
    study = next((name for key, name in IMAGING_STUDIES if key in low), None)
    if not study:
        return None
    m = re.search(r"(impression|conclusion|opinion|interpretation)\s*[:\-]\s*(.+)", text, flags=re.I | re.S)
    impression = re.sub(r"\s+", " ", m.group(2)).strip()[:400] if m else ""
    return {"study": study, "impression": impression}


_MED_LINE = re.compile(r"\b(tab|tablet|cap|capsule|inj|injection|syp|syrup|susp|suspension|drop|drops|oint|ointment|cream|gel|inhaler|sachet)\b\.?\s*:?\s*(.+)", re.I)


def parse_prescription(text: str) -> List[Dict]:
    meds = []
    for raw in text.translate(_BN_DIGITS).splitlines():
        m = _MED_LINE.search(raw)
        if not m:
            continue
        form = m.group(1).lower().rstrip(".")
        rest = m.group(2).strip()
        name_part = re.split(r"\s(?=\d+\s*\+\s*\d)|\s-{2,}|_{2,}", rest)[0]
        name = re.sub(r"\s+\d+(\.\d+)?\s*(mg|ml|mcg|g|iu)?\b.*$", "", name_part, flags=re.I).strip(" .,:;-") or name_part.strip()
        pattern = re.search(r"(\d)\s*\+\s*(\d)\s*\+\s*(\d)", rest)
        days = re.search(r"(\d+)\s*(days?|din|দিন|দিন|weeks?|months?)", rest, re.I)
        schedule = None
        if pattern:
            parts = [("morning", pattern.group(1)), ("noon", pattern.group(2)), ("night", pattern.group(3))]
            schedule = ", ".join(f"{n} {when}" for when, n in parts if n != "0") or None
        recognised = name.lower() in _MED_LOWER or bool(difflib.get_close_matches(name.lower(), _MED_LOWER.keys(), n=1, cutoff=0.85))
        duration_days = None
        if days:
            n = int(days.group(1))
            unit = days.group(2).lower()
            duration_days = n * 7 if unit.startswith("week") else n * 30 if unit.startswith("month") else n
        meds.append({"form": {"tab": "tablet", "cap": "capsule", "inj": "injection", "syp": "syrup"}.get(form, form),
                     "name": name[:60], "recognised": recognised, "schedule": schedule, "duration_days": duration_days})
    return meds


def classify_document(text: str, hint: Optional[str], values: Dict, meds: List, imaging: Optional[Dict]) -> str:
    if hint in ("lab_report", "imaging_report", "prescription"):
        if hint == "lab_report" and not values and imaging:
            return "imaging_report"
        return hint
    if len(meds) >= 1 and len(values) < 2:
        return "prescription"
    if imaging and len(values) < 2:
        return "imaging_report"
    if values:
        return "lab_report"
    return "other"


# ----------------------------------------------------------------- interpretation
def _range_for(field: str, sex: Optional[str]):
    ref = REFERENCE.get(field)
    if not ref:
        return None, ref
    if "range" in ref:
        return ref["range"], ref
    return ref.get("female" if (sex or "").lower().startswith("f") else "male"), ref


def flag_values(values: Dict, sex: Optional[str]) -> Tuple[List[Dict], List[str], str]:
    findings, reasons = [], []
    urgency = "NORMAL"
    order = {"NORMAL": 0, "ROUTINE": 1, "URGENT": 2, "EMERGENCY": 3}

    def raise_to(level, reason):
        nonlocal urgency
        if order[level] > order[urgency]:
            urgency = level
        if reason and level in ("URGENT", "EMERGENCY"):
            reasons.append(reason)

    for field, value in values.items():
        name, unit = (field.split(" (")[0], field.split("(")[1].rstrip(")")) if "(" in field else (field, "")
        if isinstance(value, str):
            positive = value.lower() in ("positive", "reactive", "detected", "present", "large", "trace")
            status = "positive" if positive else "negative"
            if positive and field in INFO_POSITIVES:
                status = "info"
            findings.append({"test": name, "value": value, "unit": "", "range": "Negative", "status": status})
            if positive and field in URGENT_POSITIVES:
                raise_to("URGENT", f"{name} is positive - needs treatment today")
            elif positive and field not in INFO_POSITIVES:
                raise_to("ROUTINE", None)
            continue
        rng, ref = _range_for(field, sex)
        status = "normal"
        if field == "Beta hCG (mIU/mL)":
            status = "info" if value >= 5 else "normal"
            findings.append({"test": name, "value": value, "unit": unit, "range": "< 5 if not pregnant", "status": status})
            continue
        if rng:
            low, high = rng
            if value < low:
                status = "low"
            elif value > high:
                status = "high"
        if ref:
            if ref.get("emerg_low") is not None and value < ref["emerg_low"]:
                status = "critical_low"; raise_to("EMERGENCY", f"{name} {value} {unit} is dangerously low")
            elif ref.get("emerg_high") is not None and value >= ref["emerg_high"]:
                status = "critical_high"; raise_to("EMERGENCY", f"{name} {value} {unit} is dangerously high")
            elif ref.get("crit_low") is not None and value < ref["crit_low"]:
                status = "critical_low"; raise_to("URGENT", f"{name} {value} {unit} is very low")
            elif ref.get("crit_high") is not None and value >= ref["crit_high"]:
                status = "critical_high"; raise_to("URGENT", f"{name} {value} {unit} is very high")
        if status in ("low", "high"):
            raise_to("ROUTINE", None)
        findings.append({"test": name, "value": round(value, 2) if isinstance(value, float) else value, "unit": unit,
                         "range": f"{rng[0]}-{rng[1]}" if rng else "", "status": status})
    return findings, reasons, urgency


def imaging_urgency(imaging: Dict) -> Tuple[str, List[str]]:
    imp = (imaging.get("impression") or "").lower()
    if any(w in imp for w in EMERGENCY_IMAGING):
        return "EMERGENCY", [f"{imaging['study']} impression mentions a finding that needs emergency care"]
    if any(w in imp for w in URGENT_IMAGING):
        return "URGENT", [f"{imaging['study']} impression needs a specialist's review soon"]
    if imp and re.search(r"\b(normal|no abnormality|within normal limits|unremarkable|wnl)\b", imp):
        return "NORMAL", []
    return "ROUTINE", []


SPECIALISTS = {
    "MRI brain": ("Neurologist", "न्यूरोलॉजिस्ट", "न्यूरोलॉजिस्ट", ["neuro"]),
    "EEG": ("Neurologist", "न्यूरोलॉजिस्ट", "न्यूरोलॉजिस्ट", ["neuro"]),
    "CT": ("General Physician, then the specialist the CT points to", "जनरल फिजिशियन", "जनरल फिजिशियन", ["general medicine", "internal", "emergency"]),
    "Chest X-ray": ("Chest physician (Pulmonologist)", "छाती रोग विशेषज्ञ", "छातीरोग तज्ज्ञ", ["pulmo", "chest", "general medicine"]),
    "Ultrasound abdomen": ("General Surgeon / Gastroenterologist", "सर्जन / पेट रोग विशेषज्ञ", "सर्जन / पोटविकार तज्ज्ञ", ["surg", "gastro", "general medicine"]),
    "2D Echo": ("Cardiologist", "हृदय रोग विशेषज्ञ", "हृदयरोग तज्ज्ञ", ["cardio"]),
    "TMT": ("Cardiologist", "हृदय रोग विशेषज्ञ", "हृदयरोग तज्ज्ञ", ["cardio"]),
    "ECG": ("Cardiologist", "हृदय रोग विशेषज्ञ", "हृदयरोग तज्ज्ञ", ["cardio"]),
    "Elevated PSA": ("Urologist", "मूत्र रोग विशेषज्ञ", "मूत्ररोग तज्ज्ञ", ["urolog", "general medicine"]),
    "Elevated CA-125": ("Gynaecologist", "स्त्री रोग विशेषज्ञ", "स्त्रीरोग तज्ज्ञ", ["gyn", "obstet"]),
    "Endocrinology": ("Endocrinologist (diabetes & thyroid)", "एंडोक्राइनोलॉजिस्ट (शुगर व थायरॉइड)", "एंडोक्रायनोलॉजिस्ट (मधुमेह व थायरॉइड)", ["endocrin", "diabet", "general medicine"]),
    "Infectious Disease": ("General Physician", "जनरल फिजिशियन", "जनरल फिजिशियन", ["general medicine", "internal", "emergency"]),
    "Cardiometabolic": ("General Physician / Cardiologist", "जनरल फिजिशियन / हृदय रोग विशेषज्ञ", "जनरल फिजिशियन / हृदयरोग तज्ज्ञ", ["cardio", "general medicine"]),
    "Hematology": ("General Physician (Haematologist if severe)", "जनरल फिजिशियन (गंभीर हो तो हेमेटोलॉजिस्ट)", "जनरल फिजिशियन (गंभीर असल्यास हिमॅटोलॉजिस्ट)", ["haemat", "hemat", "general medicine"]),
    "Radiology": ("Doctor who ordered the scan / General Physician", "जांच लिखने वाले डॉक्टर / जनरल फिजिशियन", "तपासणी सांगणारे डॉक्टर / जनरल फिजिशियन", ["general medicine"]),
    "Nutrition": ("General Physician", "जनरल फिजिशियन", "जनरल फिजिशियन", ["general medicine", "community"]),
    "Hepatology": ("Gastroenterologist / Hepatologist", "पेट व लिवर रोग विशेषज्ञ", "पोट व यकृत तज्ज्ञ", ["gastro", "hepat", "general medicine"]),
    "Nephrology": ("Nephrologist (kidney specialist)", "किडनी रोग विशेषज्ञ (नेफ्रोलॉजिस्ट)", "मूत्रपिंड तज्ज्ञ (नेफ्रोलॉजिस्ट)", ["nephro", "general medicine"]),
    "Rheumatology / Immunology": ("Rheumatologist", "र्यूमेटोलॉजिस्ट", "र्‍युमॅटोलॉजिस्ट", ["rheumat", "general medicine"]),
    "Oncology": ("Oncologist", "कैंसर रोग विशेषज्ञ", "कर्करोग तज्ज्ञ", ["oncol", "general medicine"]),
    "Obstetrics / Gynecology": ("Obstetrician-Gynaecologist", "स्त्री व प्रसूति रोग विशेषज्ञ", "स्त्रीरोग व प्रसूती तज्ज्ञ", ["obstet", "gyn", "maternal"]),
    "Cardiology": ("Cardiologist", "हृदय रोग विशेषज्ञ", "हृदयरोग तज्ज्ञ", ["cardio"]),
    "Preventive Health": ("General Physician", "जनरल फिजिशियन", "जनरल फिजिशियन", ["general medicine", "community"]),
}
GENERAL = ("General Physician", "जनरल फिजिशियन", "जनरल फिजिशियन", ["general medicine", "community", "internal"])


def _specialist_for(pattern: Optional[str], category: Optional[str]):
    if pattern in SPECIALISTS:
        return SPECIALISTS[pattern]
    if category in SPECIALISTS:
        return SPECIALISTS[category]
    return GENERAL


def find_facility(db: Session, keywords: List[str], district: Optional[str]) -> Optional[Dict]:
    facilities = db.query(models.Facility).filter(models.Facility.district == district).order_by(models.Facility.distance_km).all() if district else []
    if not facilities:
        facilities = db.query(models.Facility).order_by(models.Facility.distance_km).all()
    generic = {"general medicine", "community", "internal", "emergency"}
    for kw in keywords:
        for fac in facilities:
            doc = db.query(models.Doctor).filter(models.Doctor.facility_id == fac.id, models.Doctor.is_available_today == True,
                                                 models.Doctor.specialty.ilike(f"%{kw}%")).first()
            if doc:
                return {"facility_id": fac.id, "facility_name": fac.name, "distance_km": fac.distance_km,
                        "travel_time_mins": fac.travel_time_mins, "doctor_id": doc.id, "doctor_name": doc.name, "specialty": doc.specialty,
                        "specialist_match": kw not in generic or keywords[0] in generic}
    return None


# When the model is unsure, route by the most important abnormal value instead.
FIELD_CATEGORY = {
    "Hemoglobin": "Hematology", "Hematocrit": "Hematology", "MCV": "Hematology", "Platelets": "Hematology", "WBC": "Infectious Disease",
    "Ferritin": "Hematology", "Serum iron": "Hematology", "TIBC": "Hematology",
    "Fasting glucose": "Endocrinology", "Random glucose": "Endocrinology", "HbA1c": "Endocrinology",
    "TSH": "Endocrinology", "Free T4": "Endocrinology",
    "LDL": "Cardiometabolic", "HDL": "Cardiometabolic", "Triglycerides": "Cardiometabolic",
    "Creatinine": "Nephrology", "Urea": "Nephrology", "eGFR": "Nephrology",
    "ALT": "Hepatology", "AST": "Hepatology", "Total bilirubin": "Hepatology", "HBsAg": "Hepatology",
    "25-OH Vitamin D": "Nutrition", "Vitamin D": "Nutrition", "Vitamin B12": "Nutrition",
    "CRP": "Infectious Disease", "ESR": "Rheumatology / Immunology", "ANA": "Rheumatology / Immunology",
    "PSA": "Oncology", "CA-125": "Oncology", "Malaria parasite test": "Infectious Disease", "Dengue NS1 antigen": "Infectious Disease",
    "Typhoid IgM": "Infectious Disease", "Nitrite": "Infectious Disease", "Leukocyte esterase": "Infectious Disease",
    "LH": "Obstetrics / Gynecology", "FSH": "Obstetrics / Gynecology", "AMH": "Obstetrics / Gynecology",
    "Total testosterone": "Obstetrics / Gynecology", "Ejection fraction": "Cardiology",
}
SEVERITY = {"critical_low": 3, "critical_high": 3, "positive": 2, "low": 1, "high": 1}
MIN_CONFIDENCE = 0.6


def trusted_pattern(preds: List[Dict], present_fields: set) -> Optional[Dict]:
    """Use the model only when it is confident AND the report contains a test that pattern is based on."""
    if not preds or preds[0]["confidence"] < MIN_CONFIDENCE:
        return None
    key_fields = set(report_model.guidance_for(preds[0]["pattern"]).get("key_fields", []))
    if key_fields and not (key_fields & present_fields):
        return None
    return preds[0]


def route_by_values(findings: List[Dict]) -> Tuple[Optional[str], List[str]]:
    abnormal = sorted((f for f in findings if f["status"] in SEVERITY), key=lambda f: -SEVERITY[f["status"]])
    categories = list(dict.fromkeys(FIELD_CATEGORY[f["test"]] for f in abnormal if f["test"] in FIELD_CATEGORY))
    if not categories:
        return None, []
    # Several unrelated systems -> start with a General Physician who can see the whole picture.
    return (categories[0] if len(categories) == 1 else None), [f["test"] for f in abnormal]


DISCLAIMER = ("Decision support only - not a diagnosis or prescription. A doctor must review the report in full clinical context. "
              "Estimates of recovery time and cost are indicative, not predictions for you.")


def analyze(db: Session, patient: models.Patient, data: bytes, content_type: str, symptoms: str = "", language: str = "en") -> Dict:
    lang = language if language in ("hi", "mr", "en") else "en"
    doc = read_document(data, content_type)
    text = doc["text"] or ""
    values, _ = parse_lab_values(text)
    imaging = detect_imaging(text)
    meds = parse_prescription(text)
    report_type = classify_document(text, doc["doc_hint"], values, meds, imaging)
    sex = patient.gender

    result: Dict = {"report_type": report_type, "read_method": doc["method"], "extracted_text": text[:6000],
                    "findings": [], "medicines": [], "imaging": None, "patterns": [], "urgency": "NORMAL",
                    "urgency_reasons": [], "next_steps": [], "specialist": None, "recommended_facility": None,
                    "estimates": None, "symptom_triage": None, "disclaimer": DISCLAIMER}

    if report_type == "other" and not values and not meds:
        raise ReportError("No lab values, scan impression or medicines could be found. Check that the right file was uploaded, "
                          "or paste the report text.")

    if report_type == "prescription":
        result["medicines"] = meds
        result["urgency"] = "ROUTINE"
        longest = max([m["duration_days"] or 0 for m in meds] or [0])
        result["specialist"] = {"title": {"en": "The doctor who wrote this prescription", "hi": "पर्चा लिखने वाले डॉक्टर",
                                          "mr": "औषधपत्र लिहिणारे डॉक्टर"}[lang], "why": "Follow-up questions about these medicines should go to the prescribing doctor."}
        result["next_steps"] = ["Take the medicines exactly as written; do not stop or change them without asking the doctor.",
                                "Ask the pharmacist if any medicine name is unclear - handwritten names are easy to misread.",
                                "Come back to the doctor if symptoms do not improve by the end of the course or get worse."]
        result["estimates"] = {"recovery": f"The longest course on this prescription is {longest} days." if longest else
                               "The prescription does not state a course length.",
                               "cost_government": ESTIMATES["government_note"], "cost_private": "Depends on the brands chosen; ask the pharmacist for generic equivalents (Jan Aushadhi stores sell them at low cost).",
                               "ongoing": False, "notice": ESTIMATES["notice"]}
    else:
        findings, reasons, urgency = flag_values(values, sex)
        result["findings"] = findings
        if imaging:
            result["imaging"] = imaging
            img_level, img_reasons = imaging_urgency(imaging)
            order = {"NORMAL": 0, "ROUTINE": 1, "URGENT": 2, "EMERGENCY": 3}
            if order[img_level] > order[urgency]:
                urgency = img_level
            reasons += img_reasons
        abnormal = [f for f in findings if f["status"] not in ("normal", "negative", "info")]
        imaging_abnormal = bool(imaging) and urgency != "NORMAL"
        if abnormal or imaging_abnormal:
            lab_for_model = dict(values)
            if imaging:
                lab_for_model["Study" if imaging["study"] in ("ECG", "TMT", "2D Echo") else "Imaging study"] = imaging["study"]
                lab_for_model["Impression"] = imaging["impression"]
            symptom_list = [s.strip() for s in re.split(r"[,;\n]", symptoms or "") if s.strip()]
            preds = report_model.predict(lab_for_model, symptom_list, patient.age, sex)
            preds = [{"pattern": str(p["pattern"]), "confidence": p["confidence"], "category": p["category"]} for p in preds]
            trusted = trusted_pattern(preds, set(lab_for_model))
            result["patterns"] = [trusted] if trusted else []
            result["model_considered"] = [p for p in preds if p["confidence"] >= 0.05]
        result["urgency"] = urgency
        result["urgency_reasons"] = reasons

        top = result["patterns"][0] if result["patterns"] else None
        if imaging and imaging["study"] == "EEG":   # not in the training data
            top = {"pattern": "EEG", "confidence": None, "category": None}
        routed_category, routed_tests = (None, [])
        if not top and (abnormal or imaging_abnormal):
            routed_category, routed_tests = route_by_values(findings)
        if top:
            spec = _specialist_for(top["pattern"], top["category"])
            guide = report_model.guidance_for(top["pattern"])
            result["next_steps"] = guide.get("next_steps", [])
            est = ESTIMATES["patterns"].get(top["pattern"])
            if est:
                result["estimates"] = {**est, "cost_government": ESTIMATES["government_note"], "notice": ESTIMATES["notice"]}
            why = f"The report best matches the pattern '{top['pattern']}'" + (f" ({int(top['confidence'] * 100)}% model confidence)." if top.get("confidence") else ".")
        elif routed_tests:
            spec = _specialist_for(None, routed_category) if routed_category else GENERAL
            result["next_steps"] = ["Show this report to the doctor; repeat or confirmatory tests may be needed.",
                                    "Bring any earlier reports and the list of medicines you take."]
            why = ("Abnormal: " + ", ".join(routed_tests[:5]) + ". " +
                   ("These point to one area." if routed_category else "Several different areas are affected, so start with a General Physician who can look at the whole picture."))
        else:
            spec = GENERAL
            result["next_steps"] = ["No value is outside the usual adult range. Keep the report for your records.",
                                    "If you still have symptoms, a routine visit to a General Physician is enough."]
            why = "Nothing in the report is outside the usual range."
        idx = {"en": 0, "hi": 1, "mr": 2}[lang]
        result["specialist"] = {"title": spec[idx], "why": why}
        result["recommended_facility"] = find_facility(db, spec[3], patient.district)

    if symptoms.strip():
        triage = analyze_symptoms(symptoms, lang)
        result["symptom_triage"] = {"level": triage["triage_level"], "advice": triage.get("emergency_advice") or triage["explanation_patient"]}
        if triage["is_emergency"]:
            result["urgency"] = "EMERGENCY"
            result["urgency_reasons"].append("Your symptoms include emergency warning signs - call 112/108")
    result["model"] = report_model.model_info()
    return result
