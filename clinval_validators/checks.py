"""Deterministic validation checks for medical-imaging prediction tables.

Pure Python compute layer. No network access: this module and the package it
lives in must run fully offline. Each public function computes one piece of the
report JSON contract that ``reporter`` consumes, and none of them call an LLM.
"""

from __future__ import annotations

from typing import Literal, TypedDict

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

# Subgroup flag thresholds, calibrated on the committed fixtures. A subgroup
# flags when its AUC is at least 0.10 below the rest of the table and the
# patient-level 95% interval for that drop lies entirely below zero. M030 in
# subgroup_scanner_degradation must flag; clean_patient_grouped must not.
_FLAG_DELTA = -0.10
_MIN_SUBGROUP_N = 50
_BOOTSTRAP_REPLICATES = 200
_BOOTSTRAP_SEED = 0

# Columns the checks read by name. Anything else in the table is ignored.
_REQUIRED_COLUMNS = ("patient_id", "machine_id", "site_id", "y_true", "y_prob", "split")

__all__ = [
    "LeakageResult",
    "SplitAuditResult",
    "SubgroupResult",
    "SubgroupSummary",
    "PooledMetric",
    "ReportPayload",
    "validate_predictions",
    "check_patient_leakage",
    "audit_split_quality",
    "check_subgroup_degradation",
    "compute_pooled_metric",
    "compute_risk",
    "run_checks",
    "RiskResult",
]


# --- Report JSON contract -------------------------------------------------
# The validators produce this payload; the reporter sends it to Claude.


class LeakageResult(TypedDict):
    overlapping_patient_ids: int
    leakage_rate: float


class SplitAuditResult(TypedDict):
    metric: str
    test_split_as_given: float
    patient_disjoint_sample: float | None
    sample_range95: list[float] | None
    gap: float | None


class SubgroupResult(TypedDict):
    key: str
    value: str
    n: int
    auc: float
    auc_rest: float
    delta_vs_rest: float
    delta_ci95: list[float] | None
    mean_predicted: float
    observed_rate: float
    flagged: bool


class SubgroupSummary(TypedDict):
    evaluated: int
    flagged: int
    interval_below_zero: int
    interval_above_zero: int


class PooledMetric(TypedDict):
    name: str
    rows: str
    value: float


class RiskResult(TypedDict):
    level: Literal["RED", "YELLOW", "GREEN"]
    reasons: list[str]


class ReportPayload(TypedDict):
    leakage: LeakageResult
    split_audit: SplitAuditResult
    subgroups: list[SubgroupResult]
    subgroup_summary: SubgroupSummary
    pooled_metric: PooledMetric
    risk: RiskResult


# --- Checks ---------------------------------------------------------------


