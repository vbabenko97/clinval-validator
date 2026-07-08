"""Detector checks against the labeled scenarios (xfail until Phase 1 lands)."""

from __future__ import annotations

from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

from validators import check_patient_leakage, check_subgroup_degradation  # noqa: E402

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "claude-science-artifacts" / "scenarios"


@pytest.mark.xfail(reason="Phase 1 not implemented", raises=NotImplementedError, strict=True)
def test_detects_train_test_patient_overlap(demo_csv_path: Path) -> None:
    df = pd.read_csv(demo_csv_path)
    result = check_patient_leakage(df)
    assert result["overlapping_patient_ids"] == 940


@pytest.mark.xfail(reason="Phase 1 not implemented", raises=NotImplementedError, strict=True)
def test_subgroup_degradation_is_detectable() -> None:
    df = pd.read_csv(SCENARIOS_DIR / "subgroup_scanner_degradation.csv")
    subgroups = check_subgroup_degradation(df)
    assert any(sg["flagged"] for sg in subgroups)
