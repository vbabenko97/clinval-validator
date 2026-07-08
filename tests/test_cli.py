"""End-to-end CLI smoke test (xfail until Phase 1 lands)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CLI = REPO_ROOT / "cli.py"
DEMO_CSV = REPO_ROOT / "claude-science-artifacts" / "scenarios" / "weak_random_split_leakage.csv"


@pytest.mark.xfail(reason="Phase 1 not implemented", strict=False)
def test_cli_smoke_end_to_end() -> None:
    result = subprocess.run(
        [sys.executable, str(CLI), "--predictions", str(DEMO_CSV)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert result.stdout.strip()
