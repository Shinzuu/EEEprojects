#!/usr/bin/env python3
"""Build FAISS index over products.csv.

Run once. Outputs:
  index.faiss        — vector index (cosine via L2-normalized inner product)
  meta.parquet       — row metadata aligned to index ids
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
CSV = os.path.join(HERE, "products.csv")
INDEX = os.path.join(HERE, "index.faiss")
META = os.path.join(HERE, "meta.csv")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

WS = re.compile(r"\s+")


def clean(s):
    if not isinstance(s, str):
        return ""
    s = html.unescape(s)
    return WS.sub(" ", s).strip()


def make_text(row):
    parts = [row["name"], row["categories"], row["short_description"]]
    return " | ".join(p for p in (clean(x) for x in parts) if p)


def main():
    print(f"loading {CSV}")
    df = pd.read_csv(CSV, dtype=str).fillna("")
    df["name"] = df["name"].map(clean)
    df["categories"] = df["categories"].map(clean)
    df["short_description"] = df["short_description"].map(clean)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
    df["text"] = df.apply(make_text, axis=1)
    print(f"{len(df)} rows, encoding...")

    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(
        df["text"].tolist(),
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    faiss.write_index(index, INDEX)
    print(f"wrote {INDEX} ({index.ntotal} vectors, dim={dim})")

    df.drop(columns=["text"]).to_csv(META, index=False)
    print(f"wrote {META}")


if __name__ == "__main__":
    sys.exit(main())
