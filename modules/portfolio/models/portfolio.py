from pydantic import BaseModel

from modules.portfolio.models.distribution import Distribution
from modules.portfolio.models.position import Position


class Portfolio(BaseModel):
    """Aggregate portfolio containing all positions and their distributions."""

    positions: list[Position]
    distributions: list[Distribution]
