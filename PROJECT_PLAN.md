# PROJECT_PLAN — clinval-validator

## Problem statement

Small-dataset medical-imaging models routinely report headline metrics (AUC)
that are artifacts of *how the data was split*, not of the model's ability to
generalize. The three most common failure modes — patient-level leakage across
the train/test split, image-level random splits that ignore patient grouping,
and silent performance collapse in a scanner/site/density subgroup — are
invisible in a single pooled AUC. A researcher can publish "AUC 0.96" that would
not survive a leakage-safe re-evaluation. This tool detects those failure modes
deterministically and explains their consequences for what can be claimed.

## Named user

A clinical-AI researcher / radiology-lab PhD student who trained a model on a
small biomedical dataset and needs to know whether the result is genuinely
validatable or an artifact of leakage and weak splitting — before writing it up.

## MVP definition (Phase 1)

A fresh clone runs the validator on a synthetic scenario CSV, prints the
deterministic flags, calls Claude to render the Validation Risk Report, and the
whole path is captured in a <3-minute demo. Four checks:

1. **Patient-level leakage** — `patient_id` overlap between train and test.
2. **Split-quality audit** — headline metric under random vs grouped split.
3. **Subgroup degradation** — per-`machine_id`/`site_id` AUC vs pooled.
4. **Claude risk report** — GREEN/YELLOW/RED prose over the Phase-1 JSON.

## Non-goals

- No model training, inference, or image handling — the tool consumes a
  predictions table only.
- No real patient data, PHI, or RSNA images. Synthetic / public-schema only.
- No LLM-computed metrics. Claude never computes AUC, runs a bootstrap, or
  decides a flag — it only narrates the deterministic JSON.
- No configurability, plugin system, or abstractions built "for later."
- No web service or persistent storage. A CSV in, a report out.

## Architecture — two clean layers

```
predictions.csv
   │
   ▼
validators/   (pure Python, offline, no network imports)
   check_patient_leakage / audit_split_quality /
   check_subgroup_degradation / compute_pooled_metric
   │  → ReportPayload (TypedDict contract)
   ▼
reporter/     (the only network-touching code)
   render_report(payload) → calls claude-opus-4-8 → report string
   │
   ▼
cli.py  wires: load CSV → validators → assemble payload → reporter → print
```

The contract (`ReportPayload` and its parts) is defined once in
`validators/checks.py` and re-exported from `validators/__init__.py`. The
reporter imports it for typing only; validators never import the reporter. This
keeps the compute layer runnable with no network and no LLM dependency.

## Data-generation plan

Do **not** build a new generator. The labeled fixtures already exist and are the
validators' test oracle:

- `claude-science-artifacts/leakage_generator.py` — RSNA-like table generator
  with manifest-verified injected flaws.
- `claude-science-artifacts/make_scenarios.py` — builds the full suite.
- `claude-science-artifacts/scenarios/*.csv` + `*.manifest.json` +
  `_scenario_summary.csv` — 6 ground-truth-labeled scenarios.

Each manifest records `injected_flaws` and `expected_detections` (overlap
counts, target AUCs) that the validators are checked against. `data/` copies
nothing; validators read scenarios directly.

## The four Phase-1 checks

| # | Function (`validators/checks.py`) | Reads | Produces (contract field) |
|---|---|---|---|
| 1 | `check_patient_leakage` | `patient_id`, `split` | `leakage` |
| 2 | `audit_split_quality` | `patient_id`/`site_id`, `y_true`, `y_prob`, `split` | `split_audit` |
| 3 | `check_subgroup_degradation` | `machine_id`/`site_id`, `y_true`, `y_prob` | `subgroups` |
| — | `compute_pooled_metric` | `y_true`, `y_prob` | `pooled_metric` |

All AUCs via scikit-learn `roc_auc_score`. Grouping via pandas. No LLM.

## Claude report plan

The reporter sends the assembled `ReportPayload` (JSON) to `claude-opus-4-8`
under the reviewer system prompt at
[`prompts/opus-4-8/reporter_system_prompt.md`](prompts/opus-4-8/reporter_system_prompt.md),
loaded from disk (never duplicated inline). That prompt pins the output: an
Overall risk line (GREEN/YELLOW/RED), What the data shows, What can be claimed,
What cannot be claimed, and the Next validation step — every figure drawn only
from the JSON, under 300 words. The API key is read from `ANTHROPIC_API_KEY`;
credits run on a personal claude.ai account.

## Risks and scope cuts

- **Over-engineering (primary risk).** Opus tends to add breadth. Mitigation:
  one module per package, stubs only until Phase 1, no speculative config.
- **Demo depends on the network.** The LLM step is the only online part; if the
  API is unavailable during the demo, fall back to a cached report captured from
  a prior run (compute layer still runs offline).
- **Statistical significance for subgroup flags.** MVP uses a simple threshold
  on `delta_vs_pooled` + minimum `n`; bootstrap CIs are Phase 2, not a blocker.
- **Time.** If Phase 1 slips, cut to checks 1, 2, and 4 (leakage + split audit +
  report); subgroup degradation is the first droppable item.

## Demo story

Primary scenario: `weak_random_split_leakage` (random split, 940 train/test
patient overlaps, pooled AUC 0.8425). Naive split looks publishable → grouped
re-split collapses it and the leakage check names the shared patients → Claude
explains why the claim is unsafe → Claude names the corrected next step.
Contrast bookends: `clean_patient_grouped` (GREEN control) and, for drama,
`optimistic_site_shortcut` (AUC 0.9647 under a leaking split).

## Stretch goals (Phase 2 — only after Phase 1 is fully done)

5. Bootstrap confidence intervals on reported metrics.
6. Calibration plots per subgroup.
7. Reporting-completeness checklist mapped to **TRIPOD+AI** and **CLAIM**.
8. Reviewer-style critique + a corrected Methods paragraph draft.
9. Submission-ready reproducibility checklist output.
