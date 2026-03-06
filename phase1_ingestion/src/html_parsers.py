"""
HTML parsing helpers for mutual fund pages.

These functions are intentionally written to be:
- Independent of Playwright (operate on raw HTML strings).
- Relatively robust to minor DOM changes, by using label-based search where possible.

They will likely need tuning once real page structures are inspected, but they
provide a solid starting point and are covered by tests using representative snippets.
"""

from __future__ import annotations

import json
from typing import Optional, List, Dict, Any

from bs4 import BeautifulSoup  # type: ignore

from .models import (
    NavInfo,
    ReturnsInfo,
    RiskInfo,
    NewsItem,
    FundSnapshot,
    FundIdentity,
    PortfolioInfo,
    Holding,
    AssetAllocation,
    OperationsInfo,
    MinInvestment,
    FundManagerInfo,
)


def _text_or_none(node) -> Optional[str]:
    if not node:
        return None
    text = node.get_text(strip=True)
    return text or None


def _parse_numeric_from_text(text: str) -> Optional[float]:
    """
    Try to parse a numeric value (e.g. NAV or percentage) from a text snippet.

    Rejects strings that still contain alphabetic characters after removing
    common currency markers, to avoid accidentally parsing dates like
    "04 Mar 2026" into 42026.0.
    """
    if not text:
        return None

    cleaned = (
        text.replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace(",", "")
        .strip()
    )

    # If any alphabetic characters remain (e.g., month names), treat as non-numeric.
    if any(ch.isalpha() for ch in cleaned):
        return None

    numeric_part = "".join(ch for ch in cleaned if ch.isdigit() or ch in ".-")
    if not numeric_part:
        return None

    try:
        return float(numeric_part)
    except ValueError:
        return None


def parse_nav_and_date(html: str) -> NavInfo:
    """Extract latest NAV and date from a fund page HTML snippet."""
    soup = BeautifulSoup(html, "html.parser")
    nav_info = NavInfo()

    # Heuristic: look for text containing "NAV" and a nearby number.
    nav_label = soup.find(string=lambda t: t and "NAV" in t.upper())
    if nav_label:
        parent = nav_label.parent
        # Try to find a numeric sibling or following element that looks like a price
        candidate = parent.find_next(string=lambda t: t and any(ch.isdigit() for ch in t))
        while candidate:
            value = _parse_numeric_from_text(str(candidate))
            if value is not None:
                nav_info.value = value
                break
            candidate = candidate.find_next(string=lambda t: t and any(ch.isdigit() for ch in t))

    # Heuristic: look for date patterns near "as on" or "as of"
    date_label = soup.find(string=lambda t: t and ("AS ON" in t.upper() or "AS OF" in t.upper()))
    if date_label:
        next_text = date_label.parent.get_text(" ", strip=True)
        # Keep the full string; normalization will happen in Phase 2.
        nav_info.date = next_text

    return nav_info


def parse_returns_table(html: str) -> ReturnsInfo:
    """Extract returns for 1Y/3Y/5Y/SI, plus benchmark and category averages, from a generic performance table."""
    soup = BeautifulSoup(html, "html.parser")
    returns = ReturnsInfo()

    # Very generic approach: look for a table with headers containing "1Y" / "3Y" / "5Y".
    tables = soup.find_all("table")
    for table in tables:
        header_cells = [c.get_text(strip=True).upper() for c in table.find_all("th")]
        if any("1Y" in h or "1 YEAR" in h for h in header_cells):
            rows = table.find_all("tr")
            for row in rows:
                label = (row.find("td") or row.find("th"))
                if not label:
                    continue
                label_text = label.get_text(strip=True).upper()
                values = [c.get_text(strip=True) for c in row.find_all("td")[1:]]

                def parse_pct(value: str) -> Optional[float]:
                    value = value.replace("%", "").strip()
                    if not value:
                        return None
                    try:
                        return float(value)
                    except ValueError:
                        return None

                if "FUND" in label_text or "SCHEME" in label_text:
                    # Scheme returns row
                    if len(values) >= 1:
                        returns.one_year = parse_pct(values[0])
                    if len(values) >= 2:
                        returns.three_year = parse_pct(values[1])
                    if len(values) >= 3:
                        returns.five_year = parse_pct(values[2])
                elif "BENCHMARK" in label_text:
                    if len(values) >= 1:
                        returns.benchmark_one_year = parse_pct(values[0])
                    if len(values) >= 2:
                        returns.benchmark_three_year = parse_pct(values[1])
                    if len(values) >= 3:
                        returns.benchmark_five_year = parse_pct(values[2])
                elif "CATEGORY" in label_text:
                    if len(values) >= 1:
                        returns.category_avg_one_year = parse_pct(values[0])
                    if len(values) >= 2:
                        returns.category_avg_three_year = parse_pct(values[1])
                    if len(values) >= 3:
                        returns.category_avg_five_year = parse_pct(values[2])

    return returns