def validate_predictions(df: pd.DataFrame) -> list[str]:
    """Return readable problems with a predictions table.

    An empty list means the deterministic checks can run. Called at the CLI
    and upload boundary, which is the one input this tool does not control.
    A missing column stops the remaining checks, because they read columns by
    name.
    """
    missing = [column for column in _REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        needed = ", ".join(_REQUIRED_COLUMNS)
        return [
            "Missing required column(s): "
            + ", ".join(missing)
            + f". A predictions table needs {needed}."
        ]

    problems: list[str] = []
    if not (df["split"] == "train").any():
        problems.append('No rows with split == "train".')
    if not (df["split"] == "test").any():
        problems.append('No rows with split == "test".')

    y_true = pd.to_numeric(df["y_true"], errors="coerce")
    if y_true.isna().any() or not y_true.dropna().isin([0, 1]).all():
        problems.append("y_true has values outside {0, 1}.")

    test_y = y_true[df["split"] == "test"]
    if len(test_y) and not ((test_y == 0).any() and (test_y == 1).any()):
        problems.append("Test rows do not contain both classes (0 and 1).")

    y_prob = pd.to_numeric(df["y_prob"], errors="coerce")
    if y_prob.isna().any():
        problems.append("y_prob is not numeric.")
    if (y_prob.notna() & ((y_prob < 0) | (y_prob > 1))).any():
        problems.append("y_prob has values outside [0, 1].")
    return problems


def check_patient_leakage(df: pd.DataFrame) -> LeakageResult:
    """Detect ``patient_id`` overlap between the train and test splits.

    Returns the count of patient IDs present in **both** the train and test
    splits (a ``val`` split also exists but is not a train/test leak) and the
    leakage rate: the fraction of distinct test patients that also appear in
    train — how much of the test evaluation is contaminated.
    """
    train = set(df.loc[df["split"] == "train", "patient_id"])
    test = set(df.loc[df["split"] == "test", "patient_id"])
    overlapping = len(train & test)
    return {
        "overlapping_patient_ids": overlapping,
        "leakage_rate": overlapping / len(test),
    }


def audit_split_quality(df: pd.DataFrame) -> SplitAuditResult:
    """Compare two AUCs computed from the same fixed predictions.

    ``test_split_as_given`` is the AUC on rows with ``split == "test"``.
    ``patient_disjoint_sample`` is the AUC on a seed-0 sample of 15% of
    patients drawn from every row, so that sample includes training rows.
    ``sample_range95`` is the 2.5th and 97.5th percentile of that sample AUC
    over seeds 0–199. ``gap`` is ``test_split_as_given`` minus
    ``patient_disjoint_sample``.

    On a small table a sample can hold one class, where AUC is undefined.
    Such seeds are left out of ``sample_range95``. When the seed-0 sample
    holds one class, ``patient_disjoint_sample`` and ``gap`` are None; when
    every seed does, ``sample_range95`` is None.

    The comparison cannot measure how much leakage inflated a metric. Both
    numbers rescore predictions that already exist; they do not come from
    retraining under a patient-grouped split. The leakage count is
    :func:`check_patient_leakage`.
    """
    y_true = df["y_true"].to_numpy()
    y_prob = df["y_prob"].to_numpy()
    test_rows = df["split"].to_numpy() == "test"
    test_split_as_given = float(roc_auc_score(y_true[test_rows], y_prob[test_rows]))

    groups = df["patient_id"]
    sample_aucs: list[float] = []
    patient_disjoint_sample: float | None = None
    for seed in range(200):
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=seed)
        _, sample_idx = next(splitter.split(df, groups=groups))
        if not _both_classes(y_true[sample_idx]):
            continue
        auc = float(roc_auc_score(y_true[sample_idx], y_prob[sample_idx]))
        if seed == 0:
            patient_disjoint_sample = auc
        sample_aucs.append(auc)

    sample_range95 = (
        [float(bound) for bound in np.percentile(sample_aucs, [2.5, 97.5])]
        if sample_aucs
        else None
    )
    return {
        "metric": "auc",
        "test_split_as_given": test_split_as_given,
        "patient_disjoint_sample": patient_disjoint_sample,
        "sample_range95": sample_range95,
        "gap": (
            None
            if patient_disjoint_sample is None
            else test_split_as_given - patient_disjoint_sample
        ),
    }


