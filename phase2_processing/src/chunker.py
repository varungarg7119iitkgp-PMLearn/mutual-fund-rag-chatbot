from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import uuid

from phase1_ingestion.src.models import FundSnapshot, NewsItem


@dataclass
class Chunk:
    chunk_id: str
    fund_id: str
    fund_name: str
    category: str
    data_type: str
    text: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _new_chunk_id() -> str:
    return str(uuid.uuid4())


def build_overview_chunk(s: FundSnapshot) -> Chunk:
    identity = s.identity
    risk_label = s.risk.riskometer or "Not specified"
    nav_part = ""
    if s.nav.value is not None and s.nav.date:
        nav_part = f" Latest NAV as of {s.nav.date} is ₹{s.nav.value:.2f}."
    elif s.nav.value is not None:
        nav_part = f" Latest NAV is ₹{s.nav.value:.2f}."

    text = (
        f"{identity.name} is a {identity.category} mutual fund scheme"
        f" from {identity.amc_name or 'an AMC'} with a risk level rated as {risk_label}."
        f"{nav_part}"
    ).strip()

    return Chunk(
        chunk_id=_new_chunk_id(),
        fund_id=identity.fund_id or identity.name,
        fund_name=identity.name,
        category=identity.category,
        data_type="overview",
        text=text,
        metadata={
            "fund_id": identity.fund_id,
            "amc_name": identity.amc_name,
            "benchmark_name": identity.benchmark_name,
            "riskometer": s.risk.riskometer,
            "nav": {"value": s.nav.value, "date": s.nav.date},
            "last_scraped_at": s.last_scraped_at,
            "source_urls": s.source_urls,
        },
    )


def build_performance_chunk(s: FundSnapshot) -> Chunk:
    r = s.returns
    parts: List[str] = []
    if r.one_year is not None:
        parts.append(f"1Y returns: {r.one_year:.2f}%.")
    if r.three_year is not None:
        parts.append(f"3Y annualised returns: {r.three_year:.2f}%.")
    if r.five_year is not None:
        parts.append(f"5Y annualised returns: {r.five_year:.2f}%." )
    if r.since_inception is not None:
        parts.append(f"Since inception returns: {r.since_inception:.2f}%." )

    cat_parts: List[str] = []
    if r.category_avg_one_year is not None:
        cat_parts.append(f"category 1Y average {r.category_avg_one_year:.2f}%.")
    if r.category_avg_three_year is not None:
        cat_parts.append(f"category 3Y average {r.category_avg_three_year:.2f}%.")
    if r.category_avg_five_year is not None:
        cat_parts.append(f"category 5Y average {r.category_avg_five_year:.2f}%." )

    perf_text = " ".join(parts) if parts else "Performance data is not available."
    if cat_parts:
        perf_text += " Compared with " + " ".join(cat_parts)

    return Chunk(
        chunk_id=_new_chunk_id(),
        fund_id=s.identity.fund_id or s.identity.name,
        fund_name=s.identity.name,
        category=s.identity.category,
        data_type="performance",
        text=perf_text.strip(),
        metadata={
            "returns": asdict(s.returns),
            "last_scraped_at": s.last_scraped_at,
            "source_urls": s.source_urls,
        },
    )


def build_risk_chunk(s: FundSnapshot) -> Chunk:
    risk = s.risk
    parts: List[str] = []
    if risk.riskometer:
        parts.append(f"Risk level: {risk.riskometer}.")
    if risk.standard_deviation is not None:
        parts.append(f"Standard deviation: {risk.standard_deviation:.2f}.")
    if risk.sharpe_ratio is not None:
        parts.append(f"Sharpe ratio: {risk.sharpe_ratio:.2f}.")
    if risk.alpha is not None:
        parts.append(f"Alpha: {risk.alpha:.2f}.")
    if risk.beta is not None:
        parts.append(f"Beta: {risk.beta:.2f}.")

    text = " ".join(parts) if parts else "Risk metrics are not available."

    return Chunk(
        chunk_id=_new_chunk_id(),
        fund_id=s.identity.fund_id or s.identity.name,
        fund_name=s.identity.name,
        category=s.identity.category,
        data_type="risk",
        text=text.strip(),
        metadata={
            "risk": asdict(risk),
            "last_scraped_at": s.last_scraped_at,
            "source_urls": s.source_urls,
        },
    )


