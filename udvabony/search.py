#!/usr/bin/env python3
"""Semantic + filter search over the udvabony product index.

Examples:
  python search.py "esp32 dev board"
  python search.py "10k ohm 1/4 watt resistor" -k 5
  python search.py "lipo 3.7v" --max-price 500 --in-stock
  python search.py "ultrasonic sensor" --category sensors
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.faiss")
META = os.path.join(HERE, "meta.csv")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load():
    if not (os.path.exists(INDEX) and os.path.exists(META)):
        print("index missing — run build_index.py first", file=sys.stderr)
        sys.exit(1)
    return faiss.read_index(INDEX), pd.read_csv(META)


def search(query, k=10, category=None, max_price=None, min_price=None, in_stock=False, oversample=10):
    index, meta = load()
    model = SentenceTransformer(MODEL_NAME)
    q = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    n = min(k * oversample, index.ntotal)
    scores, ids = index.search(q, n)
    rows = meta.iloc[ids[0]].copy()
    rows["score"] = scores[0]
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
            f"        BDT {r['price']:.2f}  | {r['in_stock']:>3s} | {r['categories']}\n"
            f"        sku={r['sku']}  {r['permalink']}"
        )
    return "\n\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=10, help="results to show")
    ap.add_argument("--category", help="substring filter on categories")
    ap.add_argument("--max-price", type=float)
    ap.add_argument("--min-price", type=float)
    ap.add_argument("--in-stock", action="store_true")
    args = ap.parse_args()
    rows = search(
        args.query,
        k=args.k,
        category=args.category,
        max_price=args.max_price,
        min_price=args.min_price,
        in_stock=args.in_stock,
    )
    print(fmt(rows))


if __name__ == "__main__":
    main()
