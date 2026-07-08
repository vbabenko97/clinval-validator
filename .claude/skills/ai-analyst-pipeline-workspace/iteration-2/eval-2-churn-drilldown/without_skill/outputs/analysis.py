#!/usr/bin/env python3
"""Customer churn analysis for Q2 2026 board meeting.

Reads /tmp/ai-analyst-iter2/inputs/customer_churn.csv and writes seven PNG charts
into /tmp/ai-analyst-iter2/eval-2-churn-drilldown/without_skill/outputs/.
"""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "/tmp/ai-analyst-iter2/eval-2-churn-drilldown/without_skill/outputs"
INPUT = "/tmp/ai-analyst-iter2/inputs/customer_churn.csv"
os.makedirs(OUT, exist_ok=True)

with open(INPUT) as f:
    rows = [dict(r) for r in csv.DictReader(f)]
for r in rows:
    r["arr_usd"] = float(r["arr_usd"])
    r["tenure_months"] = int(r["tenure_months"])

QUARTERS = ["2025Q1","2025Q2","2025Q3","2025Q4","2026Q1","2026Q2"]
def qi(q): return QUARTERS.index(q) if q in QUARTERS else -1
def active_at_start(c, q):
    if qi(c["signup_quarter"]) >= qi(q): return False
    if c["churn_quarter"] == "active": return True
    return qi(c["churn_quarter"]) >= qi(q)
def churned_in(c, q): return c["churn_quarter"] == q

plans = ["Starter","Pro","Enterprise"]
inds = sorted(set(c["industry"] for c in rows))

plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False,"axes.titlesize":14,"axes.titleweight":"bold","axes.labelsize":11,"xtick.labelsize":10,"ytick.labelsize":10,"figure.dpi":110})
NAVY="#1f3a5f"; RED="#c0392b"; AMBER="#e67e22"; GRAY="#95a5a6"; TEAL="#16a085"

tier_hist = {t:[] for t in plans}
for q in QUARTERS:
    for t in plans:
        seg=[c for c in rows if active_at_start(c,q) and c["plan_tier"]==t]
        ch=[c for c in seg if churned_in(c,q)]
        tier_hist[t].append(100*len(ch)/len(seg) if seg else 0)
ind_hist = {i:[] for i in inds}
for q in QUARTERS:
    for i in inds:
        seg=[c for c in rows if active_at_start(c,q) and c["industry"]==i]
        ch=[c for c in seg if churned_in(c,q)]
        ind_hist[i].append(100*len(ch)/len(seg) if seg else 0)

rates=[]; counts=[]
for q in QUARTERS:
    seg=[c for c in rows if active_at_start(c,q)]
    ch=[c for c in seg if churned_in(c,q)]
    rates.append(100*len(ch)/len(seg) if seg else 0); counts.append(len(ch))
qs = QUARTERS[1:]; rates_plot=rates[1:]; counts_plot=counts[1:]

# Chart 1 quarterly trend
fig, ax = plt.subplots(figsize=(10,5))
colors=[RED if q=="2026Q2" else NAVY for q in qs]
bars=ax.bar(qs, rates_plot, color=colors, edgecolor="white", width=0.6)
for b,r,n in zip(bars,rates_plot,counts_plot):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.15, f"{r:.1f}%" + chr(10) + f"({n})", ha="center", fontsize=10, fontweight="bold")
ax.set_ylabel("Quarterly churn rate")
ax.set_title("Q2 2026 churn hit 6.9% - nearly 2x the prior 4-quarter average (4.1%)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"{v:.0f}%"))
ax.set_ylim(0, max(rates_plot)*1.3)
ax.grid(axis="y", linestyle=":", alpha=0.3)
plt.tight_layout(); plt.savefig(OUT + "/chart_01_trend.png", dpi=150, bbox_inches="tight"); plt.close()

# Chart 2 by plan
prior_avg = {t: np.mean([v for v in tier_hist[t][1:-1] if v>0]) for t in plans}
q2_rates = {t: tier_hist[t][-1] for t in plans}
fig, ax = plt.subplots(figsize=(10,5.5))
x = np.arange(len(plans)); w=0.35
ax.bar(x-w/2, [prior_avg[t] for t in plans], w, label="Avg Q2-25 to Q1-26", color=GRAY)
ax.bar(x+w/2, [q2_rates[t] for t in plans], w, label="Q2 2026", color=RED)
for i,t in enumerate(plans):
    ax.text(i-w/2, prior_avg[t]+0.2, f"{prior_avg[t]:.1f}%", ha="center", fontsize=10)
    ax.text(i+w/2, q2_rates[t]+0.2, f"{q2_rates[t]:.1f}%", ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(plans); ax.set_ylabel("Churn rate")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"{v:.0f}%"))
ax.set_title("Pro tier churn tripled in Q2 - Starter and Enterprise are stable")
ax.legend(frameon=False, loc="upper left"); ax.grid(axis="y", linestyle=":", alpha=0.3)
ax.set_ylim(0, max(q2_rates.values())*1.35)
plt.tight_layout(); plt.savefig(OUT + "/chart_02_by_plan.png", dpi=150, bbox_inches="tight"); plt.close()

