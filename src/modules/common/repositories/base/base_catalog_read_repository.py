from abc import ABC
from abc import abstractmethod

from modules.common.models import Fibra


class BaseCatalogReadRepository(ABC):
    """Abstract interface for reading the FIBRA catalog from any data source."""

    @abstractmethod
    def retrieve_data(self) -> list[Fibra]:
        """Return all FIBRA catalog entries.

        Returns:
            list[Fibra]: All FIBRA entries from the data source.
        """
        ...
