from abc import ABC
from abc import abstractmethod

from modules.common.models import InflationRecord


class BaseInflationReadRepository(ABC):
    """Abstract interface for reading annual inflation data from any data source."""

    @abstractmethod
    def retrieve_data(self) -> list[InflationRecord]:
        """Return all annual inflation records.

        Returns:
            list[InflationRecord]: All annual inflation entries from the data source.
        """
        ...
