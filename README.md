# clinval-validator

Flag the failure modes that make a clinical-AI performance claim unsafe —
patient-level data leakage, weak evaluation splits, and subgroup degradation —
in a model's `predictions.csv`, then render a human-readable Validation Risk
Report.

![ClinVal Validator browser UI flagging 940 patients shared across train and test in the weak_random_split_leakage scenario](docs/images/app-weak-random-split-leakage.png)

*Offline audit of the bundled synthetic `weak_random_split_leakage` scenario in the
[browser UI](#browser-ui); no Claude report was requested. The fourth metric is AUC on
the patient-disjoint subset: its +0.072 delta compares two evaluation populations
under unchanged predictions — it is not a model improvement and does not mean the
leakage is fixed.*

Built from scratch for **Built with Claude: Life Sciences** (Builder Track),
started 2026-07-07.

**Python computes the metrics; Claude explains the risk.** Every metric,
statistical test, and pass/fail flag is computed by deterministic Python in
`clinval_validators/` (runs fully offline). Claude (`claude-opus-4-8`) is used only to
turn that structured JSON into prose in `reporter/` — it never computes a number.

> **Disclaimer.** Synthetic / public-schema data only, modeled on the RSNA
> Screening Mammography schema. No PHI, no real patient data, no RSNA images in
> this repo. Not medical advice.

**Status:** Phase 1 complete, plus the first Phase-2 feature. The four
deterministic checks (patient leakage, split-quality audit, subgroup
degradation, pooled AUC) and the Claude reporter are implemented and verified
against the labeled scenario manifests — `pytest` is green, and
`clinval-validate` runs end-to-end (a real `ANTHROPIC_API_KEY` is needed only for
the report step). A reviewer-critique mode (`--mode critique`) adds a
journal-reviewer critique and a corrected, leakage-safe Methods paragraph over
the same deterministic JSON. See [TASKS.md](TASKS.md) and
[demo/run_demo.sh](demo/run_demo.sh).

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

# 3. Validate a labeled scenario and print the GREEN / YELLOW / RED risk report.
clinval-validate --predictions claude-science-artifacts/scenarios/weak_random_split_leakage.csv

# Or ask for a journal-reviewer critique plus a corrected, leakage-safe Methods paragraph.
clinval-validate --predictions claude-science-artifacts/scenarios/weak_random_split_leakage.csv --mode critique

# Run the test suite.
python -m pytest

# Launch the browser UI (no terminal needed after this line).
python -m pip install -e '.[demo]' && streamlit run app.py
```

## Browser UI

`streamlit run app.py` is the path a collaborator can run without you in the room:

- Pick a bundled scenario **or upload your own `predictions.csv`**. A missing
  required column is reported by name — not as a stack trace.
- The deterministic checks run **offline and without an API key**: leakage count,
  split audit, per-subgroup AUC, and the exact JSON that Claude would receive.
- Press **Generate with Claude** for the risk report or the reviewer critique.
  Both are optional — the validation stands on its own.
- **Download** the payload as JSON and the report as Markdown.

## Sample output

Running `--mode risk` on `weak_random_split_leakage`, the deterministic layer
computes this payload (this is what Python hands to Claude — no metric is ever
computed by the model):

```json
{
  "leakage": {"overlapping_patient_ids": 940, "leakage_rate": 0.9802},
  "split_audit": {"metric": "auc", "random_split": 0.8273, "grouped_split": 0.8994, "gap": -0.0721},
  "subgroups": [{"key": "site_id", "value": "S03", "n": 2125, "auc": 0.7896, "delta_vs_pooled": -0.0528, "flagged": false}],
  "pooled_metric": {"name": "auc", "value": 0.8425}
}
```

Claude renders that into a reviewer-style report. An illustrative excerpt (the
wording is model-generated and varies run to run; the numbers are fixed by the
payload above):

```
1. Overall risk — RED. 940 patient IDs appear in both train and test, so the
   reported metrics do not reflect held-out performance.

2. What the data shows — The leakage check finds 940 shared patients (98.0% of
   the test patients also appear in training). Pooled AUC is 0.84, but that
   figure is measured across a contaminated split. No machine_id or site_id
   subgroup falls more than 0.10 below pooled.

5. Next validation step — Re-evaluate the same predictions on a patient-grouped
   split so no patient spans the train/test boundary, and report the grouped AUC
   as the headline number.
```

The full 3-minute demo script — synthetic opener, real RSNA cohort, clean
control, and the `--mode critique` close — is in [docs/DEMO.md](docs/DEMO.md).

## Demo narrative (3-minute video)

1. Run the validator on `weak_random_split_leakage` — the headline pooled AUC
   (≈ 0.84) looks publishable.
2. The leakage check finds **940 patients shared across train and test** and
   marks the random split as not leakage-safe; the split-quality audit
   re-evaluates the same predictions on a patient-grouped fold.
3. Claude reads the deterministic JSON and explains, in reviewer language, why an
   AUC measured under patient overlap does not reflect deployment, and what may
   still be claimed.
4. Claude names the single next validation step (a leakage-safe grouped
   re-evaluation). For contrast, `optimistic_site_shortcut` shows the same
   failure at its most dramatic: AUC 0.9647 under a leaking split.

## License

MIT — see [LICENSE](LICENSE).
