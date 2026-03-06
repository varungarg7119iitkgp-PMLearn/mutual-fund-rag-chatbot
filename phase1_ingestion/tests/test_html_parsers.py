from phase1_ingestion.src.html_parsers import (
    parse_nav_and_date,
    parse_returns_table,
    parse_risk_section,
    parse_news_section,
)


def test_parse_nav_and_date_basic() -> None:
    html = """
    <div>
      <span>NAV as on 04 Mar 2026</span>
      <span>₹ 123.45</span>
    </div>
    """
    nav_info = parse_nav_and_date(html)
    assert nav_info.value == 123.45
    assert "NAV as on" in (nav_info.date or "")


def test_parse_returns_table_basic() -> None:
    html = """
    <table>
      <thead>
        <tr>
          <th></th><th>1Y</th><th>3Y</th><th>5Y</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Fund Returns</td><td>10%</td><td>12%</td><td>15%</td></tr>
        <tr><td>Benchmark</td><td>8%</td><td>10%</td><td>11%</td></tr>
        <tr><td>Category Average</td><td>7%</td><td>9%</td><td>10%</td></tr>
      </tbody>
    </table>
    """
    returns = parse_returns_table(html)
    assert returns.one_year == 10.0
    assert returns.three_year == 12.0
    assert returns.five_year == 15.0
    assert returns.benchmark_one_year == 8.0
    assert returns.category_avg_five_year == 10.0


def test_parse_risk_section_basic() -> None:
    html = """
    <div>
      <div>Riskometer: Moderately High</div>
      <div>Standard Deviation 18.50</div>
      <div>Sharpe Ratio 1.10</div>
      <div>Alpha 2.0</div>
      <div>Beta 0.9</div>
    </div>
    """
    risk = parse_risk_section(html)
    assert "Moderately High" in (risk.riskometer or "")
    assert risk.standard_deviation == 18.50
    assert risk.sharpe_ratio == 1.10
    assert risk.alpha == 2.0
    assert risk.beta == 0.9


def test_parse_news_section_basic() -> None:
    html = """
    <div class="news-card">
      <h3>Fund sees inflows</h3>
      <p>Investors poured money into the fund last week.</p>
      <span>2026-03-01</span>
      <a href="https://example.com/news1">Read more</a>
    </div>
    """
    items = parse_news_section(html)
    assert len(items) >= 1
    first = items[0]
    assert first.headline == "Fund sees inflows"
    assert first.url == "https://example.com/news1"

