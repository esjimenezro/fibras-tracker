from modules.common.models import Fibra
from modules.common.models import MarketPrice

from modules.portfolio.models import EnrichedDistribution
from modules.portfolio.models import EnrichedPosition
from modules.portfolio.models import Position


class PositionsProcessor:
    """Enriches Position records with catalog metadata, market data, and distributions into EnrichedPosition output models.

    Transformation: Position + Fibra + MarketPrice + list[EnrichedDistribution] → EnrichedPosition

    Formulas implemented:
        purchase_cost                        = average_purchase_cost * cbfis
        market_value                         = market_price * cbfis
        return_per_cbfi                      = market_price - average_purchase_cost
        return_pct                           = return_per_cbfi / average_purchase_cost
        total_return                         = return_per_cbfi * cbfis
        total_net_fiscal_result_received     = sum(d.net_fiscal_result_income for d in distributions)
        total_return_including_distributions = total_return + total_net_fiscal_result_received

    Injected from catalog (Fibra):
        name, payment_frequency, sector_exposure

    Invariant: average_purchase_cost is the broker-adjusted cost base. It must NOT be
        reduced by reimbursements received — those are accounted for separately via
        total_net_fiscal_result_received.
    """

    def enrich(
        self,
        position: Position,
        market_price: MarketPrice,
        distributions: list[EnrichedDistribution],
        fibra: Fibra,
    ) -> EnrichedPosition:
        """Compute all derived fields for a single position.

        Args:
            position: The raw FIBRA position.
            market_price: Current market price for the position's ticker.
            distributions: Enriched distribution records already filtered to this ticker.
            fibra: Catalog entry for the position's ticker, providing name, payment
                frequency, and sector exposure.

        Returns:
            EnrichedPosition with the following derived fields:
                name                                 = fibra.name
                payment_frequency                    = fibra.payment_frequency
                sector_exposure                      = fibra.sector_exposure
                purchase_cost                        = average_purchase_cost * cbfis
                market_value                         = market_price * cbfis
                return_per_cbfi                      = market_price - average_purchase_cost
                return_pct                           = return_per_cbfi / average_purchase_cost
                total_return                         = return_per_cbfi * cbfis
                total_net_fiscal_result_received     = sum(d.net_fiscal_result_income for d in distributions)
                total_return_including_distributions = total_return + total_net_fiscal_result_received

            Note: average_purchase_cost is the broker-adjusted cost base and must NOT be
            reduced by reimbursements. Capital reimbursements are already captured in
            total_net_fiscal_result_received via each distribution's net_fiscal_result_income.
        """
        return_per_cbfi = market_price.price - position.average_purchase_cost
        total_net_fiscal_result_received = sum(d.net_fiscal_result_income for d in distributions)
        total_return = return_per_cbfi * position.cbfis

        return EnrichedPosition(
            **position.model_dump(),
            name=fibra.name,
            payment_frequency=fibra.payment_frequency,
            sector_exposure=fibra.sector_exposure,
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
        distributions: list[EnrichedDistribution],
        fibras: list[Fibra],
    ) -> list[EnrichedPosition]:
        """Enrich all positions by joining market prices, distributions, and catalog entries by ticker.

        Args:
            positions: All raw FIBRA positions.
            market_prices: Market prices for each ticker. Every position must have a matching entry.
            distributions: All enriched distribution records across all tickers.
            fibras: FIBRA catalog entries. Every position must have a matching entry.

        Returns:
            list[EnrichedPosition]: One enriched position per input position, in the same order.

        Raises:
            ValueError: If any position has no matching market price.
            ValueError: If any position has no matching catalog entry.
        """
        prices_by_ticker: dict[str, MarketPrice] = {mp.ticker: mp for mp in market_prices}
        fibras_by_ticker: dict[str, Fibra] = {f.ticker: f for f in fibras}
        distributions_by_ticker: dict[str, list[EnrichedDistribution]] = {}
        for d in distributions:
            distributions_by_ticker.setdefault(d.ticker, []).append(d)

        enriched = []
        for position in positions:
            if position.ticker not in prices_by_ticker:
                raise ValueError(f"No market price found for ticker '{position.ticker}'")
            if position.ticker not in fibras_by_ticker:
                raise ValueError(f"No catalog entry found for ticker '{position.ticker}'")
            enriched.append(
                self.enrich(
                    position=position,
                    market_price=prices_by_ticker[position.ticker],
                    distributions=distributions_by_ticker.get(position.ticker, []),
                    fibra=fibras_by_ticker[position.ticker],
                )
            )
        return enriched
