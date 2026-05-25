from typing import Optional

from modules.common.models import Fibra
from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FundamentalsHistory


class FundamentalsHistoryProcessor:
    """Aggregates a list of EnrichedFundamentalsRecord into a FundamentalsHistory output model.

    Transformation: list[EnrichedFundamentalsRecord] → FundamentalsHistory

    Produces:
        records           = all records sorted by (ticker asc, year asc, quarter asc)
        latest_by_ticker  = most recent record per ticker, keyed from catalog fibras;
                            None if no record exists for that ticker
        fibras            = catalog Fibra list passed in directly

    Invariant: period strings (e.g. "1T2026") are parsed as (year, quarter) integers —
        never compared lexicographically. "1T2026" sorts after "4T2025" because
        (2026, 1) > (2025, 4).
    """

    def process(self, records: list[EnrichedFundamentalsRecord], fibras: list[Fibra]) -> FundamentalsHistory:
        """Aggregate enriched fundamentals records into a sorted history.

        Args:
            records: All enriched fundamentals records across all tickers and periods.
                Must not be empty.
            fibras: FIBRA catalog entries. Every ticker in fibras appears as a key in
                latest_by_ticker; value is None if no record exists for that ticker.

        Returns:
            FundamentalsHistory with the following fields:
                records              = all records sorted by ticker asc, then period asc
                                       (year first, then quarter — never lexicographic)
                latest_by_ticker     = most recent record per ticker, keyed from catalog fibras;
                                       None if no record exists for that ticker
                prior_year_by_ticker = record for the same quarter one year prior per ticker;
                                       None if no such record exists or the ticker has no records
                fibras               = the catalog Fibra list passed in directly

        Raises:
            ValueError: If records is empty.
        """
        if not records:
            raise ValueError("Cannot build FundamentalsHistory from an empty records list.")

        sorted_records = sorted(
            records,
            key=lambda r: (r.ticker, *self._parse_period(period=r.period)),
        )

        latest_by_ticker: dict[str, Optional[EnrichedFundamentalsRecord]] = {f.ticker: None for f in fibras}
        for record in sorted_records:
            if record.ticker in latest_by_ticker:
                latest_by_ticker[record.ticker] = record

        prior_year_by_ticker: dict[str, Optional[EnrichedFundamentalsRecord]] = {}
        for ticker, latest in latest_by_ticker.items():
            if latest is None:
                prior_year_by_ticker[ticker] = None
            else:
                year, quarter = self._parse_period(period=latest.period)
                prior_period = f"{quarter}T{year - 1}"
                prior_year_by_ticker[ticker] = next(
                    (r for r in sorted_records if r.ticker == ticker and r.period == prior_period),
                    None,
                )

        return FundamentalsHistory(
            records=sorted_records,
            latest_by_ticker=latest_by_ticker,
            prior_year_by_ticker=prior_year_by_ticker,
            fibras=fibras,
        )

    @staticmethod
    def _parse_period(period: str) -> tuple[int, int]:
        """Parse a period string into a comparable (year, quarter) integer tuple.

        Args:
            period: Period string in the format "QTYear" (e.g. "1T2026", "4T2025").

        Returns:
            tuple[int, int]: (year, quarter) suitable for numeric comparison and sorting.
        """
        quarter_str, year_str = period.split("T")
        return (int(year_str), int(quarter_str))
