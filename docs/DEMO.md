# ClinVal Validator — 3-Minute Demo Script

Note (2026-10-18). The narration below is the script of a recorded video and is unchanged. Corrections since that recording:

- The 0.9875 → 0.9521 drop lies inside the sample range the tool now reports.
- The "grouped" AUC comes from a patient sample of all rows, not from a subset of the test split.
- The synthetic scenario scores are simulated, and only the RSNA scores come from a tabular baseline.
- The risk level is now computed in Python.
- Install `.[dev,demo]` before running pytest on camera.
- Produce predictions_rsna_random.csv with `python rsna_to_predictions.py --input data/rsna/train.csv`.

**Logline.** A clinical-AI model reports an AUC that looks publishable. ClinVal
Validator answers whether that number is real or an artifact of data leakage —
deterministic Python computes every flag, Claude only explains the risk.

Recorded through the Streamlit UI, with a short terminal cut at the end to prove
the pipeline is a real, reproducible tool and not just a button.

Every `Say:` block below is measured. Total narration is ~158 seconds at a normal
reading pace (~145 words/minute), leaving ~20 seconds for clicks and pauses inside
the 3-minute cap. Do not ad-lib extra sentences — that is what pushed the first
take to four minutes.

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

- **Talk over the waiting.** The Claude spinner (~15s) and the RSNA upload (~10s)
  are free if you keep narrating through them. Go silent and they cost you half a
  minute. Both beats below are written to cover their own wait.
- **Two numbers, not three.** The arc is 0.9875 → 0.9521 — the same predictions on
  two evaluation populations. Pooled AUC (0.9647) is a *different* quantity, computed
  over all rows; it stays in the JSON and never enters the narration. Three AUCs in
  the ear is a number salad.
- **Never say "corrected AUC", "true AUC", or "honest performance"** for 0.9521. The
  model was not retrained. Say: *the same predictions, scored where no patient crosses
  the boundary.* Overclaiming here, in a talk about overclaiming, is an own goal.
- Speak the numbers out: "zero point nine eight seven five". Say **patient-disjoint**
  slowly — it's the load-bearing term.
- It's **Claude**, not "cloud".
- **If you still run long, cut the terminal beat** (2:27–2:40). It is the only
  droppable segment: the repo, the README, and the green suite carry that signal
  without it. Never cut Beat 2 or Beat 3 — real data and the negative control are
  what a life-sciences reviewer weighs.

---

## 0:00–0:11 — The hook

**Say:** A model returns an AUC that looks publishable. The question is whether the
evaluation deserves belief. Here, Python computes the checks deterministically.
Claude explains the risk.

---

## Beat 1 — 0:11–0:54 — One number, two evaluation populations

**Do:** Sidebar → *Predictions source* = **Bundled scenario** → *Scenario* =
`optimistic_site_shortcut`.

**Say:** On the randomly selected test rows, this model scores zero point nine eight
seven five. Now the leakage check. 990 of the 1,002 test patients also appear in
training — 98.8 percent overlap. This was split by image, not by patient, so images
of the same woman crossed the train-test boundary. Take the same predictions — no
retraining — and score them only where no patient sits on both sides of that line.
Zero point nine five two. That is not a corrected truth. It measures how much the
reported result depends on where you draw the split. Every number here was computed
in Python.

---

## Beat 2 — 0:54–1:33 — Real RSNA data

**Do:** Sidebar → *Predictions source* = **Upload CSV** → upload
`predictions_rsna_random.csv`. Keep talking while it loads.

**Say:** Now real data — the actual RSNA screening mammography cohort, mapped into
our schema by a local adapter. It's gitignored: the license bans redistribution, so
this repo stays synthetic. Each patient has four to five images — two sides, two
views — so a row-level random split scatters one patient across train and test. The
result: 7,511 of 7,524 test patients — 99.8 percent — also sit in training. Nothing
is wrong with RSNA. The mistake is splitting by image instead of by patient. One
caveat: this is a deliberately weak metadata baseline, not an imaging model.

---

## Beat 3 — 1:33–1:57 — The clean control

**Do:** Sidebar → *Predictions source* = **Bundled scenario** → *Scenario* =
`clean_patient_grouped`. Let the red-to-green flip land before you speak.

**Say:** Same tool, same checks — but this split is grouped by patient. Zero leaked
patients, and the banner turns green. Look at the two AUCs: zero point eight eight
two, and zero point eight eight five. They barely move. The result doesn't depend on
where you draw the boundary. That's an evaluation you can believe — and it's why the
tool doesn't cry wolf.

---

## Beat 4 — 1:57–2:27 — Claude names the correction

**Do:** *Scenario* = `optimistic_site_shortcut` → *Mode* = **Critique** → press
**Generate with Claude**. Narrate through the spinner.

**Say:** Now Claude. It receives only the JSON on the left — every number already
computed. It comes back with a journal reviewer's verdict on what those numbers
actually support, then rewrites the study's Methods paragraph so the evaluation is
leakage-safe. This split screen is the whole thesis: Python computes, Claude
explains. It cites only the figures in that payload, and invents none.

---

## 2:27–2:40 — Terminal cut: it's a real tool

**Do:** Export the key **in this shell first** — a terminal you just opened does not
inherit it from the one running Streamlit, and without it the CLI prints the JSON
plus a "key is not set" notice instead of the critique.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
clinval-validate --predictions claude-science-artifacts/scenarios/optimistic_site_shortcut.csv --mode critique
python -m pytest -q
```

**Say:** And it isn't only a UI. The same pipeline runs as a CLI — with thirty-six
tests green against ground-truth-labeled manifests.

---

## 2:40–2:50 — Close

**Say:** The leakage check runs fully offline in under a second. Only the
explanation goes to Claude. That's the tool.

---

## Honesty note

The leakage finding is structural and real: under a row-level random split, patient
IDs genuinely appear in both train and test, and the validator counts the exact
overlaps from the CSV. It is a finding about the **split method**, not a claim that
RSNA is an inherently leaky dataset — it is not.

The AUC magnitudes shown come from tabular baselines built to illustrate the failure
mode. The RSNA baseline uses pre-imaging metadata only and deliberately excludes
post-imaging outcomes; none of these numbers are a claim about any specific imaging
model's clinical performance.

The split-quality audit compares the same fixed predictions on two different test
subsets. It is a sensitivity diagnostic, not a retrained proof of split-induced
optimism — the rigorous leakage signal is the patient-overlap count.

All data in this repo is synthetic or public-schema only, modeled on the RSNA
Screening Mammography schema. No PHI, no RSNA images, no real patient records. This
tool is not medical advice.
