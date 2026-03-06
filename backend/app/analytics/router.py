"""
Analytics API endpoints for observability and the Trending Funds module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter
from loguru import logger

from .tracker import tracker

router = APIRouter(prefix="/analytics", tags=["analytics"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@router.get("/trending")
async def trending_funds(top_n: int = 5) -> List[Dict[str, object]]:
    """Return the top-N most queried funds in the last 24 hours."""
    return tracker.get_trending_funds(top_n=min(top_n, 20))


@router.get("/summary")
async def analytics_summary() -> Dict[str, object]:
    """Return overall query analytics (anonymized)."""
    return tracker.get_summary()


@router.get("/data-freshness")
async def data_freshness() -> Dict[str, Any]:
    """
    Report the freshness of scraped data by reading last_scraped_at
    from the RAG index metadata.
    """
    index_meta_path = PROJECT_ROOT / "backend" / "rag_index" / "metadata.json"

    if not index_meta_path.exists():
        return {"status": "no_index", "funds": []}

    with index_meta_path.open(encoding="utf-8") as f:
        records = json.load(f)

    fund_freshness: Dict[str, str] = {}
    for rec in records:
        meta = rec.get("metadata") or {}
        fund_name = meta.get("fund_name") or meta.get("identity_name") or "Unknown"
        ts = meta.get("last_scraped_at") or ""

        if fund_name not in fund_freshness or ts > fund_freshness.get(fund_name, ""):
            fund_freshness[fund_name] = ts

    funds_list = [
        {"fund_name": name, "last_scraped_at": ts}
        for name, ts in sorted(fund_freshness.items())
    ]

    all_timestamps = [ts for ts in fund_freshness.values() if ts]
    oldest = min(all_timestamps) if all_timestamps else None
    newest = max(all_timestamps) if all_timestamps else None

    return {
        "status": "ok",
        "total_funds_indexed": len(fund_freshness),
        "oldest_scrape": oldest,
        "newest_scrape": newest,
        "funds": funds_list,
    }
