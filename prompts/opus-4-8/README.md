Built from scratch for Built with Claude: Life Sciences, started 2026-07-07.

# ClinVal Validator

A validation tool for medical-imaging ML models. Detects patient-level data leakage,
weak train/test splits, and subgroup performance degradation in a `predictions.csv`,
then generates a human-readable Validation Risk Report.

Python computes the metrics; Claude explains the risk.

**Data:** synthetic / public-schema only (modeled on the RSNA Screening Mammography schema).
No PHI. Not medical advice.

**License:** MIT
