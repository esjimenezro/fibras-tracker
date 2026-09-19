from abc import ABC
from abc import abstractmethod


class BaseWikiCatalogReadRepository(ABC):
    """Abstract interface for listing which FIBRAs have a wiki, from any data source."""

    @abstractmethod
    def retrieve_data(self) -> list[str]:
        """Return the ticker slugs that have a wiki, sorted ascending.

        A FIBRA has a wiki when its wiki directory contains an index page.

        Returns:
            list[str]: Wiki ticker slugs (e.g. ["danhos13", "fmty14"]).
        """
        ...
