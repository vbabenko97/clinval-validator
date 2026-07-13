# ClinVal Validator — 3-Minute Demo Script

**Logline.** A clinical-AI model reports an AUC that looks publishable. ClinVal
Validator answers whether that number is real or an artifact of data leakage —
deterministic Python computes every flag, Claude only explains the risk.

Recorded through the Streamlit UI, with a short terminal cut at the end to prove
the pipeline is a real, reproducible tool and not just a button.

---

## Before you hit record

```bash
python -m pip install -e '.[demo]'     # Python 3.11+; installs Streamlit
export ANTHROPIC_API_KEY=sk-ant-...    # personal key; never committed
streamlit run app.py
```

With the key exported, the sidebar's **Anthropic API key** field is pre-filled and
masked (it's a password input) — nothing secret shows on camera. Have
`predictions_rsna_random.csv` ready in the repo root for Beat 2; it is gitignored
and local-only.

---

## 0:00–0:15 — Intro

**Say:** A model comes back with an AUC that looks publishable, and the question
nobody asks is whether that number survives contact with a correct evaluation.
This tool answers exactly that. Every flag you're about to see is computed by
deterministic Python — Claude never computes a number, it only explains the risk.

---

## Beat 1 — 0:15–0:55 — The publishable-looking result

**Do:** Sidebar → *Predictions source* = **Bundled scenario** → *Scenario* =
`optimistic_site_shortcut`.

**Say:** Pooled AUC is 0.9647. That would clear review in most venues. But look at
the left panel: 990 of the 1,002 test patients — 98.8 percent — also appear in the
training set. This split is random, not patient-grouped. So that headline number
isn't evidence of generalisation; it's an artifact of leakage. And notice what
produced that verdict: the JSON underneath it. No language model touched these
figures.

---

## Beat 2 — 0:55–1:40 — Real RSNA data, at full scale

**Do:** Sidebar → *Predictions source* = **Upload CSV** → upload
`predictions_rsna_random.csv`.

**Say:** Now the real thing — the actual RSNA Screening Mammography cohort, mapped
into the schema by a local adapter. The data and anything derived from it are
gitignored and never committed; the license bans redistribution, so the repo stays
synthetic-only. 54,706 rows. Each patient contributes about four to five mammogram
images — two sides, two views — so a naive row-level random split scatters one
patient's images across train and test. The result: 7,511 of 7,524 test patients,
99.8 percent, also sit in training. Nothing is wrong with RSNA itself — the mistake
is splitting by image instead of by patient, and that is exactly the error this
tool exists to catch. One honest caveat: the pooled AUC here, 0.625, comes from a
deliberately weak baseline built on pre-imaging metadata only. It illustrates the
failure mode; it is not a claim about any imaging model.

---

## Beat 3 — 1:40–2:05 — The clean control

**Do:** Sidebar → *Predictions source* = **Bundled scenario** → *Scenario* =
`clean_patient_grouped`.

**Say:** Same tool, same checks, but this split is grouped by patient. Watch the
panel flip: zero leaked patients, and the red banner turns green — no leakage, no
subgroup flags. Pooled AUC is 0.8598, lower than the leaky 0.96, and this is the
one you can actually trust. The tool doesn't cry wolf.

---

## Beat 4 — 2:05–2:40 — Claude names the correction

**Do:** *Scenario* = `optimistic_site_shortcut` → *Mode* = **Critique** → press
**Generate with Claude**.

**Say:** Now Claude. It receives only the JSON on the left — every number already
computed. It comes back with a journal-reviewer's verdict on what that 0.9647
actually supports, and then rewrites the study's Methods paragraph so the
evaluation is leakage-safe, on a patient-grouped split. This split screen is the
whole thesis: Python computes, Claude explains. It cites only the figures in that
payload and invents none.

---

## 2:40–2:52 — Terminal cut: it's a real tool

```bash
clinval-validate --predictions claude-science-artifacts/scenarios/optimistic_site_shortcut.csv --mode critique
python -m pytest -q
```

**Say:** And this isn't only a UI. The same pipeline runs headless as a CLI, and the
suite is green — thirty tests, including the detectors checked against
ground-truth-labeled manifests.

---

## 2:52–3:00 — Close

**Say:** The leakage check runs fully offline in under a second. Only the
explanation goes to Claude. That's the tool.

---

## Honesty note

The leakage finding is structural and real: under a row-level random split, patient
IDs genuinely appear in both train and test, and the validator counts the exact
overlaps from the CSV. It is a finding about the **split method**, not a claim that
RSNA is an inherently leaky dataset — it is not.

The AUC magnitudes shown come from tabular baselines built to illustrate the failure
mode. The RSNA baseline (0.625) uses pre-imaging metadata only and deliberately
excludes post-imaging outcomes; none of these numbers are a claim about any specific
imaging model's clinical performance.

The split-quality audit compares the same fixed predictions on two different test
subsets. It is a sensitivity diagnostic, not a retrained proof of split-induced
optimism — the rigorous leakage signal is the patient-overlap count.

All data in this repo is synthetic or public-schema only, modeled on the RSNA
Screening Mammography schema. No PHI, no RSNA images, no real patient records. This
tool is not medical advice.
