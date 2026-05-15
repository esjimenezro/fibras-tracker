from pydantic import BaseModel

from modules.portfolio.models.distribution import Distribution
from modules.portfolio.models.position import Position


class Portfolio(BaseModel):
    positions: list[Position]
    distributions: list[Distribution]
