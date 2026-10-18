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


def test_cli_rejects_an_invalid_table(tmp_path: Path, capsys) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("patient_id,y_true,y_prob\n1,0,0.2\n", encoding="utf-8")
    exit_code = cli.main(["--predictions", str(path)])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Missing required column" in captured.err
    assert "machine_id" in captured.err
    assert "Traceback" not in captured.err


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


def test_cli_defaults_to_risk_mode(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "render_report", lambda payload: "RISK-DEFAULT")
    monkeypatch.setattr(cli, "render_reviewer_critique", lambda payload: "CRITIQUE-UNUSED")
    exit_code = cli.main(["--predictions", str(DEMO_CSV)])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "RISK-DEFAULT"


def test_cli_without_an_api_key_prints_the_payload_and_a_readable_error(monkeypatch, capsys) -> None:
    # The deterministic layer runs offline, so a missing key must not lose that work
    # or dump a traceback. This is the command that appears in the demo video.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exit_code = cli.main(["--predictions", str(DEMO_CSV), "--mode", "critique"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out)["leakage"]["overlapping_patient_ids"] == 940
    assert "ANTHROPIC_API_KEY" in captured.err
    assert "Traceback" not in captured.err
    assert "KeyError" not in captured.err


def test_cli_critique_mode_uses_reviewer_critique(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "render_report", lambda payload: "RISK-UNUSED")
    monkeypatch.setattr(
        cli,
        "render_reviewer_critique",
        lambda payload: f"CRITIQUE overlap={payload['leakage']['overlapping_patient_ids']}",
    )
    exit_code = cli.main(["--predictions", str(DEMO_CSV), "--mode", "critique"])
    assert exit_code == 0
    out = capsys.readouterr().out.strip()
    assert "CRITIQUE overlap=940" in out
    assert "RISK-UNUSED" not in out
