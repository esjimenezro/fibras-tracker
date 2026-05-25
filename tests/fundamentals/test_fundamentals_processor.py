from datetime import date

import pytest

from modules.fundamentals.models import FundamentalsRecord
from modules.fundamentals.processors import FundamentalsProcessor


@pytest.fixture
def processor():
    """Return a FundamentalsProcessor instance."""
    return FundamentalsProcessor()


@pytest.fixture
def record_full():
    """FMTY14 1T2026: all fields populated with round numbers for easy manual verification."""
    return FundamentalsRecord(
        ticker="FMTY14",
        period="1T2026",
        report_date=date(2026, 3, 31),
        total_revenues=1_000_000_000,
        noi=800_000_000,
        ebitda=700_000_000,
        ffo=600_000_000,
        affo=600_000_000,
        distribution_per_cbfi=0.40,
        gross_leasable_area_m2=1_000_000,
        cbfis_outstanding=1_500_000_000,
        cbfis_with_rights=1_500_000_000,
        total_equity=20_000_000_000,
        total_debt=4_000_000_000,
        financial_debt=4_000_000_000,
        total_assets=24_000_000_000,
        occupancy_rate=0.95,
        usd_mxn_exchange_rate=17.50,
    )


@pytest.fixture
def record_null_affo():
    """FMTY14 2T2026: affo=None — all affo-derived KPIs must propagate None."""
    return FundamentalsRecord(
        ticker="FMTY14",
        period="2T2026",
        report_date=date(2026, 6, 30),
        total_revenues=1_000_000_000,
        noi=800_000_000,
        ebitda=700_000_000,
        ffo=600_000_000,
        affo=None,
        distribution_per_cbfi=0.40,
        gross_leasable_area_m2=1_000_000,
        cbfis_outstanding=1_500_000_000,
        cbfis_with_rights=1_500_000_000,
        total_equity=20_000_000_000,
        total_debt=4_000_000_000,
        financial_debt=4_000_000_000,
        total_assets=24_000_000_000,
        occupancy_rate=0.95,
        usd_mxn_exchange_rate=None,
    )


# ── Operational metrics ──────────────────────────────────────────────────────


def test_noi_margin(processor, record_full):
    """noi_margin = noi / total_revenues."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.noi_margin == pytest.approx(0.80, rel=1e-6)


def test_ebitda_margin(processor, record_full):
    """ebitda_margin = ebitda / total_revenues."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.ebitda_margin == pytest.approx(0.70, rel=1e-6)


def test_revenue_per_m2(processor, record_full):
    """revenue_per_m2 = total_revenues / gross_leasable_area_m2."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.revenue_per_m2 == pytest.approx(1_000.0, rel=1e-6)


def test_affo_per_m2(processor, record_full):
    """affo_per_m2 = affo / gross_leasable_area_m2."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.affo_per_m2 == pytest.approx(600.0, rel=1e-6)


# ── Per-CBFI metrics ─────────────────────────────────────────────────────────


def test_ffo_per_cbfi(processor, record_full):
    """ffo_per_cbfi = ffo / cbfis_with_rights."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.ffo_per_cbfi == pytest.approx(0.40, rel=1e-6)


def test_affo_per_cbfi(processor, record_full):
    """affo_per_cbfi = affo / cbfis_with_rights."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.affo_per_cbfi == pytest.approx(0.40, rel=1e-6)


