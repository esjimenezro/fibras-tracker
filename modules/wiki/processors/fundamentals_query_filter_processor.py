from typing import Optional

from modules.fundamentals.models import FundamentalsRecord


class FundamentalsQueryFilterProcessor:
    """Filters raw fundamentals records by ticker and optional period.

    Transformation: list[FundamentalsRecord] + ticker (+ period)
        -> list[FundamentalsRecord]

    Backs the ``read_fundamentals`` tool of the wiki query agent, which returns
    the raw numbers already parsed by JsonFundamentalsReadRepository. Matching is
    exact on both ticker and period; any case or format mapping is the caller's
    responsibility.
    """

    def process(
        self,
        records: list[FundamentalsRecord],
        ticker: str,
        period: Optional[str] = None,
    ) -> list[FundamentalsRecord]:
        """Return the records matching ticker, and period when given.

        Args:
            records: Fundamentals records to filter. An empty list yields [].
            ticker: BMV ticker to match exactly (e.g. "DANHOS13"). Required.
            period: Reporting-period label to match exactly (e.g. "1T2026"). When
                None, every period for the ticker is returned.

        Returns:
            list[FundamentalsRecord]: Matching records in input order. Empty when
                the ticker has no records.

        Raises:
            ValueError: If ticker is empty or blank.
        """
        if not ticker or not ticker.strip():
            raise ValueError("ticker is required to filter fundamentals records")
        return [
            record
            for record in records
            if record.ticker == ticker and (period is None or record.period == period)
        ]
