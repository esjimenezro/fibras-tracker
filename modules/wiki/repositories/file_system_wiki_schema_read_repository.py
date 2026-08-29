from config import WIKI_SCHEMA_PATH
from modules.wiki.repositories.base import BaseWikiSchemaReadRepository


class FileSystemWikiSchemaReadRepository(BaseWikiSchemaReadRepository):
    """Reads the shared wiki SCHEMA document from the local filesystem."""

    def retrieve_data(self) -> str:
        """Load ``wiki/SCHEMA.md`` from disk.

        Returns:
            str: Full markdown content of SCHEMA.md.

        Raises:
            FileNotFoundError: If SCHEMA.md does not exist at the configured path.
        """
        if not WIKI_SCHEMA_PATH.is_file():
            raise FileNotFoundError(f"Wiki schema document not found: {WIKI_SCHEMA_PATH}")
        return WIKI_SCHEMA_PATH.read_text(encoding="utf-8")