def parse_risk_section(html: str) -> RiskInfo:
    """Extract riskometer and basic risk metrics."""
    soup = BeautifulSoup(html, "html.parser")
    risk = RiskInfo()

    # Riskometer label
    risk_label = soup.find(string=lambda t: t and "RISKOMETER" in t.upper())
    if risk_label:
        # Often the actual level appears nearby.
        nearby = risk_label.find_parent().get_text(" ", strip=True)
        risk.riskometer = nearby

    # Simple label-based extraction for numeric metrics
    def find_metric(label_keywords: List[str]) -> Optional[float]:
        label_node = soup.find(
            string=lambda t: t
            and any(k in t.upper() for k in label_keywords)
        )
        if not label_node:
            return None
        candidate = label_node.parent.find_next(string=lambda t: t and any(ch.isdigit() for ch in t))
        if not candidate:
            return None
        try:
            numeric = "".join(ch for ch in candidate if ch.isdigit() or ch in ".-")
            return float(numeric)
        except ValueError:
            return None

    risk.standard_deviation = find_metric(["STANDARD DEVIATION"])
    risk.sharpe_ratio = find_metric(["SHARPE"])
    risk.alpha = find_metric(["ALPHA"])
    risk.beta = find_metric(["BETA"])

    return risk


def parse_news_section(html: str) -> List[NewsItem]:
    """Extract news items (headline, date, summary, publisher, url) from a generic news section."""
    soup = BeautifulSoup(html, "html.parser")
    items: List[NewsItem] = []

    # Heuristic: look for sections that likely correspond to news cards or list items.
    candidates = soup.find_all(["article", "li", "div"], class_=lambda c: c and "news" in c.lower()) or soup.find_all("article")

    for node in candidates:
        headline_node = node.find(["h3", "h4", "a"]) or node.find("strong")
        headline = _text_or_none(headline_node)
        if not headline:
            continue

        # Date, publisher, summary are heuristic and may require tuning per source.
        date_node = node.find(string=lambda t: t and any(k in t.lower() for k in ["202", "20"]))
        summary_node = node.find("p")
        publisher_node = node.find(string=lambda t: t and any(k in t.lower() for k in ["news", "finance", "money", "market"]))
        link_node = node.find("a", href=True)

        item = NewsItem(
            headline=headline,
            date=_text_or_none(date_node) if hasattr(date_node, "strip") else None,
            summary=_text_or_none(summary_node),
            publisher=_text_or_none(publisher_node),
            url=link_node["href"] if link_node else None,
        )
        items.append(item)

    return items


