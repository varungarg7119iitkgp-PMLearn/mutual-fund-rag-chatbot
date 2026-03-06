## Phase 2 — Data Cleaning, Normalization & RAG Chunk Preparation

This module implements **Phase 2** of the architecture:

- Load the raw **per-fund JSON snapshots** generated in `phase1_ingestion/output/raw/`.
- Apply **validation and normalization** rules (categories, risk labels, dates, etc.).
- Generate a set of **RAG-ready chunks** (text + metadata) per fund, aligned with the requirements in `Requirements.md`.

### Goals

- Provide a clean, consistent representation of each fund that downstream systems (APIs, RAG, analytics) can rely on.
- Create semantically meaningful **chunks** that:
  - Are grounded entirely in the scraped data.
  - Carry rich metadata (fund ID, name, category, data type, last updated timestamp, source URLs).
  - Are ready for embedding and indexing in Phase 3 (Gemini RAG integration).

### Layout

- `phase2_processing/`
  - `README.md` — this file.
  - `src/`
    - `loader.py` — loads and parses raw snapshots from Phase 1.
    - `normalization.py` — validation and normalization helpers (categories, risk labels, dates).
    - `chunker.py` — converts normalized fund snapshots into RAG chunks.
    - `run_phase2.py` — CLI entrypoint to process all funds and write cleaned data + chunks.
  - `output/`
    - `clean/` — cleaned/normalized per-fund JSON (one file per fund).
    - `chunks/` — RAG chunks in JSONL format (one file per fund or combined, see below).
  - `tests/`
    - `test_loader.py` — tests for loading raw snapshots and mapping to models.
    - `test_normalization.py` — tests for date/risk/category normalization utilities.
    - `test_chunker.py` — tests for chunk generation structure and metadata.

### Outputs

After running Phase 2, you will have:

- **Cleaned fund snapshots** in `phase2_processing/output/clean/`:
  - Same high-level schema as Phase 1 (`FundSnapshot`), but:
    - Normalized category labels.
    - Normalized riskometer labels.
    - NAV dates in ISO format where possible.
    - Any obvious inconsistencies flagged or fixed where feasible.
- **RAG chunks** in `phase2_processing/output/chunks/`:
  - Each chunk is a JSON object with:
    - `chunk_id` — unique identifier.
    - `fund_id`, `fund_name`, `category`.
    - `data_type` — e.g., `overview`, `performance`, `risk`, `fees`, `portfolio`, `news`.
    - `text` — human-readable, deterministic text summarizing that aspect of the fund.
    - `metadata` — structured fields (NAV, returns, expense ratio, etc.) plus `last_updated_at` and `source_urls`.

These chunks will be the primary input to **Phase 3**, where we will embed them, index them, and hook them into Gemini for Retrieval‑Augmented Generation.

### Running Phase 2 (Conceptual)

From the project root, after completing Phase 1:

```bash
python -m phase1_ingestion.src.run_ingestion        # ensure raw data is fresh
python -m phase2_processing.src.run_phase2          # perform cleaning + chunking
```

This will:

- Read all JSON snapshots from `phase1_ingestion/output/raw/`.
- Produce normalized fund JSON under `phase2_processing/output/clean/`.
- Produce per-fund chunk files under `phase2_processing/output/chunks/`.

### Running Tests

From the project root:

```bash
pytest phase2_processing/tests
```

The Phase 2 tests are designed to:

- Not depend on re-running scrapers (they operate on synthetic snapshots).
- Ensure normalization utilities behave as expected.
- Ensure the generated chunks have the required fields and reasonable text/metadata.

