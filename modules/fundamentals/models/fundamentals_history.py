from typing import Optional

from pydantic import BaseModel

from modules.common.models import Fibra
from modules.fundamentals.models.enriched_fundamentals_record import EnrichedFundamentalsRecord


class FundamentalsHistory(BaseModel):
    """Aggregated view of enriched fundamentals records across all tickers and periods.

    Produced by FundamentalsHistoryProcessor from a flat list of EnrichedFundamentalsRecord.

    Attributes:
        records: All enriched records sorted by ticker ascending, then period ascending
            (year first, then quarter number — never lexicographic ordering).
        latest_by_ticker: Most recent EnrichedFundamentalsRecord per ticker, keyed by ticker string.
            Every ticker present in fibras appears as a key; value is None if no record exists
            for that ticker.
        fibras: FIBRA catalog entries that define which tickers appear in latest_by_ticker.
    """

    records: list[EnrichedFundamentalsRecord]
    latest_by_ticker: dict[str, Optional[EnrichedFundamentalsRecord]]
    fibras: list[Fibra]
