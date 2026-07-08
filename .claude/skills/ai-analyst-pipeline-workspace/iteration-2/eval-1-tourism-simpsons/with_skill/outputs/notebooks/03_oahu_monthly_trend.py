"""03_oahu_monthly_trend.py - Track Oahu monthly YoY and show the deterioration pattern."""
import pandas as pd
from pathlib import Path

DATA = Path("/tmp/ai-analyst-iter2/inputs/tourism_monthly.csv")
df = pd.read_csv(DATA)
df["month"] = pd.to_datetime(df["month"])
df["year"] = df["month"].dt.year
df["month_of_year"] = df["month"].dt.month

oahu = df[df["island"] == "Oahu"]
monthly_yoy = oahu.groupby(["month_of_year", "year"])["visitor_arrivals"].sum().unstack()
monthly_yoy["abs_delta"] = monthly_yoy[2025] - monthly_yoy[2024]
monthly_yoy["yoy_pct"] = (monthly_yoy[2025] / monthly_yoy[2024] - 1) * 100

if __name__ == "__main__":
    print(monthly_yoy.round(2).to_string())
    print(f"\nH1 Oahu YoY: {((oahu[(oahu['year']==2025) & (oahu['month_of_year']<=6)]['visitor_arrivals'].sum() / oahu[(oahu['year']==2024) & (oahu['month_of_year']<=6)]['visitor_arrivals'].sum()) - 1)*100:.2f}%")
    print(f"H2 Oahu YoY: {((oahu[(oahu['year']==2025) & (oahu['month_of_year']>6)]['visitor_arrivals'].sum() / oahu[(oahu['year']==2024) & (oahu['month_of_year']>6)]['visitor_arrivals'].sum()) - 1)*100:.2f}%")
