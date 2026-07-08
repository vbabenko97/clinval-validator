"""
Phase 2+3+5 reproduction — part 1 of 2 (data + rate computation).

Loads CSV, builds at-risk frame, computes quarterly churn rates and Q2-26
segmentations. Part 2 (`phase5_charts.py`) produces the 8 PNGs from this output.
"""
import pandas as pd
import numpy as np

df = pd.read_csv("/tmp/ai-analyst-iter2/inputs/customer_churn.csv")
Q = ["2025Q1","2025Q2","2025Q3","2025Q4","2026Q1","2026Q2"]
def qi(x): return Q.index(x)
def at_risk(row, qt):
    s = qi(row.signup_quarter)
    if s > qt: return False
    if row.churn_quarter == "active": return True
    return qi(row.churn_quarter) >= qt

# Quarterly trend
rows=[]
for i,q in enumerate(Q):
    m = df.apply(lambda r: at_risk(r,i), axis=1)
    ar = df[m].copy(); ar["ch"] = ar.churn_quarter==q
    rows.append({"q":q,"at_risk":len(ar),"churned":int(ar.ch.sum())})
trend = pd.DataFrame(rows)
rates = [100*r["churned"]/r["at_risk"] for r in rows]

# Q2-2026 slice
i_q2 = qi("2026Q2")
m = df.apply(lambda r: at_risk(r,i_q2), axis=1)
ar_q2 = df[m].copy(); ar_q2["ch"] = ar_q2.churn_quarter=="2026Q2"

tier = ar_q2.groupby("plan_tier").agg(at_risk=("customer_id","count"),churned=("ch","sum")).reset_index()
tier["rate"] = 100*tier.churned/tier.at_risk

piv = ar_q2.groupby(["plan_tier","industry"]).agg(at_risk=("customer_id","count"),churned=("ch","sum")).reset_index()
piv["rate"] = 100*piv.churned/piv.at_risk

if __name__ == "__main__":
    print("Quarterly trend:"); print(trend.assign(rate=rates).to_string(index=False))
    print("\nTier:"); print(tier.to_string(index=False))
    print("\nTier x Industry:"); print(piv.to_string(index=False))