def parse_groww_next_data(
    html: str,
    fallback_name: str,
    fallback_category: str,
    url: str,
    keywords: List[str],
) -> Optional[FundSnapshot]:
    """
    Parse Groww's embedded __NEXT_DATA__ JSON (mfServerSideData) into a FundSnapshot.

    This is the primary source of truth for Groww pages and should populate as many
    fields as possible directly from structured data, falling back to HTML heuristics
    only when necessary.
    """
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
    if not script or not script.string:
        return None

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return None

    mf: Dict[str, Any] = (
        data.get("props", {})
        .get("pageProps", {})
        .get("mfServerSideData", {})
    )
    if not mf:
        return None

    # Identity
    identity = FundIdentity(
        fund_id=mf.get("isin"),
        name=mf.get("scheme_name") or fallback_name,
        category=mf.get("category") or fallback_category,
        amc_name=(mf.get("amc_info") or {}).get("name") or mf.get("fund_house"),
        benchmark_name=mf.get("benchmark_name") or mf.get("benchmark"),
        plan_label=mf.get("scheme_type"),
        keywords=keywords,
    )

    # NAV
    nav = NavInfo(
        value=mf.get("nav"),
        date=mf.get("nav_date"),
    )

    # Returns
    returns = ReturnsInfo()
    stats = mf.get("stats") or []
    for s in stats:
        s_type = (s.get("type") or "").upper()
        if s_type == "FUND_RETURN":
            returns.one_year = s.get("stat_1y")
            returns.three_year = s.get("stat_3y")
            returns.five_year = s.get("stat_5y")
            returns.since_inception = s.get("stat_all")
        elif s_type == "CATEGORY_AVG_RETURN":
            returns.category_avg_one_year = s.get("stat_1y")
            returns.category_avg_three_year = s.get("stat_3y")
            returns.category_avg_five_year = s.get("stat_5y")

    # Risk
    risk = RiskInfo()
    ret_stats = mf.get("return_stats") or []
    if ret_stats:
        rs0 = ret_stats[0]
        risk.riskometer = rs0.get("risk")
        risk.standard_deviation = rs0.get("standard_deviation")
        risk.sharpe_ratio = rs0.get("sharpe_ratio")
        risk.alpha = rs0.get("alpha")
        risk.beta = rs0.get("beta")

    # Portfolio (top holdings only, for now)
    holdings_data = mf.get("holdings") or []
    top_holdings: List[Holding] = []
    for h in holdings_data[:10]:
        name = (h.get("company_name") or "").strip()
        if not name:
            continue
        top_holdings.append(
            Holding(
                name=name,
                weight_pct=h.get("corpus_per"),
            )
        )

    portfolio = PortfolioInfo(
        asset_allocation=AssetAllocation(),  # can be derived in later phases
        top_holdings=top_holdings,
        sector_allocation={},  # can be derived from holdings.sector_name if needed
        turnover_ratio=mf.get("portfolio_turnover"),
    )

    # Operations
    min_inv = MinInvestment(
        sip=mf.get("min_sip_investment"),
        lumpsum=mf.get("min_investment_amount"),
    )

    expense_ratio_raw = mf.get("expense_ratio")
    try:
        expense_ratio_val = float(expense_ratio_raw) if expense_ratio_raw is not None else None
    except (TypeError, ValueError):
        expense_ratio_val = None

    category_info = mf.get("category_info") or {}
    operations = OperationsInfo(
        expense_ratio=expense_ratio_val,
        exit_load=mf.get("exit_load"),
        min_investment=min_inv,
        taxation=category_info.get("tax_impact"),
    )

    # Fund manager
    fm_details = mf.get("fund_manager_details") or []
    fund_manager = FundManagerInfo()
    if fm_details:
        primary = fm_details[0]
        fund_manager.name = primary.get("person_name")
        fund_manager.experience_summary = primary.get("experience")
        managed = primary.get("funds_managed") or []
        fund_manager.other_funds_managed = [
            fm.get("scheme_name")
            for fm in managed
            if isinstance(fm, dict) and fm.get("scheme_name")
        ]

    # News (if Groww exposes any structured news for the fund)
    news_context: List[NewsItem] = []
    for n in mf.get("fund_news") or []:
        headline = (n.get("title") or "").strip()
        if not headline:
            continue
        news_context.append(
            NewsItem(
                headline=headline,
                date=n.get("date"),
                summary=n.get("summary"),
                publisher=n.get("source"),
                url=n.get("url"),
            )
        )

    # Fallback: if the platform does not expose fund-specific news, attach a generic
    # Groww news stream link so the system can still surface a credible source of
    # recent market updates when needed.
    if not news_context:
        news_context.append(
            NewsItem(
                headline="Latest mutual fund & market news",
                date=None,
                summary="Generic news stream from Groww; not specific to this single fund.",
                publisher="Groww News",
                url="https://groww.in/blog/category/news",
            )
        )

    snapshot = FundSnapshot(
        identity=identity,
        nav=nav,
        returns=returns,
        risk=risk,
        portfolio=portfolio,
        operations=operations,
        fund_manager=fund_manager,
        news_context=news_context,
        source_urls=[url],
    )
    return snapshot

