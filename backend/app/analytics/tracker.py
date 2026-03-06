"""
Lightweight, anonymized query analytics tracker.

Stores recent query metadata in memory (no persistent DB for this version).
Provides trending fund calculations and guardrail refusal rates.
All data is fully anonymized — no user identifiers are stored.
"""

from __future__ import annotations

import csv
import os
import re
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger


@dataclass
class QueryRecord:
    timestamp: float
    question_length: int
    detected_funds: List[str]
    outcome: str  # "answered", "advice_refused", "pii_refused", "out_of_corpus", "error"
    latency_ms: float


MAX_RECORDS = 5000
ROLLING_WINDOW_SECONDS = 86400  # 24 hours


class AnalyticsTracker:
    """Thread-safe (GIL-protected) in-memory analytics store."""

    def __init__(self) -> None:
        self._records: deque[QueryRecord] = deque(maxlen=MAX_RECORDS)
        self._total_queries = 0
        self._outcome_counts: Counter[str] = Counter()

    def record_query(
        self,
        question: str,
        detected_funds: List[str],
        outcome: str,
        latency_ms: float,
    ) -> None:
        rec = QueryRecord(
            timestamp=time.time(),
            question_length=len(question),
            detected_funds=detected_funds,
            outcome=outcome,
            latency_ms=latency_ms,
        )
        self._records.append(rec)
        self._total_queries += 1
        self._outcome_counts[outcome] += 1

    def get_trending_funds(self, top_n: int = 5) -> List[Dict[str, object]]:
        """Return the top-N most queried funds within the rolling window."""
        cutoff = time.time() - ROLLING_WINDOW_SECONDS
        fund_counts: Counter[str] = Counter()
        for rec in self._records:
            if rec.timestamp >= cutoff:
                for fund in rec.detected_funds:
                    fund_counts[fund] += 1

        results = []
        for fund_name, count in fund_counts.most_common(top_n):
            results.append({"fund_name": fund_name, "query_count": count})
        return results

    def get_summary(self) -> Dict[str, object]:
        """Return an overall analytics summary."""
        cutoff = time.time() - ROLLING_WINDOW_SECONDS
        recent = [r for r in self._records if r.timestamp >= cutoff]

        recent_latencies = [r.latency_ms for r in recent if r.outcome == "answered"]
        avg_latency = (
            sum(recent_latencies) / len(recent_latencies) if recent_latencies else 0.0
        )

        recent_outcomes: Counter[str] = Counter()
        for r in recent:
            recent_outcomes[r.outcome] += 1

        return {
            "total_queries_all_time": self._total_queries,
            "queries_last_24h": len(recent),
            "avg_latency_ms_last_24h": round(avg_latency, 1),
            "outcome_counts_last_24h": dict(recent_outcomes),
            "outcome_counts_all_time": dict(self._outcome_counts),
            "trending_funds": self.get_trending_funds(top_n=5),
        }


# Singleton tracker instance
tracker = AnalyticsTracker()


# ---------------------------------------------------------------------------
# Fund name detection helpers (for tagging queries with mentioned funds)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_fund_keywords() -> List[tuple[str, List[str]]]:
    """Load fund names and their keywords from fund_universe.csv."""
    csv_path = Path(__file__).resolve().parents[3] / "config" / "fund_universe.csv"
    if not csv_path.exists():
        logger.warning("fund_universe.csv not found at %s", csv_path)
        return []

    entries: List[tuple[str, List[str]]] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name of Fund") or "").strip()
            kw_str = row.get("Keywords") or ""
            keywords = [k.strip().lower() for k in kw_str.split(",") if k.strip()]
            keywords.append(name.lower())
            entries.append((name, keywords))
    return entries


def detect_funds_in_query(question: str) -> List[str]:
    """Return canonical fund names mentioned in a query."""
    q_lower = question.lower()
    matched: List[str] = []
    for fund_name, keywords in _load_fund_keywords():
        for kw in keywords:
            if kw in q_lower:
                matched.append(fund_name)
                break
    return matched
