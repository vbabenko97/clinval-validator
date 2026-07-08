"""
make_scenarios.py
=================

Build a labeled suite of synthetic RSNA-like predictions.csv files, one per
validation scenario, each with a ground-truth manifest. Then VERIFY that the
injected flaws actually landed (overlap counts, subgroup AUCs) so the files
are trustworthy fixtures for a validator's tests.
"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from leakage_generator import (
    GeneratorConfig, Flaws, SubgroupDegradation, generate,
)

OUTDIR = "scenarios"
os.makedirs(OUTDIR, exist_ok=True)

SCENARIOS = {
    # 1. Clean negative control: proper patient-grouped split, realistic AUC.
    "clean_patient_grouped": GeneratorConfig(
        seed=1,
        flaws=Flaws(split_strategy="patient"),
    ),
    # 2. Weak split: random per-image assignment -> patient-level leakage.
    "weak_random_split_leakage": GeneratorConfig(
        seed=2,
        flaws=Flaws(split_strategy="random"),
    ),
    # 3. Explicit duplicate leakage on top of a proper split.
    "duplicate_row_leakage": GeneratorConfig(
        seed=3,
        flaws=Flaws(split_strategy="patient", duplicate_leak_frac=0.08),
    ),
    # 4. Subgroup degradation: one scanner underperforms.
    "subgroup_scanner_degradation": GeneratorConfig(
        seed=4,
        flaws=Flaws(
            split_strategy="patient",
            subgroup_degradations=[
                SubgroupDegradation("machine_id", ["M030"], target_auc=0.62),
            ],
        ),
    ),
    # 5. Subgroup degradation: dense breasts (BI-RADS C/D) underperform.
    "subgroup_density_degradation": GeneratorConfig(
        seed=5,
        flaws=Flaws(
            split_strategy="patient",
            subgroup_degradations=[
                SubgroupDegradation("density", ["C", "D"], target_auc=0.70),
            ],
        ),
    ),
    # 6. Optimistic / leakage-inflated headline AUC + site shortcut.
    "optimistic_site_shortcut": GeneratorConfig(
        seed=6,
        flaws=Flaws(
            split_strategy="random",
            optimistic_auc=0.985,
            site_shortcut_strength=0.8,
        ),
    ),
}


def measured_overlap(df: pd.DataFrame) -> int:
    tr = set(df.loc[df.split == "train", "patient_id"])
    te = set(df.loc[df.split == "test", "patient_id"])
    return len(tr & te)


def safe_auc(y, p) -> float:
    y = np.asarray(y)
    if y.min() == y.max():
        return float("nan")
    return round(roc_auc_score(y, p), 4)


def verify(name, df, manifest) -> dict:
    """Recompute key quantities and compare to the manifest's claims."""
    checks = {}
    exp = manifest["expected_detections"]

    checks["overlap_matches"] = (
        measured_overlap(df) == exp["train_test_patient_overlap"]
    )
    checks["overall_auc"] = safe_auc(df.y_true, df.y_prob)

    # subgroup AUC vs. target
    sub_ok = []
    for deg in manifest["injected_flaws"]["subgroup_degradations"]:
        m = df[deg["column"]].isin(deg["values"])
        auc_in = safe_auc(df.loc[m, "y_true"], df.loc[m, "y_prob"])
        auc_out = safe_auc(df.loc[~m, "y_true"], df.loc[~m, "y_prob"])
        sub_ok.append({
            "column": deg["column"], "values": deg["values"],
            "target_auc": deg["target_auc"],
            "measured_auc_in": auc_in, "measured_auc_out": auc_out,
            "degraded": (not np.isnan(auc_in)) and auc_in < auc_out,
        })
    checks["subgroups"] = sub_ok
    return checks


def main():
    summary_rows = []
    for name, cfg in SCENARIOS.items():
        df, manifest = generate(cfg)
        csv_path = os.path.join(OUTDIR, f"{name}.csv")
        man_path = os.path.join(OUTDIR, f"{name}.manifest.json")
        df.to_csv(csv_path, index=False)
        checks = verify(name, df, manifest)
        manifest["verification"] = checks
        with open(man_path, "w") as fh:
            json.dump(manifest, fh, indent=2)

        exp = manifest["expected_detections"]
        summary_rows.append({
            "scenario": name,
            "rows": exp["n_rows"],
            "patients": exp["n_patients"],
            "img_prev": exp["prevalence_image_level"],
            "split": manifest["injected_flaws"]["split_strategy"],
            "train_test_overlap": exp["train_test_patient_overlap"],
            "dup_leaked_pat": exp["duplicate_leaked_patients"],
            "leakage_safe": exp["split_is_leakage_safe"],
            "overall_auc": checks["overall_auc"],
            "subgroup_auc_in": checks["subgroups"][0]["measured_auc_in"]
                               if checks["subgroups"] else None,
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(os.path.join(OUTDIR, "_scenario_summary.csv"), index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
