"""
leakage_generator.py
=====================

Synthetic RSNA-mammography-like prediction tables for testing medical-imaging
ML validation tooling.

The generator produces a `predictions.csv` with the columns:

    patient_id, image_id, laterality, view, machine_id, site_id,
    age, density, y_true, y_prob, split

and can *inject* specific, detectable failure modes so that a downstream
validator has ground truth to check against:

  * PATIENT-LEVEL LEAKAGE   - the same patient_id appears in more than one
                              split (train/val/test). Comes in two forms:
                                - "random" split strategy: images assigned to
                                  splits independently, so multi-image patients
                                  naturally straddle splits.
                                - explicit duplicate leakage: near-identical
                                  rows for a patient copied into another split.
  * WEAK SPLIT              - split_strategy in {random, patient, site}. Only
                              patient- and site-grouped splits are leakage-safe.
  * SUBGROUP DEGRADATION    - the model's discrimination (AUC) is deliberately
                              lower for a chosen subgroup (a scanner, a site, a
                              density band, or an age band).
  * OPTIMISTIC / SHORTCUT   - global AUC inflated to an implausible level, or a
                              site-correlated nuisance signal (batch effect).

Every generated table is accompanied by a JSON manifest recording exactly what
was injected and the *expected* detections (overlap counts, target subgroup
AUCs, etc.), so detector unit tests can assert against known answers.

Scores are drawn so that the achieved ROC-AUC matches a requested target:
for equal-variance Gaussian scores with the positive class shifted by a
separation d, AUC = Phi(d / sqrt(2)); AUC is invariant to the monotone
sigmoid we apply to turn latent scores into y_prob in (0, 1).

No PHI. Everything here is synthetic.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Sequence

import numpy as np
import pandas as pd
from scipy.stats import norm

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DENSITY_LEVELS = ["A", "B", "C", "D"]          # BI-RADS breast density
DENSITY_PROBS = [0.10, 0.40, 0.40, 0.10]       # population proportions
VIEWS = ["CC", "MLO"]                          # standard screening views
LATERALITIES = ["L", "R"]


@dataclass
class SubgroupDegradation:
    """Lower the model's AUC for rows matching `column == value` (or value in
    list). `target_auc` is the achieved AUC *within* that subgroup."""
    column: str                       # e.g. "machine_id", "density", "site_id"
    values: Sequence                  # e.g. ["C", "D"] or ["M03"]
    target_auc: float = 0.62


@dataclass
class Flaws:
    """Which failure modes to inject. All default to off / safe."""
    # Split strategy: "patient" and "site" are leakage-safe; "random" is not.
    split_strategy: str = "patient"

    # Explicit duplicate leakage: copy this fraction of *train* patients'
    # rows into the test split (simulates duplicated / re-ingested exams).
    duplicate_leak_frac: float = 0.0

    # Subgroup degradation specs.
    subgroup_degradations: list[SubgroupDegradation] = field(default_factory=list)

    # Optimistic global AUC (e.g. 0.99) - simulates leakage-inflated metrics.
    optimistic_auc: Optional[float] = None

    # Site "shortcut": add a site-correlated nuisance term to the latent score,
    # strength in units of latent SD. 0 disables.
    site_shortcut_strength: float = 0.0


@dataclass
class GeneratorConfig:
    n_patients: int = 2000
    n_sites: int = 4
    machines_per_site: int = 2
    views_per_exam: int = 4            # 4 = LCC, LMLO, RCC, RMLO (standard)
    cancer_prevalence: float = 0.03    # patient-level cancer rate (screening)
    base_auc: float = 0.85            # target overall AUC (when not optimistic)
    split_fractions: tuple = (0.70, 0.15, 0.15)   # train / val / test
    mean_age: float = 58.0
    sd_age: float = 9.0
    min_age: int = 40
    max_age: int = 90
    seed: int = 0
    flaws: Flaws = field(default_factory=Flaws)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def auc_to_separation(auc: float) -> float:
    """Gaussian mean separation d (in SD units) that yields the given ROC-AUC
    for equal-variance positive/negative score distributions."""
    auc = float(np.clip(auc, 0.5001, 0.9999))
    return np.sqrt(2.0) * norm.ppf(auc)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# --------------------------------------------------------------------------- #
# Cohort construction
# --------------------------------------------------------------------------- #

def build_cohort(cfg: GeneratorConfig, rng: np.random.Generator) -> pd.DataFrame:
    """Build the per-image base table (everything except y_prob and split)."""
    n = cfg.n_patients
    patient_ids = np.array([f"P{idx:06d}" for idx in range(n)])

    # Assign each patient to a site, then a machine within that site.
    site_idx = rng.integers(0, cfg.n_sites, size=n)
    site_ids = np.array([f"S{si:02d}" for si in site_idx])
    machine_within = rng.integers(0, cfg.machines_per_site, size=n)
    machine_ids = np.array(
        [f"M{si:02d}{mi:d}" for si, mi in zip(site_idx, machine_within)]
    )

    # Demographics.
    age = rng.normal(cfg.mean_age, cfg.sd_age, size=n)
    age = np.clip(np.round(age), cfg.min_age, cfg.max_age).astype(int)
    density = rng.choice(DENSITY_LEVELS, size=n, p=DENSITY_PROBS)

    # Patient-level cancer. Dense breasts carry modestly higher risk.
    dens_risk = {"A": 0.6, "B": 0.9, "C": 1.2, "D": 1.7}
    risk_w = np.array([dens_risk[d] for d in density])
    p_cancer = cfg.cancer_prevalence * risk_w
    p_cancer = np.clip(p_cancer, 0, 0.99)
    patient_cancer = rng.random(n) < p_cancer
    # Affected side for cancer patients (label lives on that laterality).
    affected_side = rng.choice(LATERALITIES, size=n)

    # Expand to images. Standard screening exam = 4 images (2 views x 2 sides);
    # occasionally add extra views or drop one to make counts non-uniform.
    rows = []
    for i in range(n):
        # base 4 views, with small realistic variation
        extra = rng.choice([0, 0, 0, 1, 2], p=[0.55, 0.15, 0.15, 0.10, 0.05])
        drop = 1 if (cfg.views_per_exam == 4 and rng.random() < 0.03) else 0
        exam_views = [(lat, v) for lat in LATERALITIES for v in VIEWS]
        # add extra repeat views (e.g. spot/repeat acquisitions)
        for _ in range(extra):
            exam_views.append(
                (rng.choice(LATERALITIES), rng.choice(VIEWS))
            )
        if drop:
            exam_views = exam_views[:-1]
        for j, (lat, view) in enumerate(exam_views):
            img_pos = bool(patient_cancer[i] and lat == affected_side[i])
            rows.append(
                dict(
                    patient_id=patient_ids[i],
                    image_id=f"{patient_ids[i]}_{lat}{view}_{j}",
                    laterality=lat,
                    view=view,
                    machine_id=machine_ids[i],
                    site_id=site_ids[i],
                    age=age[i],
                    density=density[i],
                    y_true=int(img_pos),
                )
            )
    df = pd.DataFrame(rows)
    return df


# --------------------------------------------------------------------------- #
# Scores
# --------------------------------------------------------------------------- #

def assign_scores(df: pd.DataFrame, cfg: GeneratorConfig,
                  rng: np.random.Generator) -> pd.DataFrame:
    """Draw y_prob so overall AUC ~= base_auc (or optimistic_auc), with
    per-row separation reduced inside any degraded subgroups."""
    flaws = cfg.flaws
    n = len(df)

    overall_auc = flaws.optimistic_auc if flaws.optimistic_auc else cfg.base_auc
    base_sep = auc_to_separation(overall_auc)

    # Per-row separation starts at base, then is overridden by degradations.
    sep = np.full(n, base_sep, dtype=float)
    for deg in flaws.subgroup_degradations:
        mask = df[deg.column].isin(list(deg.values)).to_numpy()
        sep[mask] = auc_to_separation(deg.target_auc)

    latent = df["y_true"].to_numpy() * sep + rng.normal(0, 1, size=n)

    # Optional site "shortcut": add a site-correlated nuisance offset. Sites
    # with higher cancer prevalence get a global bump (a spurious cue).
    if flaws.site_shortcut_strength > 0:
        site_prev = df.groupby("site_id")["y_true"].transform("mean").to_numpy()
        site_z = (site_prev - site_prev.mean()) / (site_prev.std() + 1e-9)
        latent = latent + flaws.site_shortcut_strength * site_z

    df = df.copy()
    df["y_prob"] = np.round(_sigmoid(latent), 6)
    return df


# --------------------------------------------------------------------------- #
# Splitting
# --------------------------------------------------------------------------- #

def assign_split(df: pd.DataFrame, cfg: GeneratorConfig,
                 rng: np.random.Generator) -> pd.DataFrame:
    """Assign train/val/test according to the chosen strategy.

      * "patient" : group by patient_id (leakage-safe).
      * "site"    : group by site_id (leakage-safe AND distribution-safe).
      * "random"  : per-image random assignment (NOT leakage-safe: multi-image
                    patients straddle splits).
    """
    df = df.copy()
    fr_train, fr_val, fr_test = cfg.split_fractions
    strat = cfg.flaws.split_strategy

    if strat == "random":
        u = rng.random(len(df))
        split = np.where(u < fr_train, "train",
                         np.where(u < fr_train + fr_val, "val", "test"))
        df["split"] = split

    elif strat == "patient":
        groups = np.asarray(df["patient_id"].unique(), dtype=object)
        rng.shuffle(groups)
        u = rng.random(len(groups))
        g_split = np.where(u < fr_train, "train",
                           np.where(u < fr_train + fr_val, "val", "test"))
        mapping = dict(zip(groups, g_split))
        df["split"] = df["patient_id"].map(mapping)

    elif strat == "site":
        sites = np.asarray(sorted(df["site_id"].unique()), dtype=object)
        rng.shuffle(sites)
        # assign whole sites to splits, approximating the fractions by count
        n_sites = len(sites)
        n_train = max(1, round(fr_train * n_sites))
        n_val = max(1, round(fr_val * n_sites)) if n_sites - n_train > 1 else 0
        mapping = {}
        for k, s in enumerate(sites):
            if k < n_train:
                mapping[s] = "train"
            elif k < n_train + n_val:
                mapping[s] = "val"
            else:
                mapping[s] = "test"
        df["split"] = df["site_id"].map(mapping)
    else:
        raise ValueError(f"unknown split_strategy: {strat!r}")

    return df


def inject_duplicate_leakage(df: pd.DataFrame, cfg: GeneratorConfig,
                             rng: np.random.Generator) -> tuple[pd.DataFrame, int]:
    """Copy rows for a fraction of TRAIN patients into the TEST split, with a
    tiny y_prob jitter (simulates duplicated / re-ingested exams appearing in
    both partitions). Returns the augmented frame and the number of leaked
    patients."""
    frac = cfg.flaws.duplicate_leak_frac
    if frac <= 0:
        return df, 0
    train_patients = df.loc[df["split"] == "train", "patient_id"].unique()
    k = int(round(frac * len(train_patients)))
    if k == 0:
        return df, 0
    leaked = rng.choice(train_patients, size=k, replace=False)
    dup = df[df["patient_id"].isin(leaked)].copy()
    dup["split"] = "test"
    dup["image_id"] = dup["image_id"] + "_dup"
    # slight probability jitter so rows are near-duplicates, not identical
    jitter = rng.normal(0, 0.01, size=len(dup))
    dup["y_prob"] = np.clip(np.round(dup["y_prob"] + jitter, 6), 0, 1)
    out = pd.concat([df, dup], ignore_index=True)
    return out, k


# --------------------------------------------------------------------------- #
# Top-level generate
# --------------------------------------------------------------------------- #

def generate(cfg: GeneratorConfig) -> tuple[pd.DataFrame, dict]:
    """Generate a predictions table and its ground-truth manifest."""
    rng = np.random.default_rng(cfg.seed)
    df = build_cohort(cfg, rng)
    df = assign_scores(df, cfg, rng)
    df = assign_split(df, cfg, rng)
    df, n_dup_leaked = inject_duplicate_leakage(df, cfg, rng)

    df = df[
        ["patient_id", "image_id", "laterality", "view", "machine_id",
         "site_id", "age", "density", "y_true", "y_prob", "split"]
    ].reset_index(drop=True)

    manifest = build_manifest(df, cfg, n_dup_leaked)
    return df, manifest


def build_manifest(df: pd.DataFrame, cfg: GeneratorConfig,
                   n_dup_leaked: int) -> dict:
    """Record injected flaws AND expected detections computed from the data."""
    flaws = cfg.flaws

    # Patient overlap across splits (the core leakage signal).
    per_patient_splits = df.groupby("patient_id")["split"].nunique()
    overlap_patients = per_patient_splits[per_patient_splits > 1]
    train_pat = set(df.loc[df.split == "train", "patient_id"])
    test_pat = set(df.loc[df.split == "test", "patient_id"])

    injected = {
        "split_strategy": flaws.split_strategy,
        "duplicate_leak_frac": flaws.duplicate_leak_frac,
        "optimistic_auc": flaws.optimistic_auc,
        "site_shortcut_strength": flaws.site_shortcut_strength,
        "subgroup_degradations": [asdict(d) for d in flaws.subgroup_degradations],
        "base_auc_target": cfg.base_auc,
    }

    expected = {
        "n_rows": int(len(df)),
        "n_patients": int(df.patient_id.nunique()),
        "prevalence_image_level": round(float(df.y_true.mean()), 4),
        "patients_spanning_multiple_splits": int(len(overlap_patients)),
        "train_test_patient_overlap": int(len(train_pat & test_pat)),
        "duplicate_leaked_patients": int(n_dup_leaked),
        "split_is_leakage_safe": flaws.split_strategy in ("patient", "site")
                                 and n_dup_leaked == 0,
        "subgroup_targets": [
            {"column": d.column, "values": list(d.values),
             "target_auc": d.target_auc}
            for d in flaws.subgroup_degradations
        ],
    }

    return {"config": _config_to_dict(cfg),
            "injected_flaws": injected,
            "expected_detections": expected}


def _config_to_dict(cfg: GeneratorConfig) -> dict:
    d = asdict(cfg)
    return d


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="predictions.csv", help="output CSV path")
    p.add_argument("--manifest", default=None,
                   help="output manifest JSON path (default: <out>.manifest.json)")
    p.add_argument("--n-patients", type=int, default=2000)
    p.add_argument("--n-sites", type=int, default=4)
    p.add_argument("--machines-per-site", type=int, default=2)
    p.add_argument("--cancer-prevalence", type=float, default=0.03)
    p.add_argument("--base-auc", type=float, default=0.85)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--split-strategy", choices=["patient", "site", "random"],
                   default="patient")
    p.add_argument("--duplicate-leak-frac", type=float, default=0.0)
    p.add_argument("--optimistic-auc", type=float, default=None)
    p.add_argument("--site-shortcut-strength", type=float, default=0.0)
    p.add_argument("--degrade", action="append", default=[],
                   metavar="COL:VAL[,VAL]:AUC",
                   help="subgroup degradation, e.g. machine_id:M030:0.60 "
                        "or density:C,D:0.68 (repeatable)")
    return p


def _parse_degrade(specs: list[str]) -> list[SubgroupDegradation]:
    out = []
    for s in specs:
        col, vals, auc = s.split(":")
        out.append(SubgroupDegradation(column=col,
                                       values=vals.split(","),
                                       target_auc=float(auc)))
    return out


def main(argv=None):
    args = _build_argparser().parse_args(argv)
    flaws = Flaws(
        split_strategy=args.split_strategy,
        duplicate_leak_frac=args.duplicate_leak_frac,
        subgroup_degradations=_parse_degrade(args.degrade),
        optimistic_auc=args.optimistic_auc,
        site_shortcut_strength=args.site_shortcut_strength,
    )
    cfg = GeneratorConfig(
        n_patients=args.n_patients,
        n_sites=args.n_sites,
        machines_per_site=args.machines_per_site,
        cancer_prevalence=args.cancer_prevalence,
        base_auc=args.base_auc,
        seed=args.seed,
        flaws=flaws,
    )
    df, manifest = generate(cfg)
    df.to_csv(args.out, index=False)
    manifest_path = args.manifest or (args.out + ".manifest.json")
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote {len(df)} rows -> {args.out}")
    print(f"wrote manifest   -> {manifest_path}")


if __name__ == "__main__":
    main()
