from datetime import date

import pytest

from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.processors import AnnualFundamentalsProcessor


def _make_record(ticker: str, period: str, **kwargs) -> EnrichedFundamentalsRecord:
    """Build a minimal EnrichedFundamentalsRecord for annual-processor tests.

    Args:
        ticker: BMV ticker string.
        period: Period label (e.g. "1T2025").
        **kwargs: Optional field overrides for any EnrichedFundamentalsRecord attribute.

    Returns:
        EnrichedFundamentalsRecord with the given identity fields and any overrides.
    """
    return EnrichedFundamentalsRecord(
        ticker=ticker,
        period=period,
        report_date=date(2025, 1, 1),
        **kwargs,
    )


def _four_quarters(ticker: str, year: int, **kwargs) -> list[EnrichedFundamentalsRecord]:
    """Build all four quarterly records for a ticker/year with shared field values.

    Args:
        ticker: BMV ticker string.
        year: Calendar year for the four quarters.
        **kwargs: Field values applied identically to all four quarters.

    Returns:
        list[EnrichedFundamentalsRecord]: Four records for Q1–Q4 of the given year.
    """
    return [
        _make_record(ticker=ticker, period=f"{q}T{year}", **kwargs)
        for q in range(1, 5)
    ]


@pytest.fixture
def processor() -> AnnualFundamentalsProcessor:
    """Return an AnnualFundamentalsProcessor instance."""
    return AnnualFundamentalsProcessor()


# ── Sum fields ────────────────────────────────────────────────────────────────
def test_sum_fields_computed_correctly(processor):
    """Sum fields aggregate correctly when all four quarters have non-None values."""
    records = _four_quarters(
        ticker="FMTY14",
        year=2025,
        distribution_per_cbfi=0.40,
        ffo_per_cbfi=0.50,
        affo_per_cbfi=0.45,
        revenue_per_cbfi=1.00,
        total_revenues=1_000_000_000,
    )
    result = processor.process(records=records)
    annual = result[0]
    assert annual.ticker == "FMTY14"
    assert annual.year == 2025
    assert annual.distribution_per_cbfi_annual == pytest.approx(1.60, rel=1e-6)
    assert annual.ffo_per_cbfi_annual == pytest.approx(2.00, rel=1e-6)
    assert annual.affo_per_cbfi_annual == pytest.approx(1.80, rel=1e-6)
    assert annual.revenue_per_cbfi_annual == pytest.approx(4.00, rel=1e-6)
    assert annual.total_revenues_annual == 4_000_000_000


def test_sum_field_none_when_any_quarter_none(processor):
    """ffo_per_cbfi_annual is None when any quarterly ffo_per_cbfi is None."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025", ffo_per_cbfi=0.50),
        _make_record(ticker="FMTY14", period="2T2025", ffo_per_cbfi=None),
        _make_record(ticker="FMTY14", period="3T2025", ffo_per_cbfi=0.50),
        _make_record(ticker="FMTY14", period="4T2025", ffo_per_cbfi=0.50),
    ]
    result = processor.process(records=records)
    assert result[0].ffo_per_cbfi_annual is None


# ── Average fields ────────────────────────────────────────────────────────────
def test_affo_payout_ratio_avg_computed_correctly(processor):
    """affo_payout_ratio_avg is the arithmetic mean of the four quarterly values."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025", affo_payout_ratio=0.80),
        _make_record(ticker="FMTY14", period="2T2025", affo_payout_ratio=0.90),
        _make_record(ticker="FMTY14", period="3T2025", affo_payout_ratio=1.00),
        _make_record(ticker="FMTY14", period="4T2025", affo_payout_ratio=1.10),
    ]
    result = processor.process(records=records)
    assert result[0].affo_payout_ratio_avg == pytest.approx(0.95, rel=1e-6)


