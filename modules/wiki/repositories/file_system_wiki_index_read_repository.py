from config import WIKI_DIR
from modules.wiki.repositories.base import BaseWikiIndexReadRepository


class FileSystemWikiIndexReadRepository(BaseWikiIndexReadRepository):
    """Reads wiki index pages from the local wiki/ directory tree."""

    def retrieve_data(self, ticker: str) -> str:
        """Load ``wiki/<ticker>/index.md`` from disk.

        Args:
            ticker: Wiki ticker slug (e.g. "danhos13").

        Returns:
            str: Full markdown content of the index page.

        Raises:
            FileNotFoundError: If ``wiki/<ticker>/index.md`` does not exist.
        """
        index_path = WIKI_DIR / ticker / "index.md"
        if not index_path.is_file():
            raise FileNotFoundError(f"Wiki index not found for ticker '{ticker}': {index_path}")
        return index_path.read_text(encoding="utf-8")