def _roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """ROC AUC with average ranks for ties, the same definition sklearn uses.

    A rank statistic keeps the patient-level bootstrap under a few seconds.
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=np.float64)
    n_pos = int(np.sum(y_true == 1))
    n = y_true.size
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(y_score, kind="mergesort")
    y_sorted = y_true[order]
    scores = y_score[order]
    change = np.empty(n, dtype=bool)
    change[0] = True
    change[1:] = scores[1:] != scores[:-1]
    group = np.cumsum(change) - 1
    counts = np.bincount(group)
    ends = np.cumsum(counts)
    average_rank = (ends - counts + 1 + ends) / 2.0
    sum_pos = float(average_rank[group][y_sorted == 1].sum())
    return (sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def _both_classes(y_true: np.ndarray) -> bool:
    return bool(y_true.size) and bool((y_true == 0).any()) and bool((y_true == 1).any())


def _patient_bootstrap_indices(patient_id: pd.Series) -> list[np.ndarray]:
    """Row indices for each patient-level resample of the whole table.

    Patients are drawn with replacement. A patient drawn twice contributes
    their rows twice. One draw is reused for every subgroup.
    """
    codes, _ = pd.factorize(patient_id, sort=False)
    order = np.argsort(codes, kind="mergesort")
    sorted_codes = codes[order]
    starts = np.flatnonzero(np.r_[True, sorted_codes[1:] != sorted_codes[:-1]])
    counts = np.diff(np.r_[starts, len(patient_id)])
    n_patients = len(counts)
    draws = np.random.default_rng(_BOOTSTRAP_SEED).integers(
        0, n_patients, size=(_BOOTSTRAP_REPLICATES, n_patients)
    )
    indices: list[np.ndarray] = []
    for draw in draws:
        repeated = counts[draw]
        total = int(repeated.sum())
        within = np.arange(total) - np.repeat(np.cumsum(repeated) - repeated, repeated)
        indices.append(order[np.repeat(starts[draw], repeated) + within])
    return indices


def _value_masks(values: np.ndarray) -> list[tuple[str, np.ndarray]]:
    masks: list[tuple[str, np.ndarray]] = []
    for value in pd.unique(values):
        if pd.isna(value):
            continue
        masks.append((str(value), values == value))
    return masks


def _age_band_masks(age: pd.Series) -> list[tuple[str, np.ndarray]]:
    """Decade bands such as ``50-59``. Missing ages are skipped."""
    numeric = pd.to_numeric(age, errors="coerce").to_numpy(dtype=float)
    valid = ~np.isnan(numeric)
    decade = np.full(numeric.size, -1, dtype=int)
    decade[valid] = (np.floor(numeric[valid] / 10.0) * 10).astype(int)
    masks: list[tuple[str, np.ndarray]] = []
    for band in sorted(set(decade[valid].tolist())):
        masks.append((f"{band}-{band + 9}", decade == band))
    return masks


def _subgroup_specs(df: pd.DataFrame) -> list[tuple[str, str, np.ndarray]]:
    specs: list[tuple[str, str, np.ndarray]] = []
    for key in ("machine_id", "site_id"):
        for label, mask in _value_masks(df[key].to_numpy()):
            specs.append((key, label, mask))
    if "density" in df.columns:
        for label, mask in _value_masks(df["density"].to_numpy()):
            specs.append(("density", label, mask))
    if "age" in df.columns:
        for label, mask in _age_band_masks(df["age"]):
            specs.append(("age", label, mask))
    return specs


def check_subgroup_degradation(df: pd.DataFrame) -> list[SubgroupResult]:
    """Compare each subgroup's AUC with the rest of the table.

    Evaluates ``machine_id`` and ``site_id``, and ``density`` and decade age
    bands when those columns exist. A subgroup is evaluated only when it has
    at least ``_MIN_SUBGROUP_N`` rows and both the subgroup and the rest of
    the table contain both classes.

    ``delta_vs_rest`` is the subgroup AUC minus the AUC of every other row.
    ``delta_ci95`` is the 2.5th and 97.5th percentile of that difference over
    a patient-level bootstrap (resample ``patient_id`` with replacement,
    200 replicates, seed 0). Replicates that lack a class in the subgroup or
    in the rest are skipped. The subgroup is flagged when ``delta_vs_rest``
    is at or below ``_FLAG_DELTA`` and the upper end of ``delta_ci95`` is
    below zero.

    ``mean_predicted`` and ``observed_rate`` are calibration-in-the-large for
    the subgroup. They are reported and never used to flag.
    """
    y_true = df["y_true"].to_numpy()
    y_prob = df["y_prob"].to_numpy(dtype=float)
    boots = _patient_bootstrap_indices(df["patient_id"])
    results: list[SubgroupResult] = []
    for key, value, mask in _subgroup_specs(df):
        n_sub = int(mask.sum())
        if n_sub < _MIN_SUBGROUP_N:
            continue
        y_sub = y_true[mask]
        y_rest = y_true[~mask]
        if not _both_classes(y_sub) or not _both_classes(y_rest):
            continue
        auc = _roc_auc(y_sub, y_prob[mask])
        auc_rest = _roc_auc(y_rest, y_prob[~mask])
        delta = auc - auc_rest
        deltas: list[float] = []
        for idx in boots:
            drawn = mask[idx]
            if not drawn.any() or not (~drawn).any():
                continue
            y_draw = y_true[idx]
            p_draw = y_prob[idx]
            y_draw_sub = y_draw[drawn]
            y_draw_rest = y_draw[~drawn]
            if not _both_classes(y_draw_sub) or not _both_classes(y_draw_rest):
                continue
            deltas.append(
                _roc_auc(y_draw_sub, p_draw[drawn]) - _roc_auc(y_draw_rest, p_draw[~drawn])
            )
        if deltas:
            low, high = (float(bound) for bound in np.percentile(deltas, [2.5, 97.5]))
            ci: list[float] | None = [low, high]
            flagged = bool(delta <= _FLAG_DELTA and high < 0)
        else:
            ci = None
            flagged = False
        results.append(
            {
                "key": key,
                "value": value,
                "n": n_sub,
                "auc": float(auc),
                "auc_rest": float(auc_rest),
                "delta_vs_rest": float(delta),
                "delta_ci95": ci,
                "mean_predicted": float(y_prob[mask].mean()),
                "observed_rate": float(np.mean(y_sub)),
                "flagged": flagged,
            }
        )
    return results


def compute_pooled_metric(df: pd.DataFrame) -> PooledMetric:
    """Compute the pooled headline metric (AUC) over all rows.

    Assumes every row's ``y_prob`` is a held-out or out-of-fold prediction.
    AUC is computed over the full table (not the test split alone) to match
    each manifest's ``verification.overall_auc``. ``rows`` says so in the
    payload, so the reporter does not present it as the test-split AUC.
    """
    return {
        "name": "auc",
        "rows": "all",
        "value": float(roc_auc_score(df["y_true"], df["y_prob"])),
    }


def _summarize_subgroups(subgroups: list[SubgroupResult]) -> SubgroupSummary:
    """Counts the reporter would otherwise have to tally from the list itself."""
    intervals = [sg["delta_ci95"] for sg in subgroups if sg["delta_ci95"] is not None]
    return {
        "evaluated": len(subgroups),
        "flagged": sum(sg["flagged"] for sg in subgroups),
        "interval_below_zero": sum(high < 0 for _, high in intervals),
        "interval_above_zero": sum(low > 0 for low, _ in intervals),
    }


def compute_risk(leakage: LeakageResult, subgroups: list[SubgroupResult]) -> RiskResult:
    """Choose RED, YELLOW, or GREEN from leakage and subgroup flags.

    RED when any patient is in both train and test. Otherwise YELLOW when
    any subgroup is flagged. Otherwise GREEN. The split audit is not an
    input: rescoring the same predictions cannot show inflation.
    """
    overlap = leakage["overlapping_patient_ids"]
    if overlap > 0:
        rate = leakage["leakage_rate"]
        return {
            "level": "RED",
            "reasons": [
                f"{overlap} patients appear in both the train and test splits "
                f"(leakage rate {rate:.1%})."
            ],
        }

    flagged = [subgroup for subgroup in subgroups if subgroup["flagged"]]
    if flagged:
        reasons: list[str] = []
        for subgroup in flagged:
            interval = subgroup["delta_ci95"]
            if interval is None:
                interval_text = "no bootstrap interval was available"
            else:
                interval_text = f"95% interval {interval[0]:+.3f} to {interval[1]:+.3f}"
            reasons.append(
                f"{subgroup['key']} {subgroup['value']} has AUC {subgroup['auc']:.3f} "
                f"against {subgroup['auc_rest']:.3f} on the rest of the table "
                f"(delta {subgroup['delta_vs_rest']:+.3f}, {interval_text})."
            )
        return {"level": "YELLOW", "reasons": reasons}

    return {
        "level": "GREEN",
        "reasons": [
            "No patient appears in both the train and test splits, and no subgroup is flagged."
        ],
    }


def run_checks(df: pd.DataFrame) -> ReportPayload:
    """Run every deterministic check and attach the risk level."""
    leakage = check_patient_leakage(df)
    subgroups = check_subgroup_degradation(df)
    return {
        "leakage": leakage,
        "split_audit": audit_split_quality(df),
        "subgroups": subgroups,
        "subgroup_summary": _summarize_subgroups(subgroups),
        "pooled_metric": compute_pooled_metric(df),
        "risk": compute_risk(leakage, subgroups),
    }
