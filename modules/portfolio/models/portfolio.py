from pydantic import BaseModel

from modules.portfolio.models.distribution import Distribution
from modules.portfolio.models.position import Position


class Portfolio(BaseModel):
    """Aggregate portfolio containing all positions and their distributions.

    Attributes:
        positions: All FIBRA positions held in the portfolio.
        distributions: All distribution payments received across positions.
    """

    positions: list[Position]
    distributions: list[Distribution]
