"""Phase 2 exploration: produces all the numbers cited in findings.json.

Run with: python 01_explore.py
"""
import pandas as pd
import numpy as np

DATA = "/tmp/ai-analyst-iter2/inputs/funnel_monthly.csv"
df = pd.read_csv(DATA)
df["month"] = pd.to_datetime(df["month"])

def overall(df):
    g = df.groupby("month").agg(visits=("visits","sum"),
                                signups=("signups","sum"),
                                conversions=("conversions","sum"))
    g["v2s"] = g.signups/g.visits
    g["v2c"] = g.conversions/g.visits
    g["s2c"] = g.conversions/g.signups
    return g

def by_dim(df, dim):
    g = df.groupby(["month", dim]).agg(visits=("visits","sum"),
                                       signups=("signups","sum"),
                                       conversions=("conversions","sum")).reset_index()
    g["v2s"] = g.signups/g.visits
    g["v2c"] = g.conversions/g.visits
    g["s2c"] = g.conversions/g.signups
    return g

if __name__ == "__main__":
    print("Overall:"); print(overall(df).round(4))
    print("\nBy user_type:"); print(by_dim(df, "user_type").round(4))
    print("\nBy channel:"); print(by_dim(df, "channel").round(4))
