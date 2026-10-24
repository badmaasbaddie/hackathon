"""
Report-routing model trained on data/lab_reports_synthetic.jsonl (1,000 synthetic,
de-identified lab / imaging reports, each labelled with a specialty category and a
clinical pattern).

What it learns: which pattern (and therefore which specialty) a set of lab values,
imaging impression and symptoms points to. It is a decision-support router, not a
diagnosis.

Limits of the data that shape how it is used:
  * every training report is abnormal, and every infection test is "Positive" - the model
    would always find *something*, so report_analysis.py only consults it after reference
    ranges have flagged an abnormal value;
  * imaging cases have one fixed symptom list each, so for imaging the model mostly learns
    the study type; urgency comes from the written impression instead.

Training uses "symptom dropout" (every report is also seen without symptoms) so the model
still works on an uploaded report with lab values only, and both settings are evaluated.
"""

import os
import re
import json
import datetime
import warnings
from collections import Counter, defaultdict
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

warnings.filterwarnings("ignore", module="sklearn")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "data", "lab_reports_synthetic.jsonl")
MODEL_FILE = os.path.join(HERE, "models_trained", "report_classifier.joblib")
INFO_FILE = os.path.join(HERE, "models_trained", "report_model_info.json")
GUIDANCE_FILE = os.path.join(HERE, "data", "report_theme_guidance.json")

TEXT_FIELDS = ("Imaging study", "Study", "Impression")


def _qualitative(value) -> Optional[float]:
    s = str(value).strip().lower()
    if re.match(r"^(positive|reactive|detected|large|moderate|present|trace)", s):
        return 1.0
    if re.match(r"^(negative|non[- ]?reactive|not detected|absent|nil)", s):
        return 0.0
    return None


def load_rows() -> List[Dict]:
    rows = []
    for line in open(DATA_FILE, encoding="utf-8"):
        r = json.loads(line)
        inp, out = json.loads(r["input"]), json.loads(r["output"])
        rows.append({"input": inp, "output": out})
    return rows


def numeric_fields(rows: List[Dict]) -> List[str]:
    fields = Counter(k for r in rows for k in r["input"]["lab_report"] if k not in TEXT_FIELDS)
    return sorted(fields)


def featurize(lab: Dict, symptoms: List[str], age: Optional[float], sex: Optional[str], fields: List[str]) -> Dict:
    row = {}
    for f in fields:
        v = lab.get(f)
        if v is None:
            row[f] = np.nan
        elif isinstance(v, (int, float)):
            row[f] = float(v)
        else:
            q = _qualitative(v)
            if q is None:
                m = re.search(r"-?\d+(\.\d+)?", str(v))
                q = float(m.group()) if m else np.nan
            row[f] = q
    row["age"] = float(age) if age is not None else np.nan
    row["sex_female"] = 1.0 if (sex or "").lower().startswith("f") else 0.0 if sex else np.nan
    text = " ".join(str(lab.get(f, "")) for f in TEXT_FIELDS) + " " + " ".join(symptoms or [])
    row["text"] = text.lower().strip()
    return row


def _to_dense(x):
    return x.toarray()


def build_pipeline(fields: List[str]) -> Pipeline:
    pre = ColumnTransformer([
        ("num", "passthrough", fields + ["age", "sex_female"]),
        ("txt", Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=400)),
                          ("dense", FunctionTransformer(_to_dense, accept_sparse=True))]), "text"),
    ])
    return Pipeline([("pre", pre), ("clf", HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, random_state=42))])


def _frame(rows: List[Dict], fields: List[str], with_symptoms: bool) -> pd.DataFrame:
    return pd.DataFrame([
        featurize(r["input"]["lab_report"], r["input"]["presenting_symptoms"] if with_symptoms else [],
                  r["input"].get("age"), r["input"].get("sex"), fields)
        for r in rows
    ])


