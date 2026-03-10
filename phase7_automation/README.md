# Phase 7 — Scheduling, Refresh & Automation

## Purpose

Automate the daily data refresh pipeline — scrape fresh fund data, clean/chunk it, rebuild the RAG index, and commit updated files to trigger a Railway redeploy.

## Actual Code Location

```
scripts/
└── refresh_pipeline.py          # Unified Python script: scrape → clean → chunk → rebuild index

.github/
└── workflows/
    └── refresh-data.yml         # GitHub Actions workflow (daily cron + manual trigger)
```

## How It Works

1. **Trigger** — Runs daily at 06:30 UTC via cron schedule, or manually from the GitHub Actions tab.
2. **Step 1: Scrape** — Calls Phase 1's `run_scraping_session()` to fetch latest data from Groww for all 20 funds using Playwright.
3. **Step 2: Clean & Chunk** — Calls Phase 2's `run_phase2()` to normalize and generate RAG-ready text chunks.
4. **Step 3: Rebuild Index** — Calls the indexer's `build_index()` to regenerate the TF-IDF matrix from updated chunks.
5. **Auto-commit** — If any data files changed, the workflow commits and pushes them to `master`, which triggers a Railway redeploy with fresh data.

## Workflow Configuration

| Setting | Value |
|---------|-------|
| Schedule | `cron: '30 6 * * *'` (daily at 06:30 UTC) |
| Manual trigger | `workflow_dispatch` (Run workflow button) |
| Python version | 3.11 |
| Browser | Playwright Chromium (installed in CI) |
| Secret required | `GEMINI_API_KEY` (GitHub repository secret) |

## Pipeline Options

```bash
# Full pipeline (scrape + process + index)
python scripts/refresh_pipeline.py

# Skip scraping (reprocess existing data only)
python scripts/refresh_pipeline.py --skip-scrape
```

## Related Phases

- **Phase 1** (`phase1_ingestion/`) — Scraping logic called by the pipeline.
- **Phase 2** (`phase2_processing/`) — Cleaning/chunking logic called by the pipeline.
- **Phase 3** (`phase3_llm_rag/`) — Index rebuild and the backend that serves the updated data.
- **Phase 6** (`phase6_deployment/`) — Auto-commit triggers Railway redeploy.
