from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import json

from loguru import logger

from phase1_ingestion.src.models import (
    FundSnapshot,
    FundIdentity,
    NavInfo,
    ReturnsInfo,
    RiskInfo,
    AssetAllocation,
    Holding,
    PortfolioInfo,
    MinInvestment,
    OperationsInfo,
    FundManagerInfo,
    NewsItem,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "phase1_ingestion" / "output" / "raw"


def load_raw_snapshot(path: Path) -> FundSnapshot:
    """Load a single raw JSON snapshot into a FundSnapshot instance."""
    with path.open(encoding="utf-8") as f:
        data: Dict = json.load(f)

    # Reconstruct nested dataclasses so Phase 2 code can rely on attributes/types.
    identity = FundIdentity(**data["identity"])

    nav = NavInfo(**data.get("nav", {}))
    returns = ReturnsInfo(**data.get("returns", {}))
    risk = RiskInfo(**data.get("risk", {}))

    portfolio_data = data.get("portfolio", {}) or {}
    asset_alloc = AssetAllocation(**portfolio_data.get("asset_allocation", {}) or {})
    top_holdings: List[Holding] = []
    for h in portfolio_data.get("top_holdings", []) or []:
        if isinstance(h, dict):
            top_holdings.append(Holding(**h))
        else:
            top_holdings.append(h)
    portfolio = PortfolioInfo(
        asset_allocation=asset_alloc,
        top_holdings=top_holdings,
        sector_allocation=portfolio_data.get("sector_allocation", {}) or {},
        turnover_ratio=portfolio_data.get("turnover_ratio"),
    )

    operations_data = data.get("operations", {}) or {}
    min_inv = MinInvestment(**operations_data.get("min_investment", {}) or {})
    operations = OperationsInfo(
        expense_ratio=operations_data.get("expense_ratio"),
        exit_load=operations_data.get("exit_load"),
        min_investment=min_inv,
        taxation=operations_data.get("taxation"),
    )

    fm_data = data.get("fund_manager", {}) or {}
    fund_manager = FundManagerInfo(
        name=fm_data.get("name"),
        tenure_years=fm_data.get("tenure_years"),
        experience_summary=fm_data.get("experience_summary"),
        other_funds_managed=fm_data.get("other_funds_managed", []) or [],
    )

    news_items: List[NewsItem] = []
    for n in data.get("news_context", []) or []:
        if isinstance(n, dict):
            news_items.append(NewsItem(**n))
        else:
            news_items.append(n)

    snapshot = FundSnapshot(
        identity=identity,
        nav=nav,
        returns=returns,
        risk=risk,
        portfolio=portfolio,
        operations=operations,
        fund_manager=fund_manager,
        news_context=news_items,
        source_urls=data.get("source_urls", []),
        last_scraped_at=data.get("last_scraped_at", ""),
    )
    return snapshot


def load_all_snapshots(raw_dir: Path = RAW_DIR) -> Dict[str, FundSnapshot]:
    """
    Load all raw snapshots produced in Phase 1.

    Returns a dict mapping a file-safe fund key (e.g., slug based on filename)
    to a FundSnapshot instance.
    """
    if not raw_dir.exists():
        raise RuntimeError(f"Raw snapshot directory not found: {raw_dir}")

    snapshots: Dict[str, FundSnapshot] = {}
    for path in raw_dir.glob("*.json"):
        snapshot = load_raw_snapshot(path)
        key = path.stem  # e.g. HDFC_Hybrid_Equity_Fund_Direct_Growth
        snapshots[key] = snapshot
        logger.info(f"Loaded snapshot for fund '{snapshot.identity.name}' from {path}")
    return snapshots

