from __future__ import annotations

from pathlib import Path
from typing import List
import json

from loguru import logger
from playwright.sync_api import sync_playwright

from .config_loader import load_fund_universe, validate_fund_universe, FUND_UNIVERSE_PATH
from .models import FundSnapshot, FundIdentity
from .html_parsers import (
    parse_nav_and_date,
    parse_returns_table,
    parse_risk_section,
    parse_news_section,
    parse_groww_next_data,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "phase1_ingestion" / "output" / "raw"


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def scrape_fund_page(page_html: str, fund_name: str, category: str, url: str, keywords: List[str]) -> FundSnapshot:
    """
    Create a FundSnapshot from the HTML of a single fund page.

    For Groww pages, this prefers the structured __NEXT_DATA__ JSON (mfServerSideData)
    and falls back to generic HTML heuristics only if that is unavailable.
    """
    # First try to use Groww's structured JSON, which should give us the richest data.
    snapshot = parse_groww_next_data(
        html=page_html,
        fallback_name=fund_name,
        fallback_category=category,
        url=url,
        keywords=keywords,
    )
    if snapshot is not None:
        return snapshot

    # Fallback: generic HTML-based scraping (less complete, but source-agnostic).
    identity = FundIdentity(
        fund_id=None,
        name=fund_name,
        category=category,
        amc_name=None,
        benchmark_name=None,
        plan_label=None,
        keywords=keywords,
    )

    nav_info = parse_nav_and_date(page_html)
    returns_info = parse_returns_table(page_html)
    risk_info = parse_risk_section(page_html)
    news_items = parse_news_section(page_html)

    return FundSnapshot(
        identity=identity,
        nav=nav_info,
        returns=returns_info,
        risk=risk_info,
        news_context=news_items,
        source_urls=[url],
    )


def run_scraping_session() -> None:
    """Run a full scraping session for all configured funds."""
    funds = load_fund_universe(FUND_UNIVERSE_PATH)
    validate_fund_universe(funds)
    ensure_output_dir()

    logger.info(f"Starting scraping session for {len(funds)} funds")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for fund in funds:
            logger.info(f"Scraping fund: {fund.name} ({fund.category}) from {fund.url}")
            try:
                page.goto(fund.url, wait_until="networkidle")
                html = page.content()
                snapshot = scrape_fund_page(
                    page_html=html,
                    fund_name=fund.name,
                    category=fund.category,
                    url=fund.url,
                    keywords=fund.keywords,
                )

                # Write JSON snapshot
                file_safe_name = fund.name.replace(" ", "_").replace("/", "_")
                out_path = OUTPUT_DIR / f"{file_safe_name}.json"
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(snapshot.to_dict(), f, ensure_ascii=False, indent=2)

                logger.info(f"Wrote snapshot: {out_path}")
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"Error scraping {fund.name}: {exc}")

        browser.close()
    logger.info("Scraping session completed.")

