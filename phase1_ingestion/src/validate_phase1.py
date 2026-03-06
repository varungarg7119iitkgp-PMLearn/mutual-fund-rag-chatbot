"""
Validation helpers for Phase 1 outputs.

Run this AFTER a scraping session to perform basic integrity checks:

    python -m phase1_ingestion.src.validate_phase1

Checks performed:
- All URLs in `config/fund_universe.csv` respond without a 404.
- All JSON snapshots in `phase1_ingestion/output/raw/` have a non-null NAV value.
"""

from __future__ import annotations

from pathlib import Path
from typing import List
import json

import httpx
from loguru import logger

from .config_loader import load_fund_universe, FUND_UNIVERSE_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "phase1_ingestion" / "output" / "raw"


def check_urls_not_404() -> None:
    funds = load_fund_universe(FUND_UNIVERSE_PATH)
    logger.info("Checking fund URLs for 404 responses...")
    with httpx.Client(follow_redirects=True, timeout=15) as client:
        for fund in funds:
            resp = client.get(fund.url)
            if resp.status_code == 404:
                raise RuntimeError(f"URL returned 404 for fund '{fund.name}': {fund.url}")
            logger.info(f"OK {resp.status_code} - {fund.url}")


def check_nav_not_null() -> None:
    if not OUTPUT_DIR.exists():
        raise RuntimeError(f"Output directory not found: {OUTPUT_DIR}. Run the scraper first.")

    logger.info("Checking that all scraped snapshots have non-null NAV values...")
    missing_nav: List[str] = []
    for path in OUTPUT_DIR.glob("*.json"):
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        nav = (data.get("nav") or {}).get("value")
        if nav is None:
            missing_nav.append(path.name)

    if missing_nav:
        raise RuntimeError(
            "The following snapshot files have null NAV values:\n"
            + "\n".join(f"- {name}" for name in missing_nav)
        )
    logger.info("All snapshots have non-null NAV values.")


def main() -> None:
    check_urls_not_404()
    check_nav_not_null()
    logger.info("Phase 1 validation completed successfully.")


if __name__ == "__main__":
    main()

