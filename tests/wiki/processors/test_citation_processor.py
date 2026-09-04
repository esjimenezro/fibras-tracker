import pytest

from modules.wiki.processors import CitationProcessor


@pytest.fixture
def processor():
    """Return a CitationProcessor instance."""
    return CitationProcessor()


def test_no_wikilinks_returns_empty(processor):
    """Text without wikilinks yields an empty list."""
    text = "El apalancamiento subió por nueva deuda. Ver [reporte](x.pdf)."

    assert processor.process(answer_text=text) == []


def test_extracts_multiple_in_order(processor):
    """Distinct wikilinks are returned in first-appearance order."""
    text = "Según [[2024-Q1]] y luego [[2024-Q2]], más [[plan-crecimiento]]."

    assert processor.process(answer_text=text) == ["2024-Q1", "2024-Q2", "plan-crecimiento"]


def test_dedupes_preserving_first_position(processor):
    """A repeated wikilink appears once, at its first position."""
    text = "[[2024-Q1]] ... [[2024-Q2]] ... y de nuevo [[2024-Q1]]."

    assert processor.process(answer_text=text) == ["2024-Q1", "2024-Q2"]


def test_alias_contributes_target_not_display(processor):
    """[[target|display]] contributes target, not the display text."""
    assert processor.process(answer_text="Ver [[2024-Q1|primer trimestre]].") == ["2024-Q1"]


def test_ignores_markdown_links(processor):
    """A markdown link [text](url) is not a wikilink."""
    assert processor.process(answer_text="Fuente: [Fibra Danhos](https://example.com).") == []
