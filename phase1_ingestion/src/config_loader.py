"""
Load and validate the curated fund universe from config/fund_universe.csv.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from loguru import logger


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FUND_UNIVERSE_PATH = PROJECT_ROOT / "config" / "fund_universe.csv"


@dataclass
class FundEntry:
    name: str
    category: str
    url: str
    keywords: List[str] = field(default_factory=list)


def load_fund_universe(csv_path: Path) -> List[FundEntry]:
    """Load fund entries from fund_universe.csv."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Fund universe CSV not found at {csv_path}")

    entries: List[FundEntry] = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name of Fund") or "").strip()
            category = (row.get("Type of Fund") or "").strip()
            url = (row.get("URL on Groww") or "").strip()
            kw_str = row.get("Keywords") or ""
            keywords = [k.strip() for k in kw_str.split(",") if k.strip()]

            if not name or not url:
                logger.warning(f"Skipping row with missing name or URL: {row}")
                continue

            entries.append(FundEntry(name=name, category=category, url=url, keywords=keywords))

    logger.info(f"Loaded {len(entries)} funds from {csv_path}")
    return entries


def validate_fund_universe(funds: List[FundEntry]) -> None:
    """Validate that we have exactly 20 funds with 5 per category."""
    if len(funds) != 20:
        raise ValueError(f"Expected 20 funds, got {len(funds)}")

    category_counts = Counter(f.category for f in funds)
    expected_categories = {"Commodity", "Debt", "Hybrid", "Equity"}

    if set(category_counts.keys()) != expected_categories:
        raise ValueError(
            f"Expected categories {expected_categories}, got {set(category_counts.keys())}"
        )

    for cat, count in category_counts.items():
        if count != 5:
            raise ValueError(f"Expected 5 funds in category '{cat}', got {count}")

    logger.info("Fund universe validation passed: 20 funds, 5 per category.")
