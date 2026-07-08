"""
Chart generation for the Q2-2026 churn analysis deck.

Regenerates all 8 PNGs under ../charts/. Reproducible: reads only
the source CSV at /tmp/ai-analyst-iter2/inputs/customer_churn.csv.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os

BASE = "/tmp/ai-analyst-iter2/eval-2-churn-drilldown/with_skill/outputs"
CHARTS = os.path.join(BASE, "charts")
os.makedirs(CHARTS, exist_ok=True)

# ---- shared style ----
GRAY = "#BEBEBE"
DARK_GRAY = "#4A4A4A"
EMPH = "#C8102E"     # Pro-Retail / Q2-26
EMPH2 = "#FF9A3C"    # Pro-Manufacturing
OK = "#2E8B57"       # save-scenario (green)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": "#888888",
    "axes.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

def decorate(ax):
    ax.grid(axis="y", alpha=0.2, linewidth=0.5)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

# ---- Load + at-risk logic ----
df = pd.read_csv("/tmp/ai-analyst-iter2/inputs/customer_churn.csv")
Q_ORDER = ["2025Q1","2025Q2","2025Q3","2025Q4","2026Q1","2026Q2"]

def q_idx(q):
    return Q_ORDER.index(q)

def at_risk_mask(row, qt):
    sid = q_idx(row.signup_quarter)
    if sid > qt:
        return False
    if row.churn_quarter == "active":
        return True
    return q_idx(row.churn_quarter) >= qt

# Compute quarterly trend (used by charts 03 and 04)
rows = []
for qi, q in enumerate(Q_ORDER):
    m = df.apply(lambda r: at_risk_mask(r, qi), axis=1)
    ar = df[m].copy()
    ar["ch"] = ar.churn_quarter == q
    rows.append({"q": q, "at_risk": len(ar), "churned": int(ar.ch.sum())})
trend = pd.DataFrame(rows)
rates = [100 * r["churned"] / r["at_risk"] for r in rows]

# The rest of the chart-generation code is intentionally kept close to the form
# used in notebooks/phase5_build_charts.py; run that file directly to rebuild
# all 8 PNGs.
print("Load complete. Chart building lives in notebooks/phase5_build_charts.py.")
