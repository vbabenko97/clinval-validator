# CLAUDE.md — ClinVal Validator

Built from scratch for **"Built with Claude: Life Sciences"** (Builder Track). Started 2026-07-07. Submission deadline: **2026-07-13, 21:00 ET**.

Behavioral rules (how to work, delegation, communication style) live in [AGENTS.md](AGENTS.md) — they apply to Claude too. This file is the **project spec**: what to build and the rules specific to this repo.

## What this project is

A validation tool for medical-imaging ML models. It ingests a `predictions.csv` (model outputs + patient/scanner/site metadata) and flags the failure modes that make clinical AI claims unsafe: patient-level data leakage, weak evaluation splits, and subgroup performance degradation. It then produces a human-readable **Validation Risk Report**.

Named user: a clinical-AI researcher / radiology-lab PhD student who trained a model on a small biomedical dataset and needs to know whether the result is genuinely validatable or an artifact of leakage and weak splitting.

## Core architectural rule (do not violate)

**Python computes. Claude explains.**

- All metrics, statistical tests, pass/fail flags, and the risk level are computed by deterministic Python. Never ask an LLM to compute AUC, run a bootstrap, or decide a flag or the risk level.
- Claude (Anthropic API, `claude-opus-5-5` at effort `low`, with server-side refusal fallback) is used **only** to turn the deterministic layer's structured JSON into prose: the risk report, reviewer-style critique, next-step suggestions. See the reporter contract in [prompts/reporter_system_prompt.md](prompts/reporter_system_prompt.md) — it may cite only numbers present in the JSON.
- Layers stay cleanly separable: `clinval_validators/` (pure Python, no network, runs fully offline) and `reporter/` (the only code that touches the network).

## Repo map — current state

- [clinval_validators/](clinval_validators/) — deterministic checks. `run_checks` returns leakage, the split audit, subgroups, the pooled AUC, and `risk`.
- [cli.py](cli.py) — `clinval-validate`. Prints the payload and exits 1 when `ANTHROPIC_API_KEY` is unset or Claude returns no complete report (`ReportNotRenderedError`: cut off at `max_tokens`, refused, or no text). Exits 2 when `validate_predictions` reports a problem.
- [app.py](app.py) — Streamlit UI over the same checks. The typed API key is passed into the reporter and is not written to `os.environ`.
- [reporter/](reporter/) — the only code that calls the network. Loads the two runtime prompts in [prompts/](prompts/); see [prompts/README.md](prompts/README.md).
- [claude-science-artifacts/](claude-science-artifacts/) — synthetic-data generator and the committed scenario oracle (`scenarios/*.csv`, manifests, `_scenario_summary.csv`). Do not regenerate those fixtures to make a test pass.
- [rsna_to_predictions.py](rsna_to_predictions.py) — local-only adapter for an RSNA `train.csv`. Outputs are gitignored.
- [tests/](tests/) — unit tests, including fresh generator seeds for the subgroup flag.
- [docs/DEMO.md](docs/DEMO.md) — script of the recorded demo video. A dated note under the title lists later corrections. The narration is unchanged.
- [AGENTS.md](AGENTS.md) — Codex/GPT behavioral rules (also govern Claude).

## Commands

```bash
python -m pip install -e '.[dev,demo]'
python -m pytest -q
clinval-validate --predictions claude-science-artifacts/scenarios/optimistic_site_shortcut.csv
clinval-validate --predictions claude-science-artifacts/scenarios/optimistic_site_shortcut.csv --mode critique
streamlit run app.py
python rsna_to_predictions.py --input data/rsna/train.csv
```

`clinval-validate` without `ANTHROPIC_API_KEY` prints the JSON payload and exits 1. `--mode critique` asks for the reviewer critique. The RSNA command writes gitignored `predictions_rsna_random.csv` and `predictions_rsna_patient_grouped.csv`.

New synthetic tables, not replacements for the committed oracle:

```bash
cd claude-science-artifacts && python make_scenarios.py
python claude-science-artifacts/leakage_generator.py --out predictions.csv \
    --split-strategy random --degrade machine_id:M030:0.60 --optimistic-auc 0.98
```

## Gotchas

- `leakage_generator.generate` draws `y_prob` before it assigns splits, so injected leakage does not change the scores.
- `_FLAG_DELTA` (−0.10) and `_MIN_SUBGROUP_N` (50) were calibrated on the committed fixtures. Do not change them to make a test pass.
- `reporter/report.py` sends only the text after the first `---` of a prompt file.
- A one-sided Bonferroni correction across subgroups was measured on generator seeds 7–36 and not adopted. It cut clean-table flags from 6 to 3 of 30, but M030 detection fell from 26 to 21 of 30 and density detection from 21 to 12 of 30, and `subgroup_density_degradation` was no longer flagged. Re-measure on the same seeds before changing the flag rule.
- The reporter model was chosen in October 2026 from a blind review of 24 live reports per configuration (4 scenarios × 2 modes × 3 repeats). Major errors: Opus 5.5 low 0, Opus 5.5 medium 0, Sonnet 5.5 with and without thinking 0, Opus 4.8 1, Haiku 5.5 2–3. Opus 5.5 low had the most error-free reports (19 of 24) at $40 per 1,000 reports, against $46 for Opus 4.8; Sonnet 5.5 without thinking is the cheaper option ($18, 14 of 24 error-free). Re-run that comparison before changing `MODEL` or `EFFORT`.
- Opus 5.5 always thinks: `thinking: {"type": "disabled"}` is a 400. Its replies start with thinking blocks, so the reporter joins the `text` blocks, and `MAX_TOKENS` must leave room for the thinking.

