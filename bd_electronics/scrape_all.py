#!/usr/bin/env python3
"""Scrape three Bangladeshi electronics shops to per-shop CSVs.

Sites:
  - techshopbd.com         — sitemap-driven; per-product JSON-LD
  - makersbd.com           — /all-products?page=N HTML pagination
  - electronics.com.bd     — /category/<slug>/load?page=N JSON+HTML

Each writes:
  <shop>/products.csv   (id, sku, name, price, currency, in_stock, categories, short_description, permalink)
"""
import csv
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
HERE = os.path.dirname(os.path.abspath(__file__))

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def http_get(url, headers=None, retries=4):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"GET failed: {url} -- {last}")


def clean_text(s):
    if not s:
        return ""
    s = html.unescape(s)
    s = TAG_RE.sub(" ", s)
    return WS_RE.sub(" ", s).strip()


# -----------------------------------------------------------------------------
# techshopbd.com — sitemap → product page → JSON-LD
# -----------------------------------------------------------------------------
def scrape_techshopbd(out_dir):
    sm = http_get("https://techshopbd.com/sitemap.xml")
    urls = sorted(set(re.findall(r"https://techshopbd\.com/product/[^<\s]+", sm)))
    print(f"[techshopbd] sitemap: {len(urls)} products")

    out = os.path.join(out_dir, "products.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "sku", "name", "price", "currency", "in_stock", "categories", "short_description", "permalink"])
        for i, url in enumerate(urls, 1):
            try:
                body = http_get(url)
            except Exception as e:
                print(f"  [{i}/{len(urls)}] FAIL {url}: {e}", file=sys.stderr)
                continue
            blocks = re.findall(r'<script type="application/ld\+json">([^<]+)</script>', body)
            product = None
            crumbs = []
            for b in blocks:
                try:
                    data = json.loads(b)
                except json.JSONDecodeError:
                    continue
                graph = data.get("@graph") if isinstance(data, dict) else None
                nodes = graph if isinstance(graph, list) else [data]
                for n in nodes:
                    t = n.get("@type") if isinstance(n, dict) else None
                    if t == "Product":
                        product = n
                    elif t == "BreadcrumbList":
                        for it in n.get("itemListElement", []):
                            nm = (it.get("item") or {}).get("name") or it.get("name")
                            if nm and nm.lower() != "home":
                                crumbs.append(nm)
            if not product:
                continue
            offer = product.get("offers") or {}
            avail = offer.get("availability", "")
            in_stock = "yes" if "InStock" in avail else "no" if "OutOfStock" in avail else ""
            w.writerow([
                product.get("sku", "") or "",
                product.get("sku", "") or "",
                clean_text(product.get("name", "")),
                offer.get("price", ""),
                offer.get("priceCurrency", ""),
                in_stock,
                " | ".join(crumbs),
                clean_text(product.get("description", "")),
                url,
            ])
            if i % 50 == 0:
                print(f"  [{i}/{len(urls)}]")
                f.flush()
            time.sleep(0.15)
    print(f"[techshopbd] wrote {out}")


# -----------------------------------------------------------------------------
# makersbd.com — /all-products?page=N HTML
# -----------------------------------------------------------------------------
def scrape_makersbd(out_dir):
    base = "https://makersbd.com/all-products"
    out = os.path.join(out_dir, "products.csv")
    rows = 0
    seen = set()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "sku", "name", "price", "currency", "in_stock", "categories", "short_description", "permalink"])
        page = 1
        while True:
            url = f"{base}?page={page}"
            body = http_get(url)
            # Each product card has: anchor with /product/ slug → name; nearby ৳<price>
            anchors = list(re.finditer(
                r'href="(https://makersbd\.com/product/[^"]+)"[^>]*>\s*([^<][^<]{3,200})\s*</a>',
                body))
            if not anchors:
                print(f"[makersbd] page {page}: no products, stopping")
                break
            page_count = 0
            for m in anchors:
                purl = m.group(1)
                name = clean_text(m.group(2))
                if not name or purl in seen:
                    continue
                seen.add(purl)
                rest = body[m.end(): m.end() + 2500]
                price_m = re.search(r"৳\s*([0-9,.]+)", rest)
                price = price_m.group(1).replace(",", "") if price_m else ""
                slug = purl.rsplit("/", 1)[-1]
                w.writerow([slug, slug, name, price, "BDT", "yes", "", "", purl])
                rows += 1
                page_count += 1
            print(f"[makersbd] page {page}: +{page_count} (total {rows})")
            if page_count == 0:
                break
            f.flush()
            page += 1
            time.sleep(0.3)
    print(f"[makersbd] wrote {out} — {rows} rows")


