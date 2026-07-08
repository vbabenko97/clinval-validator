"""02_oahu_root_cause.py - Drill into Oahu's decline: accommodation x tier x origin."""
import pandas as pd
from pathlib import Path

DATA = Path("/tmp/ai-analyst-iter2/inputs/tourism_monthly.csv")
df = pd.read_csv(DATA)
df["month"] = pd.to_datetime(df["month"])
df["year"] = df["month"].dt.year
oahu = df[df["island"] == "Oahu"]

# Oahu decline by accommodation x tier x origin
t = oahu.groupby(["year", "accommodation_type", "tier", "origin_market"])["visitor_arrivals"].sum().unstack("year")
t["abs_delta"] = t[2025] - t[2024]
t["pct_delta"] = (t[2025] / t[2024] - 1) * 100
oahu_total_delta = oahu[oahu["year"] == 2025]["visitor_arrivals"].sum() - oahu[oahu["year"] == 2024]["visitor_arrivals"].sum()
t["share_of_oahu_decline_pct"] = t["abs_delta"] / oahu_total_delta * 100

if __name__ == "__main__":
    print(f"Oahu total YoY delta: {oahu_total_delta:+,}")
    print("\nTop 15 declining cells on Oahu:")
    print(t.sort_values("abs_delta").head(15).round(2).to_string())
    print(f"\nTop-5 cells account for {t.sort_values('abs_delta').head(5)['abs_delta'].sum()/oahu_total_delta*100:.1f}% of Oahu decline")
    print(f"Top-10 cells account for {t.sort_values('abs_delta').head(10)['abs_delta'].sum()/oahu_total_delta*100:.1f}% of Oahu decline")
