from phase2_processing.src.normalization import (
    normalize_category,
    normalize_risk_label,
    normalize_nav_date,
)


def test_normalize_category_mapping() -> None:
    assert normalize_category("DEBT") == "Debt"
    assert normalize_category("Commodity") == "Commodity"
    assert normalize_category("Hybrid") == "Hybrid"
    assert normalize_category("Equity") == "Equity"


def test_normalize_risk_label_detects_standard_levels() -> None:
    assert normalize_risk_label("This is Moderately High risk") == "Moderately High"
    assert normalize_risk_label("very high risk fund") == "Very High"
    assert normalize_risk_label(None) is None


def test_normalize_nav_date_groww_format() -> None:
    iso = normalize_nav_date("04-Mar-2026")
    assert iso == "2026-03-04"


def test_normalize_nav_date_fallback() -> None:
    raw = "NAV as on 04 Mar 2026"
    # Our parser can't handle this format yet, so we keep original
    assert normalize_nav_date(raw) == raw

