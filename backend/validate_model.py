"""Model validation report — proves the AI works (PS deliverable support).

Re-runs the teammate's EXACT training recipe from ml_scripts/train_model.py:
  - data/processed/firms_classified.csv, stratified 80/20 split, random_state=42
  - XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, multi:softprob)
  - LabelEncoders for categorical features (confidence, daynight, landcover)

Outputs (written to backend/reports/):
  validation_report.json   - machine-readable, served by GET /api/model/validation
  confusion_matrix.png     - annotated heatmap
  feature_importance.png   - horizontal bar chart
  MODEL_VALIDATION.md      - one-pager for judges / PPT

Run from backend/:
    ./.venv/bin/python validate_model.py
"""
import json
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

BACKEND = Path(__file__).resolve().parent
DATA_PATH = BACKEND / "ml" / "firms_classified.csv"
MODEL_PATH = BACKEND / "ml" / "model.pkl"
REPORTS = BACKEND / "reports"
REPORTS.mkdir(exist_ok=True)

FEATURE_COLS = [
    "bright_ti4",
    "bright_ti5",
    "frp",
    "confidence",
    "daynight",
    "detection_count",
    "unique_days",
    "distance_to_facility_m",
    "landcover_class",
]
TARGET_COL = "source_type"


def load_and_prepare(path: Path):
    """Identical logic to the teammate's train_model.py load_and_prepare()."""
    df = pd.read_csv(path)
    df = df.dropna(subset=[TARGET_COL])

    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].copy()
    y = df[TARGET_COL].copy()

    encoders = {}
    for col in X.select_dtypes(include=["object"]).columns:
        X[col] = X[col].fillna("unknown")
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le

    for col in X.select_dtypes(include=[np.number]).columns:
        X[col] = X[col].fillna(X[col].median())

    return X, y, available, encoders


