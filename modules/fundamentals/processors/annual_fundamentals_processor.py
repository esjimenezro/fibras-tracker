from typing import Optional

from modules.fundamentals.models import AnnualFundamentalsRecord
from modules.fundamentals.models import EnrichedFundamentalsRecord


class AnnualFundamentalsProcessor:
    """Aggregates quarterly EnrichedFundamentalsRecord instances into annual summaries.

    Transformation: list[EnrichedFundamentalsRecord] → dict[str, list[AnnualFundamentalsRecord]]

    Only years for which all four quarters (Q1–Q4) are present for a given ticker
    are included in the output. Incomplete years are skipped entirely — no nulls are
    produced for missing quarters.

    Aggregation rules:
        Sum fields (distribution_per_cbfi_annual, ffo_per_cbfi_annual,
                    affo_per_cbfi_annual, revenue_per_cbfi_annual,
                    total_revenues_annual, noi_annual, noi_per_cbfi_annual,
                    ebitda_annual, ebitda_per_cbfi_annual, ffo_annual,
                    affo_annual, total_distribution_annual):
            Sum of the four quarterly values. Null if any quarter value is None.
            Integer-sourced sums (noi_annual, ebitda_annual, ffo_annual,
            affo_annual, total_revenues_annual) are cast to int.

        Recomputed margin fields (noi_margin_annual, ebitda_margin_annual):
            Computed from the annual sums, not averaged from quarterly margins.
            noi_margin_annual    = noi_annual / total_revenues_annual
            ebitda_margin_annual = ebitda_annual / total_revenues_annual
            Null if either operand is None or total_revenues_annual is zero.

        Q4 snapshot fields (nav_per_cbfi, ltv, occupancy_rate, wale,
                            top_tenant_pct, top10_tenants_pct,
                            gross_leasable_area_m2, cbfis_outstanding, cbfis_per_m2):
            Value taken directly from the Q4 record. Passed through as-is (already Optional).

        Average fields (affo_payout_ratio_avg):
            Arithmetic mean of the four quarterly values. Null if any quarter value is None.
    """

    def process(
        self,
        records: list[EnrichedFundamentalsRecord],
    ) -> list[AnnualFundamentalsRecord]:
        """Aggregate quarterly records into annual summaries per ticker.

        Args:
            records: All enriched quarterly fundamentals records across all tickers
                and periods. Must not be empty.

        Returns:
            list[AnnualFundamentalsRecord]: A list of annual fundamentals records. Each annual
                record contains:

                    distribution_per_cbfi_annual = sum of quarterly distribution_per_cbfi
                    ffo_per_cbfi_annual          = sum of quarterly ffo_per_cbfi
                    affo_per_cbfi_annual         = sum of quarterly affo_per_cbfi
                    revenue_per_cbfi_annual      = sum of quarterly revenue_per_cbfi
                    total_revenues_annual        = sum of quarterly total_revenues (cast to int)
                    noi_annual                   = sum of quarterly noi (cast to int)
                    noi_per_cbfi_annual          = sum of quarterly noi_per_cbfi
                    ebitda_annual                = sum of quarterly ebitda (cast to int)
                    ebitda_per_cbfi_annual       = sum of quarterly ebitda_per_cbfi
                    ffo_annual                   = sum of quarterly ffo (cast to int)
                    affo_annual                  = sum of quarterly affo (cast to int)
                    total_distribution_annual    = sum of quarterly total_distribution

                    noi_margin_annual    = noi_annual / total_revenues_annual
                    ebitda_margin_annual = ebitda_annual / total_revenues_annual

                    nav_per_cbfi           = Q4 snapshot
                    ltv                    = Q4 snapshot
                    occupancy_rate         = Q4 snapshot
                    wale                   = Q4 snapshot
                    top_tenant_pct         = Q4 snapshot
                    top10_tenants_pct      = Q4 snapshot
                    gross_leasable_area_m2 = Q4 snapshot
                    cbfis_outstanding      = Q4 snapshot
                    cbfis_per_m2           = Q4 snapshot

                    affo_payout_ratio_avg = mean of quarterly affo_payout_ratio

                Sum and average fields are None when any quarterly value is None.
                Margin fields are None when total_revenues_annual is None or zero.
                Q4 snapshot fields are passed through as-is from the Q4 record.

        Raises:
            ValueError: If records is empty.
        """
        if not records:
            raise ValueError("Cannot aggregate an empty list of EnrichedFundamentalsRecord instances.")

        by_ticker: dict[str, dict[int, list[EnrichedFundamentalsRecord]]] = {}
        for record in records:
            year = self._parse_year(period=record.period)
            by_ticker.setdefault(record.ticker, {}).setdefault(year, []).append(record)

        annual_records: list[AnnualFundamentalsRecord] = []
        for ticker, years in by_ticker.items():
            for year, q_records in years.items():
                quarters_present = {int(r.period.split("T")[0]) for r in q_records}
                if quarters_present != {1, 2, 3, 4}:
                    continue
                annual_records.append(self._compute_annual(
                    ticker=ticker,
                    year=year,
                    q_records=q_records,
                ))

        return sorted(annual_records, key=lambda r: (r.ticker, r.year))

    def _compute_annual(
        self,
        ticker: str,
        year: int,
        q_records: list[EnrichedFundamentalsRecord],
    ) -> AnnualFundamentalsRecord:
        """Compute an annual record from exactly four quarterly records.

        Args:
            ticker: BMV ticker string.
            year: Calendar year of the aggregation.
            q_records: Exactly four quarterly records for the given ticker and year,
                one per quarter. Order is not required to be sorted.

        Returns:
            AnnualFundamentalsRecord with all fields computed according to their
            aggregation rule (sum, Q4 snapshot, or average).
        """
        q4 = next(r for r in q_records if r.period.startswith("4T"))

        total_revenues_sum = self._safe_sum(values=[r.total_revenues for r in q_records])
        noi_sum = self._safe_sum(values=[r.noi for r in q_records])
        ebitda_sum = self._safe_sum(values=[r.ebitda for r in q_records])
        ffo_sum = self._safe_sum(values=[r.ffo for r in q_records])
        affo_sum = self._safe_sum(values=[r.affo for r in q_records])

        total_revenues_annual = int(total_revenues_sum) if total_revenues_sum is not None else None
        noi_annual = int(noi_sum) if noi_sum is not None else None
        ebitda_annual = int(ebitda_sum) if ebitda_sum is not None else None
        ffo_annual = int(ffo_sum) if ffo_sum is not None else None
        affo_annual = int(affo_sum) if affo_sum is not None else None

        return AnnualFundamentalsRecord(
            ticker=ticker,
            year=year,
            distribution_per_cbfi_annual=self._safe_sum(
                values=[r.distribution_per_cbfi for r in q_records],
            ),
            ffo_per_cbfi_annual=self._safe_sum(
                values=[r.ffo_per_cbfi for r in q_records],
            ),
            affo_per_cbfi_annual=self._safe_sum(
                values=[r.affo_per_cbfi for r in q_records],
            ),
            revenue_per_cbfi_annual=self._safe_sum(
                values=[r.revenue_per_cbfi for r in q_records],
            ),
            total_revenues_annual=total_revenues_annual,
            noi_annual=noi_annual,
            noi_per_cbfi_annual=self._safe_sum(
                values=[r.noi_per_cbfi for r in q_records],
            ),
            ebitda_annual=ebitda_annual,
            ebitda_per_cbfi_annual=self._safe_sum(
                values=[r.ebitda_per_cbfi for r in q_records],
            ),
            ffo_annual=ffo_annual,
            affo_annual=affo_annual,
            total_distribution_annual=self._safe_sum(
                values=[r.total_distribution for r in q_records],
            ),
            noi_margin_annual=self._safe_div(
                numerator=noi_annual,
                denominator=total_revenues_annual,
            ),
            ebitda_margin_annual=self._safe_div(
                numerator=ebitda_annual,
                denominator=total_revenues_annual,
            ),
            nav_per_cbfi=q4.nav_per_cbfi,
            ltv=q4.ltv,
            occupancy_rate=q4.occupancy_rate,
            wale=q4.wale,
            top_tenant_pct=q4.top_tenant_pct,
            top10_tenants_pct=q4.top10_tenants_pct,
            gross_leasable_area_m2=q4.gross_leasable_area_m2,
            cbfis_outstanding=q4.cbfis_outstanding,
            cbfis_per_m2=q4.cbfis_per_m2,
            affo_payout_ratio_avg=self._safe_avg(
                values=[r.affo_payout_ratio for r in q_records],
            ),
        )

    @staticmethod
    def _parse_year(period: str) -> int:
        """Parse the year integer from a period string.

        Args:
            period: Period string in the format "QTYear" (e.g. "1T2026", "4T2025").

        Returns:
            int: The calendar year extracted from the period string.
        """
        _, year_str = period.split("T")
        return int(year_str)

    @staticmethod
    def _safe_sum(values: list[Optional[float]]) -> Optional[float]:
        """Sum a list of values, returning None if any value is None.

        Args:
            values: List of numeric values, any of which may be None.

        Returns:
            float: Sum of all values, or None if any value is None.
        """
        if any(v is None for v in values):
            return None
        return sum(values)

    @staticmethod
    def _safe_avg(values: list[Optional[float]]) -> Optional[float]:
        """Average a list of values, returning None if any value is None.

        Args:
            values: List of numeric values, any of which may be None.

        Returns:
            float: Arithmetic mean of all values, or None if any value is None.
        """
        if any(v is None for v in values):
            return None
        return sum(values) / len(values)

    @staticmethod
    def _safe_div(
        numerator: Optional[float],
        denominator: Optional[float],
    ) -> Optional[float]:
        """Divide numerator by denominator, returning None on missing data or zero denominator.

        Args:
            numerator: Dividend value, or None.
            denominator: Divisor value, or None.

        Returns:
            float: numerator / denominator, or None if either argument is None or
                denominator is zero.
        """
        if numerator is None or denominator is None or denominator == 0:
            return None
        return numerator / denominator
