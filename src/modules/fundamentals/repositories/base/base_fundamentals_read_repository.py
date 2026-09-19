from abc import ABC, abstractmethod

from modules.fundamentals.models import FundamentalsRecord


class BaseFundamentalsReadRepository(ABC):
    """Abstract interface for reading fundamentals records from any data source."""

    @abstractmethod
    def retrieve_data(self) -> list[FundamentalsRecord]:
        """Return all fundamentals records.

        Returns:
            list[FundamentalsRecord]: All fundamentals records from the data source.
        """
        ...
