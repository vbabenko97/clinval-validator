# Phase 3 -- Validation

Every quantitative claim in Phase 2 was re-derived via an independent method. All Simpson's Paradox and bias checks were worked through. Results below.

## Approach

For each finding, re-derivation used a DIFFERENT method than the original exploration — e.g., if the exploration used `groupby().sum()`, validation used `pivot_table`. For ratios, numerator and denominator were verified separately. For aggregates, parts were reconciled to the whole.

## Finding-by-finding

### F1 -- Overall flat conversion rate (High confidence)

- **Original claim:** v2c 8.67% (Jan) -> 8.76% (Jun), slope +0.021pp/mo, r^2=0.028, p=0.75
- **Re-derivation (method 1):** pivot_table over month. Matches exactly.
- **Re-derivation (method 2):** manual loop with explicit numerator/denominator per month. Matches.
- **Parts-to-whole check:** sum of per-channel conversions == overall monthly conversions. Perfect reconciliation.
- **Verdict:** Matches. Confidence: **High**.

### F2 -- New-user conversion rate rising +2.13pp (High confidence)

- **Original claim:** new-user v2c 5.24% -> 7.37% (+40.6% relative), slope +0.43pp/mo, r^2=0.94, p=0.0014.
- **Re-derivation (method 1):** filter(user_type='new').groupby('month').sum() then conv/visits. Matches (5.24%, 7.37%).
- **Re-derivation (method 2):** pivot_table on filtered slice. Matches.
- **Effect size:** 2.13pp over 6 months is ~41% relative, way above noise (r^2=0.94).
- **Verdict:** Matches. Confidence: **High**.

### F3 -- Returning-user conversion rate falling -3.88pp (High confidence)

- **Original claim:** returning v2c 13.81% -> 9.93% (-28.1% relative), slope -0.78pp/mo, r^2=0.97, p=0.0003.
- **Re-derivation (method 1 & 2):** Both match exactly.
- **Sensitivity check:** linear regression with each month dropped (leave-one-out). Slope stays in the range [-0.74, -0.84]pp/mo across all 6 runs; p-value stays < 0.005 in every case. Result is not driven by a single month.
- **Verdict:** Matches, robust to perturbation. Confidence: **High**.

### F4 -- Simpson's Paradox (High confidence)

**Simpson's Paradox procedure:**

1. Aggregate direction: v2c in Jan 8.67%, in Jun 8.76% — flat / very slight positive.
2. Decompose by user_type:
   - New: 5.24% -> 7.37% (positive)
   - Returning: 13.81% -> 9.93% (negative)
   - **Directions are opposite within subgroups while the aggregate is flat. This is Simpson's Paradox.**
3. Counterfactual decomposition (independent arithmetic):
   - If Jun had Jan's subgroup rates but Jun's mix: 9.88%. (Aggregate would have RISEN.)
   - If Jun had Jun's subgroup rates but Jan's mix: 8.39%. (Aggregate would have FALLEN.)
   - Actual Jun: 8.76%. The two opposing forces approximately cancel.
4. **Check within each channel:** run the same decomposition within paid_search, organic, email, referral. In every single channel, new-user v2c rises 1.87-2.45pp and returning-user v2c falls 2.71-5.11pp. The pattern is NOT a channel artifact.

- **Verdict:** Simpson's Paradox is confirmed and not channel-specific. Confidence: **High**.

### F5 -- Pattern holds across every channel (High confidence)

- **Original claim:** new-user gain and returning-user loss occur in every channel.
- **Re-derivation:** per-channel x user_type pivot (see table in validation notebook output).
  - Email: new +2.17pp, returning -2.71pp
  - Organic: new +2.45pp, returning -5.01pp
  - Paid_search: new +1.87pp, returning -3.26pp
  - Referral: new +2.28pp, returning -5.11pp
- **Verdict:** Matches. Confidence: **High**.

### F6 -- Movement is at visit-to-signup (High confidence)

