#!/usr/bin/env python3
import csv
from collections import Counter

CSV = "/home/shinzuu/Documents/EEEprojects/udvabony/products.csv"

cats = Counter()
top_cats = Counter()
prices = []
missing_price = 0
missing_name = 0
in_stock = 0
total = 0

with open(CSV, encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        total += 1
        if not row["name"]:
            missing_name += 1
        try:
            p = float(row["price"])
            prices.append(p)
        except (ValueError, TypeError):
            missing_price += 1
        if row["in_stock"] == "yes":
            in_stock += 1
        for c in (row["categories"] or "").split(" | "):
            c = c.strip()
            if c:
                cats[c] += 1
        first = (row["categories"] or "").split(" | ")[0].strip()
        if first:
            top_cats[first] += 1

print(f"total products: {total}")
print(f"missing name: {missing_name}")
print(f"missing price: {missing_price}")
print(f"in stock: {in_stock} ({100*in_stock/total:.1f}%)")
if prices:
    prices.sort()
    print(f"price BDT — min: {prices[0]:.2f}  max: {prices[-1]:.2f}  median: {prices[len(prices)//2]:.2f}  mean: {sum(prices)/len(prices):.2f}")
    free = sum(1 for p in prices if p == 0)
    print(f"zero-priced: {free}")
print(f"\nunique categories: {len(cats)}")
print(f"\ntop 25 primary categories:")
for c, n in top_cats.most_common(25):
    print(f"  {n:5d}  {c}")
