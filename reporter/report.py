"""LLM reporting step: turn the validators' JSON payload into prose.

This is the only module in the project that touches the network. It sends the
deterministic report payload to Claude (``claude-opus-4-8``) under the reviewer
system prompt and returns the rendered Validation Risk Report. It never computes
a metric — every number in the report comes from the payload.

Phase 1 fills in the Anthropic call; :func:`render_report` is a stub until then.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from validators import ReportPayload

MODEL = "claude-opus-4-8"
API_KEY_ENV = "ANTHROPIC_API_KEY"
SYSTEM_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "prompts"
    / "opus-4-8"
    / "reporter_system_prompt.md"
)

__all__ = ["render_report", "MODEL", "API_KEY_ENV", "SYSTEM_PROMPT_PATH"]


def _load_system_prompt() -> str:
    """Read the reviewer system prompt from disk (never duplicated inline)."""
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def render_report(payload: ReportPayload) -> str:
    """Render the Validation Risk Report from the deterministic payload.

    Reads the Anthropic API key from the ``ANTHROPIC_API_KEY`` environment
    variable, loads the system prompt via :func:`_load_system_prompt`, sends the
    payload as JSON to ``claude-opus-4-8``, and returns the report text. The key
    is never hard-coded.
    """
    raise NotImplementedError
