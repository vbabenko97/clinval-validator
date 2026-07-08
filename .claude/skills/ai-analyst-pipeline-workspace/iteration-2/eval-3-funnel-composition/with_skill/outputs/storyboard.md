# Phase 4 -- Storyboard

## Headline (one sentence)

**Conversion is flat only on the surface: new-user conversion has climbed ~41% while returning-user conversion has dropped ~28%, and a shifting visit mix is masking both -- a textbook Simpson's Paradox that means "nothing to worry about" is the wrong read.**

## Arc: Context -> Tension -> Resolution

Target audience: growth team (analytically literate). Tone: direct, data-first, actionable. Length target: ~8 beats plus recommendations.

### Context (20%)

| # | Beat | Purpose | Findings | Visualization |
|---|---|---|---|---|
| 1 | The aggregate funnel really is flat | Establish the marketing claim is arithmetically correct -- do not strawman them | F1 | Line chart of monthly visit-to-conversion with slope annotation |

### Tension (30%)

| # | Beat | Purpose | Findings | Visualization |
|---|---|---|---|---|
| 2 | But when we split by user type, the story inverts | Reveal that the aggregate hides divergent subgroups | F2 + F3 | Dual line chart: new and returning v2c with opposite trends |
| 3 | The visit mix is shifting at the same time | Show the composition side of Simpsons Paradox | F7 | Stacked area of new vs returning visit share |
| 4 | Waterfall: mix shift added +1.2pp (would have been good news at Jan rates); rate shift and interaction subtracted 1.1pp (because returning rate collapsed). Net ~0pp. | Quantify the cancelling forces | F4 | Waterfall with three effect bars |

### Resolution (50%)

| # | Beat | Purpose | Findings | Visualization |
|---|---|---|---|---|
| 5 | The divergence holds in every channel -- this is systemic, not a channel issue | Rule out channel-specific explanations | F5 | Small multiples: per-channel new vs returning v2c |
| 6 | The entire movement is at visit-to-signup. Post-signup is stable. | Locate the mechanism in the upper funnel, not product | F6 | Funnel step comparison: v2s vs s2c per user type |
| 7 | Opportunity: the returning-user regression costs ~1,190 conversions/mo; new-user volume loss costs ~570 | Make it dollars-and-cents so the team acts | F8 | Stacked opportunity bar |
| 8 | Recommendations with owners | Convert analysis to decisions | all | Recommendation table |

## Narrative coherence check

- Does each beat earn its place? Yes:
  - 1 sets up the marketing claim we will refute.
  - 2 is the core reveal.
  - 3 shows the second half of the Simpsons Paradox mechanism.
  - 4 turns the qualitative "it is hiding something" into numbers.
  - 5 rules out "maybe it is one channel doing this."
  - 6 narrows the mechanism to acquisition/targeting (signup step), not onboarding or product.
  - 7 sizes the opportunity so the team can prioritize.
  - 8 makes the call.
- Transitions are tight. No orphan beats.
- Landing is actionable: three priority recommendations plus one data-integrity check.

## So what / call to action

The flat aggregate is not reassuring. It is the sum of a gain you want to protect (new-user quality) and a loss you need to stop (returning-user acquisition quality). Three priority actions plus one data check:

### Recommendations

| # | Action | Owner | Success metric | Confidence | Follow-up |
|---|---|---|---|---|---|
| R1 | **Audit returning-user acquisition quality.** Why are we bringing in more returning-user visits but getting a lower signup rate from them? Start with: (a) attribution -- is "returning" being over-counted due to tracking changes? (b) channel-level targeting -- are we retargeting users who already signed up in a prior cohort? (c) landing-page/offer mismatch for re-activation. | Lifecycle + Attribution eng | Returning v-to-s back to >=25% (baseline was 27%); or a proven reason the decline is structural | High | 2026-05-15 (30d) |
| R2 | **Protect and scale the new-user conversion gain.** Conversion rate for new users has materially improved (+41% relative) in every channel. Figure out what is working (new landing pages? targeting? creative?) and push more spend there. New-user visit volume has fallen 23% -- there is clear room to scale. | Paid growth + CRO | New-user monthly conversions >=2,000 (currently 1,906; Jan was 1,760 but at lower rate); new-user visit volume recovered to 30k+/mo | High | 2026-05-01 (15d) |
| R3 | **Stop reporting aggregate v2c as the top-line funnel KPI.** It hides divergent subgroup movement. Split the dashboard: one new-user KPI, one returning-user KPI. Optionally keep the aggregate as a footnote with a composition caveat. | Growth analytics | Updated dashboard within 2 weeks; growth review meeting structure updated | High | 2026-05-01 (15d) |
| R4 | **Validate the data-definition assumption.** Confirm with data eng that the "returning" definition did not shift (e.g., identity-graph change, cookie-lookback change) between Jan and Jun. If it did, that alone could explain F3 without any real business change. | Data eng | Written confirmation that definition is unchanged, or patched data with consistent definition | Medium (hedges R1/R3) | 2026-05-01 (15d) |

## Headline re-state (identical text across deliverables)

> **Conversion is flat only on the surface: new-user conversion has climbed ~41% while returning-user conversion has dropped ~28%, and a shifting visit mix is masking both -- a textbook Simpson's Paradox that means "nothing to worry about" is the wrong read.**

## Style notes for the charts

- Default color: gray. One emphasis color per chart, matching the argument of that chart.
  - Beat 1 (aggregate flat): gray line, annotation only.
  - Beats 2, 5 (subgroup divergence): **blue = new (good news), red = returning (problem)** consistent across the deck.
  - Beat 3 (mix shift): same blue/red; direct labels on the areas.
  - Beat 4 (waterfall): green for positive effects, red for negative; neutral totals.
  - Beat 6 (funnel step): the v2s step uses the emphasis colors; s2c is grayed.
  - Beat 7 (opportunity): gray base, red stack for returning recovery, blue stack for new volume.
- Action titles on every chart.
- Direct labels on 2-series line charts (no legend needed).
- All line charts: no gridlines, no top/right spines, annotated first/last points.
