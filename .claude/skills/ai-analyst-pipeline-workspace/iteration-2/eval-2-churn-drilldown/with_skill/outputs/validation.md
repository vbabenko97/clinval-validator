# Phase 3 — Validation

Every finding in `findings.json` was re-derived by an independent method. Full checklist below.

## Re-derivation summary

| ID | Claim (abridged) | Primary method | Independent re-derivation | Match? |
|----|------------------|----------------|---------------------------|--------|
| F1 | Q2-26 churn events = 92, rate = 6.95% | `groupby(churn_quarter).count()` with ad-hoc at-risk logic | `pivot_table` + set-membership filter on `signup_quarter ∈ Q_ORDER[:i+1]` | Exact match (92 events, 1,324 at-risk, 6.95%) |
| F2 | Pro tier Q2-26 rate 10.58% | `groupby(plan_tier)` on at-risk frame | Verified via masked numpy sum (`at_risk_flag & tier_mask`) | Match (49/463 = 10.58%) |
| F3 | Pro-Retail Q2-26 rate 21.65% | 2-way groupby | `np.where` mask on `(plan_tier=="Pro") & (industry=="Retail")` | Match (21/97 = 21.65%) |
| F4 | Pro-Retail+Mfg = 64% of Q1→Q2 count jump | Delta arithmetic | Recounted by subtracting Q1-26 and Q2-26 churner counts directly | Match (+28 of +44) |
| F5 | Pro-Retail Q2-26 spike present in all three cohorts | 3-way groupby | Masked mean by signup_quarter, separately | Match (Q1=18.4%, Q2=20.7%, Q3=26.7%) |
| F6 | Pro-Retail 1.0% → 21.6% QoQ step | Per-quarter at-risk loop | Verified by counting Q1-26 Pro-Retail churners directly (1 of 98) and Q2-26 (21 of 97) | Match |
| F7 | ARR savings opportunity $549K over 4Q | Geometric decay model | Re-computed with closed-form `n0 · (1-r)^4 · $8,400 ARR` | Match (persist $653.6K, revert $104.5K) |
| F8 | Starter Q2-26 rate 5.34% | 2-way groupby | Re-counted 35 Starter churners / 655 at-risk | Match |

## Simpson's Paradox check (mandatory)

**Aggregate claim:** "Q2-26 churn rate is up vs. Q1-26 (3.5% → 6.9%)."

**Decomposition:** All 15 `plan_tier × industry` cells compared Q1-26 vs Q2-26 rates.

- **14 of 15 cells** moved *up* (same direction as the aggregate).
- **1 cell moved down:** Pro-Healthcare (4.5% → 3.8%, delta -0.7pp). The movement is small and the cell is small (110 customers Q1, 105 Q2), so this does not flip the headline.
- **No sign flip.** The aggregate direction is honestly representative.

**Decomposition detail (top movers):**

| Segment | Q1-26 rate | Q2-26 rate | Delta (pp) |
|---|---|---|---|
| Pro-Retail | 1.0% | 21.6% | +20.6 |
| Pro-Manufacturing | 3.7% | 14.1% | +10.4 |
| Enterprise-Healthcare | 0.0% | 4.3% | +4.3 |
| Pro-Finance | 3.8% | 8.0% | +4.2 |
| Starter-Healthcare | 2.8% | 6.5% | +3.7 |
| Enterprise-Finance | 6.1% | 9.7% | +3.6 |

**Interpretation:** The Q2-26 spike is not a Simpson's paradox artifact. It is broad-based (+ in 14/15 cells) but *concentrated* in two cells (Pro-Retail + Pro-Manufacturing), which account for 64% of the *count* jump and 50% of the *ARR* jump.

## Bias checklist

| Bias | Status | Notes |
|------|--------|-------|
| Survivorship | ✓ Checked, not present | Churned customers (268 of 1,500) are retained with non-null `churn_quarter`. |
| Selection | ⚠ Present, bounded impact | Dataset covers only 2025Q1–Q3 signups (all customers ≤18 months tenure). We cannot say whether churn among legacy (>18mo) customers also spiked — that segment is not observable here. For the Q2-26 story this matters only if board assumes conclusions extend to the full customer base. Flag in appendix. |
| Lookahead | ✓ Not present | Churn is observational; no predictions or forward-looking aggregates used. |
| Composition drift | ✓ Checked, not present | Tier mix stable across cohorts (Starter 49-53%, Pro 34-35%, Ent 13-16%). Industry mix also stable (17-22% per industry). The Q2-26 spike is not caused by a shifting customer mix. |
| Metric drift | ✓ Not applicable | Single snapshot; same measurement convention across rows. |
| Base rate neglect | ✓ Addressed | All headline comparisons use exposure-adjusted rates (at-risk denominators), not raw counts. |
| Right-censoring | ✓ Addressed | Q2-26 is current (cut-off) quarter; all 92 churn events happened within it. Comparison is apples-to-apples with prior *completed* quarters. |

## Confidence grading

| ID | Claim | Confidence | Rationale |
|----|-------|------------|-----------|
| F1 | Aggregate Q2-26 spike doubled the rate | **High** | Effect is 2× noise; re-derived two ways; composition stable. |
| F2 | Pro-tier drives the spike | **High** | Effect 2× other tiers; sample size solid (463 at-risk). |
| F3 | Pro-Retail 21.6%, Pro-Mfg 14.1% | **High** | Cell sizes 97 and 78 give tight confidence; re-derivation matches. |
| F4 | Pro-Retail+Mfg = 64% of count jump | **High** | Simple arithmetic; audited end to end. |
| F5 | Spike is segment-specific, not cohort-specific | **High** | All 3 cohorts in Pro-Retail show 18-27% Q2-26; rules out renewal cliff. |
| F6 | Structural break within Q2-26 for Pro-Retail (1% → 21.6%) | **High** | 21× quarterly multiple is far beyond noise. |
| F7 | ARR savings opportunity ~$549K | **Medium** | Depends on assumption about whether Q2-26 rate is a one-time event or new baseline. Sensitivity reported as $105K–$654K. |
| F8 | Starter drift to 5.3% is meaningful but small-dollar | **Medium** | Sample large but effect smaller; could be noise or early-warning. |

**Not a single 'High' everywhere:** F7 and F8 downgraded because forward projection (F7) and small effect size (F8) have genuine uncertainty.

## Caveats carried to the deliverable

1. Data covers only 2025Q1–Q3 signups (≤18 months tenure). If legacy customers exist, their Q2-26 trajectory is unknown.
2. We have no reason (in the data) why Pro-Retail and Pro-Mfg spiked in Q2-26 specifically. Data identifies *where* the spike is, not *why*. The narrative must name this honestly and ask the board for operational/go-to-market context to attribute mechanism.
3. ARR savings estimate ($549K over 4 quarters) assumes Q2-26 is a new baseline vs. a one-time event. Report as a range.

## Gate status

- [x] Every finding has a validation section
- [x] Simpson's Paradox check performed on the aggregate (no sign flip)
- [x] Bias checklist worked through (not just read)
- [x] Each finding has a confidence grade (High/Medium — not all High)
- [x] Unresolved issues explicitly called out as caveats (the "why" mechanism is unnamed in data)
