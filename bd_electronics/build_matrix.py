#!/usr/bin/env python3
"""Build a per-product comparison matrix across all 4 BD shops.

For each product, columns are: udvabony / techshopbd / makersbd / electronics.com.bd.
Each cell shows price (BDT) and links out to that shop's listing.

Matching strategy:
  1. Extract a normalized "key" from the name — strip ALL CAPS noise, keep alphanumeric
     part-number-looking tokens (NE5532, ESP32, 18650, MAX7219, TP4056, ...).
  2. Group rows that share at least one strong key token.
  3. Within each group, run cosine sim on the MiniLM-encoded names; rows above 0.65 sim
     collapse into the same product row.
  4. Each shop contributes the lowest-priced match to that group's cell.

Outputs:
  matrix.csv     — one row per matched product cluster, BDT price columns
  matrix.html    — readable, with clickable shop links
"""
import html
import os
import re
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

HERE = os.path.dirname(os.path.abspath(__file__))
SHOPS = [
    ("udvabony", "/home/shinzuu/Documents/EEEprojects/udvabony/products.csv"),
    ("techshopbd", os.path.join(HERE, "techshopbd/products.csv")),
    ("makersbd", os.path.join(HERE, "makersbd/products.csv")),
    ("electronics.com.bd", os.path.join(HERE, "electronics_com_bd/products.csv")),
]

WS = re.compile(r"\s+")
TOKEN_RE = re.compile(r"\b([A-Z]{2,}[0-9]+[A-Z0-9]*|[0-9]+[A-Z][A-Z0-9]*|[A-Z][A-Z]+[0-9]+)\b")
NUMERIC_TOKEN = re.compile(r"\b([0-9]+\.?[0-9]*[KkMmuUnNpPmM]?[ΩFfHhVvAaWw]?)\b")
STOPWORDS = {
    "PRICE", "BD", "RESISTOR", "CAPACITOR", "MODULE", "BOARD", "ARDUINO", "ELECTRONICS",
    "PIN", "PCS", "PCB", "DIP", "SMD", "MM", "INCH", "WATT", "VOLT", "AMP", "OHM",
    "PACKAGE", "GENERAL", "PURPOSE", "CIRCUITRY", "PARTS", "HIGH", "LOW", "QUALITY",
    "WITH", "FOR", "AND", "FROM", "INTO", "ONLY", "EACH", "PIECE", "PIECES", "EA", "QTY",
}


def clean_name(s):
    s = html.unescape(s or "")
    return WS.sub(" ", s).strip()


def key_tokens(name):
    """Strong identifier tokens that suggest a part number / model."""
    name_u = name.upper()
    raw = TOKEN_RE.findall(name_u) + NUMERIC_TOKEN.findall(name_u)
    tokens = [t for t in raw if t not in STOPWORDS and len(t) >= 2]
    # de-dup but preserve order
    out, seen = [], set()
    for t in tokens:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:8]  # first 8 are usually the meaningful ones