def train() -> Dict:
    rows = load_rows()
    fields = numeric_fields(rows)
    y = np.array([r["output"]["likely_clinical_theme"] for r in rows])

    # Honest evaluation: 5-fold cross-validation, scored both with and without symptoms.
    X_full, X_lab = _frame(rows, fields, True), _frame(rows, fields, False)
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    pred_full, pred_lab = np.empty(len(y), dtype=object), np.empty(len(y), dtype=object)
    for train_idx, test_idx in folds.split(X_full, y):
        model = build_pipeline(fields)
        X_train = pd.concat([X_full.iloc[train_idx], X_lab.iloc[train_idx]], ignore_index=True)
        y_train = np.concatenate([y[train_idx], y[train_idx]])
        model.fit(X_train, y_train)
        pred_full[test_idx] = model.predict(X_full.iloc[test_idx])
        pred_lab[test_idx] = model.predict(X_lab.iloc[test_idx])

    # Final model on everything (with symptom dropout).
    final = build_pipeline(fields)
    final.fit(pd.concat([X_full, X_lab], ignore_index=True), np.concatenate([y, y]))
    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    joblib.dump({"model": final, "fields": fields}, MODEL_FILE)

    # Per-pattern guidance taken from the dataset's own (non-prescriptive) outputs.
    by_theme = defaultdict(list)
    for r in rows:
        by_theme[r["output"]["likely_clinical_theme"]].append(r["output"])
    guidance = {}
    field_counts = defaultdict(Counter)
    for r in rows:
        field_counts[r["output"]["likely_clinical_theme"]].update(r["input"]["lab_report"].keys())
    for theme, outs in by_theme.items():
        steps = Counter(s for o in outs for s in o["recommended_next_steps"])
        guidance[theme] = {
            "category": Counter(o["category"] for o in outs).most_common(1)[0][0],
            "next_steps": [s for s, _ in steps.most_common(4)],
            "cases": len(outs),
            # The report fields this pattern is based on; a prediction is only trusted when one is present.
            "key_fields": sorted(f for f, n in field_counts[theme].items() if n >= 0.8 * len(outs) and f not in TEXT_FIELDS),
        }
    json.dump(guidance, open(GUIDANCE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    info = {
        "status": "TRAINED",
        "dataset": "synthetic_lab_report_training_1000 (de-identified, synthetic)",
        "dataset_size": len(rows),
        "patterns": len(set(y)),
        "specialties": len({g["category"] for g in guidance.values()}),
        "cv_accuracy_with_symptoms": round(accuracy_score(y, pred_full) * 100, 1),
        "cv_accuracy_lab_values_only": round(accuracy_score(y, pred_lab) * 100, 1),
        "cv_macro_f1_lab_values_only": round(f1_score(y, pred_lab, average="macro") * 100, 1),
        "lab_fields": len(fields),
        "notes": "Every training report is abnormal; the model is only consulted after reference ranges flag an abnormal value.",
        "trained_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    json.dump(info, open(INFO_FILE, "w", encoding="utf-8"), indent=2)
    lab_errors = Counter((t, p) for t, p in zip(y, pred_lab) if t != p).most_common(8)
    info["most_confused_lab_only"] = [f"{t} -> {p} ({n})" for (t, p), n in lab_errors]
    return info


_cache = {}


def _load():
    if "bundle" not in _cache:
        if not os.path.exists(MODEL_FILE):
            train()
        _cache["bundle"] = joblib.load(MODEL_FILE)
        _cache["guidance"] = json.load(open(GUIDANCE_FILE, encoding="utf-8"))
    return _cache["bundle"], _cache["guidance"]


def predict(lab: Dict, symptoms: List[str], age=None, sex=None, top: int = 3) -> List[Dict]:
    bundle, guidance = _load()
    X = pd.DataFrame([featurize(lab, symptoms, age, sex, bundle["fields"])])
    probs = bundle["model"].predict_proba(X)[0]
    classes = bundle["model"].classes_
    order = np.argsort(probs)[::-1][:top]
    return [{"pattern": classes[i], "confidence": round(float(probs[i]), 3),
             "category": guidance.get(classes[i], {}).get("category")} for i in order]


def guidance_for(pattern: str) -> Dict:
    return _load()[1].get(pattern, {})


def model_fields() -> List[str]:
    return _load()[0]["fields"]


if __name__ == "__main__":
    # Train through the imported module so the saved pipeline references report_model._to_dense,
    # not __main__._to_dense (which would not load inside the server).
    import report_model
    print(json.dumps(report_model.train(), indent=2))


def model_info() -> Dict:
    try:
        info = json.load(open(INFO_FILE, encoding="utf-8"))
    except FileNotFoundError:
        return {"status": "NOT_TRAINED"}
    return {k: info.get(k) for k in ("dataset", "dataset_size", "patterns", "specialties",
                                     "cv_accuracy_lab_values_only", "cv_accuracy_with_symptoms")}
