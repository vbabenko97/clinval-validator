# Implementation prompt — ClinVal Validator Phase 1 (Fable 5, Claude Code)

Run this in a fresh Claude Code session at the repo root, against the existing scaffold.
Recommended: `model: claude-fable-5`, `effort: high`, adaptive thinking on.

Paste everything below the line.

---

I'm building ClinVal Validator for the "Built with Claude: Life Sciences" hackathon (Builder Track). The scaffold is done and committed; this session implements Phase 1 so the tool runs end-to-end on a synthetic predictions table and renders a risk report. The named user is a radiology-lab PhD student who needs to know whether a model's headline AUC is real or an artifact of leakage and weak splitting — so correctness of the deterministic numbers is the whole point.

This is software and statistics engineering: pandas/scikit-learn metric computation over a **synthetic, public-schema** predictions CSV. No PHI, no real patient data, no clinical decision-making — the tool flags evaluation-methodology defects and Claude explains them.

## Read first (source of truth — don't restate back to me)

- `CLAUDE.md` — project spec, the "Python computes, Claude explains" rule, phases, anti-over-engineering.
- `PROJECT_PLAN.md` — architecture, the four checks, the report plan.
- `TASKS.md` — the Phase-1 checklist you are executing; check items off as you land them.
- `validators/checks.py` — the report JSON contract (TypedDicts) and the four stubs you implement.
- `reporter/report.py` — the reporter stub and its pinned constants.
- `prompts/opus-4-8/reporter_system_prompt.md` — the reviewer system prompt the reporter sends.
- `claude-science-artifacts/scenarios/*.manifest.json` and `_scenario_summary.csv` — **the oracle.** Each manifest's `expected_detections` and `verification` blocks are ground truth for your tests.

## What to build

Implement the four Phase-1 pieces against the existing contract, then wire the CLI. Do not change the contract fields, add modules, or start any Phase-2 item.

1. `validators.check_patient_leakage` → `LeakageResult`
2. `validators.audit_split_quality` → `SplitAuditResult`
3. `validators.compute_pooled_metric` + `validators.check_subgroup_degradation` → `PooledMetric` / `list[SubgroupResult]`
4. `reporter.render_report` — the Anthropic call
5. `cli._load_predictions` — `pd.read_csv`, so `clinval-validate --predictions <csv>` runs the whole flow

## Approach: test-driven, against the fixture oracle

Use the `superpowers:test-driven-development` skill. `python-coding` applies to every `.py` edit. For each check: write (or tighten) the test to the oracle number from the manifest, watch it fail, implement, watch it pass. The scaffold already has placeholder tests in `tests/` — the two in `tests/test_validators.py` are `strict` xfails, so once your implementation is correct they turn into a hard `XPASS(strict)` failure that forces you to delete the `xfail` marker. Remove markers and un-`skip` the fixture tests as each piece lands. `pytest` must end green with real assertions, not xfail/skip.

All AUCs via `sklearn.metrics.roc_auc_score` on the rows where `split == "test"` unless a check says otherwise.

## Pinned definitions (so the numbers are reproducible and match the manifests)

