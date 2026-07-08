# TASKS — clinval-validator

Every item names a concrete artifact. Phases match CLAUDE.md — Phase 1 is
complete; Phase 2 items are optional and started only now that Phase 1 is done.

## Phase 0 — Scaffold (done)

- [x] `README.md` — full project README (purpose, disclaimer, MVP scope, schema, quickstart, sample output, demo narrative, MIT).
- [x] `PROJECT_PLAN.md` — problem, user, MVP, non-goals, architecture, checks, report plan, risks, demo, stretch.
- [x] `TASKS.md` — this staged checklist.
- [x] `clinval_validators/checks.py` — contract TypedDicts + 4 typed checks.
- [x] `clinval_validators/__init__.py` — re-exports the contract + checks.
- [x] `reporter/report.py` — reporter mechanics + `MODEL`/`API_KEY_ENV`/prompt paths.
- [x] `reporter/__init__.py` — re-exports the renderers + constants.
- [x] `cli.py` — argparse entrypoint wiring (load → validators → assemble → reporter → print).
- [x] `data/README.md` — points at `claude-science-artifacts/scenarios/`, names the demo scenario.
- [x] `tests/` — `conftest.py` + `test_fixtures.py` + `test_validators.py` + `test_cli.py` + `test_reporter.py`.
- [x] `pyproject.toml` — Python 3.11+, deps `pandas`/`scikit-learn`/`anthropic`, dev `pytest`, packages declared.
- [x] `LICENSE` — MIT, 2026, vbabenko97.

## Phase 1 — MVP (the submittable product) — done

### Check 1 — Patient-level leakage
- [x] `check_patient_leakage(df)` → `LeakageResult` (count of `patient_id`s in both train and test + rate).
- [x] `test_validators.py::test_detects_train_test_patient_overlap` — `overlapping_patient_ids == 940` on `weak_random_split_leakage`; zero on `clean_patient_grouped`; 113 on `duplicate_row_leakage`; 990 on `optimistic_site_shortcut`.

### Check 2 — Split-quality audit
- [x] `audit_split_quality(df)` → `SplitAuditResult` (AUC under random vs patient-grouped split + signed `gap`).
- [x] `test_validators.py::test_audit_split_quality_structure_and_direction` + `..._is_reproducible`.

### Check 3 — Subgroup degradation
- [x] `compute_pooled_metric(df)` → `PooledMetric` (pooled AUC); matches each manifest's `overall_auc`.
- [x] `check_subgroup_degradation(df)` → `list[SubgroupResult]` (per-`machine_id`/`site_id` AUC, `delta_vs_pooled`, `flagged`).
- [x] `test_validators.py::test_subgroup_degradation_is_detectable` — M030 flagged, AUC ≈ 0.6243 on `subgroup_scanner_degradation`; no flags on the clean scenario.

### Report JSON contract
- [x] `ReportPayload` + `LeakageResult`/`SplitAuditResult`/`SubgroupResult`/`PooledMetric` in `clinval_validators/checks.py`.
- [x] `cli._assemble_payload` returns a `ReportPayload` matching the reporter prompt shape (asserted JSON-serializable in `test_cli.py`).

### Check 4 — Claude report step
- [x] `reporter.render_report(payload)` — read `ANTHROPIC_API_KEY`, load system prompt, call `claude-opus-4-8`, return report text.
- [x] `test_reporter.py` — offline test with a mocked Anthropic client (no live call); asserts payload JSON is sent and the model is `claude-opus-4-8`.

### CLI / demo entrypoint
- [x] `cli._load_predictions(path)` (`pd.read_csv`); `clinval-validate --predictions <csv>` runs end-to-end.
- [x] `test_cli.py::test_cli_smoke_end_to_end` (exit 0, report printed).
- [x] `test_fixtures.py` — schema + injected-leakage oracle checks.

### Demo + submission polish
- [x] `demo/run_demo.sh` — scripted path over `clean_patient_grouped` then `weak_random_split_leakage`.
- [x] `README.md` — verified run commands and a sample-output snippet (real deterministic JSON + illustrative report).
- [x] Fresh-clone reproducibility: `pip install -e .[dev]` on Python 3.11+ → `python -m pytest` green (28 tests) → `clinval-validate` runs.
- [ ] Record the <3-minute demo video (naive → grouped collapse → Claude explains → next step). Script: [docs/DEMO.md](docs/DEMO.md). **Owner: user.**

## Phase 2 — Stretch (Phase 1 is done; these are optional)

- [x] Reviewer-style critique + corrected Methods paragraph draft — `render_reviewer_critique` + `clinval-validate --mode critique`; system prompt in `prompts/opus-4-8/reviewer_critique_system_prompt.md`; tested offline in `test_reporter.py`.
- [x] `docs/DEMO.md` — 3-minute demo storyboard (commands + narration).
- [ ] Bootstrap confidence intervals on reported metrics.
- [ ] Calibration plots per subgroup.
- [ ] Reporting-completeness checklist mapped to TRIPOD+AI and CLAIM.
- [ ] Reproducibility checklist output.
