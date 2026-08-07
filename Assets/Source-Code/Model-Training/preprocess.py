"""Shared preprocessing & feature extraction for SQLInsight.

Used by both training (ml/train_model.py) and inference (backend/detection.py)
so the exact same transformation is applied everywhere.

Design (faithful to the thesis -- CountVectorizer + VarianceThreshold +
LogisticRegression -- with accuracy-oriented improvements):

  * Word features : CountVectorizer with an SQL-aware token pattern that keeps
    punctuation (' " -- = ; ( ) ...) as tokens, since these carry strong
    injection signal that the default tokenizer would discard.
  * Char features : CountVectorizer over character n-grams (3-5), which captures
    syntactic fingerprints of injection payloads and generalises far better to
    unseen attacks than word tokens alone.
  * VarianceThreshold removes (near-)constant columns, mirroring the thesis
    pipeline's feature-reduction stage.

The fitted vectorizer (a Pipeline) is saved separately from the classifier,
matching the thesis deployment that loads ``ML_model.pkl`` and a vectorizer
artifact independently.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_selection import VarianceThreshold
from sklearn.pipeline import FeatureUnion, Pipeline

# Words/identifiers OR any single non-word, non-space character (', ", -, =, ;, (, )...).
SQL_TOKEN_PATTERN = r"(?u)\b\w+\b|[^\w\s]"


def load_dataset(path: str | Path) -> pd.DataFrame:
    """Load a {Query,Label} CSV robustly (datasets contain non-UTF-8 bytes)."""
    df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    # Normalise column names (datasets use 'Query','Label').
    cols = {c.lower().strip(): c for c in df.columns}
    qcol = cols.get("query", df.columns[0])
    lcol = cols.get("label", df.columns[-1])
    df = df[[qcol, lcol]].rename(columns={qcol: "Query", lcol: "Label"})
    df["Query"] = df["Query"].astype(str)
    df = df.dropna(subset=["Query", "Label"])
    df = df[df["Query"].str.strip() != ""]
    df["Label"] = pd.to_numeric(df["Label"], errors="coerce")
    df = df.dropna(subset=["Label"])
    df["Label"] = df["Label"].astype(int)
    return df.reset_index(drop=True)


def build_vectorizer() -> Pipeline:
    """Construct the (unfitted) feature pipeline."""
    word_vec = CountVectorizer(
        lowercase=True,
        token_pattern=SQL_TOKEN_PATTERN,
        ngram_range=(1, 2),
        min_df=2,
        max_features=50_000,
    )
    char_vec = CountVectorizer(
        lowercase=True,
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=3,
        max_features=60_000,
    )
    features = FeatureUnion([("word", word_vec), ("char", char_vec)])
    # Thesis used VarianceThreshold(.0001 * (1 - .0001)), but with min_df already
    # filtering rare terms that value also drops discriminative 2-doc bigrams
    # (e.g. "union select"), hurting recall. threshold=0.0 keeps the stage
    # (drops only constant/zero-variance columns) without that side effect.
    selector = VarianceThreshold(threshold=0.0)
    return Pipeline([("features", features), ("variance", selector)])
