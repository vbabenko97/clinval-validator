import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

INPUT = Path("/tmp/ai-analyst-iter2/inputs/tourism_monthly.csv")
OUT = Path("/tmp/ai-analyst-iter2/eval-1-tourism-simpsons/without_skill/outputs")
OUT.mkdir(parents=True, exist_ok=True)

rows = []
with INPUT.open() as f:
    reader = csv.DictReader(f)
    for r in reader:
        r["visitor_arrivals"] = int(r["visitor_arrivals"])
        rows.append(r)

months = sorted({r["month"] for r in rows})
islands = sorted({r["island"] for r in rows})
accoms = sorted({r["accommodation_type"] for r in rows})
tiers = sorted({r["tier"] for r in rows})
markets = sorted({r["origin_market"] for r in rows})

def sum_by(keys):
    agg = defaultdict(int)
    for r in rows:
        key = tuple(r[k] for k in keys)
        agg[key] += r["visitor_arrivals"]
    return agg

total_by_month = sum_by(["month"])
total_by_island_month = sum_by(["island", "month"])
total_by_tier_month = sum_by(["tier", "month"])
total_by_market_month = sum_by(["origin_market", "month"])

def year_of(m): return m[:4]

totals_2024 = sum(v for (m,), v in total_by_month.items() if year_of(m) == "2024")
totals_2025 = sum(v for (m,), v in total_by_month.items() if year_of(m) == "2025")
agg = (totals_2025/totals_2024 - 1) * 100

island_year = defaultdict(int)
for (isl, m), v in total_by_island_month.items():
    island_year[(isl, year_of(m))] += v

tier_year = defaultdict(int)
for (t, m), v in total_by_tier_month.items():
    tier_year[(t, year_of(m))] += v

market_year = defaultdict(int)
for (mk, m), v in total_by_market_month.items():
    market_year[(mk, year_of(m))] += v

isl_tier_year = defaultdict(int)
for r in rows:
    isl_tier_year[(r["island"], r["tier"], year_of(r["month"]))] += r["visitor_arrivals"]

isl_mkt_year = defaultdict(int)
for r in rows:
    isl_mkt_year[(r["island"], r["origin_market"], year_of(r["month"]))] += r["visitor_arrivals"]

month_list = months
idx = {m: i for i, m in enumerate(month_list)}
def monthly_series(key_fn):
    out = defaultdict(lambda: [0]*len(month_list))
    for r in rows:
        k = key_fn(r)
        out[k][idx[r["month"]]] += r["visitor_arrivals"]
    return out

total_series = [total_by_month[(m,)] for m in month_list]
island_series = monthly_series(lambda r: r["island"])

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
dates = [datetime.strptime(m, "%Y-%m-%d") for m in month_list]
COLORS = {"Oahu":"#1f77b4","Maui":"#d62728","Kauai":"#2ca02c","Hawaii":"#9467bd"}

island_order = sorted(islands, key=lambda x: -island_year[(x, "2024")])
mkt_order = sorted(markets, key=lambda x: -market_year[(x, "2024")])
tier_order = ["luxury", "mid_market", "budget"]
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Chart 1: total monthly
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(dates, total_series, color="#1f77b4", linewidth=2.2, marker="o", markersize=4)
ax.set_title(f"Total monthly visitor arrivals, 2024-2025 (statewide YoY {agg:+.2f}%)")
ax.set_ylabel("Visitor arrivals")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v/1000)}k"))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b" + chr(92) + "n%Y"))
ax.axvspan(dates[0], dates[11], alpha=0.06, color="#1f77b4", label=f"2024: {totals_2024/1e6:.2f}M")
ax.axvspan(dates[12], dates[-1], alpha=0.06, color="#d62728", label=f"2025: {totals_2025/1e6:.2f}M ({agg:+.2f}%)")
ax.legend(loc="lower right", frameon=False)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "01_total_monthly.png", bbox_inches="tight")
plt.close(fig)
print("saved 01")

# Chart 2: YoY by island
fig, ax = plt.subplots(figsize=(8, 4.4))
yoy = [(island_year[(i, "2025")]/island_year[(i, "2024")]-1)*100 for i in island_order]
bar_colors = ["#2ca02c" if v >= 0 else "#d62728" for v in yoy]
bars = ax.bar(island_order, yoy, color=bar_colors)
ax.axhline(0, color="black", linewidth=0.8)
ax.axhline(agg, linestyle="--", linewidth=1.5, color="#1f77b4", label=f"Statewide aggregate: {agg:+.2f}%")
ax.set_title("Year-over-year change by island (2025 vs 2024)")
ax.set_ylabel("YoY change, %")
for bar, v in zip(bars, yoy):
    ax.text(bar.get_x()+bar.get_width()/2, v + (0.15 if v >= 0 else -0.4), f"{v:+.2f}%", ha="center", fontweight="bold")
ax.grid(axis="y", alpha=0.3)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / "02_yoy_by_island.png", bbox_inches="tight")
plt.close(fig)
print("saved 02")

