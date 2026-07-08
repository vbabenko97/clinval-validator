# Phase 1 — Framing

## Structured analytical question

**Customer churn events spiked in Q2 2026 (92 churns vs. 48 in Q1 2026 — a 92% jump QoQ). Which customer segments (plan tier, industry, signup cohort, tenure band) are driving the spike, how much ARR is at risk if the pattern continues, and what 1–3 targeted actions should the board sanction next week to arrest it?**

## Decision context

- **Who decides:** Board of Directors at next week's meeting.
- **Decision scope:** Whether (and where) to invest retention dollars — Customer Success headcount, product fixes, pricing changes, or targeted save programs — and how large that investment should be.
- **Audience:** Non-technical. Needs action titles, simple charts, clear asks with confidence levels.

## Success criteria

- **Answered:** We can attribute ≥80% of the Q2 2026 churn jump to specific, named segments (and ideally an underlying mechanism), with each claim validated by an independent re-derivation.
- **Done:** A Marp deck, ≤15 slides, action titles throughout, landing on a single clear ask (≤3 recommendations) with confidence grades.

## Data inventory

- **File:** `/tmp/ai-analyst-iter2/inputs/customer_churn.csv`
- **Rows:** 1,500 customers; no missing values.
- **Columns:** `customer_id`, `signup_quarter` (2025Q1/Q2/Q3), `churn_quarter` (`active` or 2025Q2–2026Q2), `plan_tier` (Starter $1.2K / Pro $8.4K / Enterprise $48K ARR), `industry` (Finance, Healthcare, Manufacturing, Retail, SaaS), `arr_usd`, `tenure_months` (3–18).
- **Period covered:** Signups from Q1–Q3 2025; churn observed through Q2 2026. Q2 2026 is the current quarter (cut-off = analysis date).
- **Dimensions balanced:** Signup cohorts are 485–512 customers each; industries 277–323; plan tiers 223/518/759.

## Hypotheses (at least 3 across multiple cause categories)

| ID | Category | Hypothesis | Predicted pattern in data | Will be tested in |
|----|----------|-----------|---------------------------|-------------------|
| H1 | Composition shift | The Q2 2026 spike is driven by the 2025Q1 signup cohort hitting a ~15-month renewal cliff. | 2025Q1 cohort has a disproportionate share of Q2 2026 churn events; tenure at churn clusters near 15–18 months. | Phase 2.2 / 2.4 |
| H2 | Operational / product | Low-tier (Starter) customers are churning fastest because they find less value and have weaker onboarding. | Starter share of Q2 2026 churn > Starter share of active base. | Phase 2.2 |
| H3 | Segment-specific | One industry is in distress (e.g., Retail or Manufacturing macro pressure) and is over-indexed in Q2 churn. | A single industry's churn rate in Q2 2026 is materially higher than peers'. | Phase 2.2 / 2.4 |
| H4 | ARR concentration / risk | The headline "count of churns" understates the problem because Enterprise churns are rare but huge in ARR, so $-weighted churn tells a different story than #-weighted. | Q2 2026 churned ARR is concentrated in a small number of high-ARR logos. | Phase 2.2 / 2.5 |
| H5 | Data artifact | Apparent Q2 spike is a right-censoring illusion: earlier cohorts have had more time to churn so they appear to dominate. | Churn-rate-per-tenure-month curves overlap cohorts; spike disappears when normalized. | Phase 3 (validation) |

## What carries forward to Phase 2

Test H1–H5 in this order: (a) confirm the aggregate Q2 spike is real; (b) segment the Q2 churners by cohort, tier, industry; (c) drill into whichever segment shows the strongest over-index; (d) size the ARR at risk; (e) run the Simpson's-paradox and right-censoring checks during validation.
