"""Reporter test: offline, with a mocked Anthropic client (no live API call)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import reporter
from reporter import MODEL, render_report

SAMPLE_PAYLOAD = {
    "leakage": {"overlapping_patient_ids": 940, "leakage_rate": 0.4702},
    "split_audit": {"metric": "auc", "random_split": 0.8273, "grouped_split": 0.8994, "gap": -0.0721},
    "subgroups": [
        {"key": "machine_id", "value": "M030", "n": 1048, "auc": 0.6243, "delta_vs_pooled": -0.21, "flagged": True}
    ],
    "pooled_metric": {"name": "auc", "value": 0.8425},
}


def test_render_report_sends_payload_json_to_opus(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured: dict = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(text="RED: leakage present")])

    class FakeAnthropic:
        def __init__(self, api_key=None):
            captured["api_key"] = api_key
            self.messages = FakeMessages()

    monkeypatch.setattr(reporter.report, "Anthropic", FakeAnthropic)

    report_text = render_report(SAMPLE_PAYLOAD)

    assert report_text == "RED: leakage present"
    assert captured["api_key"] == "test-key"
    assert captured["model"] == MODEL == "claude-opus-4-8"

    user_message = captured["messages"][0]
    assert user_message["role"] == "user"
    assert json.loads(user_message["content"]) == SAMPLE_PAYLOAD

    # The operative reviewer prompt is sent, not the file's Markdown doc header.
    assert "senior clinical-AI validation reviewer" in captured["system"]
    assert "# Reporter system prompt" not in captured["system"]
