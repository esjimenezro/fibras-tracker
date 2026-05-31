from datetime import date

import pytest

from modules.common.models import Fibra
from modules.common.models import PaymentFrequency
from modules.common.models import Sector
from modules.common.models import SectorExposure
from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.processors import FundamentalsHistoryProcessor


def _make_enriched_record(ticker: str, period: str, report_date: date) -> EnrichedFundamentalsRecord:
    """Build a minimal EnrichedFundamentalsRecord for history-processor tests.

    All computed fields default to None; the history processor does not use them.

    Args:
        ticker: BMV ticker string.
        period: Period label (e.g. "1T2026").
        report_date: Date the report covers.

    Returns:
        EnrichedFundamentalsRecord with only the identity fields populated.
    """
    return EnrichedFundamentalsRecord(
        ticker=ticker,
        period=period,
        report_date=report_date,
    )


def _make_enriched_record_with_affo(
    ticker: str,
    period: str,
    affo: int | None,
    affo_per_cbfi: float | None,
) -> EnrichedFundamentalsRecord:
    """Build an EnrichedFundamentalsRecord with AFFO fields populated.

    All other fields default to None. The report_date is fixed to avoid
    test noise — history-processor tests do not use it.

    Args:
        ticker: BMV ticker string.
        period: Period label (e.g. "1T2023").
        affo: AFFO value in MXN; may be None.
        affo_per_cbfi: AFFO per CBFI; may be None.

    Returns:
        EnrichedFundamentalsRecord with affo and affo_per_cbfi set.
    """
    return EnrichedFundamentalsRecord(
        ticker=ticker,
        period=period,
        report_date=date(2023, 1, 1),
        affo=affo,
        affo_per_cbfi=affo_per_cbfi,
    )


@pytest.fixture
def processor():
    """Return a FundamentalsHistoryProcessor instance."""
    return FundamentalsHistoryProcessor()


@pytest.fixture
def record_fmty14_4t2025():
    """FMTY14 Q4 2025 with a late report_date (2026-04-30) to distinguish period from report_date sorting."""
    return _make_enriched_record(ticker="FMTY14", period="4T2025", report_date=date(2026, 4, 30))


@pytest.fixture
def record_fmty14_1t2026():
    """FMTY14 Q1 2026 with an earlier report_date (2026-04-20) than the Q4 2025 record."""
    return _make_enriched_record(ticker="FMTY14", period="1T2026", report_date=date(2026, 4, 20))


@pytest.fixture
def record_danhos13_1t2026():
    """DANHOS13 Q1 2026."""
    return _make_enriched_record(ticker="DANHOS13", period="1T2026", report_date=date(2026, 4, 30))


@pytest.fixture
def record_danhos13_2t2026():
    """DANHOS13 Q2 2026."""
    return _make_enriched_record(ticker="DANHOS13", period="2T2026", report_date=date(2026, 7, 31))


@pytest.fixture
def record_fmty14_1t2025():
    """FMTY14 Q1 2025 — prior-year counterpart of record_fmty14_1t2026."""
    return _make_enriched_record(ticker="FMTY14", period="1T2025", report_date=date(2025, 4, 20))


@pytest.fixture
def fibra_fmty14():
    """Catalog entry for FMTY14."""
    return Fibra(
        ticker="FMTY14",
        name="Fibra Mty",
        payment_frequency=PaymentFrequency.MONTHLY,
        sector_exposure=[SectorExposure(sector=Sector.INDUSTRIAL, weight=1.0)],
    )


@pytest.fixture
def fibra_danhos13():
    """Catalog entry for DANHOS13."""
    return Fibra(
        ticker="DANHOS13",
        name="Fibra Danhos",
        payment_frequency=PaymentFrequency.QUARTERLY,
        sector_exposure=[SectorExposure(sector=Sector.COMERCIAL, weight=1.0)],
    )


@pytest.fixture
def fibra_fibrapl14():
    """Catalog entry for FIBRAPL14 — no fundamentals records provided in any test."""
    return Fibra(
        ticker="FIBRAPL14",
        name="Fibra Prologis",
        payment_frequency=PaymentFrequency.QUARTERLY,
        sector_exposure=[SectorExposure(sector=Sector.INDUSTRIAL, weight=1.0)],
    )


