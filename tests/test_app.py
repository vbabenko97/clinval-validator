"""Streamlit demo app: the pure scenario-listing helper.

The Streamlit UI itself is glue over already-tested functions (``_assemble_payload``
and the two reporters), so only the pure helper is unit-tested here. Importing
``app`` must not require Streamlit — it is imported lazily inside ``main``.
"""

from __future__ import annotations

from app import available_scenarios


def test_available_scenarios_lists_bundled_csvs() -> None:
    scenarios = available_scenarios()
    assert "optimistic_site_shortcut" in scenarios
    assert "clean_patient_grouped" in scenarios
    assert all(path.suffix == ".csv" for path in scenarios.values())
    assert scenarios["optimistic_site_shortcut"].exists()


def test_available_scenarios_excludes_the_summary_file() -> None:
    # _scenario_summary.csv is a different schema, not a predictions table.
    assert not any(name.startswith("_") for name in available_scenarios())
