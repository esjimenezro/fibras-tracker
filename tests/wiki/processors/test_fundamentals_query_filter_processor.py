from datetime import date

import pytest

from modules.fundamentals.models import FundamentalsRecord
from modules.wiki.processors import FundamentalsQueryFilterProcessor


@pytest.fixture
def processor():
    """Return a FundamentalsQueryFilterProcessor instance."""
    return FundamentalsQueryFilterProcessor()


def _record(ticker: str, period: str) -> FundamentalsRecord:
    """Build a minimal FundamentalsRecord for the given ticker and period."""
    return FundamentalsRecord(ticker=ticker, period=period, report_date=date(2026, 3, 31))


@pytest.fixture
def records():
    """Three records across two tickers and two periods."""
    return [
        _record(ticker="FMTY14", period="1T2026"),
        _record(ticker="FMTY14", period="2T2026"),
        _record(ticker="DANHOS13", period="1T2026"),
    ]


def test_filters_by_ticker(processor, records):
    """Only records for the requested ticker are returned, in input order."""
    result = processor.process(records=records, ticker="FMTY14")

    assert [record.period for record in result] == ["1T2026", "2T2026"]


def test_filters_by_ticker_and_period(processor, records):
    """A period narrows the result to that single quarter."""
    result = processor.process(records=records, ticker="FMTY14", period="2T2026")

    assert [(record.ticker, record.period) for record in result] == [("FMTY14", "2T2026")]


def test_ticker_with_no_records_returns_empty(processor, records):
    """A ticker absent from the records yields an empty list, not an error."""
    assert processor.process(records=records, ticker="FIBRAPL14") == []


def test_empty_records_returns_empty(processor):
    """An empty record list yields an empty list."""
    assert processor.process(records=[], ticker="FMTY14") == []


def test_blank_ticker_raises(processor, records):
    """A blank ticker is malformed input and raises ValueError."""
    with pytest.raises(ValueError):
        processor.process(records=records, ticker="   ")
