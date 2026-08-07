"""SQLInsight detection service.

Loads the trained logistic-regression model + feature vectorizer and exposes a
single ``detect(query)`` entry point. Mirrors the thesis deployment, which loads
``ML_model.pkl`` and the vectorizer artifact separately and runs
``model.predict(vectorizer.transform([query]))``.

A lightweight, regex-based ``classify_attack_type`` adds a human-readable attack
category for the dashboard. It is purely descriptive -- the malicious/benign
*verdict* always comes from the ML model, never from these rules.
"""
from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

import joblib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import MODEL_PATH, VECTORIZER_PATH  # noqa: E402

# Verdict threshold on P(malicious). 0.5 is the natural LR boundary and was
# validated to catch all canonical attacks while keeping precision ~98.5%.
THRESHOLD = 0.5

_ATTACK_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("Tautology / Auth Bypass", re.compile(r"(\bor\b|\band\b)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.I)),
    ("Tautology / Auth Bypass", re.compile(r"['\"]\s*(or|and)\s*['\"]?\w+['\"]?\s*=\s*['\"]?\w+", re.I)),
    ("Union-based", re.compile(r"\bunion\b(\s+all)?\s+select\b", re.I)),
    ("Stacked Queries", re.compile(r";\s*(drop|insert|update|delete|create|alter|exec)\b", re.I)),
    ("Time-based Blind", re.compile(r"\b(sleep|pg_sleep|waitfor\s+delay|benchmark)\b", re.I)),
    ("Error-based", re.compile(r"\b(extractvalue|updatexml|utl_inaddr|convert\s*\(|cast\s*\()", re.I)),
    ("Command Execution", re.compile(r"\b(xp_cmdshell|exec\s*\(|sp_executesql)\b", re.I)),
    ("Comment Injection", re.compile(r"(--|#|/\*)", re.I)),
    ("Schema Enumeration", re.compile(r"\b(information_schema|sys\.|all_tables|table_name|version\s*\()", re.I)),
]


@lru_cache(maxsize=1)
def _load():
    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists():
        raise FileNotFoundError(
            f"Model artifacts not found. Run `python ml/train_model.py` first.\n"
            f"  expected: {MODEL_PATH}\n            {VECTORIZER_PATH}"
        )
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    return model, vectorizer


def model_loaded() -> bool:
    try:
        _load()
        return True
    except Exception:
        return False


def classify_attack_type(query: str) -> str:
    for label, pattern in _ATTACK_PATTERNS:
        if pattern.search(query):
            return label
    return "Generic / Obfuscated"


def detect(query: str) -> dict:
    """Classify a single query/payload.

    Returns: {query, prediction(0|1), confidence(float), verdict, attack_type}
    """
    query = "" if query is None else str(query)
    model, vectorizer = _load()
    X = vectorizer.transform([query])
    proba = float(model.predict_proba(X)[0][1])
    prediction = int(proba >= THRESHOLD)
    return {
        "query": query,
        "prediction": prediction,
        "confidence": round(proba, 4),
        "verdict": "Suspicious" if prediction == 1 else "Normal",
        "attack_type": classify_attack_type(query) if prediction == 1 else None,
    }
