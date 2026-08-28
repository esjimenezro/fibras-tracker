from modules.wiki.models.wiki_answer import WikiAnswer


class WikiQueryResponse(WikiAnswer):
    """A wiki answer enriched with the wiki pages it cited.

    Extends WikiAnswer with the ordered list of unique wikilink targets referenced
    in answer_text, produced by CitationProcessor over the final answer only.

    Attributes:
        citations: Unique wikilink targets in first-appearance order (e.g. "2024-Q1",
            "affo-trend"). Empty list when the answer cites no wiki pages.
    """

    citations: list[str]
