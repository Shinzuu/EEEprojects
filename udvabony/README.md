# udvabony product RAG

Local semantic search over 4648 products scraped from https://udvabony.com.

## Files

- `products.csv` — raw scrape (id, sku, name, price, currency, in_stock, categories, short_description, permalink)
- `scrape.py` — re-scrape from the WooCommerce Store API
- `analyze.py` — quick CSV stats
- `build_index.py` — build FAISS index + meta.csv (run once)
- `search.py` — query the index from CLI
- `index.faiss`, `meta.csv` — generated artifacts

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install sentence-transformers faiss-cpu pandas numpy
.venv/bin/python build_index.py
```

## Usage

```bash
.venv/bin/python search.py "esp32 dev board"
.venv/bin/python search.py "10k ohm 1/4 watt resistor" -k 5 --max-price 5
.venv/bin/python search.py "ultrasonic sensor" --category sensors --in-stock
.venv/bin/python search.py "lipo 3.7v" --min-price 100 --max-price 500
```

Flags: `-k`, `--category` (substring), `--min-price`, `--max-price`, `--in-stock`.

Embeddings: `sentence-transformers/all-MiniLM-L6-v2` (384d). Index is cosine via L2-normalized inner product.