def test_avg_field_none_when_any_quarter_none(processor):
    """affo_payout_ratio_avg is None when any quarterly affo_payout_ratio is None."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025", affo_payout_ratio=None),
        _make_record(ticker="FMTY14", period="2T2025", affo_payout_ratio=0.90),
        _make_record(ticker="FMTY14", period="3T2025", affo_payout_ratio=1.00),
        _make_record(ticker="FMTY14", period="4T2025", affo_payout_ratio=1.10),
    ]
    result = processor.process(records=records)
    assert result[0].affo_payout_ratio_avg is None


# ── Q4 snapshot fields ────────────────────────────────────────────────────────
def test_q4_snapshot_fields_pass_through(processor):
    """Q4 snapshot fields are taken from the Q4 record, not the other quarters."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025", nav_per_cbfi=10.0, ltv=0.30),
        _make_record(ticker="FMTY14", period="2T2025", nav_per_cbfi=11.0, ltv=0.31),
        _make_record(ticker="FMTY14", period="3T2025", nav_per_cbfi=12.0, ltv=0.32),
        _make_record(
            ticker="FMTY14",
            period="4T2025",
            nav_per_cbfi=13.0,
            ltv=0.33,
            occupancy_rate=0.95,
            wale=4.5,
            top_tenant_pct=0.12,
            top10_tenants_pct=0.55,
        ),
    ]
    result = processor.process(records=records)
    annual = result[0]
    assert annual.nav_per_cbfi == pytest.approx(13.0, rel=1e-6)
    assert annual.ltv == pytest.approx(0.33, rel=1e-6)
    assert annual.occupancy_rate == pytest.approx(0.95, rel=1e-6)
    assert annual.wale == pytest.approx(4.5, rel=1e-6)
    assert annual.top_tenant_pct == pytest.approx(0.12, rel=1e-6)
    assert annual.top10_tenants_pct == pytest.approx(0.55, rel=1e-6)


