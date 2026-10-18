"""Reporter test: offline, with a mocked Anthropic client (no live API call)."""

from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest

import reporter
from reporter import (
    CRITIQUE_SYSTEM_PROMPT_PATH,
    EFFORT,
    MAX_TOKENS,
    MODEL,
    SYSTEM_PROMPT_PATH,
    MissingAPIKeyError,
    ReportNotRenderedError,
    render_report,
    render_reviewer_critique,
)


def _text(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _fake_client(monkeypatch, content: list, stop_reason: str = "end_turn") -> dict:
    """Replace the Anthropic client; return the dict that records each request."""
    captured: dict = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(content=content, stop_reason=stop_reason)

    class FakeAnthropic:
        def __init__(self, api_key=None):
            captured["api_key"] = api_key
            self.beta = SimpleNamespace(messages=FakeMessages())

    monkeypatch.setattr(reporter.report, "Anthropic", FakeAnthropic)
    return captured

# leakage_rate is 940 / 959 on weak_random_split_leakage. The other fields match
# the current payload contract; this dict is a stub, not a full scenario dump.
SAMPLE_PAYLOAD = {
    "leakage": {"overlapping_patient_ids": 940, "leakage_rate": 0.9802},
    "split_audit": {
        "metric": "auc",
        "test_split_as_given": 0.8273,
        "patient_disjoint_sample": 0.8994,
        "sample_range95": [0.7523, 0.9336],
        "gap": -0.0721,
    },
    "subgroups": [
        {
            "key": "machine_id",
            "value": "M031",
            "n": 1020,
            "auc": 0.8075,
            "auc_rest": 0.8490,
            "delta_vs_rest": -0.0415,
            "delta_ci95": [-0.1702, 0.0521],
            "mean_predicted": 0.5111,
            "observed_rate": 0.0216,
            "flagged": False,
        }
    ],
    "subgroup_summary": {
        "evaluated": 20,
        "flagged": 0,
        "interval_below_zero": 0,
        "interval_above_zero": 1,
    },
    "pooled_metric": {"name": "auc", "rows": "all", "value": 0.8425},
    "risk": {
        "level": "RED",
        "reasons": [
            "940 patients appear in both the train and test splits (leakage rate 98.0%)."
        ],
    },
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
        "subgroup_summary",
        "interval_below_zero",
        "interval_above_zero",
        "risk",
        "reasons",
    )
    for path in (SYSTEM_PROMPT_PATH, CRITIQUE_SYSTEM_PROMPT_PATH):
        text = path.read_text(encoding="utf-8")
        missing = [name for name in field_names if name not in text]
        assert missing == [], path.name


def test_prompts_keep_the_rules_live_reports_broke() -> None:
    # Live reports read the split audit as evidence of no inflation and left the
    # RED critique recommendation as "Reject or Major revision".
    for path in (SYSTEM_PROMPT_PATH, CRITIQUE_SYSTEM_PROMPT_PATH):
        assert "free of inflation" in path.read_text(encoding="utf-8"), path.name
    assert "exactly one recommendation" in CRITIQUE_SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def test_render_report_sends_payload_json_to_opus(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured = _fake_client(monkeypatch, [_text("RED: leakage present")])

    report_text = render_report(SAMPLE_PAYLOAD)

    assert report_text == "RED: leakage present"
    assert captured["api_key"] == "test-key"
    assert captured["model"] == MODEL == "claude-opus-5-5"
    assert captured["max_tokens"] == MAX_TOKENS == 4096
    # Opus 5.5 rejects thinking={"type": "disabled"}; effort is the only control.
    assert "thinking" not in captured
    assert captured["output_config"] == {"effort": EFFORT} == {"effort": "low"}
    # A classifier refusal is retried on Anthropic's recommended model for its category.
    assert captured["betas"] == ["server-side-fallback-2026-07-01"]
    assert captured["extra_body"] == {"fallbacks": "default"}

    user_message = captured["messages"][0]
    assert user_message["role"] == "user"
    assert json.loads(user_message["content"]) == SAMPLE_PAYLOAD

    # The operative reviewer prompt is sent, not the file's Markdown doc header.
    assert "senior clinical-AI validation reviewer" in captured["system"]
    assert "# Reporter system prompt" not in captured["system"]


def test_api_key_argument_reaches_the_client_without_changing_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    captured = _fake_client(monkeypatch, [_text("ok")])

    assert render_report(SAMPLE_PAYLOAD, api_key="input-key") == "ok"
    assert captured["api_key"] == "input-key"
    assert render_reviewer_critique(SAMPLE_PAYLOAD, api_key="critique-key") == "ok"
    assert captured["api_key"] == "critique-key"
    assert os.environ["ANTHROPIC_API_KEY"] == "env-key"


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


def test_text_after_a_thinking_block_is_returned(monkeypatch) -> None:
    # Models that think put a thinking block first; reading content[0].text would
    # raise AttributeError on it.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    thinking = SimpleNamespace(type="thinking", thinking="")
    fallback = SimpleNamespace(type="fallback")  # present when a refusal was rerun on another model
    _fake_client(monkeypatch, [thinking, fallback, _text("1. Overall risk"), _text(" RED")])
    assert render_report(SAMPLE_PAYLOAD) == "1. Overall risk RED"


@pytest.mark.parametrize("stop_reason", ["max_tokens", "refusal"])
def test_a_cut_off_or_refused_reply_raises_a_named_error(monkeypatch, stop_reason: str) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    _fake_client(monkeypatch, [_text("1. Overall risk — RED. 940 patients")], stop_reason)
    with pytest.raises(ReportNotRenderedError, match=stop_reason):
        render_report(SAMPLE_PAYLOAD)


def test_a_reply_without_text_raises_a_named_error(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    _fake_client(monkeypatch, [SimpleNamespace(type="thinking", thinking="")])
    with pytest.raises(ReportNotRenderedError):
        render_reviewer_critique(SAMPLE_PAYLOAD)


def test_render_reviewer_critique_sends_payload_json_to_opus(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    captured = _fake_client(monkeypatch, [_text("Reviewer verdict: reject")])

    critique_text = render_reviewer_critique(SAMPLE_PAYLOAD)

    assert critique_text == "Reviewer verdict: reject"
    assert captured["api_key"] == "test-key"
    assert captured["model"] == MODEL
    assert captured["max_tokens"] == MAX_TOKENS
    assert captured["output_config"] == {"effort": EFFORT}

    user_message = captured["messages"][0]
    assert user_message["role"] == "user"
    assert json.loads(user_message["content"]) == SAMPLE_PAYLOAD

    # The critique step loads its own prompt, distinct from the risk reporter's,
    # and sends the operative prompt rather than the file's Markdown doc header.
    assert "Methods paragraph" in captured["system"]
    assert "senior clinical-AI validation reviewer" not in captured["system"]
    assert "# Reviewer critique system prompt" not in captured["system"]
