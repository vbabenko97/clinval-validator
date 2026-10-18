"""Deterministic validation checks for medical-imaging prediction tables.

Pure Python compute layer. No network access: this module and the package it
lives in must run fully offline. Each public function computes one piece of the
report JSON contract that ``reporter`` consumes, and none of them call an LLM.
"""

from __future__ import annotations

from typing import TypedDict

import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupShuffleSplit

# Subgroup flag thresholds, calibrated against the labeled scenarios: M030 in
# subgroup_scanner_degradation sits 0.21 below pooled and must flag, while every
# subgroup in clean_patient_grouped is within 0.07 of pooled and must not.
_FLAG_DELTA = -0.10
_MIN_SUBGROUP_N = 50

# Columns the checks read by name. Anything else in the table is ignored.
_REQUIRED_COLUMNS = ("patient_id", "machine_id", "site_id", "y_true", "y_prob", "split")

__all__ = [
    "LeakageResult",
    "SplitAuditResult",
    "SubgroupResult",
    "PooledMetric",
    "ReportPayload",
    "validate_predictions",
    "check_patient_leakage",
    "audit_split_quality",
    "check_subgroup_degradation",
    "compute_pooled_metric",
]


# --- Report JSON contract -------------------------------------------------
# Shape mirrors prompts/opus-4-8/reporter_system_prompt.md exactly. The
# validators produce this payload; the reporter consumes it. Do not add fields
# beyond the ones documented there.


class LeakageResult(TypedDict):
    overlapping_patient_ids: int
    leakage_rate: float


class SplitAuditResult(TypedDict):
    metric: str
    random_split: float
    grouped_split: float
    gap: float


class SubgroupResult(TypedDict):
    key: str
    value: str
    n: int
    auc: float
    delta_vs_pooled: float
    flagged: bool


class PooledMetric(TypedDict):
    name: str
    value: float


class ReportPayload(TypedDict):
    leakage: LeakageResult
    split_audit: SplitAuditResult
    subgroups: list[SubgroupResult]
    pooled_metric: PooledMetric


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
    """Recompute the headline metric under the file's split vs a grouped split.

    Both AUCs read the same fixed ``y_prob`` on two different test subsets, so
    this measures how sensitive the headline metric is to the choice of split —
    it is a diagnostic, not a retrained proof of split-induced optimism.
    ``random_split`` uses the test rows as given in the file; ``grouped_split``
    re-partitions by ``patient_id`` with a fixed seed so no patient spans the
    fold boundary. The rigorous leakage signal is :func:`check_patient_leakage`;
    ``gap`` can be small or even negative when the leak is structural patient
    overlap rather than an inflated ``y_prob``.
    """
    test_rows = df[df["split"] == "test"]
    random_split = float(roc_auc_score(test_rows["y_true"], test_rows["y_prob"]))

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=0)
    _, grouped_test_idx = next(splitter.split(df, groups=df["patient_id"]))
    grouped_fold = df.iloc[grouped_test_idx]
    grouped_split = float(roc_auc_score(grouped_fold["y_true"], grouped_fold["y_prob"]))

    return {
        "metric": "auc",
        "random_split": random_split,
        "grouped_split": grouped_split,
        "gap": random_split - grouped_split,
    }


def check_subgroup_degradation(df: pd.DataFrame) -> list[SubgroupResult]:
    """Compute per-``machine_id``/``site_id`` AUC and flag degraded subgroups.

    Returns one entry per evaluated subgroup, each carrying its AUC, delta
    versus the pooled metric, and whether it is flagged as significantly below
    pooled performance. A subgroup is skipped (not evaluated) when it has fewer
    than ``_MIN_SUBGROUP_N`` rows or lacks both classes, since its AUC would be
    undefined or too noisy to trust.
    """
    pooled_auc = float(roc_auc_score(df["y_true"], df["y_prob"]))
    results: list[SubgroupResult] = []
    for key in ("machine_id", "site_id"):
        for value, group in df.groupby(key):
            if len(group) < _MIN_SUBGROUP_N or group["y_true"].nunique() < 2:
                continue
            auc = float(roc_auc_score(group["y_true"], group["y_prob"]))
            delta = auc - pooled_auc
            results.append(
                {
                    "key": key,
                    "value": str(value),
                    "n": len(group),
                    "auc": auc,
                    "delta_vs_pooled": delta,
                    "flagged": delta <= _FLAG_DELTA,
                }
            )
    return results


def compute_pooled_metric(df: pd.DataFrame) -> PooledMetric:
    """Compute the pooled headline metric (AUC) over all rows.

    This is the reference value that subgroup deltas are measured against and
    the ``pooled_metric`` field of the report payload. AUC is computed over the
    full table (not the test split alone) to match each manifest's
    ``verification.overall_auc`` and give every subgroup enough positives for a
    defined per-subgroup AUC at this dataset's ~1.5% prevalence.
    """
    return {"name": "auc", "value": float(roc_auc_score(df["y_true"], df["y_prob"]))}
