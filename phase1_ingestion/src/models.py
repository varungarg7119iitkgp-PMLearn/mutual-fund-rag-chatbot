"""
Data models for Phase 1 fund snapshots.

These dataclasses represent the structured output of scraping a single
mutual fund page. They are serialized to JSON for persistence and consumed
by Phase 2 for cleaning and chunk generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class FundIdentity:
    fund_id: Optional[str] = None
    name: str = ""
    category: str = ""
    amc_name: Optional[str] = None
    benchmark_name: Optional[str] = None
    plan_label: Optional[str] = None
    keywords: List[str] = field(default_factory=list)


@dataclass
class NavInfo:
    value: Optional[float] = None
    date: Optional[str] = None
    high_52w: Optional[float] = None
    high_52w_date: Optional[str] = None
    low_52w: Optional[float] = None
    low_52w_date: Optional[str] = None


@dataclass
class ReturnsInfo:
    one_year: Optional[float] = None
    three_year: Optional[float] = None
    five_year: Optional[float] = None
    since_inception: Optional[float] = None
    benchmark_one_year: Optional[float] = None
    benchmark_three_year: Optional[float] = None
    benchmark_five_year: Optional[float] = None
    category_avg_one_year: Optional[float] = None
    category_avg_three_year: Optional[float] = None
    category_avg_five_year: Optional[float] = None


@dataclass
class RiskInfo:
    riskometer: Optional[str] = None
    standard_deviation: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    beta: Optional[float] = None
    alpha: Optional[float] = None


@dataclass
class Holding:
    name: str = ""
    percentage: Optional[float] = None
    weight_pct: Optional[float] = None
    sector: Optional[str] = None


@dataclass
class AssetAllocation:
    equity: Optional[float] = None
    debt: Optional[float] = None
    cash: Optional[float] = None
    others: Optional[float] = None


@dataclass
class PortfolioInfo:
    top_holdings: List[Holding] = field(default_factory=list)
    asset_allocation: Optional[AssetAllocation] = None
    total_stocks: Optional[int] = None
    total_bonds: Optional[int] = None
    sector_allocation: Optional[Dict[str, Any]] = None
    turnover_ratio: Optional[float] = None


@dataclass
class MinInvestment:
    sip: Optional[float] = None
    lumpsum: Optional[float] = None


@dataclass
class OperationsInfo:
    expense_ratio: Optional[float] = None
    exit_load: Optional[str] = None
    min_investment: Optional[MinInvestment] = None
    fund_size_cr: Optional[float] = None
    launch_date: Optional[str] = None
    taxation: Optional[str] = None


@dataclass
class FundManagerInfo:
    name: Optional[str] = None
    tenure: Optional[str] = None
    tenure_years: Optional[float] = None
    experience_summary: Optional[str] = None
    other_funds_managed: List[str] = field(default_factory=list)


@dataclass
class NewsItem:
    headline: str = ""
    date: Optional[str] = None
    publisher: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None


@dataclass
class FundSnapshot:
    identity: FundIdentity = field(default_factory=FundIdentity)
    nav: NavInfo = field(default_factory=NavInfo)
    returns: ReturnsInfo = field(default_factory=ReturnsInfo)
    risk: RiskInfo = field(default_factory=RiskInfo)
    portfolio: PortfolioInfo = field(default_factory=PortfolioInfo)
    operations: OperationsInfo = field(default_factory=OperationsInfo)
    fund_manager: FundManagerInfo = field(default_factory=FundManagerInfo)
    news_context: List[NewsItem] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    last_scraped_at: Optional[str] = field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
