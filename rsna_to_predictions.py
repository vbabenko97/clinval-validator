"""Adapt the RSNA-SMBC ``train.csv`` into a validator ``predictions.csv``.

Local-only utility: the RSNA-SMBC license bans redistribution, so neither the
input table nor the output written here may be committed (both are gitignored).
This maps the real tabular schema onto the validator's contract, fills the two
columns RSNA does not provide — ``y_prob`` (a leakage-safe tabular baseline) and
``split`` (train/test assignment) — and writes a table the validators can read.

The baseline model uses only pre-imaging metadata (age, density, laterality,
view, site, machine); it deliberately excludes ``biopsy``/``invasive``/``BIRADS``
because those are post-imaging outcomes that would inflate the score. Its AUC is
illustrative, not an imaging-model claim. The interesting real signal is the
leakage a per-row random split creates across a patient's multiple images.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, cross_val_predict

from clinval_validators import check_patient_leakage

# The verified RSNA-SMBC train.csv header, in file order (confirmed against
# openai/mle-bench's prepare.py, which asserts this list on the real file).
EXPECTED_COLUMNS = [
    "site_id",
    "patient_id",
    "image_id",
    "laterality",
    "view",
    "age",
    "cancer",
    "biopsy",
    "invasive",
    "BIRADS",
    "implant",
    "density",
    "machine_id",
    "difficult_negative_case",
]

# The validator's predictions.csv contract, in order.
TARGET_COLUMNS = [
    "patient_id",
    "image_id",
    "laterality",
    "view",
    "machine_id",
    "site_id",
    "age",
    "density",
    "y_true",
    "y_prob",
    "split",
]

# Pre-imaging features only — no post-imaging outcome columns.
_DENSITY_CODE = {"A": 0, "B": 1, "C": 2, "D": 3}
_LATERALITY_CODE = {"L": 0, "R": 1}
_VIEW_CODE = {"CC": 0, "MLO": 1}

__all__ = [
    "EXPECTED_COLUMNS",
    "TARGET_COLUMNS",
    "load_rsna",
    "build_baseline_yprob",
    "assign_split",
    "to_predictions",
    "main",
]


def load_rsna(path: Path) -> pd.DataFrame:
    """Read the RSNA-SMBC train.csv and verify it carries the expected columns."""
    df = pd.read_csv(path)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"train.csv is missing expected columns: {missing}")
    return df


def _features(df: pd.DataFrame) -> np.ndarray:
    """Encode the six pre-imaging features into a numeric matrix (NaNs kept)."""
    return pd.DataFrame(
        {
            "age": pd.to_numeric(df["age"], errors="coerce"),
            "density": df["density"].map(_DENSITY_CODE),
            "laterality": df["laterality"].map(_LATERALITY_CODE),
            "view": df["view"].map(_VIEW_CODE).fillna(2),
            "site_id": pd.to_numeric(df["site_id"], errors="coerce"),
            "machine_id": pd.to_numeric(df["machine_id"], errors="coerce"),
        }
    ).to_numpy(dtype=float)


def build_baseline_yprob(df: pd.DataFrame, seed: int = 0, n_splits: int = 5) -> np.ndarray:
    """Out-of-fold ``y_prob`` from a patient-grouped tabular baseline.

    Folds are grouped by ``patient_id`` (so the baseline itself has no patient
    leakage) and stratified on ``cancer``. ``HistGradientBoostingClassifier``
    handles the ~50% NaN ``density``/``machine_id`` (all Site-2 rows) natively.
    """
    X = _features(df)
    y = pd.to_numeric(df["cancer"], errors="coerce").to_numpy(dtype=int)
    groups = df["patient_id"].to_numpy()

    pos_groups = df.loc[df["cancer"] == 1, "patient_id"].nunique()
    neg_groups = df.loc[df["cancer"] == 0, "patient_id"].nunique()
    folds = max(2, min(n_splits, pos_groups, neg_groups))

    cv = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    clf = HistGradientBoostingClassifier(random_state=seed)
    proba = cross_val_predict(clf, X, y, groups=groups, cv=cv, method="predict_proba")
    return proba[:, 1]


def assign_split(
    df: pd.DataFrame, mode: str = "patient_grouped", seed: int = 0, test_frac: float = 0.2
) -> pd.Series:
    """Assign a ``train``/``test`` split.

    ``patient_grouped`` keeps every image of a patient in one split (clean, the
    negative control). ``random`` splits per row, so a patient's images scatter
    across train and test — the leakage the validator is meant to catch.
    """
    rng = np.random.default_rng(seed)
    if mode == "random":
        n_test = int(round(len(df) * test_frac))
        test_rows = rng.permutation(len(df))[:n_test]
        mask = np.zeros(len(df), dtype=bool)
        mask[test_rows] = True
    elif mode == "patient_grouped":
        patients = df["patient_id"].unique()
        n_test = int(round(len(patients) * test_frac))
        test_patients = set(rng.permutation(patients)[:n_test].tolist())
        mask = df["patient_id"].isin(test_patients).to_numpy()
    else:
        raise ValueError(f"unknown split mode: {mode!r}")
    return pd.Series(np.where(mask, "test", "train"), index=df.index, name="split")


def _assemble(df: pd.DataFrame, y_prob: np.ndarray, mode: str, seed: int) -> pd.DataFrame:
    out = df.rename(columns={"cancer": "y_true"}).copy()
    out["y_prob"] = y_prob
    out["split"] = assign_split(df, mode, seed).to_numpy()
    return out[TARGET_COLUMNS].reset_index(drop=True)


def to_predictions(
    df: pd.DataFrame, split_mode: str = "patient_grouped", seed: int = 0
) -> pd.DataFrame:
    """Map RSNA rows to the validator schema with a baseline ``y_prob`` + split."""
    y_prob = build_baseline_yprob(df, seed=seed)
    return _assemble(df, y_prob, split_mode, seed)


def _diagnostics(df: pd.DataFrame, y_prob: np.ndarray) -> str:
    """Summary + the facts the research pass flagged to verify on the real file."""
    machine = pd.to_numeric(df["machine_id"], errors="coerce")
    cancer = pd.to_numeric(df["cancer"], errors="coerce")
    try:
        auc = f"{roc_auc_score(cancer, y_prob):.4f}"
    except ValueError:
        auc = "undefined (single class)"
    return "\n".join(
        [
            f"rows: {len(df)}",
            f"unique patients: {df['patient_id'].nunique()}",
            f"cancer prevalence: {cancer.mean():.4f}",
            f"OOF baseline AUC: {auc}",
            f"density NaN rate: {df['density'].isna().mean():.3f}",
            f"machine_id NaN rate: {machine.isna().mean():.3f}",
            f"machine_id distinct: {machine.nunique()}",
            f"laterality values: {sorted(df['laterality'].dropna().unique().tolist())}",
            f"view values: {df['view'].value_counts().to_dict()}",
        ]
    )


def _dest_path(output: Path, mode: str, n_modes: int) -> Path:
    if n_modes == 1:
        return output
    stem = output.with_suffix("")
    return stem.parent / f"{stem.name}_{mode}{output.suffix}"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rsna_to_predictions",
        description="Adapt RSNA-SMBC train.csv into a validator predictions.csv (gitignored).",
    )
    parser.add_argument("--input", type=Path, required=True, help="Local RSNA-SMBC train.csv.")
    parser.add_argument("--output", type=Path, default=Path("predictions_rsna.csv"))
    parser.add_argument(
        "--split-mode", choices=["random", "patient_grouped", "both"], default="both"
    )
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    df = load_rsna(args.input)
    y_prob = build_baseline_yprob(df, seed=args.seed)
    print(_diagnostics(df, y_prob))

    modes = ["random", "patient_grouped"] if args.split_mode == "both" else [args.split_mode]
    for mode in modes:
        out = _assemble(df, y_prob, mode, args.seed)
        dest = _dest_path(args.output, mode, len(modes))
        out.to_csv(dest, index=False)
        n_test = int((out["split"] == "test").sum())
        leaked = check_patient_leakage(out)["overlapping_patient_ids"]
        print(f"[{mode}] wrote {dest}  test_rows={n_test}  leaked_patients={leaked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
