from typing import Optional

from modules.common.models import Fibra
from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FibraMetrics
from modules.fundamentals.models import FundamentalsHistory


class FundamentalsHistoryProcessor:
    """Aggregates a list of EnrichedFundamentalsRecord into a FundamentalsHistory output model.

    Transformation: list[EnrichedFundamentalsRecord] → FundamentalsHistory

    Produces:
        records              = all records sorted by (ticker asc, year asc, quarter asc)
        latest_by_ticker     = most recent record per ticker, keyed from catalog fibras;
                               None if no record exists for that ticker
        prior_year_by_ticker = same-quarter prior-year record per ticker;
                               None if not found or ticker has no records
        fibra_metrics        = per-FIBRA aggregate metrics keyed by ticker;
                               every ticker in fibras has an entry
        fibras               = catalog Fibra list passed in directly

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
                fibra_metrics        = per-FIBRA aggregate metrics (AFFO CAGR, periods_count,
                                       years_of_history) keyed by ticker; every ticker in fibras
                                       has an entry; Optional fields are None when fewer than 4
                                       records exist for the ticker or source values are None
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

        fibra_metrics: dict[str, FibraMetrics] = {
            f.ticker: self._compute_fibra_metrics(ticker=f.ticker, sorted_records=sorted_records)
            for f in fibras
        }

        return FundamentalsHistory(
            records=sorted_records,
            latest_by_ticker=latest_by_ticker,
            prior_year_by_ticker=prior_year_by_ticker,
            fibra_metrics=fibra_metrics,
            fibras=fibras,
        )

    def _compute_fibra_metrics(self, ticker: str, sorted_records: list[EnrichedFundamentalsRecord]) -> FibraMetrics:
        """Compute aggregate metrics for a single ticker from its sorted historical records.

        Args:
            ticker: BMV ticker string.
            sorted_records: All records across all tickers, already sorted by
                (ticker, year, quarter) — used to filter by ticker in order.

        Returns:
            FibraMetrics with periods_count and years_of_history always set.
            All Optional fields are None when fewer than 4 records exist for the ticker,
            or when the source field (affo / affo_per_cbfi) is None in the first or last record.
        """
        ticker_records = [r for r in sorted_records if r.ticker == ticker]
        periods_count = len(ticker_records)

        if periods_count == 0:
            return FibraMetrics(
                ticker=ticker,
                periods_count=0,
                years_of_history=0.0,
            )

        first = ticker_records[0]
        last = ticker_records[-1]
        first_year, first_quarter = self._parse_period(period=first.period)
        last_year, last_quarter = self._parse_period(period=last.period)
        years_of_history = (last_year + (last_quarter - 1) / 4) - (first_year + (first_quarter - 1) / 4)

        if periods_count < 4:
            return FibraMetrics(
                ticker=ticker,
                periods_count=periods_count,
                years_of_history=years_of_history,
            )

        affo_first: Optional[float] = float(first.affo) if first.affo is not None else None
        affo_latest: Optional[float] = float(last.affo) if last.affo is not None else None

        cagr_affo_total: Optional[float] = None
        if affo_first is not None and affo_latest is not None and years_of_history != 0:
            cagr_affo_total = (affo_latest / affo_first) ** (1 / years_of_history) - 1

        affo_per_cbfi_first: Optional[float] = first.affo_per_cbfi
        affo_per_cbfi_latest: Optional[float] = last.affo_per_cbfi

        cagr_affo_per_cbfi: Optional[float] = None
        if affo_per_cbfi_first is not None and affo_per_cbfi_latest is not None and years_of_history != 0:
            cagr_affo_per_cbfi = (affo_per_cbfi_latest / affo_per_cbfi_first) ** (1 / years_of_history) - 1

        return FibraMetrics(
            ticker=ticker,
            periods_count=periods_count,
            years_of_history=years_of_history,
            affo_first=affo_first,
            affo_latest=affo_latest,
            cagr_affo_total=cagr_affo_total,
            affo_per_cbfi_first=affo_per_cbfi_first,
            affo_per_cbfi_latest=affo_per_cbfi_latest,
            cagr_affo_per_cbfi=cagr_affo_per_cbfi,
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