# Chart 3: Monthly by island
fig, ax = plt.subplots(figsize=(10, 4.6))
for isl in ["Oahu", "Maui", "Hawaii", "Kauai"]:
    ax.plot(dates, island_series[isl], color=COLORS[isl], linewidth=2, marker="o", markersize=3, label=isl)
ax.set_title("Monthly visitor arrivals by island, 2024-2025")
ax.set_ylabel("Visitor arrivals")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v/1000)}k"))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b" + chr(92) + "n%Y"))
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "03_island_monthly.png", bbox_inches="tight")
plt.close(fig)
print("saved 03")

# Chart 4: YoY by tier/market
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
y = [(tier_year[(t, "2025")]/tier_year[(t, "2024")]-1)*100 for t in tier_order]
bars = ax1.bar(tier_order, y, color=["#2ca02c" if v >= 0 else "#d62728" for v in y])
ax1.axhline(0, color="black", linewidth=0.8)
ax1.axhline(agg, linestyle="--", linewidth=1.2, color="#1f77b4", label=f"Statewide: {agg:+.2f}%")
ax1.set_title("YoY by tier")
ax1.set_ylabel("YoY %")
for b, v in zip(bars, y):
    ax1.text(b.get_x()+b.get_width()/2, v + (0.1 if v>=0 else -0.25), f"{v:+.2f}%", ha="center", fontweight="bold")
ax1.grid(axis="y", alpha=0.3)
ax1.legend(frameon=False, loc="lower right")

y = [(market_year[(m, "2025")]/market_year[(m, "2024")]-1)*100 for m in mkt_order]
bars = ax2.bar(mkt_order, y, color=["#2ca02c" if v >= 0 else "#d62728" for v in y])
ax2.axhline(0, color="black", linewidth=0.8)
ax2.axhline(agg, linestyle="--", linewidth=1.2, color="#1f77b4", label=f"Statewide: {agg:+.2f}%")
ax2.set_title("YoY by origin market")
ax2.set_ylabel("YoY %")
for b, v in zip(bars, y):
    ax2.text(b.get_x()+b.get_width()/2, v + (0.1 if v>=0 else -0.25), f"{v:+.2f}%", ha="center", fontweight="bold")
ax2.tick_params(axis="x", rotation=20)
ax2.grid(axis="y", alpha=0.3)
ax2.legend(frameon=False, loc="lower right")
fig.suptitle("Tiers and markets all declined modestly; the real signal is by island")
fig.tight_layout()
fig.savefig(OUT / "04_yoy_tier_market.png", bbox_inches="tight")
plt.close(fig)
print("saved 04")

# Chart 5: heatmap island x tier
fig, ax = plt.subplots(figsize=(7.5, 4.2))
mat = np.array([[(isl_tier_year[(isl, t, "2025")]/isl_tier_year[(isl, t, "2024")]-1)*100 for t in tier_order] for isl in island_order])
maxabs = max(abs(mat.min()), abs(mat.max()))
im = ax.imshow(mat, cmap="RdYlGn", vmin=-maxabs, vmax=maxabs, aspect="auto")
ax.set_xticks(range(len(tier_order))); ax.set_xticklabels(tier_order)
ax.set_yticks(range(len(island_order))); ax.set_yticklabels(island_order)
ax.set_title("YoY change by island x tier (%)")
for i in range(len(island_order)):
    for j in range(len(tier_order)):
        v = mat[i, j]
        color = "black" if abs(v) < maxabs*0.55 else "white"
        ax.text(j, i, f"{v:+.2f}%", ha="center", va="center", color=color, fontweight="bold")
fig.colorbar(im, ax=ax, label="YoY %")
fig.tight_layout()
fig.savefig(OUT / "05_heatmap_island_tier.png", bbox_inches="tight")
plt.close(fig)
print("saved 05")

# Chart 6: heatmap island x market
fig, ax = plt.subplots(figsize=(9.5, 4.2))
mat = np.array([[(isl_mkt_year[(isl, mk, "2025")]/isl_mkt_year[(isl, mk, "2024")]-1)*100 for mk in mkt_order] for isl in island_order])
maxabs = max(abs(mat.min()), abs(mat.max()))
im = ax.imshow(mat, cmap="RdYlGn", vmin=-maxabs, vmax=maxabs, aspect="auto")
ax.set_xticks(range(len(mkt_order))); ax.set_xticklabels(mkt_order)
ax.set_yticks(range(len(island_order))); ax.set_yticklabels(island_order)
ax.set_title("YoY change by island x origin market (%)")
for i in range(len(island_order)):
    for j in range(len(mkt_order)):
        v = mat[i, j]
        color = "black" if abs(v) < maxabs*0.55 else "white"
        ax.text(j, i, f"{v:+.2f}%", ha="center", va="center", color=color, fontweight="bold", fontsize=9)
fig.colorbar(im, ax=ax, label="YoY %")
fig.tight_layout()
fig.savefig(OUT / "06_heatmap_island_market.png", bbox_inches="tight")
plt.close(fig)
print("saved 06")

