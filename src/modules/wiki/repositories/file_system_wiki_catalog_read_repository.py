from config import WIKI_DIR
from modules.wiki.repositories.base import BaseWikiCatalogReadRepository


class FileSystemWikiCatalogReadRepository(BaseWikiCatalogReadRepository):
    """Lists FIBRAs that have a wiki by scanning the local wiki/ directory tree."""

    def retrieve_data(self) -> list[str]:
        """Return the sorted ticker slugs whose wiki directory contains an index.md.

        Returns:
            list[str]: Wiki ticker slugs (e.g. ["danhos13", "fmty14"]). Empty when
                the wiki directory does not exist.
        """
        if not WIKI_DIR.is_dir():
            return []
        tickers = [entry.name for entry in WIKI_DIR.iterdir() if (entry / "index.md").is_file()]
        return sorted(tickers)
