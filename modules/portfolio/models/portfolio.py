from datetime import datetime

from pydantic import BaseModel

from modules.portfolio.models.enriched_position import EnrichedPosition


class PositionShare(BaseModel):
    """Portfolio weight for a single FIBRA position.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        share: Position weight as a fraction of total market value (0.0 to 1.0).
    """

    ticker: str
    share: float


class Portfolio(BaseModel):
    """Aggregated enriched portfolio with all positions and summary metrics.

    Attributes:
        portfolio_positions: All enriched FIBRA positions.
        positions_share: Portfolio weight per position; sums to 1.0 across all entries.
        total_purchase_cost: Total amount invested across all positions in MXN.
        total_market_value: Current total market value across all positions in MXN.
        total_return: Unrealised gain or loss in MXN (total_market_value - total_purchase_cost).
        total_return_pct: Unrealised return as a fraction of total purchase cost.
        total_net_fiscal_result_received: Sum of net fiscal distributions received in MXN,
            net of ISR withholding and excluding capital reimbursement.
        total_return_including_distributions: Total return including net fiscal distributions in MXN.
        last_updated_at: UTC timestamp of the most recently fetched market price across all positions.
    """

    portfolio_positions: list[EnrichedPosition]
    positions_share: list[PositionShare]
    total_purchase_cost: float
    total_market_value: float
    total_return: float
    total_return_pct: float
    total_net_fiscal_result_received: float
    total_return_including_distributions: float
    last_updated_at: datetime
