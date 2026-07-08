# Phase 3 - Validation

Each finding below was re-derived independently (pivot table vs groupby vs row-filter sum) and checked for Simpson's Paradox and other biases.

## Summary table

| ID | Finding (headline) | Re-derived | Simpson's check | Bias checks | Confidence |
|---|---|---|---|---|---|
| F1 | Aggregate YoY is -1.6% | pass (3 methods) | not applicable (headline number; the paradox check is F2) | pass | High |
| F2 | Simpson's Paradox: Oahu -4.6%, Maui +3.8% | pass | CONFIRMED - aggregate direction does not hold across islands | pass | High |
| F3 | Oahu accounts for 148% of total decline | pass (parts sum to whole) | n/a | pass | High |
| F4 | Oahu decline is accelerating within 2025 | pass (pivot + boolean mask) | n/a (time pattern, not composition) | pass | High |
| F5 | Hotel concentration on Oahu (67% of Oahu decline) | pass (groupby inside Oahu, sum = -239,833 matches) | All Oahu acc x tier cells are negative; no paradox at this level | pass | High |
| F6 | Japan hotel-luxury Oahu-specific | pass (Oahu is 103.6% of net Japan-hotel-luxury decline; other islands slightly positive) | n/a | pass | High |
| F7 | US_mainland substitution (Maui gains are ~32% of Oahu losses) | pass | n/a | Caveat: correlation not causation; we cannot prove travelers are literally choosing Maui over Oahu from this data alone | Medium |
| F8 | Top-10 cells = 77.7% of Oahu decline | pass (sum of ranked cell deltas matches total) | n/a | pass | High |
| F9 | Decline is level not shape; deteriorating in H2 | pass (H2 YoY -6.3% vs H1 -2.7%) | n/a | pass | High |

## Detailed validation

### F1 - Aggregate -1.6% YoY
- **Claim:** 2024 total = 10,174,681; 2025 total = 10,012,705; YoY = -1.59%.
- **Method 1:** `df.pivot_table(values="visitor_arrivals", index="year", aggfunc="sum")` -> same numbers.
- **Method 2:** `df[df["year"]==Y]["visitor_arrivals"].sum()` row filter -> same numbers.
- **Method 3:** Monthly aggregation `df.groupby("month").sum()` then year filter -> same numbers.
- **Result:** All three independent methods agree to the integer. **Confidence: High.**

### F2 - Simpson's Paradox (Oahu -4.6%, Maui +3.8%)
- **Method 1:** `df.groupby(["year","island"]).sum().unstack()` ratio of 2025/2024.
- **Method 2:** Per-island manual loop using boolean masks. Matches to 4 decimal places.
- **Simpson's Paradox explicit check:**
  - Aggregate direction: -1.59% (negative).
  - Island-level directions: Maui +3.75%, Kauai +0.24%, Hawaii -0.65%, Oahu -4.55%.
  - **Two of four islands move OPPOSITE to the aggregate.** Simpson's Paradox is confirmed. The aggregate is misleading and must not be used as the headline.
- **Confidence: High.**

### F3 - Oahu = 148% of total decline
- **Parts-sum-to-whole:** Sum of island abs_deltas = -161,976; total abs_delta = -161,976. Match exact.
- Oahu delta / total delta = -239,833 / -161,976 = 148.1%. The "148%" is accurate because Maui+Kauai+Hawaii contributed +77,857 of offset gains.
- **Confidence: High.**

### F4 - Oahu decline accelerating through 2025
- **Method 1 (pivot by month-of-year):** Q1 YoY ranged -1.8% to -2.5%; Q4 YoY ranged -6.8% to -9.4%.
- **Method 2 (H1 vs H2 boolean masks):** H1 YoY = -2.72%, H2 YoY = -6.31%. Difference = 3.59 percentage points.
- **Trend direction:** Monotonically deteriorating from Q1 through Q4 (with a Q3-Q4 acceleration). October 2025 is the worst month in the dataset at -9.43% YoY on Oahu.
- **Confidence: High.**

### F5 - Oahu hotel segment drives 67% of Oahu decline
- **Independent re-derivation:** groupby `(accommodation_type, tier)` inside Oahu. Sum of cell abs_deltas = -239,833 = Oahu total. **Parts sum to whole.**
- Hotel total delta = -160,042 (66.7% of Oahu decline). Hotel-luxury = -73,388 (30.6%). Hotel-mid_market = -74,012 (30.9%).
- **Level-2 Simpson check (within Oahu):** Every accommodation x tier cell is negative. No paradox at this level - the decline is genuinely broad *within Oahu* but concentrated in hotels at the accommodation level.
- **Confidence: High.**

