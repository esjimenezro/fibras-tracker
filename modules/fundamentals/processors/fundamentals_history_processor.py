from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FundamentalsHistory


class FundamentalsHistoryProcessor:
    """Aggregates a list of EnrichedFundamentalsRecord into a FundamentalsHistory output model.

    Transformation: list[EnrichedFundamentalsRecord] → FundamentalsHistory

    Produces:
        records           = all records sorted by (ticker asc, year asc, quarter asc)
        latest_by_ticker  = most recent record per ticker, keyed by ticker
        tickers           = sorted list of unique tickers present in records

    Invariant: period strings (e.g. "1T2026") are parsed as (year, quarter) integers —
        never compared lexicographically. "1T2026" sorts after "4T2025" because
        (2026, 1) > (2025, 4).
    """

    def process(self, records: list[EnrichedFundamentalsRecord]) -> FundamentalsHistory:
        """Aggregate enriched fundamentals records into a sorted history.

        Args:
            records: All enriched fundamentals records across all tickers and periods.
                Must not be empty.

        Returns:
            FundamentalsHistory with the following fields:
                records          = all records sorted by ticker asc, then period asc
                                   (year first, then quarter — never lexicographic)
                latest_by_ticker = most recent record per ticker, keyed by ticker string
                tickers          = sorted list of unique tickers present in records

        Raises:
            ValueError: If records is empty.
        """
        if not records:
            raise ValueError("Cannot build FundamentalsHistory from an empty records list.")

        sorted_records = sorted(
            records,
            key=lambda r: (r.ticker, *self._parse_period(period=r.period)),
        )

        latest_by_ticker: dict[str, EnrichedFundamentalsRecord] = {}
        for record in sorted_records:
            latest_by_ticker[record.ticker] = record

        tickers = sorted(latest_by_ticker.keys())

        return FundamentalsHistory(
            records=sorted_records,
            latest_by_ticker=latest_by_ticker,
            tickers=tickers,
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
