"""ClinVal reporter: LLM layer that renders prose outputs from validator JSON."""

from .report import (
    API_KEY_ENV,
    CRITIQUE_SYSTEM_PROMPT_PATH,
    MODEL,
    SYSTEM_PROMPT_PATH,
    render_report,
    render_reviewer_critique,
)

__all__ = [
    "render_report",
    "render_reviewer_critique",
    "MODEL",
    "API_KEY_ENV",
    "SYSTEM_PROMPT_PATH",
    "CRITIQUE_SYSTEM_PROMPT_PATH",
]
