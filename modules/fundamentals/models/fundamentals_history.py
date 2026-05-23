from pydantic import BaseModel

from modules.fundamentals.models.enriched_fundamentals_record import EnrichedFundamentalsRecord


class FundamentalsHistory(BaseModel):
    """Aggregated view of enriched fundamentals records across all tickers and periods.

    Produced by FundamentalsHistoryProcessor from a flat list of EnrichedFundamentalsRecord.

    Attributes:
        records: All enriched records sorted by ticker ascending, then period ascending
            (year first, then quarter number — never lexicographic ordering).
        latest_by_ticker: Most recent EnrichedFundamentalsRecord per ticker, keyed by ticker string.
        tickers: Sorted list of unique tickers present in records.
    """

    records: list[EnrichedFundamentalsRecord]
    latest_by_ticker: dict[str, EnrichedFundamentalsRecord]
    tickers: list[str]
