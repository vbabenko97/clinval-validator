"""Streamlit demo app: the pure scenario-listing helper.

The Streamlit UI itself is glue over already-tested functions (``_assemble_payload``
and the two reporters), so only the pure helper is unit-tested here. Importing
``app`` must not require Streamlit — it is imported lazily inside ``main``.
"""

from __future__ import annotations

import pandas as pd

from app import REQUIRED_COLUMNS, available_scenarios, missing_columns


def test_available_scenarios_lists_bundled_csvs() -> None:
    scenarios = available_scenarios()
    assert "optimistic_site_shortcut" in scenarios
    assert "clean_patient_grouped" in scenarios
    assert all(path.suffix == ".csv" for path in scenarios.values())
    assert scenarios["optimistic_site_shortcut"].exists()


def test_available_scenarios_excludes_the_summary_file() -> None:
    # _scenario_summary.csv is a different schema, not a predictions table.
    assert not any(name.startswith("_") for name in available_scenarios())


def test_bundled_scenario_satisfies_the_required_schema() -> None:
    df = pd.read_csv(available_scenarios()["clean_patient_grouped"])
    assert missing_columns(df) == []


def test_missing_columns_names_every_absent_required_column() -> None:
    df = pd.DataFrame({"patient_id": [1], "y_true": [0], "y_prob": [0.5]})
    assert missing_columns(df) == ["machine_id", "site_id", "split"]


def test_missing_columns_ignores_extra_columns() -> None:
    df = pd.DataFrame({column: [0] for column in REQUIRED_COLUMNS} | {"laterality": ["L"]})
    assert missing_columns(df) == []
