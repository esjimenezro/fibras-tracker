from abc import ABC, abstractmethod

from modules.portfolio.models.distribution import Distribution


class BaseDistributionsReadRepository(ABC):
    """Abstract interface for reading distribution records from any data source."""

    @abstractmethod
    def retrieve_data(self) -> list[Distribution]:
        """Return all distribution records.

        Returns:
            list[Distribution]: All distribution records from the data source.
        """
        ...
