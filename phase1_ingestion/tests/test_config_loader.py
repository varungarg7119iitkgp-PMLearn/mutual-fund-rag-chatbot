from pathlib import Path

from phase1_ingestion.src.config_loader import load_fund_universe, validate_fund_universe, FUND_UNIVERSE_PATH


def test_fund_universe_csv_exists() -> None:
    assert FUND_UNIVERSE_PATH.exists(), f"Fund universe CSV not found at {FUND_UNIVERSE_PATH}"


def test_load_fund_universe_has_20_entries() -> None:
    funds = load_fund_universe(FUND_UNIVERSE_PATH)
    assert len(funds) == 20


def test_validate_fund_universe_category_counts() -> None:
    funds = load_fund_universe(FUND_UNIVERSE_PATH)
    # Should not raise
    validate_fund_universe(funds)

