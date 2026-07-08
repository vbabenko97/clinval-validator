# Phase 1 -- Framing

## Structured analytical question

Between January and June 2026, the aggregate visit-to-conversion rate for our acquisition funnel has been roughly flat (8.67% in Jan -> 8.76% in Jun, range ~8.66%-9.25%). Marketing has characterized this as stable and healthy. **Is the flat aggregate masking divergent underlying trends across channels and user types -- and if so, what mechanism explains the pattern, and what should the growth team do about it?**

- **Metric of interest:** Visit -> Conversion rate (overall, and at each funnel step). Also: visit mix by channel and user_type, signup->conversion efficiency.
- **Time scope:** Jan 2026 - Jun 2026 (6 months of data).
- **Population scope:** All traffic, segmented by channel (paid_search, organic, email, referral) and user_type (new, returning).
- **Comparison:** Jan 2026 as the baseline; also month-over-month slopes.

## Decision context

- The growth team is debating whether to keep increasing paid spend and whether to worry about their funnel.
- The marketing narrative is "conversion is flat, nothing is wrong." The requester's gut disagrees because paid spend is up and organic traffic is up, yet conversions are not scaling.
- Output supports: (a) confirmation/refutation of the "flat" narrative, (b) identification of what is actually moving underneath, (c) pointed actions the growth team can run.

## Success criteria

A "good" answer:

1. Decides -- with validated numbers -- whether conversion is genuinely flat or a composition artifact.
2. Isolates the specific segments where conversion moved (direction + magnitude).
3. Identifies at least one mechanism explaining *why* the shift happened (e.g., paid mix, user-type mix, channel-level efficiency).
4. Lands on 3-5 actionable recommendations, each ranked by confidence and owner.
5. Is delivered as a Jupyter notebook the growth team can re-run end-to-end without me.

## Hypotheses

| ID | Hypothesis | Category | Expected pattern if true | How we test it |
|---|---|---|---|---|
| H1 | Aggregate is flat, and channel-level conversion rates are also flat -- nothing to worry about. | Baseline (null) | Conversion rate per channel stays in a narrow band; user-type rates also stable. | Phase 2.2: pivot conv rate by channel and user_type by month. |
| H2 | User-type mix is shifting (more returning, fewer new) and hiding opposite trends -- Simpsons Paradox. | Composition shift | New-user visits shrink as share of total; returning rises; within each group, conv rate moves. | Phase 2.2 + 2.4: visit share trend + conv rate by user_type by month. |
| H3 | Paid search volume is up but paid efficiency is declining (returning paid users declining specifically), and organic is absorbing the slack. | Operational / channel economics | Paid visits flat-to-down; organic visits up; paid conv rate deteriorating vs organic. | Phase 2.2-2.4: visits + conv rate by channel by month. |
| H4 | New-user quality is actually improving (better targeting, better landing pages), and the flat aggregate is hiding this win. | Operational | New-user conv rate climbs materially; returning-user conv rate falls (possibly due to saturation or retention issues). | Phase 2.3 trend of conv rate by user_type. |
| H5 | Signup-to-conversion step (post-signup) is where the real movement is, not visit-to-signup. | Funnel-step | Signup rate stable but signup-to-conv rate diverges by segment. | Compute each step of the funnel by month and segment. |

## Data inventory

- **File:** `/tmp/ai-analyst-iter2/inputs/funnel_monthly.csv`
- **Grain:** 1 row per (month x channel x user_type). 48 rows total (6 months x 4 channels x 2 user types). No duplicates.
- **Columns:**
  - `month` (date; 1st of month, Jan-Jun 2026)
  - `channel` (categorical: paid_search, organic, email, referral)
  - `user_type` (categorical: new, returning)
  - `visits` (int)
  - `signups` (int)
  - `conversions` (int)
- **Quality:** No nulls, no duplicates. Sample size is healthy (~55-56k visits/month).

## Carry-forward to Phase 2

- Initial peek at the data already signals a strong H2/H4 pattern: new-user conv rate 5.24% -> 7.37% while returning 13.81% -> 9.93%, and the visit mix is moving toward returning users. Phase 2 will formalize this and drill into whats causing returning-user decline.
- Also carry H3: paid_search visits are down slightly while organic visits are up -- need to reconcile with the "spending more on paid" claim (spend data isnt in the CSV, so we can only reason about traffic-side efficiency).
