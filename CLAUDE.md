# EEEprojects

Personal electronics workbench. The user (Shinzuu, BD-region) builds DIY hardware — pedals, mics, clocks — and sources parts locally from Bangladeshi online shops. Everything in this repo is geared to that workflow.

## What lives here

- **`udvabony/`** — scraped catalog of <https://udvabony.com> (4648 products) plus a local FAISS RAG built on `sentence-transformers/all-MiniLM-L6-v2`. This was the original supplier scrape and is the workhorse search index when picking parts.
- **`bd_electronics/`** — multi-shop scraper that adds two more BD shops (makersbd.com, electronics.com.bd) and produces a cross-shop comparison matrix. ~6900 products total, 307 confirmed on 2+ shops.
- **`1.usb mic/`** — DIY USB condenser microphone build. Reference docs from the DIY Perks + ElectroNoobs videos and a v2 validated schematic with every BOM row linked to udvabony.
- **`2.digital clock/`** — ESP32 + MAX7219 4×(8×8) WiFi clock, 18650-powered. Spec + Arduino sketch + linked BOM.

GitHub: <https://github.com/Shinzuu/EEEprojects>

## How the catalog scrape works (udvabony)

The site is WordPress + WooCommerce. **WebFetch is blocked by Cloudflare (403)**, but the WooCommerce Store API is open and unauthenticated. Use a browser User-Agent string and hit:

```
GET https://udvabony.com/wp-json/wc/store/v1/products?per_page=100&page=N
```

Response headers carry `X-WP-Total` and `X-WP-TotalPages` so pagination is exact. Prices come back in minor units (e.g. `9900` BDT minor = 99.00 BDT) — divide by `10 ** currency_minor_unit`. Categories arrive as a list of `{id,name,slug,link}` objects. The scraper at `udvabony/scrape.py` handles all of this with retries and per-page flushing to CSV.

`udvabony/build_index.py` then encodes `name | categories | short_description` for each row, L2-normalises, writes a FAISS `IndexFlatIP`. `udvabony/search.py` is the CLI; it accepts `--category`, `--in-stock`, `--max-price`, `--min-price`, `-k`. **Use this instead of WebFetch when picking parts** — it is the source of truth for what's locally available.

## How the multi-shop scrape works (bd_electronics)

Each BD shop exposes a different surface:

- **makersbd.com** — server-rendered `/all-products?page=N`. Parse anchor tags + nearby `৳<price>` regex.
- **electronics.com.bd** — OpenCart with JS-rendered category pages, but it has an internal JSON loader at `/category/<slug>/load?page=N` that returns `{html: "..."}`. The HTML uses `mn-price-new` / `mn-price-old` classes; SKU is in a `Model: <id>` text block. We probe `Cloudflare 500` on its sitemap, so we walk the homepage's category list instead. Prices are now correctly captured (1839 / 1841 rows).
- **techshopbd.com** — sitemap-driven (2264 URLs) with one HTTP request per product page to read JSON-LD. **Removed from the active scrape on 2026-04-26** because the per-product fetch was too slow (~150 ms × 2264 = 6+ min) and the user prefers fast iteration. The scraper code is still in `bd_electronics/scrape_all.py` if anyone wants to revive it.

`bd_electronics/build_matrix.py` clusters all rows across shops:
1. Pull strong "part-number" tokens from each name (e.g. `NE5532`, `MAX7219`, `18650`, `TP4056`).
2. Bucket rows that share at least one strong token.
3. Within each bucket, encode names with MiniLM and merge rows greedily where cosine sim ≥ 0.72.
4. For each cluster, pick the longest name as canonical and the lowest in-stock priced row from each shop.
5. Emit `matrix.csv` and `matrix.html` (sortable, filterable, links open the shop pages).

`bd_electronics/build_index.py` is the same idea as the udvabony index but unifies all three shops into `bd_index.faiss` + `bd_meta.csv` with a `shop` column. `bd_electronics/search.py` exposes `--shop` filter on top of the others.

## How parts get picked (the user's workflow)

The user is **building hardware they will physically buy**. Two non-negotiables:

