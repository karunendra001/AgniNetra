# Model Validation Report

**Model:** XGBoost (200 trees, depth 6, lr 0.1) · **Data:** 8297 labeled FIRMS hotspots
**Protocol:** stratified 80/20 train/test split, `random_state=42` — identical to `ml_scripts/train_model.py`

| Metric | Score |
|---|---|
| **Accuracy** | **95.4%** |
| Precision (weighted) | 95.3% |
| Recall (weighted) | 95.4% |
| F1 (weighted) | 95.4% |

Deployed `model.pkl` reproduces this: ✅ yes (accuracy 95.4%).

## Per-class performance

| Class | Precision | Recall | F1 | Test rows |
|---|---|---|---|---|
| crop_burning | 99.0% | 98.6% | 98.8% | 484 |
| gas_flare | 67.4% | 64.4% | 65.9% | 45 |
| industrial_fire | 89.4% | 92.3% | 90.8% | 220 |
| mining_activity | 80.7% | 72.0% | 76.1% | 93 |
| unclassified_other | 97.3% | 100.0% | 98.6% | 213 |
| wildfire | 98.2% | 98.3% | 98.3% | 605 |

## What the model relies on

Top features: **landcover_class** (50.3%), **daynight** (21.9%), **distance_to_facility_m** (15.2%).

![Confusion matrix](confusion_matrix.png)

![Feature importance](feature_importance.png)

## Honest limitations

- Labels come from the team's rule-based heuristic (`source_type`), so this measures
  agreement with those rules — a human-labeled subset would strengthen the claim.
- Random (not spatial) split: neighbouring hotspots share conditions, so real-world
  accuracy on a brand-new region may be somewhat lower.
- Landcover coverage is partial for live data (see enrichment notes).

*Generated 2026-09-07 13:40 UTC · run `python validate_model.py` to regenerate*