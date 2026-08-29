import pytest

from modules.wiki.repositories import FileSystemWikiIndexReadRepository


@pytest.fixture
def repo():
    """Return a FileSystemWikiIndexReadRepository instance."""
    return FileSystemWikiIndexReadRepository()


def test_returns_index_markdown(repo):
    """retrieve_data returns the ticker's index.md content."""
    content = repo.retrieve_data("danhos13")

    assert "## Trimestres" in content


def test_missing_ticker_raises(repo):
    """An unknown ticker raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        repo.retrieve_data("nonexistent")
