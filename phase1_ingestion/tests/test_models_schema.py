from phase1_ingestion.src.models import (
    FundSnapshot,
    FundIdentity,
    NavInfo,
    ReturnsInfo,
    RiskInfo,
    PortfolioInfo,
    OperationsInfo,
    FundManagerInfo,
    NewsItem,
)


def test_fund_snapshot_to_dict_has_expected_keys() -> None:
    identity = FundIdentity(
        fund_id="TESTISIN",
        name="Test Fund",
        category="Equity",
        amc_name="Test AMC",
        benchmark_name="Test Index",
        plan_label="Direct Plan - Growth",
        keywords=["Test", "Equity"],
    )

    snapshot = FundSnapshot(
        identity=identity,
        nav=NavInfo(value=100.0, date="2026-03-04"),
        returns=ReturnsInfo(one_year=10.0, three_year=12.0, five_year=15.0),
        risk=RiskInfo(riskometer="Moderately High", standard_deviation=18.5, sharpe_ratio=1.0),
        portfolio=PortfolioInfo(),
        operations=OperationsInfo(),
        fund_manager=FundManagerInfo(name="Manager Name"),
        news_context=[NewsItem(headline="Sample News")],
        source_urls=["https://example.com"],
        last_scraped_at="2026-03-04T00:00:00Z",
    )

    data = snapshot.to_dict()

    assert data["identity"]["name"] == "Test Fund"
    assert data["identity"]["category"] == "Equity"
    assert data["nav"]["value"] == 100.0
    assert data["returns"]["one_year"] == 10.0
    assert data["risk"]["riskometer"] == "Moderately High"
    assert data["news_context"][0]["headline"] == "Sample News"
    assert data["source_urls"] == ["https://example.com"]

