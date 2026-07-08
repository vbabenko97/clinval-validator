#!/usr/bin/env python3
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

print(f"Loaded {len(rows)} rows")

months = sorted({r["month"] for r in rows})
islands = sorted({r["island"] for r in rows})
accoms = sorted({r["accommodation_type"] for r in rows})
tiers = sorted({r["tier"] for r in rows})
markets = sorted({r["origin_market"] for r in rows})
print(f"Months: {len(months)} ({months[0]} to {months[-1]})")
print(f"Islands: {islands}")
print(f"Accoms: {accoms}")
print(f"Tiers: {tiers}")
print(f"Markets: {markets}")

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
total_by_accom_month = sum_by(["accommodation_type", "month"])
total_by_island_tier_month = sum_by(["island", "tier", "month"])
total_by_island_market_month = sum_by(["island", "origin_market", "month"])
total_by_island_accom_month = sum_by(["island", "accommodation_type", "month"])

def year_of(m): return m[:4]

totals_2024 = sum(v for (m,), v in total_by_month.items() if year_of(m) == "2024")
totals_2025 = sum(v for (m,), v in total_by_month.items() if year_of(m) == "2025")
print(f"2024 total: {totals_2024:,}")
print(f"2025 total: {totals_2025:,}")
print(f"YoY: {(totals_2025/totals_2024-1)*100:+.2f}%")

island_year = defaultdict(int)
for (isl, m), v in total_by_island_month.items():
    island_year[(isl, year_of(m))] += v
for isl in islands:
    a = island_year[(isl, "2024")]; b = island_year[(isl, "2025")]
    print(f"  {isl:8s}: 2024={a:>10,}  2025={b:>10,}  YoY={(b/a-1)*100:+6.2f}%")

tier_year = defaultdict(int)
for (t, m), v in total_by_tier_month.items():
    tier_year[(t, year_of(m))] += v
print("tier YoY:")
for t in tiers:
    a = tier_year[(t, "2024")]; b = tier_year[(t, "2025")]
    print(f"  {t:10s}: 2024={a:>10,}  2025={b:>10,}  YoY={(b/a-1)*100:+6.2f}%")

market_year = defaultdict(int)
for (mk, m), v in total_by_market_month.items():
    market_year[(mk, year_of(m))] += v
print("market YoY:")
for mk in markets:
    a = market_year[(mk, "2024")]; b = market_year[(mk, "2025")]
    print(f"  {mk:12s}: 2024={a:>10,}  2025={b:>10,}  YoY={(b/a-1)*100:+6.2f}%")

accom_year = defaultdict(int)
for (ac, m), v in total_by_accom_month.items():
    accom_year[(ac, year_of(m))] += v
print("accom YoY:")
for a in accoms:
    x = accom_year[(a, "2024")]; y = accom_year[(a, "2025")]
    print(f"  {a:16s}: 2024={x:>10,}  2025={y:>10,}  YoY={(y/x-1)*100:+6.2f}%")

isl_tier_year = defaultdict(int)
for (isl, t, m), v in total_by_island_tier_month.items():
    isl_tier_year[(isl, t, year_of(m))] += v
print("island x tier YoY:")
for isl in islands:
    for t in tiers:
        a = isl_tier_year[(isl, t, "2024")]; b = isl_tier_year[(isl, t, "2025")]
        print(f"  {isl:<10}{t:<12}2024={a:>10,}  2025={b:>10,}  YoY={(b/a-1)*100:+6.2f}%")

isl_mkt_year = defaultdict(int)
for (isl, mk, m), v in total_by_island_market_month.items():
    isl_mkt_year[(isl, mk, year_of(m))] += v
print("island x market YoY:")
for isl in islands:
    for mk in markets:
        a = isl_mkt_year[(isl, mk, "2024")]; b = isl_mkt_year[(isl, mk, "2025")]
        print(f"  {isl:<10}{mk:<14}2024={a:>10,}  2025={b:>10,}  YoY={(b/a-1)*100:+6.2f}%")

isl_accom_year = defaultdict(int)
for (isl, ac, m), v in total_by_island_accom_month.items():
    isl_accom_year[(isl, ac, year_of(m))] += v
print("island x accom YoY:")
for isl in islands:
    for ac in accoms:
        a = isl_accom_year[(isl, ac, "2024")]; b = isl_accom_year[(isl, ac, "2025")]
        print(f"  {isl:<10}{ac:<18}2024={a:>10,}  2025={b:>10,}  YoY={(b/a-1)*100:+6.2f}%")

# monthly YoY
month_num = ["%02d" % i for i in range(1, 13)]
names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
print("monthly YoY:")
for mn, name in zip(month_num, names):
    m24 = total_by_month[(f"2024-{mn}-01",)]
    m25 = total_by_month[(f"2025-{mn}-01",)]
    print(f"  {name}: 2024={m24:>8,}  2025={m25:>8,}  YoY={(m25/m24-1)*100:+5.2f}%")

# Mix shifts
print("tier share:")
total_24 = sum(tier_year[(t, "2024")] for t in tiers)
total_25 = sum(tier_year[(t, "2025")] for t in tiers)
for t in tiers:
    s24 = tier_year[(t, "2024")] / total_24 * 100
    s25 = tier_year[(t, "2025")] / total_25 * 100
    print(f"  {t:10s} 2024={s24:5.1f}%  2025={s25:5.1f}%  diff={s25-s24:+.2f}pp")

print("market share:")
total_24 = sum(market_year[(mk, "2024")] for mk in markets)
total_25 = sum(market_year[(mk, "2025")] for mk in markets)
for mk in markets:
    s24 = market_year[(mk, "2024")] / total_24 * 100
    s25 = market_year[(mk, "2025")] / total_25 * 100
    print(f"  {mk:12s} 2024={s24:5.1f}%  2025={s25:5.1f}%  diff={s25-s24:+.2f}pp")

print("island share:")
total_24 = sum(island_year[(isl, "2024")] for isl in islands)
total_25 = sum(island_year[(isl, "2025")] for isl in islands)
for isl in islands:
    s24 = island_year[(isl, "2024")] / total_24 * 100
    s25 = island_year[(isl, "2025")] / total_25 * 100
    print(f"  {isl:8s} 2024={s24:5.1f}%  2025={s25:5.1f}%  diff={s25-s24:+.2f}pp")

# contribution to delta
total_delta = totals_2025 - totals_2024
print(f"total delta = {total_delta:+,}")
print("contribution by island:")
for isl in islands:
    d = island_year[(isl, "2025")] - island_year[(isl, "2024")]
    print(f"  {isl:8s}: {d:+10,}  ({d/total_delta*100:+5.1f}% of delta)")

print("contribution by tier:")
for t in tiers:
    d = tier_year[(t, "2025")] - tier_year[(t, "2024")]
    print(f"  {t:10s}: {d:+10,}  ({d/total_delta*100:+5.1f}% of delta)")

print("contribution by market:")
for mk in markets:
    d = market_year[(mk, "2025")] - market_year[(mk, "2024")]
    print(f"  {mk:12s}: {d:+10,}  ({d/total_delta*100:+5.1f}% of delta)")
