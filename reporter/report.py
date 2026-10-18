"""LLM reporting step: turn the validators' JSON payload into prose.

This is the only module in the project that touches the network. It sends the
deterministic report payload to Claude (``claude-opus-5-5`` at low effort) under
one of two system prompts and returns the rendered text: :func:`render_report` produces the
GREEN/YELLOW/RED Validation Risk Report, :func:`render_reviewer_critique`
produces a journal-reviewer critique with a corrected Methods paragraph. Neither
computes a metric — every number in the output comes from the payload.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from anthropic import Anthropic, APIError

if TYPE_CHECKING:
    from clinval_validators import ReportPayload

MODEL = "claude-opus-5-5"
# Opus 5.5 always thinks; effort sets how much. In a blind review of 24 live
# reports per setting, neither "low" nor "medium" made a major error, and "low"
# cost less ($40 vs $45 per 1,000 reports).
EFFORT = "low"
# Thinking counts toward max_tokens. The longest live low-effort reply used 1,292
# output tokens. Only generated tokens are billed; the cap is a ceiling, not a cost.
MAX_TOKENS = 4096
# On a safety-classifier refusal the API reruns the request on the model Anthropic
# recommends for that refusal category, instead of returning the refusal.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
API_KEY_ENV = "ANTHROPIC_API_KEY"
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "reporter_system_prompt.md"
CRITIQUE_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "reviewer_critique_system_prompt.md"

__all__ = [
    "render_report",
    "render_reviewer_critique",
    "MissingAPIKeyError",
    "ReportNotRenderedError",
    "MODEL",
    "EFFORT",
    "MAX_TOKENS",
    "API_KEY_ENV",
    "SYSTEM_PROMPT_PATH",
    "CRITIQUE_SYSTEM_PROMPT_PATH",
]


class MissingAPIKeyError(RuntimeError):
    """Raised when the Anthropic key is absent from the environment.

    Callers can distinguish "the user has not set a key" — an expected, actionable
    condition — from a genuine failure, and report it without a traceback.
    """


class ReportNotRenderedError(RuntimeError):
    """Raised when Claude's reply holds no complete report.

    That happens when the API request fails (for example no credits, an
    invalid key, or no connection), or when the reply stops at ``max_tokens``,
    is refused (``stop_reason == "refusal"``), or contains no text block. The
    deterministic payload is unaffected, so callers can still show it.
    """


def _load_system_prompt(path: Path) -> str:
    """Read the operative system prompt from disk.

    The file opens with a short Markdown doc header; the operative prompt is the
    content after the first ``---`` separator. Only that part is returned.
    """
    text = path.read_text(encoding="utf-8")
    return text.split("---", 1)[1].strip()


def _render(
    payload: ReportPayload, system_prompt_path: Path, api_key: str | None = None
) -> str:
    """Send the deterministic payload to :data:`MODEL` under one prompt.

    ``api_key`` overrides ``ANTHROPIC_API_KEY`` when it is passed, so a browser
    session can use the key typed into that session without writing
    ``os.environ``. The key is never hard-coded, and no number is computed here.
    """
    if api_key is None:
        try:
            api_key = os.environ[API_KEY_ENV]
        except KeyError as exc:
            raise MissingAPIKeyError(
                f"{API_KEY_ENV} is not set in the environment."
            ) from exc
    if not api_key:
        raise MissingAPIKeyError(f"{API_KEY_ENV} is not set in the environment.")

    client = Anthropic(api_key=api_key)
    try:
        message = client.beta.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=_load_system_prompt(system_prompt_path),
            messages=[{"role": "user", "content": json.dumps(payload)}],
            output_config={"effort": EFFORT},
            betas=[FALLBACK_BETA],
            # The SDK types `fallbacks` as a list of models; the "default" mode is a
            # string the API accepts, so it goes in the raw body.
            extra_body={"fallbacks": "default"},
        )
    except APIError as exc:
        detail = str(exc).rstrip(".")
        raise ReportNotRenderedError(f"The Claude API request failed: {detail}.") from exc
    # Opus 5.5 returns thinking blocks (and, after a fallback, a fallback block)
    # before the text, so the first block is not always the report.
    text = "".join(block.text for block in message.content if block.type == "text")
    if message.stop_reason in ("max_tokens", "refusal") or not text:
        raise ReportNotRenderedError(
            f"Claude returned no complete report (stop_reason: {message.stop_reason})."
        )
    return text


def render_report(payload: ReportPayload, api_key: str | None = None) -> str:
    """Render the GREEN/YELLOW/RED Validation Risk Report from the payload."""
    return _render(payload, SYSTEM_PROMPT_PATH, api_key)


def render_reviewer_critique(payload: ReportPayload, api_key: str | None = None) -> str:
    """Render a journal-reviewer critique plus a corrected Methods paragraph."""
    return _render(payload, CRITIQUE_SYSTEM_PROMPT_PATH, api_key)
