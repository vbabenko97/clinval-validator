# Synthetic RSNA-like predictions + leakage generator

Fixtures for a medical-imaging validation tool. RSNA is the Radiological Society of North America Screening Mammography Breast Cancer Detection dataset. The generator writes `predictions.csv` tables with that column layout and injects known flaws, so a validator can be tested against ground truth. The rows are synthetic.

## Schema

`patient_id, image_id, laterality, view, machine_id, site_id, age, density, y_true, y_prob, split`

- A screening exam is about 4 images: left and right, each in two views. CC is the craniocaudal view and MLO is the mediolateral oblique view. Occasional extra or dropped views make the image count per patient uneven, which is what lets an image-level random split put one patient in both train and test.
- `machine_id` is the letter `M`, a two-digit site number, and a one-digit machine number. `M030` is site 03, machine 0. The cancer label is on the affected laterality.
- `density` is a Breast Imaging Reporting and Data System (BI-RADS) category, `A` through `D`. Denser categories carry a higher cancer risk in the generator. Image-level prevalence is about 1.5%.
- `d` is the separation, in standard deviations, between the mean latent score of positive rows and the mean latent score of negative rows. Scores are drawn so the ROC AUC is `Φ(d/√2)`. The sigmoid that maps the latent score to a `y_prob` in (0, 1) does not change that AUC.

## Injected failure modes

| Family | Knob | Detectable signal |
|---|---|---|
| Patient-level leakage (weak split) | `split_strategy=random` | same `patient_id` in train & test |
| Patient-level leakage (duplicates) | `duplicate_leak_frac` | near-duplicate rows copied train→test |
| Weak vs safe split | `split_strategy` ∈ {random, **patient**, **site**} | only patient/site are leakage-safe |
| Subgroup degradation | `subgroup_degradations` | AUC lower within a scanner/site/density/age band |
| Optimistic metric | `optimistic_auc` | implausibly high headline AUC |
| Site shortcut / batch effect | `site_shortcut_strength` | site-correlated nuisance signal |

`leakage_generator.py` writes a `*.manifest.json` with `injected_flaws` and
`expected_detections` (overlap counts and target AUCs). The `verification`
block is added only by `make_scenarios.py`, after it recomputes those
quantities on the written table. A manifest from `leakage_generator.py` alone
does not contain `verification`.

Expectations for the six committed scenarios are in
[`scenarios/_scenario_summary.csv`](scenarios/_scenario_summary.csv).

## Usage

Run these from `claude-science-artifacts/`. They need NumPy, pandas, and
scikit-learn. From the repository root, `python -m pip install -e .` installs
pandas and scikit-learn, and NumPy comes with them. `make_scenarios.py`
imports `leakage_generator` as a local module, so the working directory matters.

CLI:
```bash
cd claude-science-artifacts
python leakage_generator.py --out predictions.csv \
    --split-strategy random \
    --degrade machine_id:M030:0.60 --degrade density:C,D:0.68 \
    --optimistic-auc 0.98
```

Programmatic, with `claude-science-artifacts/` on `sys.path`:
```python
from leakage_generator import GeneratorConfig, Flaws, SubgroupDegradation, generate
cfg = GeneratorConfig(seed=4, flaws=Flaws(
    split_strategy="patient",
    subgroup_degradations=[SubgroupDegradation("machine_id", ["M030"], 0.62)]))
df, manifest = generate(cfg)
```

Build the labeled suite and write the `verification` block:
```bash
cd claude-science-artifacts
python make_scenarios.py    # writes scenarios/*.csv + manifests + _scenario_summary.csv
```

## Scenario suite

`clean_patient_grouped` (negative control), `weak_random_split_leakage`,
`duplicate_row_leakage`, `subgroup_scanner_degradation`,
`subgroup_density_degradation`, `optimistic_site_shortcut`.

The committed CSVs and manifests are the test oracle. Regenerating them
replaces that oracle.