def test_q4_snapshot_passes_through_none(processor):
    """wale is None in the annual record when wale is None in the Q4 record."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025", wale=3.0),
        _make_record(ticker="FMTY14", period="2T2025", wale=3.5),
        _make_record(ticker="FMTY14", period="3T2025", wale=4.0),
        _make_record(ticker="FMTY14", period="4T2025", wale=None),
    ]
    result = processor.process(records=records)
    assert result[0].wale is None


# ── Incomplete year omission ──────────────────────────────────────────────────
def test_year_with_only_3_quarters_omitted(processor):
    """A year with only 3 quarters is omitted; only the complete year appears in output."""
    records_2024 = [
        _make_record(ticker="FMTY14", period="1T2024"),
        _make_record(ticker="FMTY14", period="2T2024"),
        _make_record(ticker="FMTY14", period="3T2024"),
    ]
    records_2025 = _four_quarters(ticker="FMTY14", year=2025)
    result = processor.process(records=records_2024 + records_2025)
    annual_years = [r.year for r in result]
    assert 2024 not in annual_years
    assert 2025 in annual_years


def test_year_with_1_quarter_omitted(processor):
    """A year with only 1 quarter is omitted entirely from the output."""
    records = [
        _make_record(ticker="FMTY14", period="1T2024"),
        *_four_quarters(ticker="FMTY14", year=2025),
    ]
    result = processor.process(records=records)
    annual_years = [r.year for r in result]
    assert 2024 not in annual_years
    assert 2025 in annual_years


# ── Sorting and multi-ticker ──────────────────────────────────────────────────
def test_output_sorted_by_year_ascending(processor):
    """Annual records for a ticker are sorted by year ascending regardless of input order."""
    records = _four_quarters(ticker="FMTY14", year=2026) + _four_quarters(ticker="FMTY14", year=2025)
    result = processor.process(records=records)
    years = [r.year for r in result]
    assert years == [2025, 2026]


def test_multiple_tickers_processed_independently(processor):
    """Two tickers with complete years each appear as independent keys in the output."""
    records = (
        _four_quarters(ticker="FMTY14", year=2025, ffo_per_cbfi=0.50)
        + _four_quarters(ticker="DANHOS13", year=2025, ffo_per_cbfi=0.30)
    )
    result = processor.process(records=records)
    assert "FMTY14" in [r.ticker for r in result]
    assert "DANHOS13" in [r.ticker for r in result]
    assert result[0].ffo_per_cbfi_annual == pytest.approx(1.20, rel=1e-6)
    assert result[1].ffo_per_cbfi_annual == pytest.approx(2.00, rel=1e-6)


# ── Error handling ────────────────────────────────────────────────────────────
def test_empty_records_raises(processor):
    """process() raises ValueError when the records list is empty."""
    with pytest.raises(ValueError):
        processor.process(records=[])


# ── New sum fields ────────────────────────────────────────────────────────────

def test_new_sum_fields_computed_correctly(processor):
    """noi_annual, ebitda_annual, ffo_annual, affo_annual, total_distribution_annual,
    noi_per_cbfi_annual, and ebitda_per_cbfi_annual are sums of four quarterly values."""
    records = _four_quarters(
        ticker="FMTY14",
        year=2025,
        noi=800_000_000,
        ebitda=700_000_000,
        ffo=600_000_000,
        affo=550_000_000,
        total_distribution=600_000_000.0,
        noi_per_cbfi=0.40,
        ebitda_per_cbfi=0.35,
    )
    result = processor.process(records=records)
    annual = result[0]
    assert annual.noi_annual == 3_200_000_000
    assert annual.ebitda_annual == 2_800_000_000
    assert annual.ffo_annual == 2_400_000_000
    assert annual.affo_annual == 2_200_000_000
    assert annual.total_distribution_annual == pytest.approx(2_400_000_000.0, rel=1e-6)
    assert annual.noi_per_cbfi_annual == pytest.approx(1.60, rel=1e-6)
    assert annual.ebitda_per_cbfi_annual == pytest.approx(1.40, rel=1e-6)


def test_annual_margins_computed_from_annual_sums_not_quarterly_averages(processor):
    """noi_margin_annual and ebitda_margin_annual use sum(noi)/sum(revenues),
    not mean(quarterly margins) — verified with unequal revenue quarters."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025",
                     noi=600_000_000, ebitda=400_000_000, total_revenues=1_000_000_000),
        _make_record(ticker="FMTY14", period="2T2025",
                     noi=600_000_000, ebitda=400_000_000, total_revenues=1_000_000_000),
        _make_record(ticker="FMTY14", period="3T2025",
                     noi=600_000_000, ebitda=400_000_000, total_revenues=1_000_000_000),
        _make_record(ticker="FMTY14", period="4T2025",
                     noi=200_000_000, ebitda=100_000_000, total_revenues=200_000_000),
    ]
    # Annual sums: noi=2_000_000_000, ebitda=1_300_000_000, revenues=3_200_000_000
    # Correct annual margins:  2_000/3_200 = 0.625,  1_300/3_200 = 0.40625
    # Wrong (avg of quarterly): (0.60+0.60+0.60+1.00)/4 = 0.70 != 0.625
    result = processor.process(records=records)
    annual = result[0]
    assert annual.noi_margin_annual == pytest.approx(2_000_000_000 / 3_200_000_000, rel=1e-6)
    assert annual.ebitda_margin_annual == pytest.approx(1_300_000_000 / 3_200_000_000, rel=1e-6)