def main():
    t0 = time.time()
    print(f"Loading {DATA_PATH.name} ...")
    X, y, feature_cols, encoders = load_and_prepare(DATA_PATH)
    class_counts = y.value_counts().to_dict()

    target_encoder = LabelEncoder()
    y_enc = target_encoder.fit_transform(y)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )
    print(f"Train {len(X_tr)} / Test {len(X_te)} rows, {len(target_encoder.classes_)} classes")

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=len(target_encoder.classes_),
        eval_metric="mlogloss",
        random_state=42,
    )
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)

    acc = float(accuracy_score(y_te, y_pred))
    precision = float(precision_score(y_te, y_pred, average="weighted", zero_division=0))
    recall = float(recall_score(y_te, y_pred, average="weighted", zero_division=0))
    f1 = float(f1_score(y_te, y_pred, average="weighted", zero_division=0))
    print(f"Accuracy {acc:.4f} | precision {precision:.4f} | recall {recall:.4f} | F1 {f1:.4f}")

    classes = [str(c) for c in target_encoder.classes_]
    cm = confusion_matrix(y_te, y_pred)

    # ---- confusion matrix heatmap ----
    plt.figure(figsize=(8, 6.5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="mako",
        xticklabels=classes,
        yticklabels=classes,
        cbar_kws={"label": "test rows"},
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"Confusion Matrix — XGBoost hotspot classifier (accuracy {acc*100:.1f}%)")
    plt.tight_layout()
    plt.savefig(REPORTS / "confusion_matrix.png", dpi=150)
    plt.close()

    # ---- feature importance ----
    importances = model.feature_importances_
    order = np.argsort(importances)
    plt.figure(figsize=(8, 5))
    plt.barh(np.array(feature_cols)[order], np.array(importances)[order], color="#ff6b35")
    plt.xlabel("Importance (gain share)")
    plt.title("What the model looks at — XGBoost feature importance")
    plt.tight_layout()
    plt.savefig(REPORTS / "feature_importance.png", dpi=150)
    plt.close()

    # ---- per-class report (machine-readable) ----
    report = classification_report(
        y_te, y_pred, target_names=classes, output_dict=True, zero_division=0
    )

    # ---- sanity: saved model.pkl must agree with this retrain ----
    saved_ok, saved_acc = False, None
    try:
        payload = joblib.load(MODEL_PATH)
        saved_pred = payload["model"].predict(X_te[payload["feature_cols"]])
        saved_acc = float(accuracy_score(y_te, saved_pred))
        saved_ok = abs(saved_acc - acc) < 0.01
    except Exception as exc:  # pragma: no cover
        print(f"Could not verify saved model: {exc}")

    # ---- markdown one-pager ----
    def pct(v):
        return f"{v*100:.1f}%"

    md = [
        "# Model Validation Report",
        "",
        f"**Model:** XGBoost (200 trees, depth 6, lr 0.1) · **Data:** {len(X)} labeled FIRMS hotspots",
        f"**Protocol:** stratified 80/20 train/test split, `random_state=42` — identical to `ml_scripts/train_model.py`",
        "",
        "| Metric | Score |",
        "|---|---|",
        f"| **Accuracy** | **{pct(acc)}** |",
        f"| Precision (weighted) | {pct(precision)} |",
        f"| Recall (weighted) | {pct(recall)} |",
        f"| F1 (weighted) | {pct(f1)} |",
        "",
        f"Deployed `model.pkl` reproduces this: {'✅ yes' if saved_ok else '⚠️ check'} (accuracy {pct(saved_acc) if saved_acc is not None else 'n/a'}).",
        "",
        "## Per-class performance",
        "",
        "| Class | Precision | Recall | F1 | Test rows |",
        "|---|---|---|---|---|",
    ]
    for cls in classes:
        r = report.get(cls, {})
        md.append(
            f"| {cls} | {pct(r.get('precision', 0))} | {pct(r.get('recall', 0))} "
            f"| {pct(r.get('f1-score', 0))} | {int(r.get('support', 0))} |"
        )
    top3 = sorted(zip(feature_cols, importances), key=lambda t: -t[1])[:3]
    md += [
        "",
        "## What the model relies on",
        "",
        f"Top features: **{top3[0][0]}** ({pct(top3[0][1])}), "
        f"**{top3[1][0]}** ({pct(top3[1][1])}), **{top3[2][0]}** ({pct(top3[2][1])}).",
        "",
        "![Confusion matrix](confusion_matrix.png)",
        "",
        "![Feature importance](feature_importance.png)",
        "",
        "## Honest limitations",
        "",
        "- Labels come from the team's rule-based heuristic (`source_type`), so this measures",
        "  agreement with those rules — a human-labeled subset would strengthen the claim.",
        "- Random (not spatial) split: neighbouring hotspots share conditions, so real-world",
        "  accuracy on a brand-new region may be somewhat lower.",
        "- Landcover coverage is partial for live data (see enrichment notes).",
        "",
        f"*Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} · run `python validate_model.py` to regenerate*",
    ]
    (REPORTS / "MODEL_VALIDATION.md").write_text("\n".join(md), encoding="utf-8")

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_type": "XGBoost multi-class classifier",
        "n_estimators": 200,
        "max_depth": 6,
        "dataset_rows": int(len(X)),
        "train_rows": int(len(X_tr)),
        "test_rows": int(len(X_te)),
        "classes": classes,
        "class_distribution": {str(k): int(v) for k, v in class_counts.items()},
        "accuracy": round(acc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "per_class": report,
        "confusion_matrix": cm.tolist(),
        "feature_importance": sorted(
            ({"feature": f, "importance": round(float(i), 4)} for f, i in zip(feature_cols, importances)),
            key=lambda d: -d["importance"],
        ),
        "saved_model_matches": saved_ok,
        "saved_model_accuracy": round(saved_acc, 4) if saved_acc is not None else None,
        "train_seconds": round(time.time() - t0, 1),
    }
    (REPORTS / "validation_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {REPORTS/'validation_report.json'}, MODEL_VALIDATION.md, 2 charts "
          f"({payload['train_seconds']}s)")


if __name__ == "__main__":
    main()
