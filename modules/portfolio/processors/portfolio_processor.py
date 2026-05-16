from modules.portfolio.models.enriched_position import EnrichedPosition
from modules.portfolio.models.portfolio import Portfolio, PositionShare


class PortfolioProcessor:
    """Aggregates a list of EnrichedPosition records into a single Portfolio output model."""

    def process(self, positions: list[EnrichedPosition]) -> Portfolio:
        """Compute all portfolio-level aggregates from enriched positions.

        Args:
            positions: All enriched FIBRA positions. Must not be empty.

        Returns:
            Portfolio: Aggregated portfolio with totals, weights, and timestamp.

        Raises:
            ValueError: If positions is empty.
        """
        if not positions:
            raise ValueError("Cannot build a Portfolio from an empty positions list.")

        total_market_value = sum(p.market_value for p in positions)
        total_purchase_cost = sum(p.purchase_cost for p in positions)
        total_return = total_market_value - total_purchase_cost
        total_net_fiscal_result_received = sum(p.total_net_fiscal_result_received for p in positions)

        return Portfolio(
            portfolio_positions=positions,
            positions_share=[
                PositionShare(ticker=p.ticker, share=p.market_value / total_market_value)
                for p in positions
            ],
            total_purchase_cost=total_purchase_cost,
            total_market_value=total_market_value,
            total_return=total_return,
            total_return_pct=total_return / total_purchase_cost,
            total_net_fiscal_result_received=total_net_fiscal_result_received,
            total_return_including_distributions=total_return + total_net_fiscal_result_received,
            last_updated_at=max(p.price_updated_at for p in positions),
        )
