from modules.common.repositories import JsonCatalogReadRepository
from modules.wiki.processors import WikiRosterProcessor
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository


def test_process_lists_every_wiki_ticker_sorted_with_sector_and_link():
    """Every FIBRA with a wiki gets one sorted line naming its sector(s) and index link."""
    fibras = JsonCatalogReadRepository().retrieve_data()
    wiki_tickers = FileSystemWikiCatalogReadRepository().retrieve_data()

    result = WikiRosterProcessor().process(fibras=fibras, wiki_tickers=wiki_tickers)

    lines = result.split("\n")
    assert len(lines) == len(wiki_tickers)
    assert lines == sorted(lines)
    assert "- FMTY14 — Fibra Mty (" in result
    assert "[[fmty14/index]]" in result


def test_process_returns_empty_string_for_no_wiki_tickers():
    """An empty wiki roster produces an empty string, not a stray newline."""
    fibras = JsonCatalogReadRepository().retrieve_data()

    result = WikiRosterProcessor().process(fibras=fibras, wiki_tickers=[])

    assert result == ""