# Chart 7: monthly 2024 vs 2025 by island
fig, axs = plt.subplots(2, 2, figsize=(11, 6.4), sharex=True)
for ax, isl in zip(axs.flat, island_order):
    data_24 = [island_series[isl][i] for i in range(12)]
    data_25 = [island_series[isl][i+12] for i in range(12)]
    x = np.arange(12)
    ax.plot(x, data_24, color="#7f7f7f", linewidth=2, marker="o", label="2024", markersize=4)
    ax.plot(x, data_25, color=COLORS[isl], linewidth=2.4, marker="o", label="2025", markersize=4)
    y = (sum(data_25)/sum(data_24)-1)*100
    ax.set_title(f"{isl}: {y:+.2f}% YoY")
    ax.set_xticks(x); ax.set_xticklabels(month_names, fontsize=8)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v/1000)}k"))
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, loc="lower left", fontsize=9)
fig.suptitle("Monthly arrivals by island: 2024 vs 2025")
fig.tight_layout()
fig.savefig(OUT / "07_island_2024_vs_2025.png", bbox_inches="tight")
plt.close(fig)
print("saved 07")

# Chart 8: contribution by island
fig, ax = plt.subplots(figsize=(9, 4.4))
island_delta = {isl: island_year[(isl, "2025")] - island_year[(isl, "2024")] for isl in islands}
ord_isl = sorted(islands, key=lambda x: island_delta[x])
vals = [island_delta[isl] for isl in ord_isl]
colors = ["#d62728" if v < 0 else "#2ca02c" for v in vals]
bars = ax.bar(ord_isl, vals, color=colors)
ax.axhline(0, color="black", linewidth=0.8)
total_delta = totals_2025 - totals_2024
for b, v in zip(bars, vals):
    pct = v/total_delta*100
    lbl = f"{v:+,}" + chr(92) + "n(" + f"{pct:+.0f}" + "% of total delta)"
    ax.text(b.get_x()+b.get_width()/2, v + (5000 if v>=0 else -12000), lbl, ha="center", fontsize=9, fontweight="bold", color="black")
ax.set_title(f"Contribution to statewide decline by island (total delta = {total_delta:+,})")
ax.set_ylabel("Change in arrivals, 2025 vs 2024")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v/1000)}k"))
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "08_contribution_by_island.png", bbox_inches="tight")
plt.close(fig)
print("saved 08")

# Chart 9: island x tier cells vs aggregate
fig, ax = plt.subplots(figsize=(12, 5))
cells = [(isl, t) for isl in island_order for t in tier_order]
y_cells = [(isl_tier_year[(isl, t, "2025")]/isl_tier_year[(isl, t, "2024")]-1)*100 for isl, t in cells]
labels = [isl + chr(92) + "n" + t for isl, t in cells]
colors = ["#2ca02c" if v >= 0 else "#d62728" for v in y_cells]
bars = ax.bar(range(len(cells)), y_cells, color=colors)
ax.axhline(0, color="black", linewidth=0.8)
ax.axhline(agg, color="#1f77b4", linewidth=2, linestyle="--", label=f"Statewide aggregate: {agg:+.2f}%")
ax.set_xticks(range(len(cells)))
ax.set_xticklabels(labels, rotation=0, fontsize=8)
ax.set_ylabel("YoY %")
ax.set_title("Segment YoY (island x tier): recovery is not uniform across the state")
for i, v in enumerate(y_cells):
    ax.text(i, v + (0.2 if v >= 0 else -0.55), f"{v:+.1f}%", ha="center", fontweight="bold", fontsize=8)
ax.legend(loc="lower right", frameon=False)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "09_segments_vs_aggregate.png", bbox_inches="tight")
plt.close(fig)
print("saved 09")

# Chart 10: monthly YoY
fig, ax = plt.subplots(figsize=(10, 4.2))
yoy_m = []
for mi in range(12):
    m24 = total_series[mi]; m25 = total_series[mi+12]
    yoy_m.append((m25/m24-1)*100)
colors = ["#2ca02c" if v >= 0 else "#d62728" for v in yoy_m]
bars = ax.bar(month_names, yoy_m, color=colors)
ax.axhline(0, color="black", linewidth=0.8)
ax.axhline(agg, linestyle="--", linewidth=1.5, color="#1f77b4", label=f"Annual YoY: {agg:+.2f}%")
ax.set_title("Monthly YoY 2025 vs 2024: decline is persistent, not a blip")
ax.set_ylabel("YoY %")
for b, v in zip(bars, yoy_m):
    ax.text(b.get_x()+b.get_width()/2, v + (0.05 if v>=0 else -0.2), f"{v:+.2f}%", ha="center", fontweight="bold", fontsize=8)
ax.grid(axis="y", alpha=0.3)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / "10_monthly_yoy.png", bbox_inches="tight")
plt.close(fig)
print("saved 10")
print("Done")
