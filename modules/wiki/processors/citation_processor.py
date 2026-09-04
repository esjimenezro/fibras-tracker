import re


_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


class CitationProcessor:
    """Extracts the wiki pages cited in a final answer.

    Transformation: answer_text (str) -> list[str] of unique wikilink targets.

    Scans for ``[[wikilink]]`` tokens, keeps the target of an Obsidian alias
    (``[[target|display]]`` -> ``target``), and returns each distinct target
    once, in first-appearance order. Runs once over a final answer; it never
    accumulates across conversation turns.
    """

    def process(self, answer_text: str) -> list[str]:
        """Return the unique wikilink targets cited in answer_text, in order.

        Args:
            answer_text: The final assistant answer as markdown.

        Returns:
            list[str]: Distinct wikilink targets in first-appearance order. Empty
                when the answer contains no wikilinks.
        """
        targets: list[str] = []
        seen: set[str] = set()
        for raw_target in _WIKILINK.findall(answer_text):
            target = raw_target.split("|", 1)[0].strip()
            if target and target not in seen:
                seen.add(target)
                targets.append(target)
        return targets
