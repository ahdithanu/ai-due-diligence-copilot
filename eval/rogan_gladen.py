#!/usr/bin/env python3
"""
eval/rogan_gladen.py: Rogan-Gladen Bias Correction & Bootstrap Confidence Interval Module.

In production deployments, evaluating an LLM agent over thousands of unlabeled production
traces with an imperfect LLM judge yields an observed pass rate p_obs that is mathematically
biased by the judge's false positives and false negatives.

This module implements:
1. Empirical TPR (True Positive Rate / Sensitivity) and TNR (True Negative Rate / Specificity)
   calculation against human-labeled ground truth.
2. Cohen's Kappa (kappa) inter-rater agreement measurement.
3. The Rogan-Gladen adjustment to recover the true underlying population pass rate theta_hat:
       theta_hat = (p_obs + TNR - 1) / (TPR + TNR - 1)
4. Empirical bootstrap confidence intervals (e.g. 10,000 resamples) for statistical error margins.
"""

import sys
import math
import random
from typing import List, Tuple, Dict, Any, Optional


def calculate_tpr_tnr(
    human_labels: List[int],
    judge_predictions: List[int],
) -> Dict[str, float]:
    """
    Computes True Positive Rate (TPR), True Negative Rate (TNR),
    False Positive Rate (FPR), and False Negative Rate (FNR).
    
    Labels: 1 = Pass / Positive, 0 = Fail / Negative.
    """
    if len(human_labels) != len(judge_predictions):
        raise ValueError("Length mismatch between human labels and judge predictions.")
    if not human_labels:
        return {"tpr": 0.0, "tnr": 0.0, "fpr": 0.0, "fnr": 0.0, "raw_accuracy": 0.0}

    tp = sum(1 for h, j in zip(human_labels, judge_predictions) if h == 1 and j == 1)
    fn = sum(1 for h, j in zip(human_labels, judge_predictions) if h == 1 and j == 0)
    tn = sum(1 for h, j in zip(human_labels, judge_predictions) if h == 0 and j == 0)
    fp = sum(1 for h, j in zip(human_labels, judge_predictions) if h == 0 and j == 1)

    actual_positives = tp + fn
    actual_negatives = tn + fp
    total = len(human_labels)

    tpr = tp / actual_positives if actual_positives > 0 else 1.0
    tnr = tn / actual_negatives if actual_negatives > 0 else 1.0
    fpr = fp / actual_negatives if actual_negatives > 0 else 0.0
    fnr = fn / actual_positives if actual_positives > 0 else 0.0
    raw_acc = (tp + tn) / total if total > 0 else 0.0

    return {
        "tp": float(tp),
        "fp": float(fp),
        "tn": float(tn),
        "fn": float(fn),
        "tpr": tpr,
        "tnr": tnr,
        "fpr": fpr,
        "fnr": fnr,
        "raw_accuracy": raw_acc,
    }


def calculate_cohens_kappa(
    rater1: List[int],
    rater2: List[int],
) -> float:
    """
    Calculates Cohen's Kappa (kappa) between two raters on binary decisions.
    Guards against artificially inflated raw agreement on class-imbalanced data.
    """
    if len(rater1) != len(rater2) or not rater1:
        return 0.0

    n = len(rater1)
    po = sum(1 for a, b in zip(rater1, rater2) if a == b) / n

    # Expected agreement by chance
    p1_pos = sum(rater1) / n
    p1_neg = 1.0 - p1_pos
    p2_pos = sum(rater2) / n
    p2_neg = 1.0 - p2_pos

    pe = (p1_pos * p2_pos) + (p1_neg * p2_neg)

    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


def rogan_gladen_correction(
    observed_pass_rate: float,
    tpr: float,
    tnr: float,
) -> float:
    """
    Applies the Rogan-Gladen equation:
        theta_hat = (p_obs + TNR - 1) / (TPR + TNR - 1)

    If (TPR + TNR - 1) < 0.05, the evaluator is operating near random chance,
    and the corrected prevalence is mathematically unstable.
    """
    denominator = tpr + tnr - 1.0

    if abs(denominator) < 0.05:
        raise ValueError(
            f"Evaluator operating near chance: TPR ({tpr:.2f}) + TNR ({tnr:.2f}) - 1 = {denominator:.3f} < 0.05. "
            "Cannot reliably apply Rogan-Gladen correction."
        )

    theta_hat = (observed_pass_rate + tnr - 1.0) / denominator

    # Constrain to valid probability range [0.0, 1.0]
    return max(0.0, min(1.0, theta_hat))


