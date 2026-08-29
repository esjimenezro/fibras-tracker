from config import WIKI_DIR
from modules.wiki.repositories.base import BaseWikiPageReadRepository
from modules.wiki.repositories.wiki_slug_guard import validate_wiki_slug


_PAGE_SUBDIRS = ("pages/quarters", "pages/concepts")


class FileSystemWikiPageReadRepository(BaseWikiPageReadRepository):
    """Reads wiki pages from the local wiki/ tree, resolving wikilink-style names."""

    def retrieve_data(self, ticker: str, page_name: str) -> str:
        """Resolve a wikilink-style page name and load the matching page from disk.

        Resolution steps:
            1. Strip surrounding ``[[`` / ``]]`` if present.
            2. On an Obsidian alias (``target|display``), keep ``target``.
            3. Strip a trailing ``.md`` if present.
            4. Reject a name containing ``/`` (cross-FIBRA form, out of scope).
            5. Reject ``ticker`` and the resolved name unless each is a safe slug
               (path-traversal guard: no path separators, no ``..``).
            6. Look up ``wiki/<ticker>/pages/quarters/<name>.md``; if absent, try
               ``wiki/<ticker>/pages/concepts/<name>.md``. Match is exact
               (case-sensitive) against on-disk filenames.

        Args:
            ticker: Wiki ticker slug (e.g. "danhos13").
            page_name: Wikilink-style page name.

        Returns:
            str: Full markdown content of the resolved page.

        Raises:
            ValueError: If the resolved name contains "/" (cross-FIBRA reference),
                or if ``ticker`` or the resolved name is not a safe slug.
            FileNotFoundError: If no quarter or concept page matches; the message
                lists the valid page names for the ticker.
        """
        name = page_name.strip()
        if name.startswith("[[") and name.endswith("]]"):
            name = name[2:-2].strip()
        if "|" in name:
            name = name.split("|", 1)[0].strip()
        if name.endswith(".md"):
            name = name[:-3]
        if "/" in name:
            raise ValueError(
                f"Cross-FIBRA wiki reference '{page_name}' is not supported for a single-FIBRA query"
            )

        validate_wiki_slug(ticker, label="ticker")
        validate_wiki_slug(name, label="page name")

        for subdir in _PAGE_SUBDIRS:
            candidate = WIKI_DIR / ticker / subdir / f"{name}.md"
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")

        valid_names: list[str] = []
        for subdir in _PAGE_SUBDIRS:
            directory = WIKI_DIR / ticker / subdir
            if directory.is_dir():
                valid_names.extend(sorted(path.stem for path in directory.glob("*.md")))
        raise FileNotFoundError(
            f"Wiki page '{name}' not found for ticker '{ticker}'. Valid names: {valid_names}"
        )
