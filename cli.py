"""Command-line entrypoint: validate a predictions CSV and print the risk report.

Wires the two layers: load predictions -> run the deterministic validators ->
assemble the report payload -> hand it to the reporter -> print the report. The
compute and LLM logic live in ``validators`` and ``reporter``; the pieces that
raise ``NotImplementedError`` are what Phase 1 fills in.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from reporter import render_report
from validators import (
    ReportPayload,
    audit_split_quality,
    check_patient_leakage,
    check_subgroup_degradation,
    compute_pooled_metric,
)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clinval-validate",
        description="Flag leakage, weak splits, and subgroup degradation in a predictions.csv.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        required=True,
        help="Path to the predictions CSV (see README for the expected schema).",
    )
    return parser.parse_args(argv)


def _load_predictions(path: Path) -> pd.DataFrame:
    """Load the predictions table (Phase 1: read the CSV with pandas)."""
    return pd.read_csv(path)


def _assemble_payload(df: pd.DataFrame) -> ReportPayload:
    """Run every validator and assemble the report JSON contract."""
    return {
        "leakage": check_patient_leakage(df),
        "split_audit": audit_split_quality(df),
        "subgroups": check_subgroup_degradation(df),
        "pooled_metric": compute_pooled_metric(df),
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    df = _load_predictions(args.predictions)
    payload = _assemble_payload(df)
    report = render_report(payload)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
