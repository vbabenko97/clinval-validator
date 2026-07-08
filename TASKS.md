# TASKS — clinval-validator

Every item names a concrete artifact. Phases match CLAUDE.md — finish Phase 1
completely before starting any Phase 2 item.

## Phase 0 — Scaffold (done)

- [x] `README.md` — full project README (purpose, disclaimer, MVP scope, schema, quickstart, demo narrative, MIT).
- [x] `PROJECT_PLAN.md` — problem, user, MVP, non-goals, architecture, checks, report plan, risks, demo, stretch.
- [x] `TASKS.md` — this staged checklist.
- [x] `clinval_validators/checks.py` — contract TypedDicts + 4 typed check stubs (`raise NotImplementedError`).
- [x] `clinval_validators/__init__.py` — re-exports the contract + checks.
- [x] `reporter/report.py` — `render_report` stub; `_load_system_prompt`; `MODEL`/`API_KEY_ENV`/`SYSTEM_PROMPT_PATH`.
- [x] `reporter/__init__.py` — re-exports `render_report` + constants.
- [x] `cli.py` — argparse entrypoint wiring (load → validators → assemble → reporter → print).
- [x] `data/README.md` — points at `claude-science-artifacts/scenarios/`, names the demo scenario.
- [x] `tests/` — `conftest.py` + `test_fixtures.py` + `test_validators.py` + `test_cli.py`, all xfail/skip.
- [x] `pyproject.toml` — Python 3.11+, deps `pandas`/`scikit-learn`/`anthropic`, dev `pytest`, packages declared.
- [x] `LICENSE` — MIT, 2026, vbabenko97.

## Phase 1 — MVP (the submittable product)

### Check 1 — Patient-level leakage
- [ ] Implement `check_patient_leakage(df)` → `LeakageResult` (count of `patient_id`s in >1 split + rate).
- [ ] `tests/test_validators.py::test_detects_train_test_patient_overlap` passes: `overlapping_patient_ids == 940` on `weak_random_split_leakage`. Remove its `xfail`.

### Check 2 — Split-quality audit
- [ ] Implement `audit_split_quality(df)` → `SplitAuditResult` (AUC under random vs patient/site-grouped split + `gap`).
- [ ] Add `tests/test_validators.py` case: grouped-split AUC < random-split AUC on `weak_random_split_leakage`.

### Check 3 — Subgroup degradation
- [ ] Implement `compute_pooled_metric(df)` → `PooledMetric` (pooled test-split AUC).
- [ ] Implement `check_subgroup_degradation(df)` → `list[SubgroupResult]` (per-`machine_id`/`site_id` AUC, `delta_vs_pooled`, `flagged`).
- [ ] `tests/test_validators.py::test_subgroup_degradation_is_detectable` passes on `subgroup_scanner_degradation` (flagged AUC ≈ 0.62 vs pooled ≈ 0.83). Remove its `xfail`.

### Report JSON contract
- [x] `ReportPayload` + `LeakageResult`/`SplitAuditResult`/`SubgroupResult`/`PooledMetric` defined in `clinval_validators/checks.py`.
- [ ] `cli._assemble_payload` returns a `ReportPayload` that matches the reporter prompt shape (assert against a hand-checked JSON in a test).

### Check 4 — Claude report step
- [ ] Implement `reporter.render_report(payload)` — read `ANTHROPIC_API_KEY`, load system prompt, call `claude-opus-4-8`, return report text.
- [ ] `tests/test_reporter.py` — offline test with a mocked Anthropic client (no live call); assert the payload JSON is sent and the model string is `claude-opus-4-8`.

### CLI / demo entrypoint
- [ ] Implement `cli._load_predictions(path)` (`pd.read_csv`) so `clinval-validate --predictions <csv>` runs end-to-end.
- [ ] `tests/test_cli.py::test_cli_smoke_end_to_end` passes (exit 0, non-empty report). Remove its `xfail`.
- [ ] Un-skip `tests/test_fixtures.py` (schema + injected-leakage oracle checks).

### Demo + submission polish
- [ ] `demo/run_demo.sh` — scripted path over `clean_patient_grouped` then `weak_random_split_leakage`, printing both reports.
- [ ] Record the <3-minute demo video (naive → grouped collapse → Claude explains → next step).
- [ ] `README.md` — replace the "scaffold stage" status with real, verified run commands and a sample report snippet.
- [ ] Confirm fresh-clone reproducibility: `pip install -e .` → set key → `clinval-validate ...` → `python -m pytest` green.

## Phase 2 — Stretch (only if Phase 1 is fully done)

- [ ] Bootstrap confidence intervals on reported metrics.
- [ ] Calibration plots per subgroup.
- [ ] Reporting-completeness checklist mapped to TRIPOD+AI and CLAIM.
- [ ] Reviewer-style critique + corrected Methods paragraph draft.
- [ ] Reproducibility checklist output.
