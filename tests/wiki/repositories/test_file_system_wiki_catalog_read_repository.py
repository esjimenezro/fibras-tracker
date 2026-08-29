from modules.wiki.repositories import FileSystemWikiCatalogReadRepository


def test_lists_committed_wiki_tickers_sorted():
    """retrieve_data returns exactly the ticker slugs with a committed index.md, sorted."""
    repo = FileSystemWikiCatalogReadRepository()

    assert repo.retrieve_data() == ["danhos13", "fmty14"]
