#!/usr/bin/env python3
"""Build a combined FAISS index across all four shops:
   udvabony + techshopbd + makersbd + electronics.com.bd

Run from this folder. Reuses the same model + topology as the udvabony index.

Outputs:
   bd_index.faiss
   bd_meta.csv      (id, sku, name, price, currency, in_stock, categories,
                     short_description, permalink, shop)
"""
import html
import os
import re
import sys

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "bd_index.faiss")
META = os.path.join(HERE, "bd_meta.csv")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

SHOPS = {
    "udvabony": "/home/shinzuu/Documents/EEEprojects/udvabony/products.csv",
    "techshopbd": os.path.join(HERE, "techshopbd/products.csv"),
    "makersbd": os.path.join(HERE, "makersbd/products.csv"),
    "electronics.com.bd": os.path.join(HERE, "electronics_com_bd/products.csv"),
}

WS = re.compile(r"\s+")


def clean(s):
    if not isinstance(s, str):
        return ""
    return WS.sub(" ", html.unescape(s)).strip()


def load_shop(name, path):
    if not os.path.exists(path):
        print(f"  [skip] {name}: {path} missing")
        return None
    df = pd.read_csv(path, dtype=str).fillna("")
    df["shop"] = name
    print(f"  [{name}] {len(df)} rows")
    return df


def main():
    frames = []
    for name, path in SHOPS.items():
        df = load_shop(name, path)
        if df is not None:
            frames.append(df)
    if not frames:
        print("no shops loaded", file=sys.stderr)
        sys.exit(1)
    df = pd.concat(frames, ignore_index=True)
    for col in ["name", "categories", "short_description"]:
        df[col] = df[col].map(clean)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["text"] = (df["name"] + " | " + df["categories"] + " | " + df["short_description"]).str.strip()

    print(f"total: {len(df)} rows across {len(frames)} shops")
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(
        df["text"].tolist(),
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    faiss.write_index(index, INDEX)
    df.drop(columns=["text"]).to_csv(META, index=False)
    print(f"wrote {INDEX} ({index.ntotal} vectors)  +  {META}")


if __name__ == "__main__":
    main()