def load_all():
    frames = []
    for shop, path in SHOPS:
        if not os.path.exists(path):
            print(f"[skip] {shop}: {path} missing")
            continue
        df = pd.read_csv(path, dtype=str).fillna("")
        df["shop"] = shop
        df["name"] = df["name"].map(clean_name)
        df["price_num"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
        df = df[df["name"].str.len() > 4]
        frames.append(df)
        print(f"[load] {shop}: {len(df)}")
    return pd.concat(frames, ignore_index=True)


def cluster(df, sim_threshold=0.72):
    """Greedy clustering: encode names, group by shared tokens, then merge by similarity."""
    print("encoding names...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    emb = model.encode(
        df["name"].tolist(), batch_size=64, show_progress_bar=True,
        normalize_embeddings=True, convert_to_numpy=True,
    ).astype("float32")

    # Bucket by first strong token to keep candidate sets small
    print("bucketing by part tokens...")
    buckets = defaultdict(list)  # token -> [row_indices]
    rows_tokens = []
    for i, name in enumerate(df["name"].tolist()):
        toks = key_tokens(name)
        rows_tokens.append(toks)
        for t in toks[:3]:  # first 3 strongest
            buckets[t].append(i)
    # also bucket by lowercased simplified-name first 4 chars to catch token-less rows
    for i, name in enumerate(df["name"].tolist()):
        if not rows_tokens[i]:
            simp = re.sub(r"[^a-z0-9]", "", name.lower())[:5]
            if simp:
                buckets[f"~{simp}"].append(i)

    # Greedy: walk rows in order, assign to first existing cluster within sim_threshold
    print(f"clustering {len(df)} rows ({len(buckets)} buckets)...")
    cluster_id = np.full(len(df), -1, dtype=np.int32)
    cluster_centers = []  # list of (representative_idx, member_idxs)

    for i in range(len(df)):
        if cluster_id[i] >= 0:
            continue
        toks = rows_tokens[i]
        candidates = set()
        for t in toks[:3]:
            candidates.update(buckets.get(t, []))
        if not toks:
            simp = re.sub(r"[^a-z0-9]", "", df["name"].iloc[i].lower())[:5]
            if simp:
                candidates.update(buckets.get(f"~{simp}", []))
        # only earlier-seen rows can absorb this one
        candidates = [c for c in candidates if c < i and cluster_id[c] >= 0]
        best_cid, best_sim = -1, sim_threshold
        for c in candidates:
            cid = cluster_id[c]
            rep_idx = cluster_centers[cid][0]
            sim = float(np.dot(emb[i], emb[rep_idx]))
            if sim > best_sim:
                best_sim = sim
                best_cid = cid
        if best_cid >= 0:
            cluster_id[i] = best_cid
            cluster_centers[best_cid][1].append(i)
        else:
            cluster_id[i] = len(cluster_centers)
            cluster_centers.append((i, [i]))

    print(f"clusters: {len(cluster_centers)}")
    df["cluster"] = cluster_id
    return df, cluster_centers


def build_matrix(df, cluster_centers):
    """Per-cluster: pick canonical name (longest), per-shop pick lowest-price match."""
    shop_names = [s for s, _ in SHOPS]
    rows = []
    for cid, (rep, members) in enumerate(cluster_centers):
        sub = df.iloc[members]
        # canonical name: longest from the cluster
        canon = sub.loc[sub["name"].str.len().idxmax(), "name"]
        row = {"product": canon, "n_shops": sub["shop"].nunique(), "n_rows": len(sub)}
        for shop in shop_names:
            shop_rows = sub[sub["shop"] == shop]
            if shop_rows.empty:
                row[f"{shop}_price"] = ""
                row[f"{shop}_url"] = ""
                row[f"{shop}_name"] = ""
            else:
                in_stock = shop_rows[shop_rows["in_stock"] == "yes"]
                pool = in_stock if not in_stock.empty else shop_rows
                priced = pool[pool["price_num"] > 0]
                pick = priced.sort_values("price_num").iloc[0] if not priced.empty else pool.iloc[0]
                row[f"{shop}_price"] = float(pick["price_num"]) if pick["price_num"] > 0 else ""
                row[f"{shop}_url"] = pick["permalink"]
                row[f"{shop}_name"] = pick["name"]
        rows.append(row)
    return pd.DataFrame(rows), shop_names


def write_outputs(matrix, shops):
    csv_path = os.path.join(HERE, "matrix.csv")
    matrix.to_csv(csv_path, index=False)
    print(f"wrote {csv_path}  ({len(matrix)} rows)")

    multi = matrix[matrix["n_shops"] >= 2].copy()
    multi.sort_values(["n_shops", "n_rows"], ascending=[False, False], inplace=True)
    print(f"products with >=2 shop matches: {len(multi)}")

    html_path = os.path.join(HERE, "matrix.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("""<!doctype html><html><head><meta charset="utf-8">
<title>BD electronics — cross-shop comparison</title>
<style>
body{font:13px/1.4 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e6e6e6;margin:0;padding:20px}
h1{font-size:22px;margin:0 0 6px}
.meta{color:#9aa0a6;margin-bottom:14px;font-size:12px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border:1px solid #262b36;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#161a22;color:#6ee7b7;position:sticky;top:0;z-index:1}
tr:nth-child(even) td{background:rgba(255,255,255,0.02)}
a{color:#93c5fd;text-decoration:none}a:hover{text-decoration:underline}
.price{font-weight:600;color:#34d399}
.empty{color:#444}
.product{max-width:380px}
.filter{margin:10px 0;padding:8px 12px;background:#161a22;border:1px solid #262b36;border-radius:8px}
input{background:#0b0d12;border:1px solid #262b36;color:#e6e6e6;padding:6px 10px;border-radius:6px;font:inherit;width:280px}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;background:rgba(110,231,183,.12);color:#6ee7b7;border:1px solid rgba(110,231,183,.3)}
</style></head><body>
<h1>BD electronics — cross-shop product matrix</h1>
""")
        f.write(f'<p class="meta">Showing {len(multi)} products that appear on 2+ shops (out of {len(matrix)} total clusters). Cluster matching: token-buckets + MiniLM cosine ≥ 0.72. Lowest in-stock price per shop is shown.</p>\n')
        f.write('<div class="filter"><input id="q" placeholder="filter by product name…" oninput="filt()"></div>\n')
        f.write("<table id=\"t\"><thead><tr><th>Product</th><th># shops</th>")
        for s in shops:
            f.write(f"<th>{s}</th>")
        f.write("</tr></thead><tbody>\n")

        for _, r in multi.iterrows():
            prod = html.escape(str(r["product"]))[:200]
            f.write(f'<tr><td class="product">{prod}</td><td>{int(r["n_shops"])}</td>')
            for s in shops:
                price = r.get(f"{s}_price", "")
                url = r.get(f"{s}_url", "")
                if price != "" and url:
                    f.write(f'<td><a href="{html.escape(str(url))}" target="_blank"><span class="price">৳ {float(price):.2f}</span></a></td>')
                else:
                    f.write('<td><span class="empty">—</span></td>')
            f.write("</tr>\n")
        f.write("""</tbody></table>
<script>
function filt(){
  const q = document.getElementById('q').value.toLowerCase();
  for (const tr of document.querySelectorAll('#t tbody tr')) {
    tr.style.display = tr.cells[0].textContent.toLowerCase().includes(q) ? '' : 'none';
  }
}
</script>
</body></html>
""")
    print(f"wrote {html_path}")


def main():
    df = load_all()
    df, centers = cluster(df, sim_threshold=0.72)
    matrix, shops = build_matrix(df, centers)
    write_outputs(matrix, shops)


if __name__ == "__main__":
    main()
