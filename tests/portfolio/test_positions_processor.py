from datetime import date, datetime, timezone

import pytest

from modules.portfolio.models.enriched_distribution import EnrichedDistribution
from modules.portfolio.models.market_price import MarketPrice
from modules.portfolio.models.position import PaymentFrequency, Position
from modules.portfolio.processors.positions_processor import PositionsProcessor


@pytest.fixture
def processor():
    """Return a PositionsProcessor instance."""
    return PositionsProcessor()


@pytest.fixture
def position_a():
    """FMTY14 position: 1500 CBFIs at 9.58 MXN average cost."""
    return Position(
        ticker="FMTY14",
        name="Fibra Mty",
        sector="Industrial / Offices",
        cbfis=1500,
        average_purchase_cost=9.58,
        payment_frequency=PaymentFrequency.MONTHLY,
    )


@pytest.fixture
def position_b():
    """FSHOP13 position: 1000 CBFIs at 10.00 MXN average cost."""
    return Position(
        ticker="FSHOP13",
        name="Fibra Shop",
        sector="Retail / Shopping centers",
        cbfis=1000,
        average_purchase_cost=10.00,
        payment_frequency=PaymentFrequency.QUARTERLY,
    )


@pytest.fixture
def market_price_a():
    """Current market price for FMTY14: 10.50 MXN."""
    return MarketPrice(
        ticker="FMTY14",
        price=10.50,
        currency="MXN",
        retrieved_at=datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def market_price_b():
    """Current market price for FSHOP13: 11.00 MXN."""
    return MarketPrice(
        ticker="FSHOP13",
        price=11.00,
        currency="MXN",
        retrieved_at=datetime(2026, 5, 16, 11, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def dist_fmty14():
    """EnrichedDistribution for FMTY14 with net_fiscal_result_income=50.715.

    Derived from: reimbursement=0.0331, fiscal=0.0483, cbfis=1500.
    """
    return EnrichedDistribution(
        ticker="FMTY14",
        payment_date=date(2026, 3, 6),
        reimbursement_per_cbfi=0.0331,
        fiscal_result_per_cbfi=0.0483,
        cbfis_at_time=1500,
        gross_fiscal_result_income=72.45,
        net_reimbursement_income=49.65,
        gross_income=122.10,
        fiscal_result_withholding=21.735,
        net_fiscal_result_income=50.715,
        net_income=100.365,
    )


@pytest.fixture
def dist_fshop13():
    """EnrichedDistribution for FSHOP13 with net_fiscal_result_income=35.0.

    Derived from: reimbursement=0.0, fiscal=0.05, cbfis=1000.
    """
    return EnrichedDistribution(
        ticker="FSHOP13",
        payment_date=date(2026, 3, 31),
        reimbursement_per_cbfi=0.0,
        fiscal_result_per_cbfi=0.05,
        cbfis_at_time=1000,
        gross_fiscal_result_income=50.0,
        net_reimbursement_income=0.0,
        gross_income=50.0,
        fiscal_result_withholding=15.0,
        net_fiscal_result_income=35.0,
        net_income=35.0,
    )


def test_return_per_cbfi(processor, position_a, market_price_a):
    """return_per_cbfi = market_price - average_purchase_cost."""
    result = processor.enrich(position_a, market_price_a, [])
    assert result.return_per_cbfi == pytest.approx(0.92, rel=1e-6)


def test_purchase_cost(processor, position_a, market_price_a):
    """purchase_cost = average_purchase_cost * cbfis."""
    result = processor.enrich(position_a, market_price_a, [])
    assert result.purchase_cost == pytest.approx(14_370.0, rel=1e-6)


def test_market_value(processor, position_a, market_price_a):
    """market_value = market_price * cbfis."""
    result = processor.enrich(position_a, market_price_a, [])
    assert result.market_value == pytest.approx(15_750.0, rel=1e-6)


def test_return_pct(processor, position_a, market_price_a):
    """return_pct = return_per_cbfi / average_purchase_cost."""
    result = processor.enrich(position_a, market_price_a, [])
    assert result.return_pct == pytest.approx(0.92 / 9.58, rel=1e-6)


def test_total_return(processor, position_a, market_price_a):
    """total_return = return_per_cbfi * cbfis."""
    result = processor.enrich(position_a, market_price_a, [])
    assert result.total_return == pytest.approx(1_380.0, rel=1e-6)


def test_total_net_fiscal_result_received(processor, position_a, market_price_a, dist_fmty14):
    """total_net_fiscal_result_received = sum of net_fiscal_result_income for all distributions."""
    result = processor.enrich(position_a, market_price_a, [dist_fmty14])
    assert result.total_net_fiscal_result_received == pytest.approx(50.715, rel=1e-6)


def test_total_return_including_distributions(processor, position_a, market_price_a, dist_fmty14):
    """total_return_including_distributions = total_return + total_net_fiscal_result_received."""
    result = processor.enrich(position_a, market_price_a, [dist_fmty14])
    assert result.total_return_including_distributions == pytest.approx(1_430.715, rel=1e-6)


def test_price_updated_at_propagated(processor, position_a, market_price_a):
    """price_updated_at on the enriched position matches the market price timestamp."""
    result = processor.enrich(position_a, market_price_a, [])
    assert result.price_updated_at == market_price_a.retrieved_at


def test_missing_market_price_raises(processor, position_a):
    """process() raises ValueError when a position has no matching market price."""
    with pytest.raises(ValueError):
        processor.process([position_a], [], [])


def test_no_distributions_gives_zero_fiscal(processor, position_a, market_price_a):
    """When distributions=[], total_net_fiscal_result_received=0 and total_return_including_distributions equals total_return."""
    result = processor.enrich(position_a, market_price_a, [])
    assert result.total_net_fiscal_result_received == pytest.approx(0.0, abs=1e-9)
    assert result.total_return_including_distributions == pytest.approx(result.total_return, rel=1e-6)


def test_process_multiple_positions(processor, position_a, position_b, market_price_a, market_price_b):
    """process() returns one enriched position per input position, joined by ticker."""
    results = processor.process([position_a, position_b], [market_price_a, market_price_b], [])
    assert len(results) == 2
    assert results[0].ticker == "FMTY14"
    assert results[1].ticker == "FSHOP13"


def test_distributions_filtered_by_ticker(processor, position_a, position_b, market_price_a, market_price_b, dist_fmty14, dist_fshop13):
    """Each enriched position only receives distributions whose ticker matches its own."""
    results = processor.process(
        [position_a, position_b],
        [market_price_a, market_price_b],
        [dist_fmty14, dist_fshop13],
    )
    assert results[0].distributions == [dist_fmty14]
    assert results[1].distributions == [dist_fshop13]
