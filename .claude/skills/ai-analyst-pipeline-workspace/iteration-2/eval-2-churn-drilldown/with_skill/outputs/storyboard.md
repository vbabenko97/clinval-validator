# Phase 4 — Storyboard

## Headline (single sentence)

**The Q2-2026 churn spike is not broad — two segments (Pro-Retail and Pro-Manufacturing) drove 64% of the new churn, and a targeted 90-day intervention there can save roughly $0.5M ARR over the next year.**

## Audience

Board of Directors (non-technical). Looking for: *what's broken, how big, what we should do*. 15 slides or fewer, action titles, clear ask.

## Narrative arc (Context → Tension → Resolution)

Target: 20% Context, 30% Tension, 50% Resolution.

| # | Section | Beat (action-title form) | Purpose | Findings | Visualization |
|---|---------|--------------------------|---------|----------|---------------|
| 1 | Title | "Q2-2026 churn doubled — here's what drove it and what we do next" | Anchor, ≤10 sec read | — | Title slide |
| 2 | Title | "Headline, Evidence, Ask" | Pre-brief the board on structure | — | Three-column exec summary |
| 3 | Context | "We've lost 268 customers and $2.2M in ARR since 2025 — the rate was drifting, but Q2 broke trend" | Set baseline | F1 | Line: quarterly churn count |
| 4 | Tension | "Q2-2026 churn rate nearly doubled (3.5% → 6.9%) — a real step, not drift" | Make the spike undeniable | F1 | Bar: quarterly churn rate, Q2-26 highlighted |
| 5 | Tension | "The spike isn't the low-end — Pro-tier customers left 2x faster than Starter or Enterprise" | Overturn intuitive assumption | F2 | Bar: Q2-26 rate by tier |
| 6 | Tension | "Inside Pro, two industries break the pattern: Retail at 22% and Manufacturing at 14%" | Zero in | F3 | Heatmap: tier × industry Q2-26 |
| 7 | Tension | "Pro-Retail didn't drift — it stepped from 1% to 22% in one quarter" | Show structural break | F6 | Line: Pro-Retail quarterly rate |
| 8 | Tension | "Two segments account for 64% of the churn jump and 50% of the ARR walked" | Quantify concentration | F4 | Waterfall: Q1→Q2 churn decomposition |
| 9 | Resolution | "This is not a renewal-cliff story — all three signup cohorts churned at similar rates inside Pro-Retail" | Rule out the easy explanation, frame mechanism question | F5 | Small multiples: Pro-Retail by cohort |
| 10 | Resolution | "We don't yet know the *why* — the data names the *where*; we need GTM and product to identify the trigger" | Honest caveat; frame the ask | F5, caveat | Callout slide |
| 11 | Resolution | "If Q2 rates persist through 2027, Pro-Retail+Mfg alone cost us $654K; if we revert to Q1 baseline, only $105K — the save is ~$549K" | Size the ask | F7 | Bar: two-scenario ARR projection |
| 12 | Resolution | "Three actions we recommend the board sanction today" | The ask | — | Recommendation table |
| 13 | Resolution | "Action 1 — Stand up a Pro-Retail save team this quarter" | Detail R1 | — | Text slide |
| 14 | Resolution | "Actions 2 & 3 — Root-cause the trigger; put Pro-Mfg on early-warning watch" | Detail R2/R3 | — | Text slide |
| 15 | Close | "Ask, owners, decision timeline" | Decision moment | — | Recommendation summary with confidence |

**Actual slide count: 15 (the cap the user requested). Drops candidates if we need to trim further: slides 7 and 9 could merge; slides 13-14 could compress into one.**

## Narrative coherence check

- **Beat 3** sets the context: we've been losing customers all year, this isn't new.
- **Beat 4** introduces the tension: Q2 broke the trend.
- **Beats 5-8** progressively narrow the focus: tier → industry → segment → time. Each earns its place by refuting a weaker explanation ("it's the cheap plan" → no; "it's everyone" → no; "it's drifting" → no).
- **Beat 9** preempts the obvious follow-up ("is it just cohorts renewing?") and answers no.
- **Beat 10** is the honest-analyst slide: the data says where, not why. This is the setup for the ask.
- **Beats 11-15** convert the diagnosis into a decision.

The arc holds: removing any single beat breaks the argument, and every slide transitions naturally.

## Recommendations (with owners, success metrics, confidence, follow-up)

| # | What | Who | Success metric | Confidence | Follow-up |
|---|------|-----|----------------|------------|-----------|
| R1 | Stand up a 90-day Pro-Retail save program: dedicated CSM, executive sponsor outreach to all 76 remaining Pro-Retail accounts, offer structured save conversation | VP Customer Success (owner), CRO (sponsor) | Pro-Retail Q3-26 churn rate ≤ 8% (halfway back to Q1-26 baseline of 1%) | **High** (direct, evidence-backed) | Week-4 check-in; Q3-26 board update |
| R2 | Root-cause the Q2 trigger within 2 weeks: run 15 customer interviews with Pro-Retail churners + 10 with at-risk actives; cross-ref with product release notes, pricing changes, and competitive moves in Q2 | Head of Product + Head of Sales (joint) | Written root-cause memo by 2026-05-02 naming the trigger with high confidence | **High** (the data is unambiguous about *where*, so interviews are targeted) | 2 weeks |
| R3 | Put Pro-Manufacturing on early-warning: weekly churn-rate and NPS watch, health-score review of all 67 remaining accounts; trigger a save play if Q3-26 rate exceeds 10% | VP Customer Success | Pro-Mfg Q3-26 rate ≤ 7% | **Medium** (Pro-Mfg spike less dramatic than Pro-Retail; trigger may or may not extend) | Monthly |

## Gate status

- [x] Single-sentence headline written
- [x] CTR arc laid out with 15 beats (user-requested cap)
- [x] Each beat maps to a validated finding or is a transition/decision slide
- [x] Coherence re-read performed
- [x] Recommendations have owners, metrics, confidence, follow-up