def test_cbfis_with_rights_used_for_per_cbfi_metrics(processor):
    """ffo_per_cbfi and affo_per_cbfi use cbfis_with_rights; market_cap and nav_per_cbfi use cbfis_outstanding."""
    record = FundamentalsRecord(
        ticker="FMTY14",
        period="3T2026",
        report_date=date(2026, 9, 30),
        total_revenues=1_000_000_000,
        noi=800_000_000,
        ebitda=700_000_000,
        ffo=600_000_000,
        affo=600_000_000,
        distribution_per_cbfi=0.40,
        gross_leasable_area_m2=1_000_000,
        cbfis_outstanding=1_500_000_000,
        cbfis_with_rights=1_200_000_000,
        total_equity=20_000_000_000,
        total_debt=4_000_000_000,
        financial_debt=4_000_000_000,
        total_assets=24_000_000_000,
        occupancy_rate=0.95,
        usd_mxn_exchange_rate=17.50,
    )
    result = processor._enrich(record=record, market_price=10.50)
    assert result.ffo_per_cbfi == pytest.approx(600_000_000 / 1_200_000_000, rel=1e-6)
    assert result.affo_per_cbfi == pytest.approx(600_000_000 / 1_200_000_000, rel=1e-6)
    assert result.market_cap == pytest.approx(10.50 * 1_500_000_000, rel=1e-6)
    assert result.nav_per_cbfi == pytest.approx(20_000_000_000 / 1_500_000_000, rel=1e-6)


def test_nav_per_cbfi(processor, record_full):
    """nav_per_cbfi = total_equity / cbfis_outstanding."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.nav_per_cbfi == pytest.approx(20_000_000_000 / 1_500_000_000, rel=1e-6)


# ── Capital structure ─────────────────────────────────────────────────────────


def test_ltv(processor, record_full):
    """ltv = financial_debt / total_assets."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.ltv == pytest.approx(4_000_000_000 / 24_000_000_000, rel=1e-6)


def test_affo_payout_ratio(processor, record_full):
    """affo_payout_ratio = (distribution_per_cbfi * cbfis_outstanding) / affo."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.affo_payout_ratio == pytest.approx(1.0, rel=1e-6)


# ── Market metrics (price present) ───────────────────────────────────────────


def test_market_cap(processor, record_full):
    """market_cap = market_price * cbfis_outstanding."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.market_cap == pytest.approx(15_750_000_000, rel=1e-6)


def test_price_to_ffo(processor, record_full):
    """price_to_ffo = market_price / ffo_per_cbfi."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.price_to_ffo == pytest.approx(26.25, rel=1e-6)


def test_price_to_affo(processor, record_full):
    """price_to_affo = market_price / affo_per_cbfi."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.price_to_affo == pytest.approx(26.25, rel=1e-6)


def test_dividend_yield(processor, record_full):
    """dividend_yield = (distribution_per_cbfi * 4) / market_price."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.dividend_yield == pytest.approx(1.60 / 10.50, rel=1e-6)


def test_price_to_nav(processor, record_full):
    """price_to_nav = market_price / nav_per_cbfi."""
    result = processor._enrich(record=record_full, market_price=10.50)
    assert result.price_to_nav == pytest.approx(10.50 * 1_500_000_000 / 20_000_000_000, rel=1e-6)


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_market_kpis_none_when_no_price(processor, record_full):
    """All market KPIs are None when no market price is available for the ticker."""
    result = processor._enrich(record=record_full, market_price=None)
    assert result.market_cap is None
    assert result.price_to_ffo is None
    assert result.price_to_affo is None
    assert result.dividend_yield is None
    assert result.price_to_nav is None


def test_null_input_propagates_to_derived_kpis(processor, record_null_affo):
    """KPIs that depend on affo are None when affo=None; independent KPIs still compute."""
    result = processor._enrich(record=record_null_affo, market_price=10.50)
    assert result.affo_per_cbfi is None
    assert result.affo_per_m2 is None
    assert result.price_to_affo is None
    assert result.affo_payout_ratio is None
    assert result.noi_margin == pytest.approx(0.80, rel=1e-6)


def test_zero_denominator_returns_none_not_exception(processor, record_full):
    """When a denominator field is zero, the derived KPI is None rather than raising ZeroDivisionError."""
    record_zero_affo = FundamentalsRecord(
        **{**record_full.model_dump(), "affo": 0},
    )
    result = processor._enrich(record=record_zero_affo, market_price=10.50)
    assert result.affo_payout_ratio is None


def test_empty_records_raises(processor):
    """process() raises ValueError when the records list is empty."""
    with pytest.raises(ValueError):
        processor.process(records=[], market_prices=[])