1. **Every BOM line must be sourceable from a BD shop.** "Use a THAT2180" is useless if udvabony / makersbd / electronics.com.bd don't stock it. When designing, query the RAG for each component and pick from what's actually in stock. If the ideal part is missing, substitute and explain the trade-off.
2. **Audio-grade parts in audio-signal paths.** The user explicitly called out that `LM358` is mediocre. Use NE5532 (4.5 nV/√Hz) for mic preamps and signal paths. TL072 is OK for guitar-pedal duty and DC sidechains. LM358 is banished from anything you'd hear. Don't mix part numbers carelessly (don't use TL081 in design and TL071 in BOM — pick one and stick to it).

When picking a part, **always grep the catalog before recommending**:

```bash
cd /home/shinzuu/Documents/EEEprojects/udvabony
.venv/bin/python search.py "ne5532" -k 5 --in-stock
```

Or for direct value lookups, pandas on `meta.csv` is faster than the embedding search:

```python
import pandas as pd
df = pd.read_csv('udvabony/meta.csv')
df = df[df.in_stock=='yes']
df[df['name'].str.contains('1M', case=False) & df['name'].str.contains('1/4w')]
```

## Project documents are HTML, not Markdown

For build specs (`1.usb mic/schematic.html`, `2.digital clock/schematic.html`) the user wanted clickable BOM tables straight to the shop, dark/light auto theme, sticky tables — so the canonical artefact is **a single self-contained HTML file** with inline CSS, opened locally in Chrome. Don't replace these with `.md` unless asked. Follow the same template if creating a new project.

The mic project went through a v1 → v2 cycle because v1 had:
1. Stage 2 inverting topology drawn but labelled non-inverting (gain math wrong).
2. JFET gate with no DC return path (R3 + R4 both terminating at source).
3. Source resistor R2 = 2.2 k that put the JFET into saturation on ±9 V rails.
4. TL072 used as a comparator → phase reversal near the negative rail.

These were caught by an explicit **validation pass** (skeptical agent reads the schematic and looks for unbuildable / broken bits). For any non-trivial schematic, do that pass before building HTML / committing. The `simplify` skill is also available.

## Shell / power architecture defaults for the user

- Linux (Ubuntu 24.04, zsh). PEP 668 system Python — must use a `venv`. The udvabony venv at `udvabony/.venv` already has sentence-transformers / faiss-cpu / pandas / numpy installed.
- The user has isolated DC-DC modules in 5 V / 9 V / 12 V single-rail. For audio designs we synthesize ±9 V from two single-rails by inverting one — but only if the modules are actually galvanically isolated. Recommended: buy a real dual-rail NMA0509SC instead.
- Region: BD. Currency: BDT. NTP timezone defaults to `<+06>-6` (Asia/Dhaka, no DST).

## Communication style

- The user enables a **caveman mode** via SessionStart hook: drop articles/filler/pleasantries/hedging, fragments are fine, terse pattern `[thing] [action] [reason]`. Keep code/commits/security writing normal.
- Auto mode: when active, execute autonomously, don't ask questions for routine decisions, prefer action over planning. Still confirm before destructive operations (force push, dropping data, etc).
- The user often messages while a long-running task is in progress. Treat new messages as live input, finish the current task quickly or pause it, address the new message.

## Git defaults

- Remote: `https://github.com/Shinzuu/EEEprojects` (HTTPS, the user has credentials cached).
- Always commit with `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` — except when commits are produced via the in-conversation `git -c user.email=...` form during scripted commits.
- `.gitignore` keeps `.venv/`, scrape logs, and Python cache out. Don't commit log files.
- The user said "stage everything" once; that is **not** a standing rule. Confirm scope each time you `git add`, especially for large data files.

## Useful one-liners

```bash
# Search udvabony catalog (most-used)
cd /home/shinzuu/Documents/EEEprojects/udvabony
.venv/bin/python search.py "your query" -k 5 --in-stock

# Search across all 3 shops
cd /home/shinzuu/Documents/EEEprojects/bd_electronics
/home/shinzuu/Documents/EEEprojects/udvabony/.venv/bin/python search.py "your query" --shop udvabony

# Rebuild the cross-shop matrix after re-scraping
cd /home/shinzuu/Documents/EEEprojects/bd_electronics
/home/shinzuu/Documents/EEEprojects/udvabony/.venv/bin/python build_matrix.py

# Open both schematics in Chrome
google-chrome "/home/shinzuu/Documents/EEEprojects/1.usb mic/schematic.html" \
              "/home/shinzuu/Documents/EEEprojects/2.digital clock/schematic.html"
```
