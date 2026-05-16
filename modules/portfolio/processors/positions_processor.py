from modules.portfolio.models.enriched_distribution import EnrichedDistribution
from modules.portfolio.models.enriched_position import EnrichedPosition
from modules.portfolio.models.market_price import MarketPrice
from modules.portfolio.models.position import Position


class PositionsProcessor:
    """Processes Position, MarketPrice, and EnrichedDistribution records into EnrichedPosition output models."""

    def enrich(
        self,
        position: Position,
        market_price: MarketPrice,
        distributions: list[EnrichedDistribution]
    ) -> EnrichedPosition:
        """Compute all derived fields for a single position.

        Args:
            position: The raw FIBRA position.
            market_price: Current market price for the position's ticker.
            distributions: Enriched distribution records already filtered to this ticker.

        Returns:
            EnrichedPosition: The position with all market, calculated, and distribution fields populated.
        """
        return_per_cbfi = market_price.price - position.average_purchase_cost
        total_net_fiscal_result_received = sum(d.net_fiscal_result_income for d in distributions)
        total_return = return_per_cbfi * position.cbfis

        return EnrichedPosition(
            **position.model_dump(),
            market_price=market_price.price,
            price_updated_at=market_price.retrieved_at,
            purchase_cost=position.average_purchase_cost * position.cbfis,
            market_value=market_price.price * position.cbfis,
            return_per_cbfi=return_per_cbfi,
            return_pct=return_per_cbfi / position.average_purchase_cost,
            total_return=total_return,
            distributions=distributions,
            total_net_fiscal_result_received=total_net_fiscal_result_received,
            total_return_including_distributions=total_return + total_net_fiscal_result_received,
        )

    def process(
        self,
        positions: list[Position],
        market_prices: list[MarketPrice],
        distributions: list[EnrichedDistribution]
    ) -> list[EnrichedPosition]:
        """Enrich all positions by joining market prices and distributions by ticker.

        Args:
            positions: All raw FIBRA positions.
            market_prices: Market prices for each ticker. Every position must have a matching entry.
            distributions: All enriched distribution records across all tickers.

        Returns:
            list[EnrichedPosition]: One enriched position per input position, in the same order.

        Raises:
            ValueError: If any position has no matching market price.
        """
        prices_by_ticker: dict[str, MarketPrice] = {mp.ticker: mp for mp in market_prices}
        distributions_by_ticker: dict[str, list[EnrichedDistribution]] = {}
        for d in distributions:
            distributions_by_ticker.setdefault(d.ticker, []).append(d)

        enriched = []
        for position in positions:
            if position.ticker not in prices_by_ticker:
                raise ValueError(f"No market price found for ticker '{position.ticker}'")
            enriched.append(
                self.enrich(
                    position=position,
                    market_price=prices_by_ticker[position.ticker],
                    distributions=distributions_by_ticker.get(position.ticker, []),
                )
            )
        return enriched