### F6 - Japan hotel-luxury is Oahu-specific
- **Cross-island Japan-hotel-luxury table:**
  - Hawaii -792, Kauai +35, Maui +1,328, Oahu -16,506. Net = -15,935.
  - **Oahu accounts for 103.6% of the net Japan-hotel-luxury decline** (Maui offsets some of it).
- On Oahu hotel-luxury, Japan is -12.59% YoY (deepest of any origin); US_mainland is -9.77% (largest absolute).
- **Caveat:** The Japan-luxury drop being Oahu-specific might reflect hotel-product fit (Oahu's Waikiki luxury stock) or Japan travel patterns to specific properties. This analysis cannot distinguish the mechanism from the data alone.
- **Confidence: High** (finding itself is airtight; the mechanism is where uncertainty lives, flagged in the caveats).

### F7 - US_mainland substitution (Maui vs Oahu)
- Oahu US_mainland delta = -157,463; Maui US_mainland delta = +50,688; Maui gain as share of Oahu loss = 32%.
- Monthly shape: In Q3/Q4 2025, Maui gained and Oahu lost on the same months (not opposite months), which is consistent with substitution.
- **BUT:** This analysis shows association, not causation. Travelers might be choosing Maui over Oahu; they might also be new Maui travelers while separate Oahu travelers are declining. We cannot distinguish these without individual-trip data.
- **Confidence: Medium.** The pattern is real; the "why" is inferred.

### F8 - Top-10 cells = 77.7% of Oahu decline
- Ranked all 45 (accommodation x tier x origin) cells on Oahu by abs_delta.
- Top-5 cells sum to -148,763 (62.03% of Oahu decline).
- Top-10 cells sum to -186,428 (77.73% of Oahu decline).
- **Independent check:** Top-5 + bottom-40 = -239,833 = Oahu total (parts sum to whole).
- Interpretation: Oahu's problem is not "everything on Oahu is declining a little"; it's "a narrow set of segments is declining a lot." This makes the problem targetable.
- **Confidence: High.**

### F9 - Decline is level, not shape
- Seasonal peaks (June/July/August, December) remain the highest months on Oahu in both years.
- The H2 gap widens: -6.31% H2 vs -2.72% H1.
- The shape is preserved; demand is shifted *downward* by a structural amount, not redistributed across the calendar.
- **Confidence: High.**

## Bias checklist (worked through, not just read)

| Bias | Applicable? | Verdict |
|---|---|---|
| Survivorship | No entities dropped from the panel (4,320 rows = 2,160 cells x 2 years, fully balanced). | No issue. |
| Selection | All islands, accommodations, tiers, origins are present; no filter excluded. | No issue. |
| Lookahead | Compare two disjoint years (2024 full, 2025 full); no future info used. | No issue. |
| Composition shift | Oahu's share of total arrivals fell from 51.8% to 50.2% (-1.56 pp); Maui's rose from 22.3% to 23.5% (+1.21 pp). This IS a composition shift, and it's consistent with the underlying story - not a hidden driver. Weighted-average percentages are honest because we report both the within-island YoY and the absolute deltas. | No issue. |
| Metric drift | `visitor_arrivals` schema is consistent across the two years by inspection. | Caveat: we are measuring ARRIVALS, not spend or nights. Recovery in arrivals does not imply recovery in economic value. Flagged in final report caveats. |
| Base rate neglect | All percentages use matched-segment denominators. Re-derivations confirm. | No issue. |

## Caveats to carry into the final deliverable

1. **Metric scope.** We have visitor arrivals only. Spend, length of stay, occupancy, and average daily rate are not in the data - an arrivals dip can understate or overstate economic impact.
2. **Substitution is inferred, not proven.** F7 (Maui gaining while Oahu loses US_mainland travelers) is consistent with substitution but could also be independent growth on Maui with independent decline on Oahu.
3. **No external signal.** The dataset has no price, capacity, weather, event, or news data. A deep "why" requires joining this to external context (e.g., Oahu hotel closures, Japanese yen FX, Maui post-fire recovery messaging).
4. **Two years is a short panel.** Trend claims are directional. Whether the H2 Oahu decline persists into 2026 requires continued monitoring.
5. **Dataset is pre-processed / fully balanced.** Real raw data usually has gaps. We're trusting the data provider that 4,320 exact cells reflect complete measurement, not imputation.

## Recommendation rankability

All recommendations in the final report will carry High / Medium / Low confidence grades aligned to the underlying findings' grades. A Low-confidence recommendation that is also low-impact will be dropped; one that is low-confidence but high-impact will be flagged as "monitor / experiment" rather than "execute."
