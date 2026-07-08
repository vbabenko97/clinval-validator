"""CLI wiring tests: load -> validators -> payload -> reporter -> print.

Runs in-process with the reporter stubbed, so the whole pipeline is exercised
end-to-end with no network call.
"""

from __future__ import annotations

import json
from pathlib import Path

import cli
from cli import _assemble_payload, _load_predictions

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_CSV = REPO_ROOT / "claude-science-artifacts" / "scenarios" / "weak_random_split_leakage.csv"


def test_load_predictions_reads_the_table() -> None:
    df = _load_predictions(DEMO_CSV)
    assert len(df) == 8342
    assert {"patient_id", "machine_id", "site_id", "y_true", "y_prob", "split"} <= set(df.columns)


def test_assemble_payload_matches_contract_and_is_json_serializable() -> None:
    payload = _assemble_payload(_load_predictions(DEMO_CSV))
    assert set(payload) == {"leakage", "split_audit", "subgroups", "pooled_metric"}
    assert payload["leakage"]["overlapping_patient_ids"] == 940
    assert payload["pooled_metric"]["name"] == "auc"
    assert isinstance(payload["subgroups"], list)
    # The reporter serializes the payload with json.dumps; guard that boundary.
    assert json.loads(json.dumps(payload)) == payload


def test_cli_smoke_end_to_end(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli, "render_report", lambda payload: f"REPORT overlap={payload['leakage']['overlapping_patient_ids']}"
    )
    exit_code = cli.main(["--predictions", str(DEMO_CSV)])
    assert exit_code == 0
    out = capsys.readouterr().out.strip()
    assert "REPORT overlap=940" in out
