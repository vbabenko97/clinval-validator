"""LLM reporting step: turn the validators' JSON payload into prose.

This is the only module in the project that touches the network. It sends the
deterministic report payload to Claude (``claude-opus-4-8``) under one of two
system prompts and returns the rendered text: :func:`render_report` produces the
GREEN/YELLOW/RED Validation Risk Report, :func:`render_reviewer_critique`
produces a journal-reviewer critique with a corrected Methods paragraph. Neither
computes a metric — every number in the output comes from the payload.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from anthropic import Anthropic

if TYPE_CHECKING:
    from clinval_validators import ReportPayload

MODEL = "claude-opus-4-8"
API_KEY_ENV = "ANTHROPIC_API_KEY"
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts" / "opus-4-8"
SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "reporter_system_prompt.md"
CRITIQUE_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "reviewer_critique_system_prompt.md"

__all__ = [
    "render_report",
    "render_reviewer_critique",
    "MissingAPIKeyError",
    "MODEL",
    "API_KEY_ENV",
    "SYSTEM_PROMPT_PATH",
    "CRITIQUE_SYSTEM_PROMPT_PATH",
]


class MissingAPIKeyError(RuntimeError):
    """Raised when the Anthropic key is absent from the environment.

    Callers can distinguish "the user has not set a key" — an expected, actionable
    condition — from a genuine failure, and report it without a traceback.
    """


def _load_system_prompt(path: Path) -> str:
    """Read the operative system prompt from disk.

    The file opens with a short Markdown doc header; the operative prompt is the
    content after the first ``---`` separator. Only that part is returned.
    """
    text = path.read_text(encoding="utf-8")
    return text.split("---", 1)[1].strip()


def _render(payload: ReportPayload, system_prompt_path: Path) -> str:
    """Send the deterministic payload to ``claude-opus-4-8`` under one prompt.

    Reads the Anthropic API key from the ``ANTHROPIC_API_KEY`` environment
    variable, loads the operative system prompt from ``system_prompt_path``, sends
    the payload as JSON, and returns the model's text. The key is never
    hard-coded, and no number is computed here — every figure comes from the JSON.
    """
    try:
        api_key = os.environ[API_KEY_ENV]
    except KeyError as exc:
        raise MissingAPIKeyError(f"{API_KEY_ENV} is not set in the environment.") from exc

    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=_load_system_prompt(system_prompt_path),
        messages=[{"role": "user", "content": json.dumps(payload)}],
    )
    return message.content[0].text


def render_report(payload: ReportPayload) -> str:
    """Render the GREEN/YELLOW/RED Validation Risk Report from the payload."""
    return _render(payload, SYSTEM_PROMPT_PATH)


def render_reviewer_critique(payload: ReportPayload) -> str:
    """Render a journal-reviewer critique plus a corrected Methods paragraph."""
    return _render(payload, CRITIQUE_SYSTEM_PROMPT_PATH)
