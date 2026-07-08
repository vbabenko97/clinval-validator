# Synthetic RSNA-like predictions + leakage generator

Fixtures for a medical-imaging ML **validation** tool. Produces
`predictions.csv` tables that look like RSNA screening-mammography outputs and
**inject known, detectable flaws**, so a validator can be tested against ground
truth.

## Schema

`patient_id, image_id, laterality, view, machine_id, site_id, age, density, y_true, y_prob, split`

- Screening exam ≈ 4 images (L/R × CC/MLO), with occasional extra/dropped views → **non-uniform images per patient** (this is what makes image-level random splits leak).
- Machines are nested in sites (`M<site><n>`); cancer label lives on the affected laterality; density (BI-RADS A–D) modestly raises risk and prevalence is screening-realistic (~1.5% image-level).
- `y_prob` is drawn so overall ROC-AUC hits a target (`AUC = Φ(d/√2)`); AUC survives the sigmoid that maps latent scores to (0,1).

## Injected failure modes

| Family | Knob | Detectable signal |
|---|---|---|
| Patient-level leakage (weak split) | `split_strategy=random` | same `patient_id` in train & test |
| Patient-level leakage (duplicates) | `duplicate_leak_frac` | near-duplicate rows copied train→test |
| Weak vs safe split | `split_strategy` ∈ {random, **patient**, **site**} | only patient/site are leakage-safe |
| Subgroup degradation | `subgroup_degradations` | AUC lower within a scanner/site/density/age band |
| Optimistic metric | `optimistic_auc` | implausibly high headline AUC |
| Site shortcut / batch effect | `site_shortcut_strength` | site-correlated nuisance signal |

Every table ships a `*.manifest.json` with `injected_flaws`, recomputed
`expected_detections` (overlap counts, target AUCs), and a `verification`
block confirming the flaw landed.

## Usage

CLI:
```bash
python leakage_generator.py --out predictions.csv \
    --split-strategy random \
    --degrade machine_id:M030:0.60 --degrade density:C,D:0.68 \
    --optimistic-auc 0.98
```

Programmatic:
```python
from leakage_generator import GeneratorConfig, Flaws, SubgroupDegradation, generate
cfg = GeneratorConfig(seed=4, flaws=Flaws(
    split_strategy="patient",
    subgroup_degradations=[SubgroupDegradation("machine_id", ["M030"], 0.62)]))
df, manifest = generate(cfg)
```

Build + self-verify the full labeled suite:
```bash
python make_scenarios.py    # writes scenarios/*.csv + manifests + _scenario_summary.csv
```

## Scenario suite

`clean_patient_grouped` (negative control), `weak_random_split_leakage`,
`duplicate_row_leakage`, `subgroup_scanner_degradation`,
`subgroup_density_degradation`, `optimistic_site_shortcut`.
