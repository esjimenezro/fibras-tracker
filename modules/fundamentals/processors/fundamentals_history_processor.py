from typing import Optional

from modules.common.models import Fibra
from modules.common.models import InflationRecord
from modules.fundamentals.models import AnnualFundamentalsRecord
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
        annual_records       = annual aggregates per ticker (passed through from caller)
        inflation_records    = full inflation history (passed through from caller)

    Invariant: period strings (e.g. "1T2026") are parsed as (year, quarter) integers —
        never compared lexicographically. "1T2026" sorts after "4T2025" because
        (2026, 1) > (2025, 4).
    """

    def process(
        self,
        records: list[EnrichedFundamentalsRecord],
        fibras: list[Fibra],
        annual_records: list[AnnualFundamentalsRecord],
        inflation_records: list[InflationRecord],
    ) -> FundamentalsHistory:
        """Aggregate enriched fundamentals records into a sorted history.

        Args:
            records: All enriched fundamentals records across all tickers and periods.
                Must not be empty.
            fibras: FIBRA catalog entries. Every ticker in fibras appears as a key in
                latest_by_ticker; value is None if no record exists for that ticker.
            annual_records: Optional annual aggregates per ticker produced by
                AnnualFundamentalsProcessor. When provided, used to compute annual-period
                FibraMetrics fields (growth counters, CAGRs). Defaults to None (all annual
                FibraMetrics fields remain None).
            inflation_records: Optional full annual Mexican inflation history (INPC).
                Used alongside annual_records to compute cagr_inflation and
                distribution_vs_inflation. Defaults to None (treated as empty list).

        Returns:
            FundamentalsHistory with the following fields:
                records              = all records sorted by ticker asc, then period asc
                                       (year first, then quarter — never lexicographic)
                latest_by_ticker     = most recent record per ticker, keyed from catalog fibras;
                                       None if no record exists for that ticker
                prior_year_by_ticker = record for the same quarter one year prior per ticker;
                                       None if no such record exists or the ticker has no records
                fibra_metrics        = per-FIBRA aggregate metrics keyed by ticker; every ticker
                                       in fibras has an entry; AFFO Optional fields are None when
                                       fewer than 4 records exist; annual fields are None when
                                       annual_records is not provided or has fewer than 2 entries
                fibras               = the catalog Fibra list passed in directly
                annual_records       = annual_records or empty dict
                inflation_records    = inflation_records or empty list

        Raises:
            ValueError: If records is empty.
        """
        if not records:
            raise ValueError("Cannot build FundamentalsHistory from an empty records list.")

        if not fibras:
            raise ValueError("Fibras list cannot be empty; used to key latest_by_ticker and fibra_metrics.")

        if not annual_records:
            raise ValueError("Annual records list cannot be empty; used to compute annual FibraMetrics fields.")

        if not inflation_records:
            raise ValueError("Inflation records list cannot be empty; used to compute cagr_inflation and distribution_vs_inflation.")

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
            f.ticker: self._compute_fibra_metrics(
                ticker=f.ticker,
                sorted_records=sorted_records,
                annual_records=annual_records,
                inflation_records=inflation_records,
            )
            for f in fibras
        }

        return FundamentalsHistory(
            records=sorted_records,
            latest_by_ticker=latest_by_ticker,
            prior_year_by_ticker=prior_year_by_ticker,
            fibra_metrics=fibra_metrics,
            fibras=fibras,
            annual_records=annual_records,
            inflation_records=inflation_records,
        )

    def _compute_fibra_metrics(
        self,
        ticker: str,
        sorted_records: list[EnrichedFundamentalsRecord],
        annual_records: list[AnnualFundamentalsRecord],
        inflation_records: list[InflationRecord],
    ) -> FibraMetrics:
        """Compute aggregate metrics for a single ticker from its sorted historical records.

        Args:
            ticker: BMV ticker string.
            sorted_records: All records across all tickers, already sorted by
                (ticker, year, quarter) — used to filter by ticker in order.
            annual_records: Optional annual aggregated records for this ticker only,
                sorted by year ascending. When provided, used to compute growth counters
                and annual-period CAGRs. When None or empty, all 10 annual fields are None.
            inflation_records: Annual inflation records used to compute cagr_inflation.
                When None or empty, cagr_inflation and distribution_vs_inflation are None.

        Returns:
            FibraMetrics with periods_count and years_of_history always set.
            AFFO Optional fields are None when fewer than 4 records exist for the ticker
            or when the source field is None in the first or last record.
            Annual fields are None when annual_records is not provided or has fewer than 2 entries.
        """
        ticker_records = [r for r in sorted_records if r.ticker == ticker]
        periods_count = len(ticker_records)

        ticker_annual_records = [r for r in annual_records if r.ticker == ticker]

        if periods_count == 0:
            return FibraMetrics(
                ticker=ticker,
                periods_count=0,
                years_of_history=0.0,
                **self._compute_annual_metrics(
                    annual_records=ticker_annual_records,
                    inflation_records=inflation_records
                ),
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
                **self._compute_annual_metrics(
                    annual_records=ticker_annual_records,
                    inflation_records=inflation_records
                ),
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
            **self._compute_annual_metrics(
                annual_records=ticker_annual_records,
                inflation_records=inflation_records
            ),
        )

    def _compute_annual_metrics(
        self,
        annual_records: list[AnnualFundamentalsRecord],
        inflation_records: list[InflationRecord],
    ) -> dict:
        """Compute the 10 annual-data FibraMetrics fields for a single ticker.

        Args:
            annual_records: Annual aggregated records for this ticker, sorted by year ascending.
                None or empty → all 10 fields are None.
            inflation_records: Annual inflation records for cagr_inflation computation.

        Returns:
            dict: Keyword arguments for the 10 annual FibraMetrics fields, ready to unpack
                into a FibraMetrics constructor call.
        """
        null_result: dict = {
            "total_annual_years": None,
            "years_with_distribution": None,
            "years_distribution_grew": None,
            "years_affo_per_cbfi_grew": None,
            "years_nav_per_cbfi_grew": None,
            "years_revenue_per_cbfi_grew": None,
            "cagr_distribution_per_cbfi": None,
            "cagr_revenue_per_cbfi": None,
            "cagr_inflation": None,
            "distribution_vs_inflation": None,
        }

        if not annual_records:
            return null_result

        total_annual_years = len(annual_records)
        years_with_distribution = sum(
            1 for r in annual_records
            if r.distribution_per_cbfi_annual is not None and r.distribution_per_cbfi_annual > 0
        )
        years_distribution_grew = self._count_years_grew(
            values=[r.distribution_per_cbfi_annual for r in annual_records],
        )
        years_affo_per_cbfi_grew = self._count_years_grew(
            values=[r.affo_per_cbfi_annual for r in annual_records],
        )
        years_nav_per_cbfi_grew = self._count_years_grew(
            values=[r.nav_per_cbfi for r in annual_records],
        )
        years_revenue_per_cbfi_grew = self._count_years_grew(
            values=[r.revenue_per_cbfi_annual for r in annual_records],
        )

        cagr_distribution_per_cbfi: Optional[float] = None
        cagr_revenue_per_cbfi: Optional[float] = None
        cagr_inflation: Optional[float] = None
        distribution_vs_inflation: Optional[float] = None

        if len(annual_records) >= 2:
            first_annual = annual_records[0]
            last_annual = annual_records[-1]
            years = last_annual.year - first_annual.year

            cagr_distribution_per_cbfi = self._safe_cagr(
                first=first_annual.distribution_per_cbfi_annual,
                last=last_annual.distribution_per_cbfi_annual,
                years=years,
            )
            cagr_revenue_per_cbfi = self._safe_cagr(
                first=first_annual.revenue_per_cbfi_annual,
                last=last_annual.revenue_per_cbfi_annual,
                years=years,
            )
            cagr_inflation = self._cagr_inflation(
                first_year=first_annual.year,
                last_year=last_annual.year,
                inflation_records=inflation_records,
            )
            if cagr_distribution_per_cbfi is not None and cagr_inflation is not None:
                distribution_vs_inflation = cagr_distribution_per_cbfi - cagr_inflation

        return {
            "total_annual_years": total_annual_years,
            "years_with_distribution": years_with_distribution,
            "years_distribution_grew": years_distribution_grew,
            "years_affo_per_cbfi_grew": years_affo_per_cbfi_grew,
            "years_nav_per_cbfi_grew": years_nav_per_cbfi_grew,
            "years_revenue_per_cbfi_grew": years_revenue_per_cbfi_grew,
            "cagr_distribution_per_cbfi": cagr_distribution_per_cbfi,
            "cagr_revenue_per_cbfi": cagr_revenue_per_cbfi,
            "cagr_inflation": cagr_inflation,
            "distribution_vs_inflation": distribution_vs_inflation,
        }

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

    @staticmethod
    def _count_years_grew(values: list[Optional[float]]) -> int:
        """Count consecutive year pairs where the later value exceeds the earlier one.

        Args:
            values: Ordered list of values (one per year). May contain None.

        Returns:
            int: Number of year-over-year increases; None pairs are skipped, not counted.
        """
        count = 0
        for i in range(1, len(values)):
            prev, curr = values[i - 1], values[i]
            if prev is not None and curr is not None and curr > prev:
                count += 1
        return count

    @staticmethod
    def _safe_cagr(first: Optional[float], last: Optional[float], years: int) -> Optional[float]:
        """Compound annual growth rate from first to last over years.

        Args:
            first: Starting value.
            last: Ending value.
            years: Number of years between first and last.

        Returns:
            float: CAGR as a decimal, or None if either value is None or years is zero.
        """
        if first is None or last is None or years == 0:
            return None
        return (last / first) ** (1 / years) - 1

    @staticmethod
    def _cagr_inflation(
        first_year: int,
        last_year: int,
        inflation_records: list[InflationRecord],
    ) -> Optional[float]:
        """Geometric mean annual inflation rate over [first_year, last_year).

        Multiplies (1 + rate) for each year in [first_year, last_year), then raises
        the product to 1/years.

        Args:
            first_year: Start year (inclusive).
            last_year: End year (exclusive boundary — same as last annual record's year).
            inflation_records: Annual inflation records to look up rates from.

        Returns:
            float: Inflation CAGR as a decimal, or None if any year in the range is
                missing from inflation_records, or if years is zero.
        """
        years = last_year - first_year
        if years == 0:
            return None
        inflation_map = {r.year: r.annual_inflation for r in inflation_records}
        compound = 1.0
        for y in range(first_year, last_year):
            if y not in inflation_map:
                return None
            compound *= (1 + inflation_map[y])
        return compound ** (1 / years) - 1
