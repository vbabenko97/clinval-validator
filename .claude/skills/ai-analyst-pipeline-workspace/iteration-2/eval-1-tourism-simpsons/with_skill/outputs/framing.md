# Phase 1 - Framing

## Structured analytical question

**Primary question:** Is the tourism authority's "recovery is complete" claim supported by the 2024-2025 monthly visitor-arrivals data when we look below the aggregate - and if not, which islands, accommodation types, tiers, or origin markets explain the tension between the director's view and the regional offices' complaints?

**Specific metric:** Monthly visitor arrivals (count of visitors), aggregated from the 4,320-row `tourism_monthly.csv` file which covers every combination of month x island x accommodation type x tier x origin market.

**Time scope:** January 2024 through December 2025, compared YoY (2025 vs 2024 - 12 full months each).

**Population scope:** All four Hawaiian islands (Hawaii/Big Island, Kauai, Maui, Oahu), three accommodation types (hotel, timeshare, vacation_rental), three tiers (budget, mid_market, luxury), and five origin markets (US_mainland, Japan, Canada, Europe, Other).

**Comparison baseline:** 2024 arrivals by segment (YoY). "Recovery is done" implies 2025 ~ 2024 in aggregate - which as the first-pass numbers show is approximately true at the total level (-1.6% YoY) but may mask meaningful divergence below.

## Decision context

The director of the tourism authority is using aggregate numbers to conclude that recovery is complete and no intervention is needed. Regional offices are pushing back. The output needs to (a) tell the director what is actually happening, (b) give them language to respond to regional concerns, and (c) recommend different actions per island so regional allocation of marketing/development dollars and attention can be rebalanced.

The audience is an executive who "knows the business but doesn't look at data much" - so the output must be a markdown report in plain language, with charts that stand on their own via action-oriented titles. Methodology goes in an appendix.

## Success criteria

- **Answered:** Every headline claim in the report is backed by a validated number that has been re-derived a second way, with Simpson's Paradox explicitly checked. The report names which islands are recovering, which are still struggling, and what is driving each pattern down to an actionable sub-segment.
- **Done:** A markdown `report.md` file with 5-8 embedded PNG charts, an executive summary, a findings section, a ranked recommendations table with owners and confidence grades, and an appendix covering methodology, validation, and caveats.

## Hypotheses (to test in Phase 2)

| # | Hypothesis | Cause category | Prediction if true | Refutes if |
|---|---|---|---|---|
| H1 | The "recovery is done" story is a Simpson's Paradox - aggregate is flat but islands diverge materially | Composition shift | Within-island YoY ranges from clearly negative to clearly positive | All islands YoY within +-1% |
| H2 | Oahu is the drag; the other three islands are recovering or holding | External drivers + composition | Oahu YoY materially negative while Maui/Kauai/Hawaii are flat-or-positive | All islands moving in the same direction |
| H3 | Within the declining island(s), the decline concentrates in a specific accommodation x tier x market cell (not broadly distributed) | Operational / segmented demand | A small number of sub-cells accounts for most of the YoY loss | Decline is broadly distributed proportional to segment size |
| H4 | Origin market mix is shifting - a specific source market (e.g., Japanese inbound) is the primary lever and is not distributed evenly across islands | External drivers | One origin market shows a large, disproportionate YoY change; the effect is stronger on some islands than others | All markets move roughly in proportion |
| H5 | The seasonal shape is intact (peak months are still peak) - the decline is level, not shape - meaning it is a structural demand issue rather than a one-off event | Trend characterization | June/July/August/December 2025 peaks are similar-shaped to 2024 peaks but shifted downward in the declining segment | Summer or holiday peaks are materially redistributed |

## Data inventory

| Asset | Details |
|---|---|
| File | `/tmp/ai-analyst-iter2/inputs/tourism_monthly.csv` |
| Rows | 4,320 (fully balanced: 24 months x 4 islands x 3 accommodation x 3 tier x 5 markets) |
| Null values | None in any column |
| Metric | `visitor_arrivals` (integer count) |
| Dimensions | `month` (2024-01 through 2025-12), `island` (4), `accommodation_type` (3), `tier` (3), `origin_market` (5) |
| Quality flags | None detected at profile stage. Dataset is clean and fully balanced - unusual in real life but convenient for analysis. Worth noting in caveats that this is pre-processed, not raw. |

## What I'm carrying into Phase 2

- Confirm H1 (Simpson's Paradox on the aggregate) - already strongly suggested by first-pass numbers (total -1.6% YoY but Maui +3.8%, Oahu -4.6%).
- Drill into Oahu to test H3 (segmented decline) and H4 (origin-market lever).
- Cross-check seasonal shape (H5) to distinguish a level shift from a timing change.
- Size the opportunity: what is Oahu's YoY shortfall in absolute visitors, and where in the mix could intervention recover the gap?