def build_fees_chunk(s: FundSnapshot) -> Chunk:
    ops = s.operations
    parts: List[str] = []
    if ops.expense_ratio is not None:
        parts.append(f"Expense ratio is {ops.expense_ratio:.2f}%.")
    if ops.exit_load:
        parts.append(f"Exit load policy: {ops.exit_load}")
    if ops.min_investment.sip is not None:
        parts.append(f"Minimum SIP investment is ₹{ops.min_investment.sip:.0f}.")
    if ops.min_investment.lumpsum is not None:
        parts.append(f"Minimum lump-sum investment is ₹{ops.min_investment.lumpsum:.0f}.")
    if ops.taxation:
        parts.append(f"Taxation: {ops.taxation}")

    text = " ".join(parts) if parts else "Operational details (expenses, exit load, minimum investments) are not available."

    return Chunk(
        chunk_id=_new_chunk_id(),
        fund_id=s.identity.fund_id or s.identity.name,
        fund_name=s.identity.name,
        category=s.identity.category,
        data_type="fees",
        text=text.strip(),
        metadata={
            "operations": asdict(ops),
            "last_scraped_at": s.last_scraped_at,
            "source_urls": s.source_urls,
        },
    )


def build_portfolio_chunk(s: FundSnapshot) -> Chunk:
    holdings = s.portfolio.top_holdings or []
    if not holdings:
        text = "No portfolio holdings data is available."
    else:
        top_names = ", ".join(
            f"{h.name} ({h.weight_pct:.2f}%)" if h.weight_pct is not None else h.name
            for h in holdings[:10]
        )
        text = f"Top holdings include: {top_names}."

    return Chunk(
        chunk_id=_new_chunk_id(),
        fund_id=s.identity.fund_id or s.identity.name,
        fund_name=s.identity.name,
        category=s.identity.category,
        data_type="portfolio",
        text=text.strip(),
        metadata={
            "top_holdings": [asdict(h) for h in holdings],
            "turnover_ratio": s.portfolio.turnover_ratio,
            "last_scraped_at": s.last_scraped_at,
            "source_urls": s.source_urls,
        },
    )


def build_news_chunks(s: FundSnapshot) -> List[Chunk]:
    chunks: List[Chunk] = []
    for item in s.news_context:
        if not isinstance(item, NewsItem):
            # item might be a plain dict when loaded from JSON
            headline = item.get("headline")
            date = item.get("date")
            summary = item.get("summary")
            publisher = item.get("publisher")
            url = item.get("url")
        else:
            headline = item.headline
            date = item.date
            summary = item.summary
            publisher = item.publisher
            url = item.url

        if not headline:
            continue

        parts: List[str] = [headline]
        if summary:
            parts.append(summary)
        news_text = " ".join(parts)

        chunks.append(
            Chunk(
                chunk_id=_new_chunk_id(),
                fund_id=s.identity.fund_id or s.identity.name,
                fund_name=s.identity.name,
                category=s.identity.category,
                data_type="news",
                text=news_text.strip(),
                metadata={
                    "headline": headline,
                    "date": date,
                    "summary": summary,
                    "publisher": publisher,
                    "url": url,
                    "last_scraped_at": s.last_scraped_at,
                    "source_urls": s.source_urls,
                },
            )
        )
    return chunks


def build_all_chunks(snapshot: FundSnapshot) -> List[Chunk]:
    """Build the full set of chunks for a single fund snapshot."""
    chunks: List[Chunk] = []
    chunks.append(build_overview_chunk(snapshot))
    chunks.append(build_performance_chunk(snapshot))
    chunks.append(build_risk_chunk(snapshot))
    chunks.append(build_fees_chunk(snapshot))
    chunks.append(build_portfolio_chunk(snapshot))
    chunks.extend(build_news_chunks(snapshot))
    return chunks

