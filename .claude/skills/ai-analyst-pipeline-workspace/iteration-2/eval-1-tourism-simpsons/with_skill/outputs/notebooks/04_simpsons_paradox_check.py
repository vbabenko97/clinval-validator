"""04_simpsons_paradox_check.py - Explicit Simpson's Paradox check on aggregate vs island."""
import pandas as pd
from pathlib import Path

DATA = Path("/tmp/ai-analyst-iter2/inputs/tourism_monthly.csv")
df = pd.read_csv(DATA)
df["month"] = pd.to_datetime(df["month"])
df["year"] = df["month"].dt.year

# Aggregate
agg_2024 = df[df["year"] == 2024]["visitor_arrivals"].sum()
agg_2025 = df[df["year"] == 2025]["visitor_arrivals"].sum()
agg_pct = (agg_2025 / agg_2024 - 1) * 100

# By island
by_island = df.groupby(["year", "island"])["visitor_arrivals"].sum().unstack().T
by_island["pct_delta"] = (by_island[2025] / by_island[2024] - 1) * 100

if __name__ == "__main__":
    print(f"AGGREGATE YoY: {agg_pct:+.2f}% ({agg_2025-agg_2024:+,})")
    print("\nBy island YoY:")
    print(by_island.round(2).to_string())
    # Sign check
    signs = by_island["pct_delta"].apply(lambda x: "+" if x > 0 else "-" if x < 0 else "0").tolist()
    print(f"\nSigns: {signs}. Mixed: {len(set(signs)) > 1}")
    print("Simpson's Paradox CONFIRMED if aggregate is small but subgroups diverge in sign or magnitude.")
