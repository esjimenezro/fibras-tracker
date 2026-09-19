from modules.common.models import Fibra


class WikiRosterProcessor:
    """Formats the FIBRA roster used by the cross-FIBRA discovery tool and wiki/index.md.

    Transformation: (list[Fibra], list[str] of lower-case wiki ticker slugs) ->
    a markdown bullet list, one line per FIBRA that has a wiki, sorted by
    ticker. Pure formatting: no I/O, no knowledge of where either input came
    from — the same output feeds both the runtime discovery tool and the
    committed wiki/index.md, so they never drift apart.
    """

    def process(self, fibras: list[Fibra], wiki_tickers: list[str]) -> str:
        """Build one markdown bullet line per FIBRA that has a wiki.

        Args:
            fibras: The full FIBRA catalog (name, sector_exposure per ticker).
            wiki_tickers: Lower-case wiki directory slugs (e.g. ["danhos13",
                "fmty14"]), as returned by BaseWikiCatalogReadRepository.

        Returns:
            str: One line per ticker in ``wiki_tickers``, sorted alphabetically,
                formatted as
                ``"- {TICKER} — {name} ({sector} {weight%}, ...) — [[{slug}/index]]"``.
                Empty string when ``wiki_tickers`` is empty.

        Raises:
            KeyError: If a wiki ticker slug has no matching entry in ``fibras``
                (upper-cased) — the catalog and the wiki roster are expected to
                stay in sync.
        """
        fibras_by_ticker = {fibra.ticker: fibra for fibra in fibras}
        lines = []
        for slug in sorted(wiki_tickers):
            ticker = slug.upper()
            fibra = fibras_by_ticker[ticker]
            sectors = ", ".join(
                f"{exposure.sector.value} {exposure.weight:.0%}"
                for exposure in fibra.sector_exposure
            )
            lines.append(f"- {ticker} — {fibra.name} ({sectors}) — [[{slug}/index]]")
        return "\n".join(lines)
