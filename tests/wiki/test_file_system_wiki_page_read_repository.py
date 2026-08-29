import pytest

from modules.wiki.repositories import FileSystemWikiPageReadRepository


@pytest.fixture
def repo():
    """Return a FileSystemWikiPageReadRepository instance."""
    return FileSystemWikiPageReadRepository()


def test_resolves_quarter_page(repo):
    """A bare quarter name resolves to pages/quarters/<name>.md."""
    assert repo.retrieve_data("danhos13", "2024-Q1").strip()


def test_resolves_concept_page(repo):
    """A bare concept name resolves to pages/concepts/<name>.md."""
    assert repo.retrieve_data("danhos13", "plan-crecimiento").strip()


def test_strips_brackets_and_takes_alias_target(repo):
    """[[target|display]] resolves to target, same as the bare name."""
    aliased = repo.retrieve_data("danhos13", "[[2024-Q1|primer trimestre]]")

    assert aliased == repo.retrieve_data("danhos13", "2024-Q1")


def test_tolerates_trailing_md(repo):
    """A trailing .md on the name is accepted."""
    assert repo.retrieve_data("danhos13", "2024-Q1.md") == repo.retrieve_data("danhos13", "2024-Q1")


def test_rejects_cross_fibra_reference(repo):
    """A name containing '/' (cross-FIBRA form) raises ValueError."""
    with pytest.raises(ValueError):
        repo.retrieve_data("danhos13", "fmty14/2024-Q1")


def test_missing_page_raises_with_valid_names(repo):
    """An unknown page raises FileNotFoundError whose message lists valid names."""
    with pytest.raises(FileNotFoundError) as exc_info:
        repo.retrieve_data("danhos13", "2099-Q9")

    assert "2024-Q1" in str(exc_info.value)