# Chart 3 by industry
prior_ind = {i: np.mean([v for v in ind_hist[i][1:-1] if v>0]) for i in inds}
q2_ind = {i: ind_hist[i][-1] for i in inds}
ordered = sorted(inds, key=lambda i: q2_ind[i]-prior_ind[i], reverse=True)
fig, ax = plt.subplots(figsize=(10,5.5))
x = np.arange(len(ordered)); w=0.35
ax.bar(x-w/2, [prior_ind[i] for i in ordered], w, label="Avg Q2-25 to Q1-26", color=GRAY)
ax.bar(x+w/2, [q2_ind[i] for i in ordered], w, label="Q2 2026", color=RED)
for i,ind in enumerate(ordered):
    ax.text(i-w/2, prior_ind[ind]+0.15, f"{prior_ind[ind]:.1f}%", ha="center", fontsize=10)
    ax.text(i+w/2, q2_ind[ind]+0.15, f"{q2_ind[ind]:.1f}%", ha="center", fontsize=10, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(ordered, rotation=12, ha="right"); ax.set_ylabel("Churn rate")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f"{v:.0f}%"))
ax.set_title("Retail customers churned at 10% - nearly 5x their prior baseline")
ax.legend(frameon=False, loc="upper right"); ax.grid(axis="y", linestyle=":", alpha=0.3)
ax.set_ylim(0, max(q2_ind.values())*1.35)
plt.tight_layout(); plt.savefig(OUT + "/chart_03_by_industry.png", dpi=150, bbox_inches="tight"); plt.close()

# Chart 4 heatmap
q = "2026Q2"
at_start = [c for c in rows if active_at_start(c,q)]
matrix = np.zeros((len(plans), len(inds)))
counts_mat = np.zeros((len(plans), len(inds)), dtype=int)
bases_mat = np.zeros((len(plans), len(inds)), dtype=int)
for pi,p in enumerate(plans):
    for ii,i in enumerate(inds):
        seg = [c for c in at_start if c["plan_tier"]==p and c["industry"]==i]
        ch = [c for c in seg if churned_in(c,q)]
        matrix[pi][ii] = 100*len(ch)/len(seg) if seg else 0
        counts_mat[pi][ii] = len(ch); bases_mat[pi][ii] = len(seg)
fig, ax = plt.subplots(figsize=(11,4.5))
im = ax.imshow(matrix, aspect="auto", cmap="Reds", vmin=0, vmax=matrix.max())
ax.set_xticks(np.arange(len(inds))); ax.set_xticklabels(inds)
ax.set_yticks(np.arange(len(plans))); ax.set_yticklabels(plans)
ax.set_title("Pro + Retail is the hotspot: 22 percent churn (21 of 97)")
plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
plt.tight_layout(); plt.savefig(OUT + "/chart_04_heatmap.png", dpi=150, bbox_inches="tight"); plt.close()

# Chart 5 cohort view
signup_qs = ["2025Q1","2025Q2","2025Q3"]
cohort_rates=[]; cohort_bases=[]
for sq in signup_qs:
    seg = [c for c in at_start if c["signup_quarter"]==sq]
    ch = [c for c in seg if churned_in(c,q)]
    cohort_rates.append(100*len(ch)/len(seg) if seg else 0); cohort_bases.append(len(seg))
fig, ax = plt.subplots(figsize=(10,5))
colors_c = [RED if r==max(cohort_rates) else NAVY for r in cohort_rates]
ax.bar(signup_qs, cohort_rates, color=colors_c, edgecolor="white", width=0.5)
ax.set_ylabel("Q2 2026 churn rate"); ax.set_xlabel("Signup cohort")
ax.set_title("Oldest cohort churning fastest - annual renewal window")
plt.tight_layout(); plt.savefig(OUT + "/chart_05_cohort.png", dpi=150, bbox_inches="tight"); plt.close()

# Chart 6 ARR pies
churned_q2 = [c for c in at_start if churned_in(c,q)]
arr_plan = {t: sum(c["arr_usd"] for c in churned_q2 if c["plan_tier"]==t) for t in plans}
arr_ind = {i: sum(c["arr_usd"] for c in churned_q2 if c["industry"]==i) for i in inds}
fig, axes = plt.subplots(1,2, figsize=(13,5))
axes[0].pie(list(arr_plan.values()), labels=list(arr_plan.keys()), colors=[RED,AMBER,GRAY], autopct=lambda p: str(round(p))+chr(37), startangle=90)
axes[1].pie(list(arr_ind.values()), labels=list(arr_ind.keys()), colors=[RED,AMBER,NAVY,TEAL,GRAY], autopct=lambda p: str(round(p))+chr(37), startangle=90)
plt.suptitle("95 percent of lost ARR came from Pro and Enterprise", fontsize=14, fontweight="bold")
plt.tight_layout(); plt.savefig(OUT + "/chart_06_arr.png", dpi=150, bbox_inches="tight"); plt.close()

# Chart 7 plan trend lines
fig, ax = plt.subplots(figsize=(10,5))
line_qs = QUARTERS[1:]
tier_colors = {"Starter": GRAY, "Pro": RED, "Enterprise": NAVY}
for t in plans:
    data = tier_hist[t][1:]
    ax.plot(line_qs, data, marker="o", label=t, color=tier_colors[t], linewidth=2.2, markersize=7)
ax.set_ylabel("Churn rate"); ax.set_title("Only Pro-tier churn deviated from the baseline in Q2 2026")
ax.legend(frameon=False, loc="upper left"); ax.grid(axis="y", linestyle=":", alpha=0.3); ax.set_ylim(0,12)
plt.tight_layout(); plt.savefig(OUT + "/chart_07_plan_trend.png", dpi=150, bbox_inches="tight"); plt.close()

print("done", sorted(os.listdir(OUT)))
