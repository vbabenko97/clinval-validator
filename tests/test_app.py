"""Streamlit demo app: the pure scenario-listing helper.

The Streamlit UI itself is glue over already-tested functions (``run_checks``
and the two reporters), so only the pure helper is unit-tested here. Importing
``app`` must not require Streamlit — it is imported lazily inside ``main``.
The upload boundary is ``validate_predictions``, tested in ``test_validators``.
"""

from __future__ import annotations

import pandas as pd

from app import available_scenarios
from clinval_validators import validate_predictions


def test_available_scenarios_lists_bundled_csvs() -> None:
    scenarios = available_scenarios()
    assert "optimistic_site_shortcut" in scenarios
    assert "clean_patient_grouped" in scenarios
    assert all(path.suffix == ".csv" for path in scenarios.values())
    assert scenarios["optimistic_site_shortcut"].exists()


def test_available_scenarios_excludes_the_summary_file() -> None:
    # _scenario_summary.csv is a different schema, not a predictions table.
    assert not any(name.startswith("_") for name in available_scenarios())


def test_bundled_scenario_passes_validation() -> None:
    df = pd.read_csv(available_scenarios()["clean_patient_grouped"])
    assert validate_predictions(df) == []
