from datetime import datetime, timezone

import pytest

from modules.portfolio.models.enriched_position import EnrichedPosition
from modules.portfolio.models.position import PaymentFrequency
from modules.portfolio.processors.portfolio_processor import PortfolioProcessor


def _make_enriched_position(
    ticker: str,
    cbfis: int,
    average_purchase_cost: float,
    market_price: float,
    purchase_cost: float,
    market_value: float,
    total_net_fiscal_result_received: float,
    price_updated_at: datetime,
) -> EnrichedPosition:
    """Build an EnrichedPosition with computed fields set explicitly for test control.

    Args:
        ticker: BMV ticker string.
        cbfis: Number of CBFIs held.
        average_purchase_cost: Weighted average purchase cost per CBFI.
        market_price: Current market price per CBFI.
        purchase_cost: Total invested (average_purchase_cost * cbfis).
        market_value: Current market value (market_price * cbfis).
        total_net_fiscal_result_received: Sum of net fiscal distributions received.
        price_updated_at: UTC timestamp of the market price fetch.

    Returns:
        EnrichedPosition: Fully populated model ready for PortfolioProcessor input.
    """
    return_per_cbfi = market_price - average_purchase_cost
    total_return = return_per_cbfi * cbfis
    return EnrichedPosition(
        ticker=ticker,
        name=ticker,
        sector="Test sector",
        cbfis=cbfis,
        average_purchase_cost=average_purchase_cost,
        payment_frequency=PaymentFrequency.QUARTERLY,
        market_price=market_price,
        price_updated_at=price_updated_at,
        purchase_cost=purchase_cost,
        market_value=market_value,
        return_per_cbfi=return_per_cbfi,
        return_pct=return_per_cbfi / average_purchase_cost,
        total_return=total_return,
        distributions=[],
        total_net_fiscal_result_received=total_net_fiscal_result_received,
        total_return_including_distributions=total_return + total_net_fiscal_result_received,
    )


T1 = datetime(2026, 5, 16, 10, 0, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def processor():
    """Return a PortfolioProcessor instance."""
    return PortfolioProcessor()


@pytest.fixture
def enriched_a():
    """FMTY14 position: purchase_cost=14_370, market_value=15_750, fiscal_received=50.715."""
    return _make_enriched_position(
        ticker="FMTY14",
        cbfis=1500,
        average_purchase_cost=9.58,
        market_price=10.50,
        purchase_cost=14_370.0,
        market_value=15_750.0,
        total_net_fiscal_result_received=50.715,
        price_updated_at=T1,
    )


@pytest.fixture
def enriched_b():
    """FSHOP13 position: purchase_cost=10_000, market_value=11_000, fiscal_received=30.0."""
    return _make_enriched_position(
        ticker="FSHOP13",
        cbfis=1000,
        average_purchase_cost=10.00,
        market_price=11.00,
        purchase_cost=10_000.0,
        market_value=11_000.0,
        total_net_fiscal_result_received=30.0,
        price_updated_at=T2,
    )


def test_empty_positions_raises(processor):
    """process() raises ValueError when the positions list is empty."""
    with pytest.raises(ValueError):
        processor.process([])


def test_total_purchase_cost(processor, enriched_a, enriched_b):
    """total_purchase_cost = sum of purchase_cost across all positions."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert portfolio.total_purchase_cost == pytest.approx(24_370.0, rel=1e-6)


def test_total_market_value(processor, enriched_a, enriched_b):
    """total_market_value = sum of market_value across all positions."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert portfolio.total_market_value == pytest.approx(26_750.0, rel=1e-6)


def test_total_return(processor, enriched_a, enriched_b):
    """total_return = total_market_value - total_purchase_cost."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert portfolio.total_return == pytest.approx(2_380.0, rel=1e-6)


def test_total_return_pct(processor, enriched_a, enriched_b):
    """total_return_pct = total_return / total_purchase_cost."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert portfolio.total_return_pct == pytest.approx(2_380.0 / 24_370.0, rel=1e-6)


def test_total_net_fiscal_result_received(processor, enriched_a, enriched_b):
    """total_net_fiscal_result_received = sum of total_net_fiscal_result_received across all positions."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert portfolio.total_net_fiscal_result_received == pytest.approx(80.715, rel=1e-6)


def test_total_return_including_distributions(processor, enriched_a, enriched_b):
    """total_return_including_distributions = total_return + total_net_fiscal_result_received."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert portfolio.total_return_including_distributions == pytest.approx(2_460.715, rel=1e-6)


def test_positions_share_sums_to_one(processor, enriched_a, enriched_b):
    """Sum of all position shares equals 1.0."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert sum(ps.share for ps in portfolio.positions_share) == pytest.approx(1.0, rel=1e-6)


def test_positions_share_per_ticker(processor, enriched_a, enriched_b):
    """Each position share = market_value / total_market_value."""
    portfolio = processor.process([enriched_a, enriched_b])
    shares = {ps.ticker: ps.share for ps in portfolio.positions_share}
    assert shares["FMTY14"] == pytest.approx(15_750.0 / 26_750.0, rel=1e-6)
    assert shares["FSHOP13"] == pytest.approx(11_000.0 / 26_750.0, rel=1e-6)


def test_last_updated_at(processor, enriched_a, enriched_b):
    """last_updated_at = max of price_updated_at across all positions."""
    portfolio = processor.process([enriched_a, enriched_b])
    assert portfolio.last_updated_at == T2


def test_portfolio_positions_preserved(processor, enriched_a, enriched_b):
    """portfolio_positions contains the same enriched position objects passed in."""
    positions = [enriched_a, enriched_b]
    portfolio = processor.process(positions)
    assert portfolio.portfolio_positions == positions


def test_single_position_share_is_one(processor, enriched_a):
    """A portfolio with one position has a positions_share of exactly 1.0."""
    portfolio = processor.process([enriched_a])
    assert portfolio.positions_share[0].share == pytest.approx(1.0, rel=1e-6)
