#!/usr/bin/env python3
"""Search the combined BD electronics index. Filters by shop, category, price.

Examples:
  python search.py "esp32 dev board"
  python search.py "10k 1/4 watt" --shop udvabony --max-price 5
  python search.py "ne5532" --in-stock
  python search.py "max7219 8x8" --shop techshopbd
"""
import argparse
import os
import sys

import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "bd_index.faiss")
META = os.path.join(HERE, "bd_meta.csv")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def search(q, k=10, shop=None, category=None, max_price=None, min_price=None, in_stock=False):
    if not (os.path.exists(INDEX) and os.path.exists(META)):
        print("run build_index.py first", file=sys.stderr); sys.exit(1)
    index = faiss.read_index(INDEX)
    meta = pd.read_csv(META)
    model = SentenceTransformer(MODEL_NAME)
    qv = model.encode([q], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    n = min(k * 15, index.ntotal)
    scores, ids = index.search(qv, n)
    rows = meta.iloc[ids[0]].copy()
    rows["score"] = scores[0]
    if shop:
        rows = rows[rows["shop"].str.contains(shop, case=False, na=False)]
    if category:
        rows = rows[rows["categories"].str.contains(category, case=False, na=False)]
    if max_price is not None:
        rows = rows[rows["price"] <= max_price]
    if min_price is not None:
        rows = rows[rows["price"] >= min_price]
    if in_stock:
        rows = rows[rows["in_stock"] == "yes"]
    return rows.head(k)


def fmt(rows):
    if rows.empty:
        return "no results"
    out = []
    for _, r in rows.iterrows():
        out.append(
            f"[{r['score']:.3f}]  {r['name']}\n"
            f"        BDT {float(r['price'] or 0):>7.2f}  | {str(r['in_stock']):>3s}  | {r['shop']:<20s} | {r['categories']}\n"
            f"        {r['permalink']}"
        )
    return "\n\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=10)
    ap.add_argument("--shop")
    ap.add_argument("--category")
    ap.add_argument("--max-price", type=float)
    ap.add_argument("--min-price", type=float)
    ap.add_argument("--in-stock", action="store_true")
    args = ap.parse_args()
    print(fmt(search(args.query, k=args.k, shop=args.shop, category=args.category,
                     max_price=args.max_price, min_price=args.min_price, in_stock=args.in_stock)))


if __name__ == "__main__":
    main()
