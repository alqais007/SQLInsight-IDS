"""Train and evaluate the SQLInsight logistic-regression detector.

Experiment 1 (within-distribution): train/test 80/20 split of
    data/Modified_SQL_Dataset.csv          (~30.9k rows)
Experiment 2 (generalisation): evaluate on
    data/clean_sql_dataset.csv             (~148.3k rows)
  reported two ways:
    - full        : the whole clean dataset (thesis style)
    - unseen-only : clean rows whose Query never appears in the training set
                    (~79% of clean) -> the honest generalisation number.

Artifacts written to ml/artifacts/:
    ML_model.pkl       fitted LogisticRegression (deployed on 100% of train)
    vectorizer.joblib  fitted feature pipeline
    metrics.json       all metrics + metadata (consumed by the dashboard)

Run:  python ml/train_model.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    EVAL_DATASET,
    METRICS_PATH,
    MODEL_PATH,
    TRAIN_DATASET,
    VECTORIZER_PATH,
)
from ml.preprocess import build_vectorizer, load_dataset  # noqa: E402

RANDOM_STATE = 42


def _scores(y_true, y_pred) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)) * 100, 2),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)) * 100, 2),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)) * 100, 2),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)) * 100, 2),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "samples": int(len(y_true)),
    }


def _print_block(title: str, m: dict) -> None:
    cm = m["confusion_matrix"]
    print(f"\n=== {title} ({m['samples']:,} samples) ===")
    print(f"  Accuracy : {m['accuracy']:.2f}%   Precision: {m['precision']:.2f}%")
    print(f"  Recall   : {m['recall']:.2f}%   F1-score : {m['f1']:.2f}%")
    print(f"  Confusion: TP={cm['tp']:,}  TN={cm['tn']:,}  FP={cm['fp']:,}  FN={cm['fn']:,}")


def main() -> None:
    t0 = time.time()
    print("Loading datasets...")
    train_df = load_dataset(TRAIN_DATASET)
    eval_df = load_dataset(EVAL_DATASET)
    print(f"  train (exp1): {len(train_df):,} rows  {train_df['Label'].value_counts().to_dict()}")
    print(f"  eval  (exp2): {len(eval_df):,} rows  {eval_df['Label'].value_counts().to_dict()}")

    # ---- Fit feature pipeline on the full training corpus ----
    print("\nFitting feature pipeline (word + char n-grams)...")
    vectorizer = build_vectorizer()
    X_all = vectorizer.fit_transform(train_df["Query"])
    y_all = train_df["Label"].to_numpy()
    print(f"  feature matrix: {X_all.shape[0]:,} x {X_all.shape[1]:,}")

    clf_kwargs = dict(C=4.0, solver="liblinear", max_iter=1000, class_weight="balanced")

    # ---- Experiment 1: 80/20 split ----
    print("\nExperiment 1 -- 80/20 split on Modified_SQL_Dataset.csv")
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_all, y_all, test_size=0.2, random_state=RANDOM_STATE, stratify=y_all
    )
    clf_split = LogisticRegression(**clf_kwargs).fit(X_tr, y_tr)
    exp1 = _scores(y_te, clf_split.predict(X_te))
    exp1["train_size"], exp1["test_size"] = int(X_tr.shape[0]), int(X_te.shape[0])
    _print_block("Experiment 1: within-distribution (held-out 20%)", exp1)

    # ---- Final deployed model: train on 100% of the training data ----
    print("\nTraining final model on 100% of training data (for deployment)...")
    model = LogisticRegression(**clf_kwargs).fit(X_all, y_all)

    # ---- Experiment 2: generalisation to clean_sql_dataset.csv ----
    print("\nExperiment 2 -- generalisation to clean_sql_dataset.csv")
    Xe = vectorizer.transform(eval_df["Query"])
    ye = eval_df["Label"].to_numpy()
    pred_full = model.predict(Xe)
    exp2_full = _scores(ye, pred_full)
    _print_block("Experiment 2: full clean dataset (thesis style)", exp2_full)

    train_queries = set(train_df["Query"].str.strip())
    unseen_mask = ~eval_df["Query"].str.strip().isin(train_queries)
    exp2_unseen = _scores(ye[unseen_mask.to_numpy()], pred_full[unseen_mask.to_numpy()])
    _print_block("Experiment 2: UNSEEN-only (honest generalisation)", exp2_unseen)

    # ---- Persist artifacts ----
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    metrics = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sklearn_version": sklearn.__version__,
        "model": "LogisticRegression",
        "model_params": clf_kwargs,
        "features": {
            "n_features": int(X_all.shape[1]),
            "vectorizer": "FeatureUnion(word 1-2 gram + char_wb 3-5 gram) -> VarianceThreshold",
        },
        "datasets": {
            "train": {"file": TRAIN_DATASET.name, "rows": int(len(train_df))},
            "eval": {"file": EVAL_DATASET.name, "rows": int(len(eval_df))},
            "overlap_note": "train is ~entirely contained in eval; unseen-only excludes it",
        },
        "experiment_1": exp1,
        "experiment_2_full": exp2_full,
        "experiment_2_unseen": exp2_unseen,
        "headline": {
            "accuracy": exp1["accuracy"],
            "precision": exp1["precision"],
            "recall": exp1["recall"],
            "f1": exp1["f1"],
        },
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    print(f"\nSaved model      -> {MODEL_PATH}")
    print(f"Saved vectorizer -> {VECTORIZER_PATH}")
    print(f"Saved metrics    -> {METRICS_PATH}")
    print(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
