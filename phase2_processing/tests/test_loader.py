from pathlib import Path
import json

from phase2_processing.src.loader import load_raw_snapshot
from phase1_ingestion.src.models import FundSnapshot


def test_load_raw_snapshot_round_trip(tmp_path: Path) -> None:
    # Arrange: create a minimal fake snapshot file
    data = {
        "identity": {
            "fund_id": "TESTISIN",
            "name": "Test Fund",
            "category": "Equity",
            "amc_name": "Test AMC",
            "benchmark_name": "Test Index",
            "plan_label": "Direct Plan - Growth",
            "keywords": ["Test", "Equity"],
        },
        "nav": {"value": 100.0, "date": "2026-03-05"},
        "returns": {"one_year": 10.0},
        "risk": {"riskometer": "Moderately High"},
        "portfolio": {"top_holdings": [], "sector_allocation": {}, "turnover_ratio": None},
        "operations": {"expense_ratio": 0.7, "exit_load": "1%"},
        "fund_manager": {"name": "Manager X"},
        "news_context": [],
        "source_urls": ["https://example.com"],
        "last_scraped_at": "2026-03-05T00:00:00Z",
    }
    path = tmp_path / "Test_Fund.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f)

    # Act
    snapshot = load_raw_snapshot(path)

    # Assert
    assert isinstance(snapshot, FundSnapshot)
    assert snapshot.identity.name == "Test Fund"
    assert snapshot.nav.value == 100.0
    assert snapshot.risk.riskometer == "Moderately High"
    assert snapshot.operations.expense_ratio == 0.7

