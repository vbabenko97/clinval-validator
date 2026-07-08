# ClinVal Validator — 3-Minute Demo Script

**Logline.** ClinVal Validator reads a model's `predictions.csv`, flags the
failure modes that make a clinical-AI AUC claim unsafe, and asks Claude to
explain the risk in plain language a reviewer or PI can act on.

---

## Prerequisites

Before hitting record, confirm both of these are in your shell:

```bash
python -m pip install -e .          # Python 3.11+
export ANTHROPIC_API_KEY=sk-ant-... # personal key; never committed
```

---

## 0:00–0:20 — Introduction

**Say:** I'm going to show you how a clinical-AI model goes from a headline AUC
that looks publishable to a finding that is structurally invalidated by data
leakage — and how ClinVal Validator catches it automatically, without any
guesswork from a language model.

---

## Beat 1 — 0:20–1:10 — Dramatic opener: a leaking "publishable" result

```bash
clinval-validate --predictions claude-science-artifacts/scenarios/optimistic_site_shortcut.csv
```

**Say:** The pooled AUC here is 0.9647. That number would pass peer review in
most venues. But the validator immediately flags it: the split is random, and 990
patients appear in both training and test. Every prediction on those 990 patients
is contaminated by their own training labels. The headline number is an artifact
of leakage, not evidence of generalisation.

---

## Beat 2 — 1:10–1:55 — Real RSNA data: the same failure at full scale

```bash
clinval-validate --predictions predictions_rsna_random.csv
```

**Say:** This runs on the actual RSNA Screening Mammography cohort, mapped into
the predictions schema by a local adapter. The RSNA data and any CSV derived from
it are gitignored and never committed — the license prohibits redistribution, so
the repo stays synthetic-only. On this real screening dataset — 54,706 rows,
7,524 test-set patients — a naive random split leaks 7,511 of those patients, 99.8
percent, back into training. That is not a misconfiguration; it is what a random
split does when patient IDs are not grouped before splitting.

---

## Beat 3 — 1:55–2:20 — The clean control: no false positives

```bash
clinval-validate --predictions claude-science-artifacts/scenarios/clean_patient_grouped.csv
```

**Say:** This scenario uses a patient-grouped split. There are zero train/test
patient overlaps. The pooled AUC is 0.8598 — still reasonable, but now the
validator has nothing to flag, and the report comes back GREEN. The tool does not
cry wolf.

---

## Beat 4 — 2:20–2:45 — Claude names the corrected next step

```bash
clinval-validate --predictions claude-science-artifacts/scenarios/optimistic_site_shortcut.csv --mode critique
```

**Say:** In `critique` mode, Claude reads only the deterministic JSON — it never
recomputes a number — and delivers a journal-reviewer-style verdict on the 0.9647
AUC: what it does and does not support. It then rewrites the study's Methods
paragraph so the evaluation is leakage-safe, with a patient-grouped split, citing
only the figures the validator computed.

---

## 2:45–3:00 — Close

**Say:** The validator runs the leakage check offline in under a second; the
Claude report step needs an API key but adds another ten seconds. That is the full
pipeline: Python computes, Claude explains.

---

## Honesty note

The leakage finding is structural and real: patient IDs genuinely overlap
train and test under a random split, and the validator counts exact overlaps from
the CSV. The AUC magnitudes shown here come from tabular synthetic baselines
designed to illustrate the failure mode — they are not a claim about any specific
imaging model's clinical performance. All data in this repo is synthetic or
public-schema only, modeled on the RSNA Screening Mammography schema. No PHI, no
RSNA images, no real patient records are present. This tool is not medical advice.
