# CLAUDE.md — ClinVal Validator

Built from scratch for "Built with Claude: Life Sciences" (Builder Track). Started 2026-07-07. Submission deadline: 2026-07-13, 21:00 ET.

## What this project is

A validation tool for medical-imaging ML models. It ingests a `predictions.csv` (model outputs + patient/scanner/site metadata) and flags the failure modes that make clinical AI claims unsafe: patient-level data leakage, weak evaluation splits, and subgroup performance degradation. It then produces a human-readable **Validation Risk Report**.

The user is a clinical AI researcher / radiology-lab PhD student who has trained a model on a small biomedical dataset and needs to know whether the result is genuinely validatable or an artifact of leakage and weak splitting.

## Core architectural rule (do not violate)

**Python computes. Claude explains.**

- All metrics, statistical tests, and pass/fail flags are computed by deterministic Python code. Never ask an LLM to compute AUC, run a bootstrap, or decide a flag.
- Claude (via the Anthropic API, `claude-opus-4-8`) is used **only** to turn the structured JSON output of the deterministic layer into prose: the risk report, the reviewer-style critique, and the next-step suggestions.
- The two layers must be cleanly separable: `validators/` (pure Python, no network) and `reporter/` (LLM calls). The tool must run its checks fully offline; only the report-generation step touches the network.

## Data

- Input schema (modeled on the RSNA Screening Mammography dataset — used as reference schema only, no RSNA images or PHI in this repo):
  `patient_id, image_id, machine_id, site_id, age, density, y_true, y_prob, split`
- Ship a **synthetic** `data/synthetic_predictions.csv` with ground-truth-labeled flaws injected: patient IDs bleeding across the split, a random split that ignores patient grouping, and one machine/site subgroup with degraded AUC. This is the test fixture the validators are checked against.
- Never commit real patient data. README must state: synthetic/public-schema data only, no PHI, not medical advice.

## Scope — build in phases, do not flatten

Opus tends to over-engineer (extra files, unrequested abstraction, breadth over depth). Judging rewards depth, working demo, and creative Claude use — not feature count. So:

### Phase 1 — MVP (this is the submittable product; finish it completely before Phase 2)
1. **Patient-level leakage check** — detect `patient_id` overlap between train and test splits; report count and rate.
2. **Split-quality audit** — recompute the headline metric under random split vs patient/site-grouped split; surface the gap.
3. **Subgroup degradation** — AUC (and calibration) per `machine_id` / `site_id`; flag subgroups significantly below the pooled metric.
4. **Claude risk report** — feed the Phase-1 JSON to the LLM; get a green/yellow/red report: what can be claimed, what cannot, what the next validation step is.

Phase 1 must be demoable end-to-end and reproducible on a fresh machine. That is the bar.

### Phase 2 — only if Phase 1 is fully done and time remains (mark each as optional)
5. Bootstrap confidence intervals on the reported metrics.
6. Calibration plots per subgroup.
7. Reporting-completeness checklist mapped to TRIPOD+AI and CLAIM.
8. Reviewer-style critique + a corrected Methods paragraph draft.
9. Submission-ready reproducibility checklist output.

Do not start Phase 2 items while any Phase 1 item is incomplete.

## Anti-over-engineering (from Anthropic's Opus guidance)

- Only build what this file asks for. No speculative configurability, no plugin systems, no abstractions "for later."
- No defensive error handling for scenarios that cannot occur. Trust the fixed input schema.
- No docstrings/comments on code you didn't write; comment only where logic isn't self-evident.
- A single-file validator beats a five-file framework if it does the job.

## Constraints

- Open source, MIT license. Everything in the repo must be original work started during the hackathon.
- Credits/API access run on a **personal** claude.ai account (institutional accounts are ineligible). Never hardcode an API key; read from env.
- Stack: Python 3.11+, pandas, scikit-learn for metrics. Streamlit **or** a thin CLI for the demo — pick one, keep it minimal.
- The 3-minute demo video is worth 30% of judging. Design the demo path first: naive split looks good → grouped split collapses it → Claude explains why the claim is unsafe → corrected next step. Build toward that narrative.

## Definition of done for the hackathon

A fresh clone runs the validator on the synthetic CSV, prints the deterministic flags, calls Claude to render the risk report, and the whole thing is captured in a <3-min demo. Anything beyond that is Phase 2.
