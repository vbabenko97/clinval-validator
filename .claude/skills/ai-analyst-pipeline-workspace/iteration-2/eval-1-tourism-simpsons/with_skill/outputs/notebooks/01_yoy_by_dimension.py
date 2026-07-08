"""01_yoy_by_dimension.py - Reproducible YoY breakdown across all dimensions."""
import pandas as pd
from pathlib import Path

DATA = Path("/tmp/ai-analyst-iter2/inputs/tourism_monthly.csv")
df = pd.read_csv(DATA)
df["month"] = pd.to_datetime(df["month"])
df["year"] = df["month"].dt.year

def yoy(dim):
    t = df.groupby(["year", dim])["visitor_arrivals"].sum().unstack().T
    t["abs_delta"] = t[2025] - t[2024]
    t["pct_delta"] = (t[2025] / t[2024] - 1) * 100
    t["share_of_2024_total"] = t[2024] / t[2024].sum() * 100
    return t.sort_values("abs_delta").round(2)

if __name__ == "__main__":
    for dim in ["island", "accommodation_type", "tier", "origin_market"]:
        print(f"\n=== YoY by {dim} ===")
        print(yoy(dim).to_string())
