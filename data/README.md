# data/

No fixtures are copied or regenerated here. The validators read directly from
the labeled scenario suite that already exists in
[`claude-science-artifacts/scenarios/`](../claude-science-artifacts/scenarios/),
which is the validators' ground-truth test oracle.

Each scenario ships a `*.csv`, a `*.manifest.json` (injected flaws +
`expected_detections`), and is indexed in `_scenario_summary.csv`.

## Demo scenario

The demo runs on **`weak_random_split_leakage`** — a random split with a known
940 train/test patient overlap and pooled AUC 0.8425. It exercises the two
headline checks (patient leakage + split-quality gap) in one table.

Contrast scenarios for the demo narrative:

- `clean_patient_grouped` — negative control; every check should pass (GREEN).
- `optimistic_site_shortcut` — inflated AUC 0.9647 under a leaking random split;
  the "looks great until you group the split" escalation.

Synthetic / public-schema data only. No PHI. Never commit real patient data.