def test_records_sorted_by_ticker_then_period(
    processor,
    record_fmty14_1t2026,
    record_danhos13_2t2026,
    record_fmty14_4t2025,
    record_danhos13_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """Records are sorted by ticker ascending, then by (year, quarter) ascending.

    Shuffled input: [FMTY14 1T2026, DANHOS13 2T2026, FMTY14 4T2025, DANHOS13 1T2026]
    Expected output: DANHOS13 1T2026, DANHOS13 2T2026, FMTY14 4T2025, FMTY14 1T2026.
    """
    result = processor.process(
        records=[record_fmty14_1t2026, record_danhos13_2t2026, record_fmty14_4t2025, record_danhos13_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.records[0].ticker == "DANHOS13"
    assert result.records[0].period == "1T2026"
    assert result.records[1].ticker == "DANHOS13"
    assert result.records[1].period == "2T2026"
    assert result.records[2].ticker == "FMTY14"
    assert result.records[2].period == "4T2025"
    assert result.records[3].ticker == "FMTY14"
    assert result.records[3].period == "1T2026"


def test_sort_is_not_lexicographic(
    processor,
    record_fmty14_1t2026,
    record_fmty14_4t2025,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """FMTY14 4T2025 sorts before 1T2026 because (2025, 4) < (2026, 1).

    Lexicographic comparison would place "1T2026" before "4T2025" (since "1" < "4"),
    which would be wrong.
    """
    result = processor.process(
        records=[record_fmty14_1t2026, record_fmty14_4t2025],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.records[0].period == "4T2025"
    assert result.records[1].period == "1T2026"


def test_latest_by_ticker_correct(
    processor,
    record_fmty14_1t2026,
    record_danhos13_2t2026,
    record_fmty14_4t2025,
    record_danhos13_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """latest_by_ticker holds the most recent record per ticker as determined by period."""
    result = processor.process(
        records=[record_fmty14_1t2026, record_danhos13_2t2026, record_fmty14_4t2025, record_danhos13_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.latest_by_ticker["DANHOS13"].period == "2T2026"
    assert result.latest_by_ticker["FMTY14"].period == "1T2026"


def test_latest_determined_by_period_not_report_date(
    processor,
    record_fmty14_1t2026,
    record_fmty14_4t2025,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """latest_by_ticker picks the record with the most recent period, not the latest report_date.

    record_fmty14_4t2025 has report_date=2026-04-30 (later than record_fmty14_1t2026's 2026-04-20).
    A sort by report_date would wrongly select 4T2025 as the latest; period-based sorting must
    select 1T2026 because (2026, 1) > (2025, 4).
    """
    result = processor.process(
        records=[record_fmty14_1t2026, record_fmty14_4t2025],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.latest_by_ticker["FMTY14"].period == "1T2026"


def test_latest_by_ticker_none_for_missing_ticker(
    processor,
    record_fmty14_1t2026,
    record_danhos13_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """latest_by_ticker contains None for a catalog ticker that has no fundamentals records."""
    result = processor.process(
        records=[record_fmty14_1t2026, record_danhos13_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.latest_by_ticker["FIBRAPL14"] is None


def test_fibras_preserved(
    processor,
    record_fmty14_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """history.fibras contains the exact Fibra list passed to process()."""
    fibras = [fibra_fmty14, fibra_danhos13, fibra_fibrapl14]
    result = processor.process(
        records=[record_fmty14_1t2026],
        fibras=fibras,
    )
    assert result.fibras == fibras


def test_empty_records_raises(processor, fibra_fmty14):
    """process() raises ValueError when the records list is empty."""
    with pytest.raises(ValueError):
        processor.process(records=[], fibras=[fibra_fmty14])


def test_prior_year_by_ticker_found(
    processor,
    record_fmty14_1t2025,
    record_fmty14_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """prior_year_by_ticker holds the same-quarter prior-year record when it exists."""
    result = processor.process(
        records=[record_fmty14_1t2025, record_fmty14_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.prior_year_by_ticker["FMTY14"] is record_fmty14_1t2025


def test_prior_year_by_ticker_none_when_not_found(
    processor,
    record_fmty14_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """prior_year_by_ticker is None when the same-quarter prior-year record does not exist."""
    result = processor.process(
        records=[record_fmty14_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.prior_year_by_ticker["FMTY14"] is None


def test_prior_year_by_ticker_none_for_missing_ticker(
    processor,
    record_fmty14_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """prior_year_by_ticker is None for a catalog ticker that has no fundamentals records."""
    result = processor.process(
        records=[record_fmty14_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.prior_year_by_ticker["FIBRAPL14"] is None


def test_fibra_metrics_cagr_computed_for_sufficient_history(
    processor,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """fibra_metrics computes CAGR correctly for a ticker with 4 records.

    Four FMTY14 records spanning 1T2023–4T2023:
      years_of_history = (2023 + 3/4) - (2023 + 0/4) = 0.75
      affo: 1000 → 1331 (geometric: *1.1 each quarter)
      affo_per_cbfi: 1.0 → 1.331 (same factor)
      cagr = (1331/1000)^(1/0.75) - 1 = 1.1^4 - 1 = 0.4641
    """
    records = [
        _make_enriched_record_with_affo(ticker="FMTY14", period="1T2023", affo=1000, affo_per_cbfi=1.0),
        _make_enriched_record_with_affo(ticker="FMTY14", period="2T2023", affo=1100, affo_per_cbfi=1.1),
        _make_enriched_record_with_affo(ticker="FMTY14", period="3T2023", affo=1210, affo_per_cbfi=1.21),
        _make_enriched_record_with_affo(ticker="FMTY14", period="4T2023", affo=1331, affo_per_cbfi=1.331),
    ]
    result = processor.process(
        records=records,
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    metrics = result.fibra_metrics["FMTY14"]
    assert metrics.ticker == "FMTY14"
    assert metrics.periods_count == 4
    assert metrics.years_of_history == pytest.approx(0.75, rel=1e-6)
    assert metrics.affo_first == pytest.approx(1000.0, rel=1e-6)
    assert metrics.affo_latest == pytest.approx(1331.0, rel=1e-6)
    assert metrics.cagr_affo_total == pytest.approx(0.4641, rel=1e-4)
    assert metrics.affo_per_cbfi_first == pytest.approx(1.0, rel=1e-6)
    assert metrics.affo_per_cbfi_latest == pytest.approx(1.331, rel=1e-6)
    assert metrics.cagr_affo_per_cbfi == pytest.approx(0.4641, rel=1e-4)


def test_fibra_metrics_optional_fields_none_for_3_records(
    processor,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """All Optional fields are None when a ticker has exactly 3 records.

    3 FMTY14 records spanning 1T2023–3T2023:
      years_of_history = (2023 + 2/4) - (2023 + 0/4) = 0.5
    """
    records = [
        _make_enriched_record_with_affo(ticker="FMTY14", period="1T2023", affo=1000, affo_per_cbfi=1.0),
        _make_enriched_record_with_affo(ticker="FMTY14", period="2T2023", affo=1100, affo_per_cbfi=1.1),
        _make_enriched_record_with_affo(ticker="FMTY14", period="3T2023", affo=1210, affo_per_cbfi=1.21),
    ]
    result = processor.process(
        records=records,
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    metrics = result.fibra_metrics["FMTY14"]
    assert metrics.periods_count == 3
    assert metrics.years_of_history == pytest.approx(0.5, rel=1e-6)
    assert metrics.affo_first is None
    assert metrics.affo_latest is None
    assert metrics.cagr_affo_total is None
    assert metrics.affo_per_cbfi_first is None
    assert metrics.affo_per_cbfi_latest is None
    assert metrics.cagr_affo_per_cbfi is None


def test_fibra_metrics_optional_fields_none_for_no_records(
    processor,
    record_fmty14_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """All Optional fields are None, periods_count=0, years_of_history=0.0 for a ticker with no records."""
    result = processor.process(
        records=[record_fmty14_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    metrics = result.fibra_metrics["FIBRAPL14"]
    assert metrics.ticker == "FIBRAPL14"
    assert metrics.periods_count == 0
    assert metrics.years_of_history == 0.0
    assert metrics.affo_first is None
    assert metrics.affo_latest is None
    assert metrics.cagr_affo_total is None
    assert metrics.affo_per_cbfi_first is None
    assert metrics.affo_per_cbfi_latest is None
    assert metrics.cagr_affo_per_cbfi is None


def test_fibra_metrics_cagr_affo_total_none_when_affo_is_none_in_first_record(
    processor,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """cagr_affo_total is None when affo is None in the first record."""
    records = [
        _make_enriched_record_with_affo(ticker="FMTY14", period="1T2023", affo=None, affo_per_cbfi=1.0),
        _make_enriched_record_with_affo(ticker="FMTY14", period="2T2023", affo=1100, affo_per_cbfi=1.1),
        _make_enriched_record_with_affo(ticker="FMTY14", period="3T2023", affo=1210, affo_per_cbfi=1.21),
        _make_enriched_record_with_affo(ticker="FMTY14", period="4T2023", affo=1331, affo_per_cbfi=1.331),
    ]
    result = processor.process(
        records=records,
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.fibra_metrics["FMTY14"].cagr_affo_total is None


def test_fibra_metrics_cagr_affo_per_cbfi_none_when_affo_per_cbfi_is_none_in_last_record(
    processor,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """cagr_affo_per_cbfi is None when affo_per_cbfi is None in the last record."""
    records = [
        _make_enriched_record_with_affo(ticker="FMTY14", period="1T2023", affo=1000, affo_per_cbfi=1.0),
        _make_enriched_record_with_affo(ticker="FMTY14", period="2T2023", affo=1100, affo_per_cbfi=1.1),
        _make_enriched_record_with_affo(ticker="FMTY14", period="3T2023", affo=1210, affo_per_cbfi=1.21),
        _make_enriched_record_with_affo(ticker="FMTY14", period="4T2023", affo=1331, affo_per_cbfi=None),
    ]
    result = processor.process(
        records=records,
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert result.fibra_metrics["FMTY14"].cagr_affo_per_cbfi is None


def test_fibra_metrics_contains_entry_for_every_ticker_in_fibras(
    processor,
    record_fmty14_1t2026,
    fibra_fmty14,
    fibra_danhos13,
    fibra_fibrapl14,
):
    """fibra_metrics contains an entry for every ticker in fibras, including those with no records."""
    result = processor.process(
        records=[record_fmty14_1t2026],
        fibras=[fibra_fmty14, fibra_danhos13, fibra_fibrapl14],
    )
    assert "FMTY14" in result.fibra_metrics
    assert "DANHOS13" in result.fibra_metrics
    assert "FIBRAPL14" in result.fibra_metrics
