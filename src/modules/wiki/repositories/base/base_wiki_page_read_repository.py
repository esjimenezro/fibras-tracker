from abc import ABC
from abc import abstractmethod


class BaseWikiPageReadRepository(ABC):
    """Abstract interface for reading one wiki page, resolved from a wikilink name."""

    @abstractmethod
    def retrieve_data(self, ticker: str, page_name: str) -> str:
        """Return the raw markdown of one wiki page, resolved from a wikilink name.

        The name is resolved wikilink-style: surrounding ``[[ ]]`` are optional, an
        Obsidian alias (``target|display``) resolves to ``target``, and a trailing
        ``.md`` is tolerated. The page is looked up as a quarter page first, then a
        concept page. A name that refers to another FIBRA (contains ``/``) is out of
        scope for a single-FIBRA query.

        Args:
            ticker: Wiki ticker slug (e.g. "danhos13").
            page_name: Wikilink-style page name (e.g. "2024-Q1", "[[la-perla]]",
                "[[2024-Q1|primer trimestre]]").

        Returns:
            str: Full markdown content of the resolved page.

        Raises:
            ValueError: If the resolved name contains "/" (cross-FIBRA reference).
            FileNotFoundError: If no quarter or concept page matches the name.
        """
        ...
