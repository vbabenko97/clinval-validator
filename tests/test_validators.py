"""Detector checks against the labeled scenarios (oracle = the manifests)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

_GENERATOR_DIR = Path(__file__).resolve().parent.parent / "claude-science-artifacts"
sys.path.insert(0, str(_GENERATOR_DIR))

from clinval_validators import (  # noqa: E402
    audit_split_quality,
    check_patient_leakage,
    check_subgroup_degradation,
    compute_pooled_metric,
    compute_risk,
    validate_predictions,
)
from leakage_generator import (  # noqa: E402
    Flaws,
    GeneratorConfig,
    SubgroupDegradation,
    generate,
)

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "claude-science-artifacts" / "scenarios"


def _load(scenario: str) -> pd.DataFrame:
    return pd.read_csv(SCENARIOS_DIR / f"{scenario}.csv")


def _valid_frame() -> pd.DataFrame:
    """Small table that satisfies every boundary check."""
    return pd.DataFrame(
        {
            "patient_id": ["P1", "P1", "P2", "P2"],
            "machine_id": ["M010", "M010", "M020", "M020"],
            "site_id": ["S01", "S01", "S02", "S02"],
            "y_true": [0, 1, 0, 1],
            "y_prob": [0.0, 1.0, 0.3, 0.7],
            "split": ["train", "train", "test", "test"],
        }
    )


# --- Input boundary ------------------------------------------------------


def test_validate_predictions_accepts_a_clean_fixture() -> None:
    assert validate_predictions(_load("clean_patient_grouped")) == []
    assert validate_predictions(_valid_frame()) == []


def test_validate_predictions_reports_missing_columns() -> None:
    df = _valid_frame().drop(columns=["machine_id", "split"])
    problems = validate_predictions(df)
    assert len(problems) == 1
    assert "machine_id" in problems[0]
    assert "split" in problems[0]


def test_validate_predictions_reports_a_missing_train_or_test_split() -> None:
    df = _valid_frame()
    df["split"] = "val"
    problems = validate_predictions(df)
    assert any('split == "train"' in problem for problem in problems)
    assert any('split == "test"' in problem for problem in problems)


def test_validate_predictions_reports_y_true_outside_0_1() -> None:
    df = _valid_frame()
    df.loc[0, "y_true"] = 2
    assert validate_predictions(df) == ["y_true has values outside {0, 1}."]


def test_validate_predictions_reports_test_rows_without_both_classes() -> None:
    df = _valid_frame()
    df.loc[df["split"] == "test", "y_true"] = 0
    assert validate_predictions(df) == ["Test rows do not contain both classes (0 and 1)."]


def test_validate_predictions_reports_non_numeric_y_prob() -> None:
    df = _valid_frame()
    df["y_prob"] = df["y_prob"].astype(object)
    df.loc[0, "y_prob"] = "high"
    assert validate_predictions(df) == ["y_prob is not numeric."]


def test_validate_predictions_reports_y_prob_outside_0_1() -> None:
    df = _valid_frame()
    df.loc[0, "y_prob"] = 1.2
    assert validate_predictions(df) == ["y_prob has values outside [0, 1]."]


# --- Check 1: patient-level leakage --------------------------------------


def test_detects_train_test_patient_overlap(demo_csv_path: Path) -> None:
    df = pd.read_csv(demo_csv_path)
    result = check_patient_leakage(df)
    assert result["overlapping_patient_ids"] == 940
    # leakage_rate = fraction of distinct test patients also seen in train = 940 / 959.
    test = set(df.loc[df["split"] == "test", "patient_id"])
    assert result["leakage_rate"] == pytest.approx(940 / len(test))
    assert result["leakage_rate"] == pytest.approx(0.9802, abs=1e-4)


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

# Seeds 7–11 were fixed before these outcomes were recorded. make_scenarios.py
# uses seeds 1–6. On seeds 7–36 (30 tables) this branch misses M030 on 4
# scanner tables (seeds 10, 11, 21, 22) and flags 6 clean tables (seeds 8, 10,
# 19, 20, 30, 32). The subgroup logic on main misses M030 on 2 of 30 (seeds
# 10, 22) and flags 6 of 30 clean tables (seeds 17, 19, 20, 25, 29, 30). A
# change in the outcomes below means the detection behaviour changed and must
# be reported in the commit message, not fixed by choosing other seeds.
_FRESH_SEEDS = (7, 8, 9, 10, 11)
_CLEAN_FLAGS = {
    7: set(),
    8: {("age", "80-89")},
    9: set(),
    10: {("age", "80-89")},
    11: set(),
}
_SCANNER_M030_FLAGGED = {7: True, 8: True, 9: True, 10: False, 11: False}


@pytest.fixture(scope="module")
def subgroups_by_scenario() -> dict[str, list]:
    """Run the subgroup check once per committed scenario."""
    names = (
        "clean_patient_grouped",
        "weak_random_split_leakage",
        "duplicate_row_leakage",
        "subgroup_scanner_degradation",
        "subgroup_density_degradation",
        "optimistic_site_shortcut",
    )
    return {name: check_subgroup_degradation(_load(name)) for name in names}


def test_subgroup_degradation_is_detectable(subgroups_by_scenario: dict[str, list]) -> None:
    subgroups = subgroups_by_scenario["subgroup_scanner_degradation"]
    assert any(sg["flagged"] for sg in subgroups)
    m030 = next(sg for sg in subgroups if sg["key"] == "machine_id" and sg["value"] == "M030")
    assert m030["flagged"]
    assert m030["auc"] == pytest.approx(0.6243, abs=1e-4)
    assert m030["delta_vs_rest"] == pytest.approx(m030["auc"] - m030["auc_rest"])
    assert m030["delta_vs_rest"] <= -0.10
    assert m030["delta_ci95"] is not None
    assert m030["delta_ci95"][1] < 0
    assert 0.0 <= m030["mean_predicted"] <= 1.0
    assert 0.0 <= m030["observed_rate"] <= 1.0


def test_density_degradation_flags_c_or_d_not_a_or_b(subgroups_by_scenario: dict[str, list]) -> None:
    flagged = {
        (sg["key"], sg["value"])
        for sg in subgroups_by_scenario["subgroup_density_degradation"]
        if sg["flagged"]
    }
    assert ("density", "C") in flagged or ("density", "D") in flagged
    assert ("density", "A") not in flagged
    assert ("density", "B") not in flagged


def test_no_subgroup_flags_on_clean_scenario(subgroups_by_scenario: dict[str, list]) -> None:
    subgroups = subgroups_by_scenario["clean_patient_grouped"]
    assert subgroups  # subgroups were evaluated
    assert not any(sg["flagged"] for sg in subgroups)


def test_subgroup_results_cover_machine_site_density_and_age(
    subgroups_by_scenario: dict[str, list],
) -> None:
    subgroups = subgroups_by_scenario["clean_patient_grouped"]
    assert {sg["key"] for sg in subgroups} == {"machine_id", "site_id", "density", "age"}
    assert "50-59" in {sg["value"] for sg in subgroups if sg["key"] == "age"}


@pytest.mark.parametrize(
    ("scenario", "level"),
    [
        ("clean_patient_grouped", "GREEN"),
        ("weak_random_split_leakage", "RED"),
        ("subgroup_scanner_degradation", "YELLOW"),
        ("subgroup_density_degradation", "YELLOW"),
    ],
)
def test_risk_level_follows_leakage_then_subgroup_flags(
    scenario: str, level: str, subgroups_by_scenario: dict[str, list]
) -> None:
    risk = compute_risk(check_patient_leakage(_load(scenario)), subgroups_by_scenario[scenario])
    assert risk["level"] == level
    assert risk["reasons"]
    assert all(isinstance(reason, str) and reason for reason in risk["reasons"])


def test_fresh_seed_subgroup_outcomes_are_recorded() -> None:
    """Record per-seed flags. Do not retune the seeds when a flag moves."""
    for seed in _FRESH_SEEDS:
        df, _manifest = generate(GeneratorConfig(seed=seed, flaws=Flaws(split_strategy="patient")))
        flagged = {
            (sg["key"], sg["value"]) for sg in check_subgroup_degradation(df) if sg["flagged"]
        }
        assert flagged == _CLEAN_FLAGS[seed]

    degradation = SubgroupDegradation("machine_id", ["M030"], target_auc=0.62)
    for seed in _FRESH_SEEDS:
        df, _manifest = generate(
            GeneratorConfig(
                seed=seed,
                flaws=Flaws(split_strategy="patient", subgroup_degradations=[degradation]),
            )
        )
        m030_flagged = any(
            sg["key"] == "machine_id" and sg["value"] == "M030" and sg["flagged"]
            for sg in check_subgroup_degradation(df)
        )
        assert m030_flagged is _SCANNER_M030_FLAGGED[seed]


# --- Check 2: split-quality audit ----------------------------------------


def test_audit_split_quality_structure_and_direction() -> None:
    df = _load("weak_random_split_leakage")
    audit = audit_split_quality(df)
    assert audit["metric"] == "auc"
    # Both AUCs are computed from the same fixed y_prob.
    assert 0.0 < audit["test_split_as_given"] < 1.0
    assert 0.0 < audit["patient_disjoint_sample"] < 1.0
    low, high = audit["sample_range95"]
    assert low <= audit["patient_disjoint_sample"] <= high
    assert audit["gap"] == pytest.approx(
        audit["test_split_as_given"] - audit["patient_disjoint_sample"]
    )
    # The primary leakage signal for a random split is shared patients.
    assert check_patient_leakage(df)["overlapping_patient_ids"] > 0


def test_audit_split_quality_is_reproducible() -> None:
    df = _load("weak_random_split_leakage")
    assert audit_split_quality(df) == audit_split_quality(df)
