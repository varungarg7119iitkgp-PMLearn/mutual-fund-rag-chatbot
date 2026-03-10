# Phase 8 — Observability, Analytics & Iteration

## Purpose

Track query patterns, surface trending funds, monitor data freshness, and provide analytics endpoints for future dashboard integration.

## Actual Code Location

Analytics code lives inside the deployed backend:

```
backend/app/analytics/
├── __init__.py
├── tracker.py                   # AnalyticsTracker class — in-memory query logging
└── router.py                    # API endpoints: /analytics/trending, /summary, /data-freshness
```

Integration point in the chat endpoint:

```
backend/app/rag/router.py        # Calls tracker.record_query() on every chat request
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analytics/trending?top_n=5` | GET | Top N most-asked-about funds (rolling 24h window) |
| `/analytics/summary` | GET | Total queries, outcome breakdown, avg latency |
| `/analytics/data-freshness` | GET | Last scrape timestamp from `rag_index/metadata.json` |

## How It Works

1. **Query Recording** — Every `/chat` request records: question length, detected fund names, outcome (answered/refused/error), and latency.
2. **Fund Detection** — `detect_funds_in_query()` cross-references the question against fund names and keywords from `config/fund_universe.csv`.
3. **Trending Calculation** — `get_trending_funds()` counts fund mentions in the rolling 24-hour window and returns the top N.
4. **Data Freshness** — Reads the `last_built` timestamp from the RAG index metadata to report when data was last refreshed.

## Current Limitations

- **In-memory storage** — Analytics reset on each Railway redeploy. Acceptable for MVP; would move to a database for persistence at scale.
- **No PII stored** — Only question length is recorded, never the actual question text.
- **Max 5,000 records** — Oldest entries are evicted via a bounded deque.

## Related Phases

- **Phase 3** (`phase3_llm_rag/`) — The chat endpoint that feeds data to the tracker.
- **Phase 7** (`phase7_automation/`) — Data refreshes update the freshness timestamp.
