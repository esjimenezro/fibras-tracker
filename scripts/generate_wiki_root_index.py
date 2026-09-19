"""Regenerate wiki/index.md from catalog.json + the wiki/ directory roster.

Run manually whenever the roster of FIBRAs with a wiki changes (a rare event —
see wiki/SCHEMA.md, "Múltiples FIBRAs"). Not part of the per-quarter ingest.

Usage (from the repo root, so "config" and "modules" resolve on sys.path):
    uv run python -m scripts.generate_wiki_root_index
"""

from config import WIKI_DIR
from modules.common.repositories import JsonCatalogReadRepository
from modules.wiki.processors import WikiRosterProcessor
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository


_HEADER = (
    "# Índice de FIBRAs\n\n"
    "Apunta al `index.md` de cada FIBRA con wiki — no duplica su contenido. "
    "Generado por `scripts/generate_wiki_root_index.py`; no editar a mano.\n\n"
)


def main() -> None:
    """Write wiki/index.md from the current catalog + wiki roster."""
    fibras = JsonCatalogReadRepository().retrieve_data()
    wiki_tickers = FileSystemWikiCatalogReadRepository().retrieve_data()
    roster = WikiRosterProcessor().process(fibras=fibras, wiki_tickers=wiki_tickers)
    (WIKI_DIR / "index.md").write_text(_HEADER + roster + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
