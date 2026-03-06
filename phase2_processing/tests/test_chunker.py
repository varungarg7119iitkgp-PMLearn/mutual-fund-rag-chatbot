from phase1_ingestion.src.models import FundSnapshot, FundIdentity, NavInfo, ReturnsInfo, RiskInfo, PortfolioInfo, OperationsInfo, FundManagerInfo, NewsItem
from phase2_processing.src.chunker import (
    build_overview_chunk,
    build_performance_chunk,
    build_risk_chunk,
    build_fees_chunk,
    build_portfolio_chunk,
    build_news_chunks,
    build_all_chunks,
)


def _make_basic_snapshot() -> FundSnapshot:
    identity = FundIdentity(
        fund_id="TESTISIN",
        name="Test Fund",
        category="Equity",
        amc_name="Test AMC",
        benchmark_name="Test Index",
        plan_label="Direct Plan - Growth",
        keywords=["Test"],
    )
    nav = NavInfo(value=123.45, date="2026-03-05")
    returns = ReturnsInfo(one_year=10.0, three_year=12.0, five_year=15.0)
    risk = RiskInfo(riskometer="Moderately High", standard_deviation=18.5, sharpe_ratio=1.1)
    portfolio = PortfolioInfo()
    operations = OperationsInfo()
    fund_manager = FundManagerInfo(name="Manager X")
    news = [NewsItem(headline="Sample headline", summary="Sample summary", url="https://example.com")]

    return FundSnapshot(
        identity=identity,
        nav=nav,
        returns=returns,
        risk=risk,
        portfolio=portfolio,
        operations=operations,
        fund_manager=fund_manager,
        news_context=news,
        source_urls=["https://example.com"],
        last_scraped_at="2026-03-05T00:00:00Z",
    )


def test_overview_chunk_contains_basic_details() -> None:
    snapshot = _make_basic_snapshot()
    chunk = build_overview_chunk(snapshot)
    assert "Test Fund" in chunk.text
    assert "Equity" in chunk.text
    assert "Moderately High" in chunk.text
    assert chunk.data_type == "overview"


def test_performance_chunk_includes_returns() -> None:
    snapshot = _make_basic_snapshot()
    chunk = build_performance_chunk(snapshot)
    assert "1Y returns" in chunk.text
    assert chunk.data_type == "performance"


def test_risk_chunk_includes_risk_metrics() -> None:
    snapshot = _make_basic_snapshot()
    chunk = build_risk_chunk(snapshot)
    assert "Risk level" in chunk.text
    assert "Standard deviation" in chunk.text
    assert chunk.data_type == "risk"


def test_fees_chunk_handles_missing_ops_gracefully() -> None:
    snapshot = _make_basic_snapshot()
    chunk = build_fees_chunk(snapshot)
    assert chunk.data_type == "fees"


def test_portfolio_chunk_handles_no_holdings() -> None:
    snapshot = _make_basic_snapshot()
    chunk = build_portfolio_chunk(snapshot)
    assert "No portfolio holdings" in chunk.text or "Top holdings" in chunk.text
    assert chunk.data_type == "portfolio"


def test_news_chunks_created_for_news_items() -> None:
    snapshot = _make_basic_snapshot()
    chunks = build_news_chunks(snapshot)
    assert len(chunks) == 1
    assert "Sample headline" in chunks[0].text
    assert chunks[0].data_type == "news"


def test_build_all_chunks_returns_multiple_chunk_types() -> None:
    snapshot = _make_basic_snapshot()
    chunks = build_all_chunks(snapshot)
    types = {c.data_type for c in chunks}
    assert {"overview", "performance", "risk", "fees", "portfolio", "news"}.issubset(types)

