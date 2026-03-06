from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar
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

T = TypeVar("T")


def _safe_init(cls: Type[T], data: Dict[str, Any]) -> T:
    """Construct a dataclass instance, silently dropping unknown fields."""
    known = {f.name for f in dataclasses.fields(cls)}
    filtered = {k: v for k, v in data.items() if k in known}
    return cls(**filtered)


def load_raw_snapshot(path: Path) -> FundSnapshot:
    """Load a single raw JSON snapshot into a FundSnapshot instance."""
    with path.open(encoding="utf-8") as f:
        data: Dict = json.load(f)

    identity = _safe_init(FundIdentity, data.get("identity", {}))

    nav = _safe_init(NavInfo, data.get("nav", {}))
    returns = _safe_init(ReturnsInfo, data.get("returns", {}))
    risk = _safe_init(RiskInfo, data.get("risk", {}))

    portfolio_data = data.get("portfolio", {}) or {}
    asset_alloc = _safe_init(AssetAllocation, portfolio_data.get("asset_allocation", {}) or {})
    top_holdings: List[Holding] = []
    for h in portfolio_data.get("top_holdings", []) or []:
        if isinstance(h, dict):
            top_holdings.append(_safe_init(Holding, h))
        else:
            top_holdings.append(h)
    portfolio = PortfolioInfo(
        asset_allocation=asset_alloc,
        top_holdings=top_holdings,
        sector_allocation=portfolio_data.get("sector_allocation", {}) or {},
        turnover_ratio=portfolio_data.get("turnover_ratio"),
    )

    operations_data = data.get("operations", {}) or {}
    min_inv = _safe_init(MinInvestment, operations_data.get("min_investment", {}) or {})
    operations = OperationsInfo(
        expense_ratio=operations_data.get("expense_ratio"),
        exit_load=operations_data.get("exit_load"),
        min_investment=min_inv,
        taxation=operations_data.get("taxation"),
    )

    fm_data = data.get("fund_manager", {}) or {}
    fund_manager = _safe_init(FundManagerInfo, fm_data)

    news_items: List[NewsItem] = []
    for n in data.get("news_context", []) or []:
        if isinstance(n, dict):
            news_items.append(_safe_init(NewsItem, n))
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

