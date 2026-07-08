# CLAUDE.md — ClinVal Validator

Built from scratch for **"Built with Claude: Life Sciences"** (Builder Track). Started 2026-07-07. Submission deadline: **2026-07-13, 21:00 ET**.

Behavioral rules (how to work, delegation, communication style) live in [AGENTS.md](AGENTS.md) — they apply to Claude too. This file is the **project spec**: what to build and the rules specific to this repo.

## What this project is

A validation tool for medical-imaging ML models. It ingests a `predictions.csv` (model outputs + patient/scanner/site metadata) and flags the failure modes that make clinical AI claims unsafe: patient-level data leakage, weak evaluation splits, and subgroup performance degradation. It then produces a human-readable **Validation Risk Report**.

Named user: a clinical-AI researcher / radiology-lab PhD student who trained a model on a small biomedical dataset and needs to know whether the result is genuinely validatable or an artifact of leakage and weak splitting.

## Core architectural rule (do not violate)

**Python computes. Claude explains.**

- All metrics, statistical tests, and pass/fail flags are computed by deterministic Python. Never ask an LLM to compute AUC, run a bootstrap, or decide a flag.
- Claude (Anthropic API, `claude-opus-4-8`) is used **only** to turn the deterministic layer's structured JSON into prose: the risk report, reviewer-style critique, next-step suggestions. See the reporter contract in [prompts/opus-4-8/reporter_system_prompt.md](prompts/opus-4-8/reporter_system_prompt.md) — it may cite only numbers present in the JSON.
- Layers stay cleanly separable: `clinval_validators/` (pure Python, no network, runs fully offline) and `reporter/` (the only code that touches the network).

## Repo map — current state

What exists:
- [claude-science-artifacts/](claude-science-artifacts/) — **working** synthetic-data generator + labeled test fixtures (this is the test oracle for the validators).
  - `leakage_generator.py` — generates one RSNA-like `predictions.csv` with injected, manifest-verified flaws.
  - `make_scenarios.py` — builds the full labeled suite in `scenarios/`.
  - `scenarios/*.csv` + `*.manifest.json` + `_scenario_summary.csv` — 6 ground-truth-labeled scenarios.
- [prompts/](prompts/) — model-specific project briefs (opus-4-8, gpt-5-5) used to bootstrap the build. Historical artifacts, not runtime code.
- [AGENTS.md](AGENTS.md) — Codex/GPT behavioral rules (also govern Claude).

To build (MVP — see Scope):
- `clinval_validators/` — deterministic checks (leakage, split audit, subgroup degradation) → structured JSON.
- `reporter/` — feeds validator JSON to Claude, renders the risk report.
- `data/` — the demo input table (copy/symlink a fixture from `claude-science-artifacts/scenarios/`).
- `tests/` — unit tests (see Definition of done).
- CLI **or** thin Streamlit demo — pick one, keep minimal.

## Commands

```bash
# Generate the full labeled scenario suite (writes scenarios/*.csv + manifests + _scenario_summary.csv)
cd claude-science-artifacts && python3 make_scenarios.py

# Generate one custom table with specific injected flaws
python3 claude-science-artifacts/leakage_generator.py --out predictions.csv \
    --split-strategy random --degrade machine_id:M030:0.60 --optimistic-auc 0.98
```

Once the MVP exists, document its real commands here (run validators, `pytest`, launch the demo). Do **not** add commands that don't run yet — a stale command is worse than none.

## Data & schema

Fixtures are the source of truth. Actual generated header:

```
patient_id, image_id, laterality, view, machine_id, site_id, age, density, y_true, y_prob, split
```

Validators consume the minimal subset: `patient_id, machine_id, site_id, y_true, y_prob, split` (plus `density`/`age` for subgroup checks). Modeled on the RSNA Screening Mammography schema — **reference schema only, no RSNA images or PHI in this repo**.

Scenario suite (`_scenario_summary.csv`), each with a `*.manifest.json` recording injected flaws + `expected_detections` the validators are checked against:

| Scenario | Flaw | Detectable signal |
|---|---|---|
| `clean_patient_grouped` | none (negative control) | all checks pass |
| `weak_random_split_leakage` | patient overlap via random split | 940 train/test patient overlaps |
| `duplicate_row_leakage` | near-duplicate rows train→test | 113 duplicate-leaked patients |
| `subgroup_scanner_degradation` | one scanner AUC low | subgroup AUC 0.62 vs pooled 0.83 |
| `subgroup_density_degradation` | one density band AUC low | subgroup AUC 0.67 vs pooled 0.73 |
| `optimistic_site_shortcut` | inflated AUC + site shortcut | AUC 0.96 under a leaking random split |

Never commit real patient data. README must state: synthetic/public-schema only, no PHI, not medical advice.

## Scope — build in phases, do not flatten

Judging rewards depth, a working demo, and creative Claude use — not feature count. Opus tends to over-engineer; resist it.

### Phase 1 — MVP (the submittable product; finish completely before Phase 2)
1. **Patient-level leakage check** — detect `patient_id` overlap between train/test; report count + rate.
2. **Split-quality audit** — recompute the headline metric under random vs patient/site-grouped split; surface the gap.
3. **Subgroup degradation** — AUC (+ calibration) per `machine_id`/`site_id`; flag subgroups significantly below pooled.
4. **Claude risk report** — feed Phase-1 JSON to the LLM; get a green/yellow/red report: what can be claimed, what cannot, the next validation step.

Phase 1 must be demoable end-to-end and reproducible on a fresh clone. That is the bar.

### Phase 2 — only if Phase 1 is fully done and time remains (each optional)
5. Bootstrap confidence intervals. 6. Calibration plots per subgroup. 7. Reporting-completeness checklist mapped to TRIPOD+AI and CLAIM. 8. Reviewer-style critique + corrected Methods paragraph. 9. Reproducibility checklist output.

Do not start Phase 2 while any Phase 1 item is incomplete.

## Anti-over-engineering

- Build only what this file asks for. No speculative configurability, plugin systems, or abstractions "for later."
- No defensive error handling for scenarios that cannot occur. Trust the fixed input schema.
- Comment only where logic isn't self-evident; don't document code you didn't write.
- A single-file validator beats a five-file framework if it does the job.

## Constraints

- Open source, **MIT**. All repo work must be original, started during the hackathon.
- Credits run on a **personal** claude.ai account (institutional accounts ineligible). Never hardcode an API key — read from env.
- Stack: Python 3.11+, pandas, scikit-learn for metrics. Streamlit **or** a thin CLI — pick one.
- The 3-minute demo video is 30% of judging. Design the demo path first: naive split looks good → grouped split collapses it → Claude explains why the claim is unsafe → corrected next step. Build toward that narrative.

## Definition of done

A fresh clone runs the validator on a synthetic scenario CSV, prints the deterministic flags, calls Claude to render the risk report, and the whole thing is captured in a <3-min demo. Verify with unit tests: schema check, leakage-is-injected, detector catches train/test overlap, subgroup degradation is detectable, and a CLI smoke test end-to-end. Anything beyond that is Phase 2.
