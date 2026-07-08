"""Deterministic validation checks for medical-imaging prediction tables.

Pure Python compute layer. No network access: this module and the package it
lives in must run fully offline. Each public function computes one piece of the
report JSON contract that ``reporter`` consumes, and none of them call an LLM.

Phase 1 fills in the bodies; every check is a stub (``NotImplementedError``)
until then.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import pandas as pd

__all__ = [
    "LeakageResult",
    "SplitAuditResult",
    "SubgroupResult",
    "PooledMetric",
    "ReportPayload",
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


def check_patient_leakage(df: pd.DataFrame) -> LeakageResult:
    """Detect ``patient_id`` overlap between the train and test splits.

    Returns the count of patient IDs that appear in more than one split and the
    corresponding leakage rate.
    """
    raise NotImplementedError


def audit_split_quality(df: pd.DataFrame) -> SplitAuditResult:
    """Recompute the headline metric under a random vs a grouped split.

    Surfaces the gap between the optimistic random-split metric and the
    leakage-safe patient/site-grouped metric.
    """
    raise NotImplementedError


def check_subgroup_degradation(df: pd.DataFrame) -> list[SubgroupResult]:
    """Compute per-``machine_id``/``site_id`` AUC and flag degraded subgroups.

    Returns one entry per evaluated subgroup, each carrying its AUC, delta
    versus the pooled metric, and whether it is flagged as significantly below
    pooled performance.
    """
    raise NotImplementedError


def compute_pooled_metric(df: pd.DataFrame) -> PooledMetric:
    """Compute the pooled headline metric (AUC) across the test-split rows.

    This is the reference value that subgroup deltas are measured against and
    the ``pooled_metric`` field of the report payload.
    """
    raise NotImplementedError
