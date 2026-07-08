# clinval-validator

Flag the failure modes that make a clinical-AI performance claim unsafe —
patient-level data leakage, weak evaluation splits, and subgroup degradation —
in a model's `predictions.csv`, then render a human-readable Validation Risk
Report.

Built from scratch for **Built with Claude: Life Sciences** (Builder Track),
started 2026-07-07.

**Python computes the metrics; Claude explains the risk.** Every metric,
statistical test, and pass/fail flag is computed by deterministic Python in
`validators/` (runs fully offline). Claude (`claude-opus-4-8`) is used only to
turn that structured JSON into prose in `reporter/` — it never computes a number.

> **Disclaimer.** Synthetic / public-schema data only, modeled on the RSNA
> Screening Mammography schema. No PHI, no real patient data, no RSNA images in
> this repo. Not medical advice.

**Status:** scaffold stage. Package skeleton, the report JSON contract, and the
CLI wiring are in place; the Phase-1 checks and the Claude call are stubs
(`raise NotImplementedError`) pending implementation. See [TASKS.md](TASKS.md).

## MVP scope (Phase 1)

1. **Patient-level leakage check** — detect `patient_id` overlap between train
   and test; report count and rate.
2. **Split-quality audit** — recompute the headline metric under a random split
   vs a patient/site-grouped split; surface the gap.
3. **Subgroup degradation** — AUC per `machine_id` / `site_id`; flag subgroups
   significantly below the pooled metric.
4. **Claude risk report** — feed the Phase-1 JSON to `claude-opus-4-8`; get a
   GREEN / YELLOW / RED report: what can be claimed, what cannot, and the next
   validation step.

Everything else (bootstrap CIs, calibration plots, TRIPOD+AI / CLAIM mapping) is
Phase 2 — see [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Input schema

Predictions CSV, modeled on the RSNA Screening Mammography schema:

```
patient_id, image_id, laterality, view, machine_id, site_id, age, density, y_true, y_prob, split
```

The validators consume the minimal subset `patient_id, machine_id, site_id,
y_true, y_prob, split` (plus `density` / `age` for subgroup checks). Labeled
fixtures live in
[`claude-science-artifacts/scenarios/`](claude-science-artifacts/scenarios/).

## Quickstart

```bash
# 1. Install (editable). Requires Python 3.11+.
python -m pip install -e .

# 2. Set your personal Anthropic API key (never commit it).
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Validate a labeled scenario and print the risk report.
clinval-validate --predictions claude-science-artifacts/scenarios/weak_random_split_leakage.csv

# Run the test suite.
python -m pytest
```

## Demo narrative (3-minute video)

1. Run the validator on a random-split table — the headline AUC looks publishable.
2. The split-quality audit re-splits by `patient_id`: the metric collapses and
   the leakage check reports the shared patients.
3. Claude reads the deterministic JSON and explains, in reviewer language, why
   the original claim is unsafe and what may still be claimed.
4. Claude names the single next validation step (a leakage-safe grouped
   re-evaluation).

## License

MIT — see [LICENSE](LICENSE).