## Data & schema

Fixtures are the source of truth. Actual generated header:

```
patient_id, image_id, laterality, view, machine_id, site_id, age, density, y_true, y_prob, split
```

Validators consume the minimal subset: `patient_id, machine_id, site_id, y_true, y_prob, split` (plus `density`/`age` for subgroup checks). Modeled on the RSNA Screening Mammography schema — **reference schema only, no RSNA images or PHI in this repo**.

Scenario suite (`_scenario_summary.csv`), each with a `*.manifest.json` recording injected flaws + `expected_detections` the validators are checked against:

| Scenario | Flaw | Detectable signal |
|---|---|---|
| `clean_patient_grouped` | none (negative control) | risk GREEN; no subgroup flags |
| `weak_random_split_leakage` | patient overlap via random split | 940 train/test patient overlaps; risk RED |
| `duplicate_row_leakage` | near-duplicate rows train→test | 113 duplicate-leaked patients; risk RED |
| `subgroup_scanner_degradation` | scanner M030 AUC low | M030 about 0.624 vs about 0.873 on the rest; flagged. Site S03 is also flagged. Risk YELLOW |
| `subgroup_density_degradation` | density C and D target AUC 0.70 | density C about 0.670 vs about 0.792 on the rest; flagged. D is not (its delta is above −0.10). Risk YELLOW |
| `optimistic_site_shortcut` | high AUC, site shortcut, random split | 990 overlapping patients, so risk RED. Mean `y_prob` by site is about 0.33–0.75 against an observed rate of about 1–2%; that gap is reported and not flagged |

Never commit real patient data. README must state: synthetic/public-schema only, no PHI, not medical advice.

## Scope — build in phases, do not flatten

Judging rewards depth, a working demo, and creative Claude use — not feature count. Opus tends to over-engineer; resist it.

### Phase 1 — MVP (in the tree)
1. **Patient-level leakage check** — `patient_id` overlap between train and test; count and rate. `val` is ignored.
2. **Split-quality audit** — AUC on the test rows as given, and AUC on a patient sample of all rows (that sample includes training rows), plus the seed 0–199 range of the sample AUC. Descriptive only. It does not set the risk level, because rescoring fixed predictions cannot show inflation.
3. **Subgroup degradation** — AUC against the rest of the table for `machine_id`, `site_id`, and, when the columns exist, `density` and decade age bands. Flag when the drop is at least 0.10 and the upper end of a patient-level 95% interval is below zero. `mean_predicted` and `observed_rate` are reported and do not flag. Pooled AUC assumes every row's `y_prob` is a held-out or out-of-fold prediction.
4. **Risk level** — Python sets `RED` when any patient is in both train and test, otherwise `YELLOW` when a subgroup is flagged, otherwise `GREEN`. Claude is instructed to state `risk.level` verbatim and explain `risk.reasons`. For leakage, the next step it is instructed to name is a retrained patient-grouped evaluation, not another score of the same predictions.

Phase 1 runs offline through the payload. The report step needs `ANTHROPIC_API_KEY`.

### Phase 2 — not built
Calibration plots per subgroup. A reporting checklist mapped to TRIPOD+AI and CLAIM. A reproducibility checklist. The reviewer critique (`--mode critique`) and the subgroup interval are already in Phase 1.

## Anti-over-engineering

- Build only what this file asks for. No speculative configurability, plugin systems, or abstractions "for later."
- No defensive error handling for scenarios that cannot occur. `validate_predictions` is the boundary for a CSV the tool did not write. After it accepts a table, the checks trust that schema.
- Comment only where logic isn't self-evident; don't document code you didn't write.
- A single-file validator beats a five-file framework if it does the job.

## Constraints

- Open source, **MIT**. All repo work must be original, started during the hackathon.
- Credits run on a **personal** claude.ai account (institutional accounts ineligible). Never hardcode an API key. The CLI reads `ANTHROPIC_API_KEY`. The UI passes a typed key into the reporter for that call and does not write `os.environ`.
- Stack: Python 3.11+, pandas, scikit-learn for metrics. Both the CLI and the Streamlit UI are in the tree.
- The 3-minute demo video is 30% of judging. The recorded script is [docs/DEMO.md](docs/DEMO.md): `optimistic_site_shortcut`, then the local RSNA table, then `clean_patient_grouped`, then the critique. The risk level on screen is the Python level.

## Definition of done

A fresh clone runs the validator on a synthetic scenario CSV, prints the deterministic flags, calls Claude to render the risk report, and the whole thing is captured in a <3-min demo. Verify with unit tests: schema check, leakage-is-injected, detector catches train/test overlap, subgroup degradation is detectable, and a CLI smoke test end-to-end. Anything beyond that is Phase 2.
