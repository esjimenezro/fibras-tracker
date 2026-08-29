from abc import ABC
from abc import abstractmethod


class BaseWikiSchemaReadRepository(ABC):
    """Abstract interface for reading the shared wiki SCHEMA document from any source."""

    @abstractmethod
    def retrieve_data(self) -> str:
        """Return the raw markdown of the shared wiki SCHEMA document.

        Read live on each call, since it is injected into the query system prompt.

        Returns:
            str: Full markdown content of SCHEMA.md.

        Raises:
            FileNotFoundError: If the schema document does not exist.
        """
        ...