def bootstrap_confidence_interval(
    values: List[float],
    n_bootstrap: int = 10000,
    ci_level: float = 0.95,
    seed: Optional[int] = 42,
) -> Tuple[float, float]:
    """
    Computes a two-sided empirical percentile bootstrap confidence interval.
    Zero external dependencies: uses pure Python standard library.
    """
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]

    rng = random.Random(seed)
    n = len(values)
    means = []

    for _ in range(n_bootstrap):
        sample = rng.choices(values, k=n)
        means.append(sum(sample) / n)

    means.sort()
    lower_idx = int(((1.0 - ci_level) / 2.0) * n_bootstrap)
    upper_idx = int((1.0 - ((1.0 - ci_level) / 2.0)) * n_bootstrap)
    upper_idx = min(upper_idx, n_bootstrap - 1)

    return round(means[lower_idx], 4), round(means[upper_idx], 4)


def calibrate_and_evaluate_production(
    human_test_labels: List[int],
    judge_test_predictions: List[int],
    unlabeled_prod_predictions: List[int],
    n_bootstrap: int = 10000,
) -> Dict[str, Any]:
    """
    Full FDE production workflow:
    1. Measure TPR, TNR, and Cohen's Kappa on held-out test split.
    2. Compute raw observed pass rate on production traces.
    3. Calculate Rogan-Gladen true success rate.
    4. Estimate 95% bootstrap confidence interval over production traces.
    """
    perf = calculate_tpr_tnr(human_test_labels, judge_test_predictions)
    kappa = calculate_cohens_kappa(human_test_labels, judge_test_predictions)

    p_obs = sum(unlabeled_prod_predictions) / len(unlabeled_prod_predictions) if unlabeled_prod_predictions else 0.0

    try:
        theta_hat = rogan_gladen_correction(p_obs, perf["tpr"], perf["tnr"])
        correction_valid = True
    except ValueError as e:
        theta_hat = p_obs
        correction_valid = False

    # Bootstrap CI on observed production data
    float_prod_values = [float(x) for x in unlabeled_prod_predictions]
    ci_lower, ci_upper = bootstrap_confidence_interval(float_prod_values, n_bootstrap=n_bootstrap)

    return {
        "calibration": {
            "tpr_sensitivity": round(perf["tpr"], 4),
            "tnr_specificity": round(perf["tnr"], 4),
            "raw_test_accuracy": round(perf["raw_accuracy"], 4),
            "cohens_kappa": round(kappa, 4),
            "is_calibrated": perf["tpr"] >= 0.80 and perf["tnr"] >= 0.80 and kappa >= 0.60,
        },
        "production_inference": {
            "total_production_traces": len(unlabeled_prod_predictions),
            "observed_pass_rate": round(p_obs, 4),
            "rogan_gladen_corrected_rate": round(theta_hat, 4),
            "correction_applied": correction_valid,
            "bootstrap_95_ci": (ci_lower, ci_upper),
        },
    }


if __name__ == "__main__":
    print("=" * 70)
    print(" Rogan-Gladen Bias Correction & Bootstrap CI Demonstration")
    print("=" * 70)

    # Simulated held-out test split (100 traces with human consensus labels)
    # Judge has 90% TPR and 80% TNR (slight tendency to over-approve)
    random.seed(42)
    human_labels = [1] * 70 + [0] * 30
    judge_preds = []
    for h in human_labels:
        if h == 1:
            judge_preds.append(1 if random.random() < 0.90 else 0)
        else:
            judge_preds.append(0 if random.random() < 0.80 else 1)

    # Production run: 1,000 unlabeled traces evaluated by the judge
    # Suppose raw observed pass rate is 84%
    unlabeled_preds = [1] * 840 + [0] * 160

    result = calibrate_and_evaluate_production(human_labels, judge_preds, unlabeled_preds)

    cal = result["calibration"]
    prod = result["production_inference"]

    print(f"Test Split Calibration (N={len(human_labels)}):")
    print(f"  - TPR (Sensitivity):  {cal['tpr_sensitivity'] * 100:.1f}%")
    print(f"  - TNR (Specificity):  {cal['tnr_specificity'] * 100:.1f}%")
    print(f"  - Cohen's Kappa:      {cal['cohens_kappa']:.3f} (>= 0.60 indicates strong agreement)")
    print()
    print(f"Production Run (N={prod['total_production_traces']}):")
    print(f"  - Observed Pass Rate:           {prod['observed_pass_rate'] * 100:.1f}%")
    print(f"  - Rogan-Gladen Corrected Rate:  {prod['rogan_gladen_corrected_rate'] * 100:.1f}%")
    ci = prod["bootstrap_95_ci"]
    print(f"  - 95% Bootstrap CI:             [{ci[0] * 100:.1f}%, {ci[1] * 100:.1f}%]")
    print("=" * 70)
