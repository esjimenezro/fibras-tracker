from datetime import date
from datetime import datetime
from datetime import timezone

import pytest

from modules.common.models import Fibra
from modules.common.models import InflationRecord
from modules.common.models import MarketPrice
from modules.common.models import PaymentFrequency
from modules.common.models import Sector
from modules.common.models import SectorExposure
from modules.common.schemas import ServiceStatus
from modules.fundamentals.models import FundamentalsRecord
from modules.fundamentals.services import FundamentalsDataRetrieverService


# --- Fakes (constructor-injected, no mocking library) -----------------------

class _FakeFundamentalsRepository:
    """Returns a fixed list of FundamentalsRecord entries."""

    def __init__(self, records):
        """Store the records to return."""
        self._records = records

    def retrieve_data(self):
        """Return the stored records."""
        return self._records


class _FakeCatalogRepository:
    """Returns a fixed list of Fibra catalog entries."""

    def __init__(self, fibras):
        """Store the fibras to return."""
        self._fibras = fibras

    def retrieve_data(self):
        """Return the stored fibras."""
        return self._fibras


class _FakeInflationRepository:
    """Returns a fixed list of InflationRecord entries."""

    def __init__(self, records):
        """Store the inflation records to return."""
        self._records = records

    def retrieve_data(self):
        """Return the stored inflation records."""
        return self._records


class _FakeMarketPriceRepository:
    """Returns a fixed list of MarketPrice records and records every call's tickers."""

    def __init__(self, prices):
        """Store the prices to return and initialise the call log."""
        self._prices = prices
        self.calls: list[list[str]] = []

    def retrieve_data(self, tickers):
        """Record the requested tickers, then return the stored prices."""
        self.calls.append(list(tickers))
        return self._prices


class _RaisingRepository:
    """Raises a scripted exception from retrieve_data(), regardless of arguments."""

    def __init__(self, exc):
        """Store the exception to raise."""
        self._exc = exc

    def retrieve_data(self, *args, **kwargs):
        """Raise the scripted exception."""
        raise self._exc


# --- Fixtures ----------------------------------------------------------------

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
def fmty14_full_year_2025():
    """Four complete FMTY14 quarters for 2025 — the minimum for one AnnualFundamentalsRecord."""
    return [
        FundamentalsRecord(ticker="FMTY14", period=f"{quarter}T2025", report_date=date(2025, quarter * 3, 1))
        for quarter in range(1, 5)
    ]


@pytest.fixture
def inflation_2025():
    """A single annual inflation record covering 2025."""
    return [InflationRecord(year=2025, annual_inflation=0.045)]


@pytest.fixture
def market_price_fmty14():
    """FMTY14 market price of 12.0 MXN."""
    return MarketPrice(
        ticker="FMTY14",
        price=12.0,
        currency="MXN",
        retrieved_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
    )


def _make_service(records, prices, fibras, inflation_records):
    """Wire FundamentalsDataRetrieverService with fake repositories.

    Args:
        records: Records the fake fundamentals repository returns.
        prices: Prices the fake market price repository returns.
        fibras: Fibras the fake catalog repository returns.
        inflation_records: Records the fake inflation repository returns.

    Returns:
        tuple[FundamentalsDataRetrieverService, _FakeMarketPriceRepository]: The wired
            service and its market price repository, so tests can inspect calls.
    """
    market_price_repository = _FakeMarketPriceRepository(prices)
    service = FundamentalsDataRetrieverService(
        fundamentals_repository=_FakeFundamentalsRepository(records),
        market_price_repository=market_price_repository,
        catalog_repository=_FakeCatalogRepository(fibras),
        inflation_repository=_FakeInflationRepository(inflation_records),
    )
    return service, market_price_repository


# --- Happy path ---------------------------------------------------------------

def test_run_ok_assembles_history(
    fibra_fmty14, fmty14_full_year_2025, inflation_2025, market_price_fmty14,
):
    """A complete year of fake data yields status=OK with an assembled FundamentalsHistory."""
    service, _ = _make_service(
        records=fmty14_full_year_2025,
        prices=[market_price_fmty14],
        fibras=[fibra_fmty14],
        inflation_records=inflation_2025,
    )

    result = service.run()

    assert result.status == ServiceStatus.OK
    assert result.error_message is None
    assert len(result.data.records) == 4
    assert isinstance(result.data.annual_records, dict)
    assert [r.year for r in result.data.annual_records["FMTY14"]] == [2025]


def test_run_computes_price_tickers_sorted_and_deduped(
    fibra_fmty14, fmty14_full_year_2025, inflation_2025, market_price_fmty14,
):
    """run() derives the market price lookup tickers from records: unique and sorted."""
    duplicated_ticker_records = fmty14_full_year_2025 + [
        FundamentalsRecord(ticker="FMTY14", period="1T2025", report_date=date(2025, 3, 1)),
    ]
    service, market_price_repository = _make_service(
        records=duplicated_ticker_records,
        prices=[market_price_fmty14],
        fibras=[fibra_fmty14],
        inflation_records=inflation_2025,
    )

    service.run()

    assert market_price_repository.calls == [["FMTY14"]]


# --- Error handling -------------------------------------------------------------

def test_run_returns_error_status_when_a_repository_raises(
    fibra_fmty14, inflation_2025, market_price_fmty14,
):
    """A repository failure (e.g. a missing data file) becomes status=ERROR, never raises."""
    service = FundamentalsDataRetrieverService(
        fundamentals_repository=_RaisingRepository(FileNotFoundError("fundamentals.json not found")),
        market_price_repository=_FakeMarketPriceRepository([market_price_fmty14]),
        catalog_repository=_FakeCatalogRepository([fibra_fmty14]),
        inflation_repository=_FakeInflationRepository(inflation_2025),
    )

    result = service.run()

    assert result.status == ServiceStatus.ERROR
    assert result.data is None
    assert "fundamentals.json not found" in result.error_message


def test_run_returns_error_status_when_no_ticker_has_a_complete_year(
    fibra_fmty14, inflation_2025, market_price_fmty14,
):
    """An incomplete year yields no AnnualFundamentalsRecord, caught as status=ERROR."""
    incomplete_year = [
        FundamentalsRecord(ticker="FMTY14", period="1T2025", report_date=date(2025, 3, 1)),
        FundamentalsRecord(ticker="FMTY14", period="2T2025", report_date=date(2025, 6, 1)),
    ]
    service, _ = _make_service(
        records=incomplete_year,
        prices=[market_price_fmty14],
        fibras=[fibra_fmty14],
        inflation_records=inflation_2025,
    )

    result = service.run()

    assert result.status == ServiceStatus.ERROR
    assert result.data is None
    assert "Annual records" in result.error_message
