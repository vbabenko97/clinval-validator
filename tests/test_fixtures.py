"""Oracle sanity checks: the labeled fixtures carry the schema and injected flaws."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

EXPECTED_COLUMNS = [
    "patient_id",
    "image_id",
    "laterality",
    "view",
    "machine_id",
    "site_id",
    "age",
    "density",
    "y_true",
    "y_prob",
    "split",
]


@pytest.mark.skip(reason="Phase 1 not implemented")
def test_fixture_has_expected_schema(demo_csv_path: Path) -> None:
    with demo_csv_path.open(newline="") as fh:
        header = next(csv.reader(fh))
    assert header == EXPECTED_COLUMNS


@pytest.mark.skip(reason="Phase 1 not implemented")
def test_leakage_is_injected(demo_manifest_path: Path) -> None:
    manifest = json.loads(demo_manifest_path.read_text())
    assert manifest["expected_detections"]["train_test_patient_overlap"] == 940