**Leakage.** `overlapping_patient_ids` = count of `patient_id`s present in **both** the train and test splits. `leakage_rate` = that count divided by the number of distinct patients in (train ∪ test), a float in [0,1]. Hard oracles: `weak_random_split_leakage` → 940, `duplicate_row_leakage` → 113, `clean_patient_grouped` → 0. (These match each manifest's `train_test_patient_overlap`.)

**Split audit.** The predictions are fixed — you cannot retrain, so this compares the metric across two ways of choosing the test rows over the same `y_prob`:
- `random_split` = test-set AUC on the split as given in the file.
- `grouped_split` = test-set AUC on a leakage-safe re-partition, grouping by `patient_id` (`sklearn.model_selection.GroupShuffleSplit`, fixed `random_state`), computed on the regrouped test fold with the same `y_prob`.
- `gap` = `random_split - grouped_split`.

There is **no manifest oracle for this gap.** The injected leak in these tables is structural (shared patients), and `y_prob` was drawn to a fixed global AUC target — so the gap may be small or near zero, and that is a legitimate finding. Measure it and report the real number; do not assume a collapse. The primary, hard leakage signal for this dataset is the patient-overlap count plus each split's leakage-safety (`split == "random"` is unsafe; `patient`/`site` are safe), which matches the manifests' `split_is_leakage_safe`. Test `audit_split_quality` on structure and direction (both AUCs finite; random split correctly identified as not leakage-safe), not on a magic gap value.

**Subgroups.** `compute_pooled_metric` = pooled test-set AUC. `check_subgroup_degradation` iterates `machine_id` and `site_id` (Phase 1 scope — density/age are a Phase-2 dimension, one line to add later), computing per-value AUC, `delta_vs_pooled = subgroup_auc - pooled_auc`, and a `flagged` boolean. Flag when a subgroup sits meaningfully below pooled with enough support (a minimum test-row `n` to avoid small-sample noise). **Calibrate the threshold and minimum `n` against the labeled scenarios**, not a guessed constant: `subgroup_scanner_degradation` must flag `machine_id` `M030` (AUC ≈ 0.6243 vs pooled ≈ 0.8345, `verification.subgroups[].degraded == true`), and `clean_patient_grouped` must produce zero flags. Pick the simplest rule that satisfies both.

### Oracle quick-reference (verify against the manifests, don't trust this table alone)

| scenario | split | train∩test patients | pooled test AUC | degraded subgroup |
|---|---|---|---|---|
| clean_patient_grouped | patient | 0 | 0.8598 | none |
| weak_random_split_leakage | random | 940 | 0.8425 | none |
| duplicate_row_leakage | patient | 113 | 0.8561 | none |
| subgroup_scanner_degradation | patient | 0 | 0.8345 | machine_id M030: 0.6243 (out 0.873) |
| subgroup_density_degradation | patient | 0 | 0.7339 | density band 0.6699 (Phase-2 dimension) |
| optimistic_site_shortcut | random | 990 | 0.9647 | none |

## The reporter step

`render_report(payload)` sends the assembled payload JSON to Claude and returns the report text. Verify the current Anthropic Python SDK call shape with the `claude-api` skill before writing it (client construction, `messages.create`, `system=`, reading the text out of the response). Requirements:
- Read the key from `ANTHROPIC_API_KEY` (already the `API_KEY_ENV` constant). Never hard-code it.
- Target model stays `claude-opus-4-8` (the `MODEL` constant) — do **not** switch the reporter to Fable 5; the reviewer prompt is written for Opus and the JSON→prose task belongs there.
- Load the system prompt from disk via `_load_system_prompt` (the `SYSTEM_PROMPT_PATH` constant). The file has a short Markdown doc header; the operative system prompt is the content **after the first `---` separator** — send that, not the header.
- Send the payload as `json.dumps(payload)` in the user message.
- Test it offline with a mocked Anthropic client (assert the model string is `claude-opus-4-8` and the payload JSON reaches the request). Do not put a live API call in the test suite.

## Demo asset

Add `demo/run_demo.sh`: run the CLI over `clean_patient_grouped` (expect GREEN) then `weak_random_split_leakage` (expect the leakage flag and Claude's explanation), printing both reports. This is the spine of the 3-minute video; recording the video is a human step, not yours.

## Boundaries

- Minimal implementation. Don't add features, refactor the scaffold, or introduce abstractions beyond what a check needs. A one-shot metric doesn't need a helper; trust the fixed input schema; validate only at the CLI boundary (the CSV path). Don't design for hypothetical inputs that cannot occur.
- One module per package. Don't split `validators` into more files or add config/plugin layers.
- Don't touch or refactor `claude-science-artifacts/` — it's the finished oracle.
- Don't start Phase 2 (bootstrap CIs, calibration plots, TRIPOD+AI/CLAIM mapping, reviewer critique).
- Don't change the report contract fields or the reporter target model.
- Local commits per completed check are welcome; do not push, open PRs, or create backup branches.

## Autonomy and reporting

When you have enough to act, act — this is a well-scoped task, so carry each check from test to green without stopping to re-confirm sub-decisions. Pause and end the turn only for a genuine blocker: a scope change, a destructive action, or input only I can provide (e.g., a missing `ANTHROPIC_API_KEY` when you reach the live report step). Before reporting progress, check each claim against a tool result from this session; if a check isn't verified against its oracle yet, say so. If `pytest` fails, show the output. State what's done and verified plainly.

If Claude declines any step because the domain reads as life-sciences, note it and continue with the parts you can — the work is deterministic statistics on synthetic data, and the report step can fall back to Opus 4.8.

## Done when

`pytest` is green with real assertions (no xfail/skip on the implemented checks); `clinval-validate --predictions claude-science-artifacts/scenarios/weak_random_split_leakage.csv` prints a risk report end-to-end with a real `ANTHROPIC_API_KEY`; `demo/run_demo.sh` exists; and `README.md`'s status line is updated from "scaffold stage" to real run instructions. Leave the demo-video recording and submission write-up to me.
