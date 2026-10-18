# prompts/

Runtime system prompts for the LLM reporting step. These are **load-bearing**:
`reporter/report.py` reads them from disk at call time (see `SYSTEM_PROMPT_PATH`
and `CRITIQUE_SYSTEM_PROMPT_PATH`), so renaming or deleting them breaks the tool.

- [`reporter_system_prompt.md`](reporter_system_prompt.md) —
  turns the validators' JSON into the GREEN/YELLOW/RED Validation Risk Report
  (`clinval-validate --mode risk`).
- [`reviewer_critique_system_prompt.md`](reviewer_critique_system_prompt.md) —
  turns the same JSON into a journal-reviewer critique plus a corrected,
  leakage-safe Methods paragraph (`clinval-validate --mode critique`).

Both follow the same on-disk format: a short Markdown doc header, a `---`
separator, then the operative prompt. The loader sends only the text after the
first `---`. Every figure a prompt may cite must be present in the JSON — the
model computes nothing.
