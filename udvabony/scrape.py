#!/usr/bin/env python3
import csv
import json
import re
import sys
import time
import urllib.request
import urllib.error

BASE = "https://udvabony.com/wp-json/wc/store/v1/products"
PER_PAGE = 100
OUT = "/home/shinzuu/Documents/EEEprojects/udvabony/products.csv"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_html(s):
    if not s:
        return ""
    s = TAG_RE.sub(" ", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#038;", "&")
    s = s.replace("&ldquo;", '"').replace("&rdquo;", '"')
    s = WS_RE.sub(" ", s).strip()
    return s


def fetch(page):
    url = f"{BASE}?per_page={PER_PAGE}&page={page}&orderby=id&order=asc"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                total_pages = int(r.headers.get("X-WP-TotalPages", "0"))
                total = int(r.headers.get("X-WP-Total", "0"))
                data = json.loads(r.read().decode("utf-8"))
                return data, total_pages, total
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  retry {attempt+1} page {page}: {e}", file=sys.stderr)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed page {page}")


def price_of(p):
    pr = p.get("prices") or {}
    raw = pr.get("price")
    if raw is None or raw == "":
        return ""
    minor = pr.get("currency_minor_unit", 2) or 0
    try:
        n = int(raw) / (10 ** int(minor))
        return f"{n:.2f}"
    except (ValueError, TypeError):
        return str(raw)


def categories_of(p):
    cats = p.get("categories") or []
    return " | ".join(c.get("name", "") for c in cats if c.get("name"))


def main():
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "id", "sku", "name", "price", "currency",
            "in_stock", "categories", "short_description", "permalink",
        ])
        page = 1
        total_pages = None
        total = None
        seen = 0
        while True:
            data, tp, tot = fetch(page)
            if total_pages is None:
                total_pages = tp
                total = tot
                print(f"total products: {total}, pages: {total_pages}")
            if not data:
                break
            for p in data:
                pr = p.get("prices") or {}
                w.writerow([
                    p.get("id", ""),
                    p.get("sku", ""),
                    strip_html(p.get("name", "")),
                    price_of(p),
                    pr.get("currency_code", ""),
                    "yes" if p.get("is_in_stock") else "no",
                    categories_of(p),
                    strip_html(p.get("short_description", "")),
                    p.get("permalink", ""),
                ])
            seen += len(data)
            print(f"page {page}/{total_pages} got {len(data)} (total {seen})")
            f.flush()
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.3)
    print(f"done. wrote {seen} rows to {OUT}")


if __name__ == "__main__":
    main()
