"""Reporter test: offline, with a mocked Anthropic client (no live API call)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import reporter
from reporter import (
    CRITIQUE_SYSTEM_PROMPT_PATH,
    MODEL,
    SYSTEM_PROMPT_PATH,
    MissingAPIKeyError,
    render_report,
    render_reviewer_critique,
)

SAMPLE_PAYLOAD = {
    "leakage": {"overlapping_patient_ids": 940, "leakage_rate": 0.4702},
    "split_audit": {"metric": "auc", "random_split": 0.8273, "grouped_split": 0.8994, "gap": -0.0721},
    "subgroups": [
        {"key": "machine_id", "value": "M030", "n": 1048, "auc": 0.6243, "delta_vs_pooled": -0.21, "flagged": True}
    ],
    "pooled_metric": {"name": "auc", "value": 0.8425},
}


def test_prompts_name_the_fields_python_computes() -> None:
    field_names = (
        "test_split_as_given",
        "patient_disjoint_sample",
        "sample_range95",
        "auc_rest",
        "delta_vs_rest",
        "delta_ci95",
        "mean_predicted",
        "observed_rate",
        "risk",
        "reasons",
    )
    for path in (SYSTEM_PROMPT_PATH, CRITIQUE_SYSTEM_PROMPT_PATH):
        text = path.read_text(encoding="utf-8")
        missing = [name for name in field_names if name not in text]
        assert missing == [], path.name


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
    assert captured["max_tokens"] == 1024

    user_message = captured["messages"][0]
    assert user_message["role"] == "user"
    assert json.loads(user_message["content"]) == SAMPLE_PAYLOAD

    # The operative reviewer prompt is sent, not the file's Markdown doc header.
    assert "senior clinical-AI validation reviewer" in captured["system"]
    assert "# Reporter system prompt" not in captured["system"]


def test_render_report_raises_a_named_error_when_the_key_is_absent(monkeypatch) -> None:
    # A missing key is a user-facing condition, not a bug: it must not surface as a
    # bare KeyError traceback. No network call is attempted.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError, match="ANTHROPIC_API_KEY"):
        render_report(SAMPLE_PAYLOAD)


def test_render_reviewer_critique_raises_a_named_error_when_the_key_is_absent(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError, match="ANTHROPIC_API_KEY"):
        render_reviewer_critique(SAMPLE_PAYLOAD)


def test_render_reviewer_critique_sends_payload_json_to_opus(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured: dict = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(text="Reviewer verdict: reject")])

    class FakeAnthropic:
        def __init__(self, api_key=None):
            captured["api_key"] = api_key
            self.messages = FakeMessages()

    monkeypatch.setattr(reporter.report, "Anthropic", FakeAnthropic)

    critique_text = render_reviewer_critique(SAMPLE_PAYLOAD)

    assert critique_text == "Reviewer verdict: reject"
    assert captured["api_key"] == "test-key"
    assert captured["model"] == MODEL == "claude-opus-4-8"
    assert captured["max_tokens"] == 1024

    user_message = captured["messages"][0]
    assert user_message["role"] == "user"
    assert json.loads(user_message["content"]) == SAMPLE_PAYLOAD

    # The critique step loads its own prompt, distinct from the risk reporter's,
    # and sends the operative prompt rather than the file's Markdown doc header.
    assert "Methods paragraph" in captured["system"]
    assert "senior clinical-AI validation reviewer" not in captured["system"]
    assert "# Reviewer critique system prompt" not in captured["system"]
