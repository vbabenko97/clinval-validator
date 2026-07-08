"""Detector checks against the labeled scenarios (oracle = the manifests)."""

from __future__ import annotations

from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

from validators import (  # noqa: E402
    audit_split_quality,
    check_patient_leakage,
    check_subgroup_degradation,
    compute_pooled_metric,
)

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "claude-science-artifacts" / "scenarios"


def _load(scenario: str) -> pd.DataFrame:
    return pd.read_csv(SCENARIOS_DIR / f"{scenario}.csv")


# --- Check 1: patient-level leakage --------------------------------------


def test_detects_train_test_patient_overlap(demo_csv_path: Path) -> None:
    df = pd.read_csv(demo_csv_path)
    result = check_patient_leakage(df)
    assert result["overlapping_patient_ids"] == 940
    # Pinned definition: overlap / distinct patients in (train ∪ test) = 940 / 1999.
    train = set(df.loc[df["split"] == "train", "patient_id"])
    test = set(df.loc[df["split"] == "test", "patient_id"])
    assert result["leakage_rate"] == pytest.approx(940 / len(train | test))
    assert result["leakage_rate"] == pytest.approx(0.4702, abs=1e-4)


def test_leakage_zero_on_clean_grouped_split() -> None:
    result = check_patient_leakage(_load("clean_patient_grouped"))
    assert result["overlapping_patient_ids"] == 0
    assert result["leakage_rate"] == 0.0


def test_detects_duplicate_row_leaked_patients() -> None:
    result = check_patient_leakage(_load("duplicate_row_leakage"))
    assert result["overlapping_patient_ids"] == 113


def test_detects_optimistic_site_shortcut_leakage() -> None:
    # The demo's dramatic case: inflated AUC co-occurs with detectable leakage.
    result = check_patient_leakage(_load("optimistic_site_shortcut"))
    assert result["overlapping_patient_ids"] == 990


# --- Pooled metric -------------------------------------------------------


@pytest.mark.parametrize(
    ("scenario", "expected_auc"),
    [
        ("clean_patient_grouped", 0.8598),
        ("weak_random_split_leakage", 0.8425),
        ("subgroup_scanner_degradation", 0.8345),
        ("optimistic_site_shortcut", 0.9647),
    ],
)
def test_pooled_metric_matches_manifest_overall_auc(scenario: str, expected_auc: float) -> None:
    result = compute_pooled_metric(_load(scenario))
    assert result["name"] == "auc"
    assert result["value"] == pytest.approx(expected_auc, abs=1e-4)


# --- Check 3: subgroup degradation ---------------------------------------


def test_subgroup_degradation_is_detectable() -> None:
    subgroups = check_subgroup_degradation(_load("subgroup_scanner_degradation"))
    assert any(sg["flagged"] for sg in subgroups)
    m030 = next(sg for sg in subgroups if sg["key"] == "machine_id" and sg["value"] == "M030")
    assert m030["flagged"]
    assert m030["auc"] == pytest.approx(0.6243, abs=1e-4)
    assert m030["delta_vs_pooled"] < -0.10


def test_no_subgroup_flags_on_clean_scenario() -> None:
    subgroups = check_subgroup_degradation(_load("clean_patient_grouped"))
    assert subgroups  # subgroups were evaluated
    assert not any(sg["flagged"] for sg in subgroups)


def test_subgroup_results_cover_machine_and_site_keys() -> None:
    keys = {sg["key"] for sg in check_subgroup_degradation(_load("clean_patient_grouped"))}
    assert keys == {"machine_id", "site_id"}


# --- Check 2: split-quality audit ----------------------------------------


def test_audit_split_quality_structure_and_direction() -> None:
    df = _load("weak_random_split_leakage")
    audit = audit_split_quality(df)
    assert audit["metric"] == "auc"
    # Both AUCs are finite probabilities computed over the same fixed y_prob.
    assert 0.0 < audit["random_split"] < 1.0
    assert 0.0 < audit["grouped_split"] < 1.0
    # gap is exactly the signed difference (may be small or negative — the leak
    # here is structural patient overlap, not an inflated y_prob).
    assert audit["gap"] == pytest.approx(audit["random_split"] - audit["grouped_split"])
    # The primary leakage signal for a random split is shared patients.
    assert check_patient_leakage(df)["overlapping_patient_ids"] > 0


def test_audit_split_quality_is_reproducible() -> None:
    df = _load("weak_random_split_leakage")
    assert audit_split_quality(df) == audit_split_quality(df)
