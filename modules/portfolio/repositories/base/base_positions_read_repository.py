from abc import ABC, abstractmethod

from modules.portfolio.models.position import Position


class BasePositionsReadRepository(ABC):
    """Abstract interface for reading portfolio positions from any data source."""

    @abstractmethod
    def retrieve_data(self) -> list[Position]:
        """Return all positions in the portfolio.

        Returns:
            list[Position]: All positions loaded from the data source.
        """
        ...
