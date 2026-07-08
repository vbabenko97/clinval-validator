"""Shared test fixtures: paths into the labeled scenario oracle."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = REPO_ROOT / "claude-science-artifacts" / "scenarios"

# Scenario the demo and end-to-end tests run against: a random split with a
# known 940 train/test patient overlap.
DEMO_SCENARIO = "weak_random_split_leakage"


@pytest.fixture
def demo_csv_path() -> Path:
    return SCENARIOS_DIR / f"{DEMO_SCENARIO}.csv"


@pytest.fixture
def demo_manifest_path() -> Path:
    return SCENARIOS_DIR / f"{DEMO_SCENARIO}.manifest.json"
