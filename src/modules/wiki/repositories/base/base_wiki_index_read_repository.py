from abc import ABC
from abc import abstractmethod


class BaseWikiIndexReadRepository(ABC):
    """Abstract interface for reading a FIBRA's wiki index page from any data source."""

    @abstractmethod
    def retrieve_data(self, ticker: str) -> str:
        """Return the raw markdown of a FIBRA's wiki index page.

        Args:
            ticker: Wiki ticker slug (e.g. "danhos13"). Case-sensitive; matched
                against the on-disk wiki layout.

        Returns:
            str: Full markdown content of the ticker's index page.

        Raises:
            FileNotFoundError: If the ticker has no wiki index page.
        """
        ...
