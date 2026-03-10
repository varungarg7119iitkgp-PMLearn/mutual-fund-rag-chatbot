# Phase 0 — Foundations & Configuration

## Purpose

Define the curated fund universe, data field requirements, and scraping targets before any code is written.

## Actual Code Location

All Phase 0 artifacts live in:

```
config/
├── fund_universe.csv            # 20 curated funds (5 per category: Equity, Debt, Hybrid, Commodity)
└── scraping_reference_guide.md  # Field-by-field scraping requirements and source mapping
```

## Key Deliverables

- **Fund Universe CSV** — Master list of 20 funds with Name, Category, Groww URL, ISIN, and search keywords.
- **Scraping Reference Guide** — Documents every data field to extract (NAV, returns, risk metrics, holdings, operations, fund manager, news) with source URLs and fallback strategies.

## Related Phases

- **Phase 1** (`phase1_ingestion/`) consumes `fund_universe.csv` to know which funds to scrape.
- **Phase 4** (`phase4/`) uses fund names/keywords from the CSV for out-of-corpus detection guardrails.
- **Backend** (`backend/app/rag/router.py`) loads the CSV at runtime for guardrail checks.
