"""Adapter tests: RSNA-SMBC train.csv -> validator predictions.csv.

No real RSNA data here — the fixture is a synthetic table shaped like the real
train.csv (the verified 14-column schema). The oracle for the split semantics is
the real ``check_patient_leakage`` validator: a patient-grouped split must be
clean, a random per-row split must leak (patients scattered across train/test).
"""

from __future__ import annotations

import numpy as np
import pytest

pd = pytest.importorskip("pandas")

from clinval_validators import check_patient_leakage  # noqa: E402
from rsna_to_predictions import (  # noqa: E402
    EXPECTED_COLUMNS,
    TARGET_COLUMNS,
    load_rsna,
    to_predictions,
)

_IMAGES_PER_PATIENT = 4  # 2 lateralities x 2 views
_N_PATIENTS = 60


def _rsna_fixture() -> pd.DataFrame:
    """Build a synthetic table with the real RSNA-SMBC 14-column schema.

    Site 1 patients carry ``density``/``machine_id``; Site 2 patients leave both
    NaN, mirroring the real dataset. ``cancer`` is assigned per patient so every
    image of a positive patient is positive.
    """
    rng = np.random.default_rng(0)
    rows = []
    image_id = 0
    for pid in range(_N_PATIENTS):
        site = 1 if pid < _N_PATIENTS // 2 else 2
        cancer = 1 if pid % 5 == 0 else 0
        age = int(rng.integers(40, 80))
        for laterality in ("L", "R"):
            for view in ("CC", "MLO"):
                rows.append(
                    {
                        "site_id": site,
                        "patient_id": pid,
                        "image_id": image_id,
                        "laterality": laterality,
                        "view": view,
                        "age": age,
                        "cancer": cancer,
                        "biopsy": int(rng.integers(0, 2)),
                        "invasive": cancer,
                        "BIRADS": int(rng.integers(0, 3)),
                        "implant": 0,
                        "density": "ABCD"[pid % 4] if site == 1 else np.nan,
                        "machine_id": float(rng.choice([21, 29, 49, 93]))
                        if site == 1
                        else np.nan,
                        "difficult_negative_case": False,
                    }
                )
                image_id += 1
    return pd.DataFrame(rows, columns=EXPECTED_COLUMNS)


def test_output_matches_target_schema() -> None:
    out = to_predictions(_rsna_fixture(), split_mode="patient_grouped", seed=0)
    assert list(out.columns) == TARGET_COLUMNS


def test_cancer_becomes_y_true_and_extras_dropped() -> None:
    fixture = _rsna_fixture()
    out = to_predictions(fixture, split_mode="patient_grouped", seed=0)
    merged = out.merge(fixture[["image_id", "cancer"]], on="image_id")
    assert (merged["y_true"] == merged["cancer"]).all()
    for dropped in ("biopsy", "invasive", "BIRADS", "implant", "difficult_negative_case"):
        assert dropped not in out.columns


def test_yprob_is_a_valid_probability() -> None:
    out = to_predictions(_rsna_fixture(), split_mode="patient_grouped", seed=0)
    assert out["y_prob"].notna().all()
    assert out["y_prob"].between(0.0, 1.0).all()
    assert len(out) == _N_PATIENTS * _IMAGES_PER_PATIENT


def test_patient_grouped_split_has_no_leakage() -> None:
    out = to_predictions(_rsna_fixture(), split_mode="patient_grouped", seed=0)
    assert check_patient_leakage(out)["overlapping_patient_ids"] == 0


def test_random_split_scatters_patients_across_train_test() -> None:
    out = to_predictions(_rsna_fixture(), split_mode="random", seed=0)
    # Each patient has 4 images; a per-row random split lands the same patient in
    # both train and test — exactly the leakage the validator is built to catch.
    assert check_patient_leakage(out)["overlapping_patient_ids"] > 0


def test_load_rsna_rejects_a_table_missing_a_column(tmp_path) -> None:
    bad = _rsna_fixture().drop(columns=["cancer"])
    path = tmp_path / "bad.csv"
    bad.to_csv(path, index=False)
    with pytest.raises(ValueError, match="cancer"):
        load_rsna(path)
