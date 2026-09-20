from datetime import date
from datetime import datetime
from datetime import timezone

import pytest

from modules.common.models import Fibra
from modules.common.models import MarketPrice
from modules.common.models import PaymentFrequency
from modules.common.models import Sector
from modules.common.models import SectorExposure
from modules.common.schemas import ServiceStatus
from modules.portfolio.models import Distribution
from modules.portfolio.models import Position
from modules.portfolio.services import PortfolioDataRetrieverService


# --- Fakes (constructor-injected, no mocking library) -----------------------

class _FakePositionsRepository:
    """Returns a fixed list of Position records."""

    def __init__(self, positions):
        """Store the positions to return."""
        self._positions = positions

    def retrieve_data(self):
        """Return the stored positions."""
        return self._positions


class _FakeDistributionsRepository:
    """Returns a fixed list of Distribution records."""

    def __init__(self, distributions):
        """Store the distributions to return."""
        self._distributions = distributions

    def retrieve_data(self):
        """Return the stored distributions."""
        return self._distributions


class _FakeCatalogRepository:
    """Returns a fixed list of Fibra catalog entries."""

    def __init__(self, fibras):
        """Store the fibras to return."""
        self._fibras = fibras

    def retrieve_data(self):
        """Return the stored fibras."""
        return self._fibras


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
def position_fmty14():
    """FMTY14 position: 100 CBFIs at 10.0 MXN average cost."""
    return Position(ticker="FMTY14", cbfis=100, average_purchase_cost=10.0)


@pytest.fixture
def distribution_fmty14():
    """A single FMTY14 distribution payment."""
    return Distribution(
        ticker="FMTY14",
        payment_date=date(2026, 3, 6),
        reimbursement_total=5.0,
        fiscal_result_total=10.0,
    )


@pytest.fixture
def market_price_fmty14():
    """FMTY14 market price of 12.0 MXN."""
    return MarketPrice(
        ticker="FMTY14",
        price=12.0,
        currency="MXN",
        retrieved_at=datetime(2026, 3, 10, tzinfo=timezone.utc),
    )


def _make_service(positions, distributions, prices, fibras):
    """Wire PortfolioDataRetrieverService with fake repositories.

    Args:
        positions: Positions the fake positions repository returns.
        distributions: Distributions the fake distributions repository returns.
        prices: Prices the fake market price repository returns.
        fibras: Fibras the fake catalog repository returns.

    Returns:
        tuple[PortfolioDataRetrieverService, _FakeMarketPriceRepository]: The wired
            service and its market price repository, so tests can inspect calls.
    """
    market_price_repository = _FakeMarketPriceRepository(prices)
    service = PortfolioDataRetrieverService(
        position_repository=_FakePositionsRepository(positions),
        distribution_repository=_FakeDistributionsRepository(distributions),
        market_price_repository=market_price_repository,
        catalog_repository=_FakeCatalogRepository(fibras),
    )
    return service, market_price_repository


# --- Happy path ---------------------------------------------------------------

def test_run_ok_assembles_portfolio(
    fibra_fmty14, position_fmty14, distribution_fmty14, market_price_fmty14,
):
    """A consistent set of fake repositories yields status=OK with an assembled Portfolio."""
    service, _ = _make_service(
        positions=[position_fmty14],
        distributions=[distribution_fmty14],
        prices=[market_price_fmty14],
        fibras=[fibra_fmty14],
    )

    result = service.run()

    assert result.status == ServiceStatus.OK
    assert result.error_message is None
    assert [p.ticker for p in result.data.portfolio_positions] == ["FMTY14"]
    assert result.data.total_purchase_cost == pytest.approx(1000.0)
    assert result.data.total_market_value == pytest.approx(1200.0)
    assert len(result.data.all_distributions) == 1


def test_run_computes_price_tickers_from_positions(
    fibra_fmty14, position_fmty14, distribution_fmty14, market_price_fmty14,
):
    """run() derives the market price lookup tickers from positions, unmodified."""
    service, market_price_repository = _make_service(
        positions=[position_fmty14],
        distributions=[distribution_fmty14],
        prices=[market_price_fmty14],
        fibras=[fibra_fmty14],
    )

    service.run()

    assert market_price_repository.calls == [["FMTY14"]]


# --- Error handling -------------------------------------------------------------

def test_run_returns_error_status_when_a_repository_raises(
    fibra_fmty14, distribution_fmty14, market_price_fmty14,
):
    """A repository failure (e.g. a missing data file) becomes status=ERROR, never raises."""
    market_price_repository = _FakeMarketPriceRepository([market_price_fmty14])
    service = PortfolioDataRetrieverService(
        position_repository=_RaisingRepository(FileNotFoundError("positions.json not found")),
        distribution_repository=_FakeDistributionsRepository([distribution_fmty14]),
        market_price_repository=market_price_repository,
        catalog_repository=_FakeCatalogRepository([fibra_fmty14]),
    )

    result = service.run()

    assert result.status == ServiceStatus.ERROR
    assert result.data is None
    assert "positions.json not found" in result.error_message


def test_run_returns_error_status_when_positions_are_empty(
    fibra_fmty14, distribution_fmty14, market_price_fmty14,
):
    """An empty positions list reaches PortfolioProcessor's ValueError, caught as status=ERROR."""
    service, _ = _make_service(
        positions=[],
        distributions=[distribution_fmty14],
        prices=[market_price_fmty14],
        fibras=[fibra_fmty14],
    )

    result = service.run()

    assert result.status == ServiceStatus.ERROR
    assert result.data is None
    assert "empty positions" in result.error_message
