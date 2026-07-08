"""Phase 5: Generate all charts for the storyboard."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

OUT = Path("/tmp/ai-analyst-iter2/eval-1-tourism-simpsons/with_skill/outputs")
CHARTS = OUT / "charts"
SCRIPTS = OUT / "chart_scripts"
CHARTS.mkdir(exist_ok=True)
SCRIPTS.mkdir(exist_ok=True)

df = pd.read_csv("/tmp/ai-analyst-iter2/inputs/tourism_monthly.csv")
df["month"] = pd.to_datetime(df["month"])
df["year"] = df["month"].dt.year
df["month_of_year"] = df["month"].dt.month

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.grid": False,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.dpi": 110,
})

GRAY = "#B0B0B0"
DARK_GRAY = "#555555"
EMPHASIS = "#C8102E"
POSITIVE = "#1F7A3F"

months = list(range(1, 13))
month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# ============================================================
# Chart 1: Total monthly arrivals 2024 vs 2025
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
monthly_total = df.groupby(["year", "month_of_year"])["visitor_arrivals"].sum().unstack("year")
ax.plot(months, monthly_total[2024]/1000, color=GRAY, linewidth=2.5, label="2024")
ax.plot(months, monthly_total[2025]/1000, color=DARK_GRAY, linewidth=2.5, label="2025")
ax.text(12.15, monthly_total.loc[12,2024]/1000, "2024", color=GRAY, fontsize=11, fontweight="bold", va="center")
ax.text(12.15, monthly_total.loc[12,2025]/1000, "2025", color=DARK_GRAY, fontsize=11, fontweight="bold", va="center")
ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.set_ylim(700, 1000)
ax.set_ylabel("Visitors (thousands)")
ax.set_title("Total Hawaii arrivals in 2025 are only 1.6% below 2024 - the aggregate looks like recovery", pad=16)
total_2024 = monthly_total[2024].sum() / 1e6
total_2025 = monthly_total[2025].sum() / 1e6
ax.text(0.02, 0.06, f"Full-year totals: 2024 = {total_2024:.2f}M   |   2025 = {total_2025:.2f}M   |   YoY = -1.6%",
        transform=ax.transAxes, fontsize=10, color=DARK_GRAY)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{int(x)}K"))
plt.tight_layout()
plt.savefig(CHARTS / "01_aggregate_recovery_illusion.png", bbox_inches="tight", dpi=150)
plt.close()
print("Saved 01")

# ============================================================
# Chart 2: Small multiples - per-island monthly trend, Oahu emphasized
# ============================================================
fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
islands = ["Oahu", "Maui", "Hawaii", "Kauai"]
colors = {"Oahu": EMPHASIS, "Maui": POSITIVE, "Hawaii": GRAY, "Kauai": GRAY}
yoys = {}
for island in islands:
    sub = df[df["island"]==island]
    pv = sub.groupby(["year","month_of_year"])["visitor_arrivals"].sum().unstack("year")
    yoys[island] = (pv[2025].sum()/pv[2024].sum()-1)*100

for i, island in enumerate(islands):
    ax = axes[i//2][i%2]
    sub = df[df["island"]==island]
    pv = sub.groupby(["year","month_of_year"])["visitor_arrivals"].sum().unstack("year")
    c = colors[island]
    ax.plot(months, pv[2024]/1000, color=GRAY, linewidth=2.0, label="2024")
    ax.plot(months, pv[2025]/1000, color=c, linewidth=2.5, label="2025")
    ax.text(12.2, pv.loc[12,2024]/1000, "'24", color=GRAY, fontsize=9, va="center")
    ax.text(12.2, pv.loc[12,2025]/1000, "'25", color=c, fontsize=9, va="center", fontweight="bold")
    sign = "+" if yoys[island] >= 0 else ""
    badge_color = POSITIVE if yoys[island] > 0.5 else EMPHASIS if yoys[island] < -1 else DARK_GRAY
    ax.text(0.98, 0.92, f"{sign}{yoys[island]:.1f}% YoY",
            transform=ax.transAxes, fontsize=12, fontweight="bold", color=badge_color, ha="right")
    ax.set_title(island, fontsize=13, pad=8, loc="left", color=c if island in ["Oahu","Maui"] else DARK_GRAY)
    ax.set_xticks(months)
    ax.set_xticklabels(month_labels, fontsize=8)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{int(x)}K"))
    if i%2==0:
        ax.set_ylabel("Visitors")

fig.suptitle("Oahu is the only island losing ground: -4.6% YoY while Maui gains +3.8%",
             fontsize=15, fontweight="bold", x=0.04, ha="left", y=0.99)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig(CHARTS / "02_island_divergence.png", bbox_inches="tight", dpi=150)
plt.close()
print("Saved 02")

# ============================================================
# Chart 3: Oahu monthly YoY % - deterioration through 2025
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5))
oahu = df[df["island"]=="Oahu"]
oahu_m = oahu.groupby(["year","month_of_year"])["visitor_arrivals"].sum().unstack("year")
oahu_m["yoy_pct"] = (oahu_m[2025]/oahu_m[2024] - 1)*100
bar_colors = []
for v in oahu_m["yoy_pct"]:
    if v > -3:
        bar_colors.append("#E89C9C")
    elif v > -6:
        bar_colors.append("#CE4A4A")
    else:
        bar_colors.append(EMPHASIS)
bars = ax.bar(months, oahu_m["yoy_pct"], color=bar_colors, edgecolor="white", linewidth=1)
for bar, val in zip(bars, oahu_m["yoy_pct"]):
    ax.text(bar.get_x()+bar.get_width()/2, val-0.3, f"{val:.1f}%",
            ha="center", va="top", fontsize=9, color="white", fontweight="bold")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(months)
ax.set_xticklabels(month_labels)
ax.set_ylim(-11, 1)
ax.set_ylabel("YoY change (%)")
ax.set_title("Oahu's decline is accelerating: -2% in Q1 widened to -9% in October 2025", pad=16)
ax.annotate("Worst month:\nOct 2025 at -9.4%", xy=(10, -9.43), xytext=(8.3, -10.5),
            fontsize=10, ha="center", color=EMPHASIS, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=EMPHASIS, lw=1.2))
ax.text(0.02, 0.07, "H1 2025 YoY: -2.7%       H2 2025 YoY: -6.3%",
        transform=ax.transAxes, fontsize=11, color=DARK_GRAY, fontweight="bold")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
plt.tight_layout()
plt.savefig(CHARTS / "03_oahu_deterioration.png", bbox_inches="tight", dpi=150)
plt.close()
print("Saved 03")

# ============================================================
# Chart 4: Oahu YoY delta by accommodation x tier (stacked)
# ============================================================
fig, ax = plt.subplots(figsize=(11, 5.5))
oahu_cells = oahu.groupby(["year","accommodation_type","tier"])["visitor_arrivals"].sum().unstack("year")
oahu_cells["abs_delta"] = oahu_cells[2025] - oahu_cells[2024]
table = oahu_cells["abs_delta"].unstack("tier")
acc_order = table.sum(axis=1).sort_values().index.tolist()
table = table.loc[acc_order]
colors_map = {"luxury": EMPHASIS, "mid_market": "#E06060", "budget": "#F1B0B0"}
left = [0, 0, 0]
tier_order = ["luxury","mid_market","budget"]
y_positions = np.arange(len(acc_order))
for tier in tier_order:
    vals = table[tier].values / 1000
    ax.barh(y_positions, vals, left=left, color=colors_map[tier], label=tier.replace("_"," "),
            edgecolor="white", linewidth=1.2)
    for i, v in enumerate(vals):
        if acc_order[i] == "hotel" and abs(v) > 8:
            ax.text(left[i] + v/2, y_positions[i], f"{int(v):+d}K", ha="center", va="center",
                    fontsize=10, color="white", fontweight="bold")
    left = [l+v for l,v in zip(left, vals)]
row_totals = table.sum(axis=1).values / 1000
for i, t in enumerate(row_totals):
    ax.text(t - 4, y_positions[i], f"  total {int(t):+d}K", va="center", ha="right",
            fontsize=10, color=DARK_GRAY, fontweight="bold")
ax.set_yticks(y_positions)
ax.set_yticklabels([a.replace("_"," ") for a in acc_order], fontsize=11)
ax.invert_yaxis()
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("YoY change in Oahu arrivals (thousands)")
ax.set_title("Two-thirds of Oahu's loss is in hotels - especially luxury and mid-market", pad=16)
ax.legend(title="Tier", frameon=False, loc="lower left", bbox_to_anchor=(0, 0))
ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x,_: f"{int(x):+d}K"))
plt.tight_layout()
plt.savefig(CHARTS / "04_oahu_hotel_concentration.png", bbox_inches="tight", dpi=150)
plt.close()
print("Saved 04")

# ============================================================
# Chart 5: Oahu hotel-luxury YoY delta by origin market (bar)
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
ohl = df[(df["island"]=="Oahu") & (df["accommodation_type"]=="hotel") & (df["tier"]=="luxury")]
ohl_origin = ohl.groupby(["year","origin_market"])["visitor_arrivals"].sum().unstack("year")
ohl_origin["abs_delta"] = ohl_origin[2025] - ohl_origin[2024]
ohl_origin["pct_delta"] = (ohl_origin[2025]/ohl_origin[2024] - 1)*100
ohl_origin = ohl_origin.sort_values("abs_delta")
y_positions = np.arange(len(ohl_origin))
colors_bar = []
for idx in ohl_origin.index:
    if idx == "US_mainland":
        colors_bar.append(EMPHASIS)
    elif idx == "Japan":
        colors_bar.append("#E06060")
    else:
        colors_bar.append(GRAY)
bars = ax.barh(y_positions, ohl_origin["abs_delta"]/1000, color=colors_bar, edgecolor="white", linewidth=1)
for bar, abs_v, pct_v in zip(bars, ohl_origin["abs_delta"]/1000, ohl_origin["pct_delta"]):
    ax.text(bar.get_width() - 0.8, bar.get_y()+bar.get_height()/2,
            f"{int(abs_v):+d}K  ({pct_v:+.1f}%)",
            va="center", ha="right", fontsize=10,
            color="white" if bar.get_width() < -5 else DARK_GRAY, fontweight="bold")
labels = [idx.replace("_"," ") for idx in ohl_origin.index]
ax.set_yticks(y_positions)
ax.set_yticklabels(labels, fontsize=11)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("YoY change in Oahu hotel-luxury arrivals (thousands)")
ax.set_title("Mainland is the volume loss (-43K); Japan is the acute loss (-12.6%)", pad=16)
plt.tight_layout()
plt.savefig(CHARTS / "05_oahu_hotel_luxury_by_origin.png", bbox_inches="tight", dpi=150)
plt.close()
print("Saved 05")

# ============================================================
# Chart 6: US_mainland YoY by island
# ============================================================
fig, ax = plt.subplots(figsize=(10, 5))
us = df[df["origin_market"]=="US_mainland"]
us_yoy = us.groupby(["year","island"])["visitor_arrivals"].sum().unstack("year")
us_yoy["abs_delta"] = us_yoy[2025] - us_yoy[2024]
us_yoy = us_yoy.sort_values("abs_delta")
bar_colors = []
for idx in us_yoy.index:
    if idx == "Maui":
        bar_colors.append(POSITIVE)
    elif idx == "Oahu":
        bar_colors.append(EMPHASIS)
    else:
        bar_colors.append(GRAY)
y_positions = np.arange(len(us_yoy))
bars = ax.barh(y_positions, us_yoy["abs_delta"]/1000, color=bar_colors, edgecolor="white", linewidth=1)
for bar, v in zip(bars, us_yoy["abs_delta"]/1000):
    ha_align = "right" if v < 0 else "left"
    off = -1.5 if v < 0 else 1.5
    xpos = bar.get_width() + off
    ax.text(xpos, bar.get_y()+bar.get_height()/2, f"{int(v):+d}K",
            va="center", ha=ha_align, fontsize=11, fontweight="bold",
            color="white" if abs(v) > 30 else DARK_GRAY)
ax.set_yticks(y_positions)
ax.set_yticklabels(us_yoy.index, fontsize=11)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("YoY change in US-mainland arrivals (thousands)")
ax.set_title("Maui gained 51K mainland visitors - only a third of Oahu's 157K mainland loss", pad=16)
ax.text(0.02, 0.05, "Substitution is partial, not offsetting. Net US-mainland change: -114K.",
        transform=ax.transAxes, fontsize=10, color=DARK_GRAY, style="italic")
plt.tight_layout()
plt.savefig(CHARTS / "06_mainland_substitution.png", bbox_inches="tight", dpi=150)
plt.close()
print("Saved 06")

# ============================================================
# Chart 7: Pareto - top Oahu declining cells
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6.5))
oahu_cells = oahu.groupby(["year","accommodation_type","tier","origin_market"])["visitor_arrivals"].sum().unstack("year")
oahu_cells["abs_delta"] = oahu_cells[2025] - oahu_cells[2024]
top10 = oahu_cells.sort_values("abs_delta").head(10).copy()
oahu_total = oahu_cells["abs_delta"].sum()
cell_labels = [f"{a} / {t} / {o}".replace("_"," ") for (a,t,o) in top10.index]
top10["cum_share"] = top10["abs_delta"].cumsum() / oahu_total * 100

x = np.arange(len(top10))
bar_colors = [EMPHASIS if i < 5 else "#E06060" for i in range(len(top10))]
bars = ax.bar(x, top10["abs_delta"]/1000, color=bar_colors, edgecolor="white")
for bar, v in zip(bars, top10["abs_delta"]/1000):
    ax.text(bar.get_x()+bar.get_width()/2, v-0.8, f"{int(v):+d}K",
            ha="center", va="top", fontsize=9, color="white", fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(cell_labels, rotation=35, ha="right", fontsize=9)
ax.set_ylabel("YoY abs. change in arrivals (thousands)")
ax.set_ylim(-65, 8)

for i, (cs, bar) in enumerate(zip(top10["cum_share"], bars)):
    ax.text(bar.get_x()+bar.get_width()/2, 4.5, f"{cs:.0f}%",
            ha="center", va="bottom", fontsize=9, color=DARK_GRAY, fontweight="bold")
ax.text(-0.6, 4.5, "cumulative\n% of Oahu\ndecline:", ha="right", va="center", fontsize=8, color=DARK_GRAY)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_title("Top-10 segments explain 78% of Oahu's decline - the problem is concentrated, not diffuse", pad=16)
plt.tight_layout()
plt.savefig(CHARTS / "07_oahu_pareto.png", bbox_inches="tight", dpi=150)
plt.close()
print("Saved 07")

print("\nAll charts rendered. Files:")
for f in sorted(CHARTS.glob("*.png")):
    print(" ", f.name)
