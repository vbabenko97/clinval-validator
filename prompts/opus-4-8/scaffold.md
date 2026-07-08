# Scaffold prompt — ClinVal Validator (Opus 4.8, Claude Code)

Run this in a fresh Claude Code session at the repo root. Recommended: `effort: high`, adaptive thinking on. The task is structural, not algorithmic — keep the prompt lean and let the model scope its own reasoning.

Paste everything below the line.

---

Read [CLAUDE.md](../../CLAUDE.md) first; it is the source of truth for this project. Then read [AGENTS.md](../../AGENTS.md), [prompts/opus-4-8/CLAUDE.md](CLAUDE.md), [prompts/opus-4-8/README.md](README.md), [prompts/opus-4-8/reporter_system_prompt.md](reporter_system_prompt.md), and [claude-science-artifacts/README.md](../../claude-science-artifacts/README.md). Do not restate their contents back to me; use them to keep this scaffold consistent with what is already decided.

<context>
This is the hackathon repo for "Built with Claude: Life Sciences" (Builder Track), described in CLAUDE.md. The synthetic-data generator and its labeled fixtures already exist in `claude-science-artifacts/` — that is the validators' test oracle and it is done. The MVP application code does not exist yet.

The architectural rule from CLAUDE.md holds throughout: Python computes every metric and flag; Claude only turns the deterministic JSON into prose. `validators/` is pure Python with no network; `reporter/` is the only code that touches the network.
</context>

<task>
Create the full project scaffold: planning documents, package structure, empty module stubs, dependency and license files, and test placeholders. This is a scaffolding pass only — set up the skeleton so the next session can implement Phase 1 immediately.

Do not implement any validation logic, metric computation, or LLM call bodies in this pass. Function bodies are signatures plus a docstring plus `raise NotImplementedError`. The building of Phase 1 happens later, against this scaffold.
</task>

<deliverables>
Planning docs (root):

1. `README.md` — expand the current one-line root README into the full project README. Build from the draft in `prompts/opus-4-8/README.md`. Include: project name (clinval-validator), one-sentence purpose, the "built from scratch for Built with Claude: Life Sciences" note, the synthetic-data / no-PHI / not-medical-advice disclaimer, MVP scope, the input CSV schema (use the real fixture header from `claude-science-artifacts/`), a quickstart, the planned 3-minute demo narrative, and the MIT license line.

2. `PROJECT_PLAN.md` — problem statement, named user, MVP definition, non-goals, architecture (the two-layer split), data-generation plan (point at the existing generator, do not redesign it), the four Phase-1 validation checks, the Claude report plan (reference the existing reporter system prompt), risks and scope cuts, and the demo story. Keep TRIPOD+AI / CLAIM mapping under stretch goals, not the MVP.

3. `TASKS.md` — a staged checklist matching CLAUDE.md's phases. Every item must produce a concrete artifact (a file, function, test, CLI command, or demo asset) — no vague items. Phase 1: leakage check, split audit, subgroup degradation, report JSON contract, Claude report step, minimal CLI or Streamlit demo, demo script + submission polish.

Package structure (create as packages to match CLAUDE.md's repo map):

4. `validators/` — `__init__.py` plus one module holding the deterministic checks as stubs: patient-level leakage, split-quality audit, subgroup degradation. Each is a typed function that returns the piece of the report JSON it owns. No network imports here.

5. `reporter/` — `__init__.py` plus one module with the LLM step as a stub: a function that takes the validators' JSON dict and returns the report string. It reads the API key from the environment (never hard-coded) and loads its system prompt from `prompts/opus-4-8/reporter_system_prompt.md` rather than duplicating it. Target model `claude-opus-4-8`.

6. The report JSON contract — define it once as typed structures (dataclasses or `TypedDict`) that exactly match the input shape documented in `prompts/opus-4-8/reporter_system_prompt.md` (`leakage`, `split_audit`, `subgroups`, `pooled_metric`). The validators produce this; the reporter consumes it. Do not invent fields beyond that contract.

7. A single CLI entrypoint stub (argparse) that wires the flow: load a predictions CSV → run validators → assemble the JSON → call the reporter → print the report. Body is the wiring shape with `raise NotImplementedError` where logic belongs.

8. `data/` — do not copy or regenerate fixtures. Add a short `data/README.md` that points to `claude-science-artifacts/scenarios/` and names which scenario the demo uses.

9. `tests/` — placeholder tests mirroring CLAUDE.md's verification plan: fixture schema check, leakage-is-injected, detector catches train/test patient overlap, subgroup degradation is detectable, CLI smoke test end-to-end. Mark them `pytest.mark.xfail(reason="Phase 1 not implemented")` or `skip` so the suite collects and runs green against the empty scaffold.

Project files:

10. `pyproject.toml` — Python 3.11+, runtime deps `pandas`, `scikit-learn`, `anthropic`; dev dep `pytest`. Declare the `validators`/`reporter` packages.

11. `LICENSE` — MIT, year 2026, author "vbabenko97".
</deliverables>

<scope_constraints>
Keep the scaffold minimal and focused. CLAUDE.md's anti-over-engineering section applies to this pass.

- Only create what the deliverables list. No extra modules, config layers, plugin systems, or abstractions "for later."
- Stubs only — no metric math, no bootstrap, no real Anthropic call body. `raise NotImplementedError` marks every place Phase 1 fills in.
- Do not add error handling, validation, or fallbacks for inputs that cannot occur. Trust the fixed schema.
- Do not touch or refactor `claude-science-artifacts/` — it is finished.
- Do not start any Phase 2 item (bootstrap CIs, calibration plots, standards mapping).
- One module per package — do not split validators into five files.
</scope_constraints>

<default_to_action>
Create the files directly. Where a detail is genuinely underdetermined (CLI vs Streamlit for the demo, dataclass vs TypedDict), pick the simpler option consistent with CLAUDE.md, state the choice, and proceed. Only stop for a decision that would be expensive to reverse.
</default_to_action>

<verification>
Before reporting done, confirm and show the output of:

- `python -c "import validators, reporter"` — packages import cleanly.
- `pytest` — the placeholder suite collects and passes (xfail/skip, no collection errors).
- Dependencies resolve (`pip install -e .` dry-run or equivalent).
- `grep -rIl -E "requests|anthropic|httpx|urllib" validators/` returns nothing — the compute layer has no network dependency.
- Every planning doc and package file listed in the deliverables exists and is non-empty.
</verification>

<output_format>
After creating the files, report:

1. Files created, grouped by planning docs / packages / project files.
2. The verification commands you ran and their results.
3. The final MVP scope in five bullets or fewer.
4. The first Phase-1 implementation task the next session should pick up.
5. Any assumptions you made or choices where you picked a default.

Do not begin implementing Phase 1 logic in this session.
</output_format>
