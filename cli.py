"""Command-line entrypoint: validate a predictions CSV and print the risk report.

Wires the two layers: load predictions -> run the deterministic validators ->
hand the payload to the reporter -> print the report. The compute logic lives in
``clinval_validators`` and runs offline; ``reporter`` is the only part that needs
the network, so without an API key the validators still run and their JSON is printed.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from clinval_validators import run_checks, validate_predictions
from reporter import (
    API_KEY_ENV,
    MissingAPIKeyError,
    ReportNotRenderedError,
    render_report,
    render_reviewer_critique,
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
    parser.add_argument(
        "--mode",
        choices=("risk", "critique"),
        default="risk",
        help="risk: GREEN/YELLOW/RED risk report (default). "
        "critique: reviewer critique + corrected Methods paragraph.",
    )
    return parser.parse_args(argv)


def _load_predictions(path: Path) -> pd.DataFrame:
    """Load the predictions table (Phase 1: read the CSV with pandas)."""
    return pd.read_csv(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    df = _load_predictions(args.predictions)
    problems = validate_predictions(df)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    payload = run_checks(df)
    render = render_reviewer_critique if args.mode == "critique" else render_report
    try:
        print(render(payload))
    except MissingAPIKeyError:
        print(json.dumps(payload, indent=2))
        print(
            f"\nThe deterministic checks above ran offline and are complete.\n"
            f"{API_KEY_ENV} is not set, so the {args.mode} report was not rendered.\n"
            f"Set a key to add Claude's narration:\n"
            f"    export {API_KEY_ENV}=sk-ant-...",
            file=sys.stderr,
        )
        return 1
    except ReportNotRenderedError as exc:
        print(json.dumps(payload, indent=2))
        print(
            f"\nThe deterministic checks above ran offline and are complete.\n"
            f"{exc} The {args.mode} report was not rendered.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
