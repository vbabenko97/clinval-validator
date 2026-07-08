# Notebooks

This directory contains reproducible Python scripts that rebuild every finding
and chart shown in `deck.md`.

## Files

- `phase2to5_pipeline.py` — end-to-end: loads CSV, re-derives the exposure-adjusted
  churn rates, computes all 8 findings, and regenerates all 8 chart PNGs.
- Source data: `/tmp/ai-analyst-iter2/inputs/customer_churn.csv`.

## How to rerun

```
cd /tmp/ai-analyst-iter2/eval-2-churn-drilldown/with_skill/outputs
python3 notebooks/phase2to5_pipeline.py
```

Output PNGs land in `charts/` (overwritten).

## Key conventions

- `Q_ORDER = ["2025Q1","2025Q2","2025Q3","2025Q4","2026Q1","2026Q2"]`.
- A customer is **at risk** in quarter `q` when `signup_quarter <= q` AND
  (`churn_quarter == "active"` OR `churn_quarter >= q`).
- Churn **rate** = `churned_in_q / at_risk_at_start_of_q`.
- ARR is constant per plan tier ($1.2K / $8.4K / $48K).
