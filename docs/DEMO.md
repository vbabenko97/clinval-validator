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

**Scenario discipline — don't improvise on camera.** Beats 1 and 4 must both use
`optimistic_site_shortcut`. There the split audit points the way the narration
does: re-scoring the same predictions on a patient-disjoint fold drops AUC from
0.9875 to 0.9521 (gap +0.035), so Claude's own output will agree with what you say.

Do **not** substitute `weak_random_split_leakage`. Its gap is *negative* (grouped
0.899 beats random 0.827), and Claude correctly reports that "the leakage did not
inflate the estimate." That is excellent science — the tool refuses a convenient
narrative — but it flatly contradicts an opener that claims the number was inflated.
Save it for the write-up, not the 3-minute cut.

## Delivery notes

- **Two numbers, not three.** The arc is 0.9875 → 0.9521 — the same predictions on
  two evaluation populations. Pooled AUC (0.9647) is a *different* quantity, computed
  over all rows; it stays in the JSON and never enters the narration. Three AUCs in
  the ear is a number salad.
- **Never say "corrected AUC", "true AUC", or "honest performance"** for 0.9521. The
  model was not retrained. Say: *the same predictions, scored where no patient crosses
  the boundary.* Overclaiming here, in a talk about overclaiming, is an own goal.
- Speak the numbers out: "zero point nine eight seven five", "fifty-four thousand
  seven hundred and six". Say **patient-disjoint** slowly — it's the load-bearing term.
- It's **Claude**, not "cloud".
- Short sentences. Let the red-to-green banner flip land before you talk over it.

---

## 0:00–0:12 — The hook

**Say:** A model returns an AUC that looks publishable. The question is whether the
evaluation deserves belief. Here, Python computes the checks deterministically.
Claude explains the risk.

---

## Beat 1 — 0:12–1:00 — One number, two evaluation populations

**Do:** Sidebar → *Predictions source* = **Bundled scenario** → *Scenario* =
`optimistic_site_shortcut`.

**Say:** On the randomly selected test rows, this model scores zero point nine eight
seven five. Now the leakage check. 990 of the 1,002 test patients also appear in the
training data — 98.8 percent overlap. This was split by image, not by patient, so
images of the same woman crossed the train-test boundary. So we take the same
predictions — no retraining, the model is untouched — and score them only where no
patient sits on both sides of that line. The AUC is zero point nine five two. That
is not a corrected truth. It is a direct measurement of how much the reported result
depends on where you draw the split. Every number on this screen was computed
deterministically in Python. Claude receives only the JSON.

---

## Beat 2 — 1:00–1:40 — Real RSNA data, at full scale

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
tool exists to catch. The same two tiles tell the same story: zero point six three
six as split, zero point six one one patient-disjoint. One honest caveat — that is
a deliberately weak baseline, built on pre-imaging metadata only. It illustrates the
failure mode. It is not a claim about any imaging model.

---

## Beat 3 — 1:40–2:05 — The clean control

**Do:** Sidebar → *Predictions source* = **Bundled scenario** → *Scenario* =
`clean_patient_grouped`.

**Say:** Same tool, same checks — but this split is grouped by patient. Zero leaked
patients, and the banner turns green. Now look at the two AUCs: zero point eight
eight two as split, zero point eight eight five patient-disjoint. They barely move.
The result does not depend on where you draw the boundary. That is what an
evaluation you can believe looks like — and it's why the tool doesn't cry wolf.

---

## Beat 4 — 2:05–2:40 — Claude names the correction

**Do:** *Scenario* = `optimistic_site_shortcut` → *Mode* = **Critique** → press
**Generate with Claude**.

**Say:** Now Claude. It receives only the JSON on the left — every number already
computed. It comes back with a journal-reviewer's verdict on what those numbers
actually support, and then rewrites the study's Methods paragraph so the evaluation
is leakage-safe, on a patient-grouped split. This split screen is the whole thesis:
Python computes, Claude explains. It cites only the figures in that payload and
invents none.

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
