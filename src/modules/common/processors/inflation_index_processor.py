from modules.common.models import InflationRecord


class InflationIndexProcessor:
    """Compounds a value forward, year over year, using annual Mexican inflation rates.

    Transformation: base year/value + ordered rate years + inflation history
        -> compounded (year, value) series

    Backs FundamentalsHistoryProcessor's cagr_inflation (a pure compounding factor,
    base_value=1.0) — the modules/-layer copy of this compounding-and-truncation loop.
    ui/components/fundamentals/detail_chart.py's compound_inflation_series is a second,
    intentionally separate copy of the exact same loop for the two UI call sites
    (detail_chart's per-FIBRA reference line, comparison_chart's base-1000 index):
    ui/components/** may only depend on modules/*/models and modules/*/schemas, never on
    modules/*/processors, so this class cannot be shared across that boundary. Keep both
    copies in sync by hand if the compounding mechanic itself ever changes.
    """

    def process(
        self,
        base_year: int,
        base_value: float,
        rate_years: list[int],
        inflation_records: list[InflationRecord],
    ) -> list[tuple[int, float]]:
        """Compound base_value forward, applying one inflation rate per entry in rate_years.

        Args:
            base_year: The starting year, paired unchanged with base_value as the series' first
                entry — no rate is applied to it.
            base_value: The starting value (e.g. 1.0 for a bare compounding factor, 1000.0 for a
                base-1000 index, or an actual per-CBFI figure for a reference line).
            rate_years: Years to look up in inflation_records and multiply in, in order. Not
                necessarily consecutive or starting at base_year + 1 — the caller decides which
                year's rate lands on which step, and whether intervening years may be skipped.
            inflation_records: Annual inflation history to look up rates from.

        Returns:
            list[tuple[int, float]]: [(base_year, base_value), (rate_years[0], value after that
                rate), ...], truncated before the first entry of rate_years missing from
                inflation_records — never raises on a gap. Length is
                1 + the count of consecutive rate_years found, so callers can detect an
                incomplete run by comparing this length against len(rate_years) + 1.
        """
        inflation_by_year: dict[int, float] = {
            record.year: record.annual_inflation for record in inflation_records
        }
        series: list[tuple[int, float]] = [(base_year, base_value)]
        current = base_value
        for year in rate_years:
            if year not in inflation_by_year:
                break
            current *= (1.0 + inflation_by_year[year])
            series.append((year, current))
        return series