- **Original claim:** for both user types, the movement in v2c is entirely at the v2s (visit-to-signup) step; the s2c (signup-to-conversion) step is stable.
- **Sanity check:** v2c should equal v2s x s2c (chain rule). For all 48 cells, max diff between direct v2c and v2s*s2c = 1.4e-17 (floating-point zero). Arithmetic confirmed.
- **Re-derivation:** v2s and s2c computed monthly by user_type.
  - New v2s: 8.72% -> 12.34% (+3.62pp) -- meaningful improvement
  - New s2c: 60.13% -> 59.73% (-0.40pp) -- effectively stable
  - Returning v2s: 27.12% -> 19.31% (-7.81pp) -- large decline
  - Returning s2c: 50.93% -> 51.43% (+0.50pp) -- effectively stable
- **Implication:** The mechanism is acquisition/targeting quality (upper funnel), not product/onboarding.
- **Verdict:** Matches. Confidence: **High**.

### F7 -- Traffic-mix shift (High confidence)

- **Original claim:** New-user visits down ~22% across every channel; returning-user visits up 28-44%; total visits flat.
- **Re-derivation:** per-cell Jan vs Jun comparison.
  - New visits: 33,583 -> 25,863 (-23%)
  - Returning visits: 22,400 -> 30,564 (+36%)
  - Total visits: 55,983 -> 56,427 (+0.8%)
- **Parts-to-whole:** per-channel totals sum to monthly totals exactly.
- **Verdict:** Matches. Confidence: **High**.

### F8 -- Opportunity sizing (Medium confidence)

- **Original claim:** ~1,187 returning-user conversions missed in June due to rate decline (~14,240 annualized); ~569 new-user conversions missed due to volume decline.
- **Re-derivation:**
  - Returning: 30,564 Jun visits x (13.81% - 9.93%) = 1,187 missed conversions/mo. Confirmed.
  - New: 33,583 Jan visits x 7.37% = 2,475 conv, actual Jun = 1,906, delta = 569. Confirmed.
- **Caveat:** These counterfactuals assume the new rates would have held for the missing volume (new-user case) and that the Jan rate is achievable again for the current returning volume (returning case). Both are plausible but not guaranteed -- hence Medium confidence.
- **Verdict:** Arithmetic matches; causal assumptions are the weak link. Confidence: **Medium**.

## Bias checklist

| Bias | Status | Note |
|---|---|---|
| Survivorship bias | n/a | No entities dropped; all 48 cells present every month. |
| Selection bias | n/a | Population is all visits across all 4 channels and both user types. |
| Lookahead bias | n/a | All calculations use only the data available at each month. |
| Composition shift | FLAGGED & analyzed (this IS Simpson's Paradox) | The user-type mix shift is the central finding. |
| Metric definition drift | No evidence | conversions<=signups<=visits in all cells; no definition change within the 6 months. |
| Base rate neglect | Checked | Denominators are visits (not rates of rates). Returning-visit denominator grew 36%, so any rate decline there is multiplied. |

## Simpson's Paradox check: explicit summary

- Done: YES (primary finding).
- Aggregate: visit-to-conversion flat (+0.09pp).
- Subgroups: new +2.13pp, returning -3.88pp.
- Direction within subgroups: opposite to each other, and both differ from the aggregate.
- **Do NOT headline the aggregate.** The headline is "flat hides divergence."

## Caveats to carry forward

1. We have only 6 months of data; short series for detecting secular vs seasonal effects. A 12-month view would be more robust.
2. No spend data was provided, so efficiency/CAC cannot be computed. The user mentioned paid spend is up; that claim cannot be tested with this CSV alone.
3. "Returning" is defined by whatever the source system uses; definition drift there (e.g., a change in lookback window) would masquerade as a real rate decline. Worth confirming with data eng.
4. The counterfactual in F8 is a point estimate; the real recovered volume would depend on what caused the returning-user decline.

## Grade distribution

- High confidence: F1, F2, F3, F4, F5, F6, F7 (7 findings)
- Medium confidence: F8 (opportunity sizing — arithmetic is right, causal assumption is the weak point)
- Low confidence: none

Grade spread is concentrated at High because (a) subgroup signals are very large relative to sample noise (p < 0.005), (b) patterns replicate across every channel, and (c) every number re-derived cleanly. The Medium grade on F8 is honest: sizing depends on an assumption about reversibility that the data cannot prove.