def test_new_sum_fields_none_when_any_quarter_none(processor):
    """noi_annual and total_distribution_annual are None when one quarter has None."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025", noi=800_000_000, total_distribution=600_000_000.0),
        _make_record(ticker="FMTY14", period="2T2025", noi=None, total_distribution=None),
        _make_record(ticker="FMTY14", period="3T2025", noi=800_000_000, total_distribution=600_000_000.0),
        _make_record(ticker="FMTY14", period="4T2025", noi=800_000_000, total_distribution=600_000_000.0),
    ]
    result = processor.process(records=records)
    annual = result[0]
    assert annual.noi_annual is None
    assert annual.total_distribution_annual is None


def test_annual_margins_none_when_total_revenues_annual_none(processor):
    """noi_margin_annual and ebitda_margin_annual are None when total_revenues is None in any quarter."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025", noi=800_000_000, ebitda=700_000_000, total_revenues=None),
        _make_record(ticker="FMTY14", period="2T2025", noi=800_000_000, ebitda=700_000_000, total_revenues=None),
        _make_record(ticker="FMTY14", period="3T2025", noi=800_000_000, ebitda=700_000_000, total_revenues=None),
        _make_record(ticker="FMTY14", period="4T2025", noi=800_000_000, ebitda=700_000_000, total_revenues=None),
    ]
    result = processor.process(records=records)
    annual = result[0]
    assert annual.noi_margin_annual is None
    assert annual.ebitda_margin_annual is None


def test_annual_margins_none_when_total_revenues_annual_zero(processor):
    """noi_margin_annual and ebitda_margin_annual are None when total_revenues_annual is zero."""
    records = _four_quarters(
        ticker="FMTY14",
        year=2025,
        noi=800_000_000,
        ebitda=700_000_000,
        total_revenues=0,
    )
    result = processor.process(records=records)
    annual = result[0]
    assert annual.noi_margin_annual is None
    assert annual.ebitda_margin_annual is None


def test_q4_new_snapshot_fields_pass_through(processor):
    """gross_leasable_area_m2, cbfis_outstanding, cbfis_per_m2 are taken from the Q4 record."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025",
                     gross_leasable_area_m2=500_000, cbfis_outstanding=1_000_000_000, cbfis_per_m2=2_000.0),
        _make_record(ticker="FMTY14", period="2T2025",
                     gross_leasable_area_m2=500_000, cbfis_outstanding=1_000_000_000, cbfis_per_m2=2_000.0),
        _make_record(ticker="FMTY14", period="3T2025",
                     gross_leasable_area_m2=500_000, cbfis_outstanding=1_000_000_000, cbfis_per_m2=2_000.0),
        _make_record(ticker="FMTY14", period="4T2025",
                     gross_leasable_area_m2=600_000, cbfis_outstanding=1_500_000_000, cbfis_per_m2=2_500.0),
    ]
    result = processor.process(records=records)
    annual = result[0]
    assert annual.gross_leasable_area_m2 == 600_000
    assert annual.cbfis_outstanding == 1_500_000_000
    assert annual.cbfis_per_m2 == pytest.approx(2_500.0, rel=1e-6)


def test_q4_new_snapshot_fields_pass_through_none(processor):
    """gross_leasable_area_m2, cbfis_outstanding, cbfis_per_m2 are None when Q4 has None."""
    records = [
        _make_record(ticker="FMTY14", period="1T2025",
                     gross_leasable_area_m2=600_000, cbfis_outstanding=1_500_000_000, cbfis_per_m2=2_500.0),
        _make_record(ticker="FMTY14", period="2T2025",
                     gross_leasable_area_m2=600_000, cbfis_outstanding=1_500_000_000, cbfis_per_m2=2_500.0),
        _make_record(ticker="FMTY14", period="3T2025",
                     gross_leasable_area_m2=600_000, cbfis_outstanding=1_500_000_000, cbfis_per_m2=2_500.0),
        _make_record(ticker="FMTY14", period="4T2025",
                     gross_leasable_area_m2=None, cbfis_outstanding=None, cbfis_per_m2=None),
    ]
    result = processor.process(records=records)
    annual = result[0]
    assert annual.gross_leasable_area_m2 is None
    assert annual.cbfis_outstanding is None
    assert annual.cbfis_per_m2 is None
