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
