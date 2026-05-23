from modules.common.models import Sector
from modules.portfolio.models import EnrichedPosition
from modules.portfolio.models import Portfolio
from modules.portfolio.models import PositionShare
from modules.portfolio.models import SectorShare


class PortfolioProcessor:
    """Aggregates a list of EnrichedPosition records into a single Portfolio output model.

    Transformation: list[EnrichedPosition] → Portfolio

    Formulas implemented:
        total_purchase_cost               = sum(p.purchase_cost for p in positions)
        total_market_value                = sum(p.market_value for p in positions)
        total_return                      = total_market_value - total_purchase_cost
        total_return_pct                  = total_return / total_purchase_cost
        total_net_fiscal_result_received  = sum(p.total_net_fiscal_result_received for p in positions)
        total_return_including_distributions = total_return + total_net_fiscal_result_received
        positions_share                   = [PositionShare(ticker=p.ticker,
                                                share=p.market_value / total_market_value)
                                            for p in positions]
        last_updated_at                   = max(p.price_updated_at for p in positions)
        sector_contribution(position, s)  = p.market_value × sector_exposure.weight  (per matching sector)
        sector_share.weight(sector)       = sum(sector_contribution) / total_market_value

    Note: positions_share always sums to exactly 1.0 across all positions.
    Note: sector_shares sums to exactly 1.0 when all positions have sector_exposure weights summing to 1.0.
    """

    def process(self, positions: list[EnrichedPosition]) -> Portfolio:
        """Compute all portfolio-level aggregates from enriched positions.

        Args:
            positions: All enriched FIBRA positions. Must not be empty.

        Returns:
            Portfolio with the following aggregated fields:
                total_purchase_cost               = sum(p.purchase_cost for p in positions)
                total_market_value                = sum(p.market_value for p in positions)
                total_return                      = total_market_value - total_purchase_cost
                total_return_pct                  = total_return / total_purchase_cost
                total_net_fiscal_result_received  = sum(p.total_net_fiscal_result_received for p in positions)
                total_return_including_distributions = total_return + total_net_fiscal_result_received
                positions_share                   = [PositionShare(ticker=p.ticker,
                                                         share=p.market_value / total_market_value)
                                                     for p in positions]
                last_updated_at                   = max(p.price_updated_at for p in positions)
                sector_shares                     = [SectorShare(sector=s, weight=total / total_market_value)
                                                     for s, total in sector_totals.items() if total > 0]

            Note: positions_share always sums to exactly 1.0 across all positions.
            Note: sector_shares sums to exactly 1.0 when all positions have sector_exposure weights summing to 1.0.

        Raises:
            ValueError: If positions is empty.
        """
        if not positions:
            raise ValueError("Cannot build a Portfolio from an empty positions list.")

        total_market_value = sum(p.market_value for p in positions)
        total_purchase_cost = sum(p.purchase_cost for p in positions)
        total_return = total_market_value - total_purchase_cost
        total_net_fiscal_result_received = sum(p.total_net_fiscal_result_received for p in positions)

        sector_totals: dict[Sector, float] = {}
        for position in positions:
            for exposure in position.sector_exposure:
                current = sector_totals.get(exposure.sector, 0.0)
                sector_totals[exposure.sector] = current + position.market_value * exposure.weight

        sector_shares = [
            SectorShare(sector=sector, weight=total / total_market_value)
            for sector, total in sector_totals.items()
            if total > 0
        ]

        return Portfolio(
            portfolio_positions=positions,
            positions_share=[
                PositionShare(ticker=p.ticker, share=p.market_value / total_market_value)
                for p in positions
            ],
            sector_shares=sector_shares,
            total_purchase_cost=total_purchase_cost,
            total_market_value=total_market_value,
            total_return=total_return,
            total_return_pct=total_return / total_purchase_cost,
            total_net_fiscal_result_received=total_net_fiscal_result_received,
            total_return_including_distributions=total_return + total_net_fiscal_result_received,
            last_updated_at=max(p.price_updated_at for p in positions),
        )
