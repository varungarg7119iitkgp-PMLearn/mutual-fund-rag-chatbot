from __future__ import annotations

from datetime import datetime
from typing import Optional

from phase1_ingestion.src.models import FundSnapshot


CATEGORY_MAP = {
    "DEBT": "Debt",
    "COMMODITY": "Commodity",
    "COMMODITIES": "Commodity",
    "HYBRID": "Hybrid",
    "EQUITY": "Equity",
}

RISK_LEVELS = [
    # Order matters: match more specific/longer labels first
    "VERY HIGH",
    "MODERATELY HIGH",
    "MODERATELY LOW",
    "MODERATE",
    "HIGH",
    "LOW",
]


def normalize_category(raw: str) -> str:
    key = (raw or "").strip().upper()
    return CATEGORY_MAP.get(key, raw)


def normalize_risk_label(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    upper = raw.upper()
    for level in RISK_LEVELS:
        if level in upper:
            # Return with title casing, e.g. "Moderately High"
            return level.title()
    return raw


def normalize_nav_date(raw_date: Optional[str]) -> Optional[str]:
    """
    Normalize NAV date into ISO format (YYYY-MM-DD) when possible.

    Groww's `nav_date` is typically like "04-Mar-2026". In other cases, we
    may have human-readable strings; if parsing fails, we leave as-is.
    """
    if not raw_date:
        return None

    raw_date = raw_date.strip()

    # Try common Groww formats
    for fmt in ("%d-%b-%Y", "%d-%b-%y"):
        try:
            dt = datetime.strptime(raw_date, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue

    # If parsing fails, return the original string.
    return raw_date


def normalize_snapshot(snapshot: FundSnapshot) -> FundSnapshot:
    """
    Apply basic normalization to a FundSnapshot:
    - Category label.
    - Riskometer label.
    - NAV date format.
    """
    snapshot.identity.category = normalize_category(snapshot.identity.category)
    snapshot.risk.riskometer = normalize_risk_label(snapshot.risk.riskometer)
    snapshot.nav.date = normalize_nav_date(snapshot.nav.date)
    return snapshot

