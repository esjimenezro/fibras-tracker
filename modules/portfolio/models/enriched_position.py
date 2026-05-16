from datetime import datetime

from modules.portfolio.models.enriched_distribution import EnrichedDistribution
from modules.portfolio.models.position import Position


class EnrichedPosition(Position):
    """A FIBRA position enriched with current market data and distribution history.

    Extends Position with market, calculated, and distribution fields produced by PositionProcessor.

    Attributes:
        market_price: Last known market price per CBFI in MXN.
        price_updated_at: UTC timestamp when the market price was fetched.
        total_purchase_cost: Total amount invested in MXN (average_purchase_cost * cbfis).
        market_value: Current market value of the position in MXN (market_price * cbfis).
        return_per_cbfi: Unrealised gain or loss per CBFI in MXN (market_price - average_purchase_cost).
        return_pct: Unrealised return as a fraction of average purchase cost (return_per_cbfi / average_purchase_cost).
        total_return: Total unrealised gain or loss in MXN (return_per_cbfi * cbfis).
        distributions: All enriched distribution payments received for this position.
        total_net_fiscal_result_received: Sum of net fiscal result income across all distributions in MXN.
            Excludes capital reimbursement; net of ISR withholding.
        total_return_including_distributions: Total return including net fiscal distributions in MXN
            (total_return + total_net_fiscal_result_received).
    """

    market_price: float
    price_updated_at: datetime
    total_purchase_cost: float
    market_value: float
    return_per_cbfi: float
    return_pct: float
    total_return: float
    distributions: list[EnrichedDistribution]
    total_net_fiscal_result_received: float
    total_return_including_distributions: float
