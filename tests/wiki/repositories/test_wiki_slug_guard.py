import pytest

from modules.wiki.repositories.wiki_slug_guard import validate_wiki_slug


@pytest.mark.parametrize(
    "value",
    [
        "danhos13",
        "fmty14",
        "2024-Q1",
        "la-perla",
        "estrategia-crecimiento-capital",
        "a",
    ],
)
def test_accepts_real_wiki_slugs(value):
    """A well-formed slug is returned unchanged."""
    assert validate_wiki_slug(value, label="ticker") == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        ".",
        "..",
        "../fmty14",
        "..\\fmty14",
        "a/b",
        "a\\b",
        "2024-Q1/../../etc",
        ".hidden",
        "trailing.",
        "with space",
    ],
)
def test_rejects_unsafe_values(value):
    """A path separator, a dot-dot sequence, or an empty value raises ValueError."""
    with pytest.raises(ValueError):
        validate_wiki_slug(value, label="ticker")