# -----------------------------------------------------------------------------
# electronics.com.bd — /category/<slug>/load?page=N (JSON-wrapped HTML)
# -----------------------------------------------------------------------------
def scrape_electronics_com_bd(out_dir):
    home = http_get("https://electronics.com.bd/")
    cats = sorted(set(re.findall(r"https://electronics\.com\.bd/category/([a-z0-9-]+)", home)))
    cats = [c for c in cats if c not in ("home",)]
    print(f"[electronics.com.bd] {len(cats)} top-level categories")

    out = os.path.join(out_dir, "products.csv")
    seen = set()
    rows = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "sku", "name", "price", "currency", "in_stock", "categories", "short_description", "permalink"])
        for cat in cats:
            page = 1
            while True:
                url = f"https://electronics.com.bd/category/{cat}/load?page={page}"
                try:
                    body = http_get(url, headers={"X-Requested-With": "XMLHttpRequest"})
                except Exception as e:
                    print(f"  [{cat} p{page}] FAIL {e}", file=sys.stderr)
                    break
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    break
                hbody = payload.get("html") or ""
                if not hbody.strip():
                    break
                # Each card: anchor with class="image" → product slug; nearby price block
                anchors = list(re.finditer(
                    r'<a href="(https://electronics\.com\.bd/[a-z0-9-]+)"[^>]*class="image"[^>]*>\s*<img[^>]*alt="([^"]+)"',
                    hbody))
                page_count = 0
                for m in anchors:
                    purl = m.group(1)
                    name = clean_text(m.group(2))
                    if purl in seen:
                        continue
                    seen.add(purl)
                    rest = hbody[m.end(): m.end() + 4000]
                    new_m = re.search(r'class="mn-price-new"[^>]*>([^<]+)', rest)
                    old_m = re.search(r'class="mn-price-old"[^>]*>(?:\s*<[^>]+>)?([^<]+)', rest)
                    price_text = clean_text(new_m.group(1)) if new_m else (clean_text(old_m.group(1)) if old_m else "")
                    price_num = re.search(r"([0-9,]+(?:\.[0-9]+)?)", price_text or "")
                    price = price_num.group(1).replace(",", "") if price_num else ""
                    model_m = re.search(r"Model:\s*([A-Za-z0-9_-]+)", rest)
                    sku = model_m.group(1) if model_m else purl.rsplit("/", 1)[-1]
                    slug = purl.rsplit("/", 1)[-1]
                    w.writerow([slug, sku, name, price, "BDT", "yes", cat, "", purl])
                    rows += 1
                    page_count += 1
                print(f"  [{cat} p{page}] +{page_count} (total {rows})")
                f.flush()
                if page_count == 0:
                    break
                page += 1
                time.sleep(0.3)
    print(f"[electronics.com.bd] wrote {out} — {rows} rows")


def main():
    targets = {
        "techshopbd": scrape_techshopbd,
        "makersbd": scrape_makersbd,
        "electronics_com_bd": scrape_electronics_com_bd,
    }
    if len(sys.argv) > 1:
        which = sys.argv[1]
        d = os.path.join(HERE, which)
        os.makedirs(d, exist_ok=True)
        targets[which](d)
        return
    for name, fn in targets.items():
        d = os.path.join(HERE, name)
        os.makedirs(d, exist_ok=True)
        try:
            fn(d)
        except Exception as e:
            print(f"!! {name} failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
