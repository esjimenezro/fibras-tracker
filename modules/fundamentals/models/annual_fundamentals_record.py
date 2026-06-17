from typing import Optional

from pydantic import BaseModel


class AnnualFundamentalsRecord(BaseModel):
    """Annual aggregation of quarterly fundamentals for a single FIBRA.

    Produced by AnnualFundamentalsProcessor from four complete quarterly
    EnrichedFundamentalsRecord instances (Q1–Q4). Only years with all four
    quarters present are included; incomplete years are omitted entirely.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        year: Calendar year of the aggregation.

        distribution_per_cbfi_annual: Sum of quarterly distribution_per_cbfi across
            the four quarters. Null if any quarter value is None.
        ffo_per_cbfi_annual: Sum of quarterly ffo_per_cbfi across the four quarters.
            Null if any quarter value is None.
        affo_per_cbfi_annual: Sum of quarterly affo_per_cbfi across the four quarters.
            Null if any quarter value is None.
        revenue_per_cbfi_annual: Sum of quarterly revenue_per_cbfi across the four
            quarters. Null if any quarter value is None.
        total_revenues_annual: Sum of quarterly total_revenues across the four quarters.
            Null if any quarter value is None.

        noi_annual: Sum of quarterly noi across the four quarters. Null if any quarter
            value is None.
        noi_per_cbfi_annual: Sum of quarterly noi_per_cbfi across the four quarters.
            Null if any quarter value is None.
        ebitda_annual: Sum of quarterly ebitda across the four quarters. Null if any
            quarter value is None.
        ebitda_per_cbfi_annual: Sum of quarterly ebitda_per_cbfi across the four quarters.
            Null if any quarter value is None.
        ffo_annual: Sum of quarterly ffo across the four quarters. Null if any quarter
            value is None.
        affo_annual: Sum of quarterly affo across the four quarters. Null if any quarter
            value is None.
        total_distribution_annual: Sum of quarterly total_distribution across the four
            quarters. Null if any quarter value is None.

        noi_margin_annual: NOI margin computed from annual sums (noi_annual / total_revenues_annual).
            Null if either operand is None or total_revenues_annual is zero.
        ebitda_margin_annual: EBITDA margin computed from annual sums
            (ebitda_annual / total_revenues_annual). Null if either operand is None or
            total_revenues_annual is zero.

        nav_per_cbfi: Q4 snapshot — nav_per_cbfi from the Q4 record. Already Optional;
            passed through as-is.
        ltv: Q4 snapshot — ltv from the Q4 record. Already Optional; passed through as-is.
        occupancy_rate: Q4 snapshot — occupancy_rate from the Q4 record. Already Optional;
            passed through as-is.
        wale: Q4 snapshot — Weighted Average Lease Expiry in years from the Q4 record.
            Already Optional; passed through as-is.
        top_tenant_pct: Q4 snapshot — largest single-tenant concentration from the Q4
            record. Already Optional; passed through as-is.
        top10_tenants_pct: Q4 snapshot — cumulative top-10 tenant concentration from the
            Q4 record. Already Optional; passed through as-is.
        gross_leasable_area_m2: Q4 snapshot — gross leasable area in square metres from
            the Q4 record. Already Optional; passed through as-is.
        cbfis_outstanding: Q4 snapshot — total CBFIs outstanding at Q4 close. Already
            Optional; passed through as-is.
        cbfis_per_m2: Q4 snapshot — cbfis_per_m2 from the Q4 record. Already Optional;
            passed through as-is.

        affo_payout_ratio_avg: Mean of quarterly affo_payout_ratio across the four
            quarters. Null if any quarter value is None.
    """

    ticker: str
    year: int

    distribution_per_cbfi_annual: Optional[float] = None
    ffo_per_cbfi_annual: Optional[float] = None
    affo_per_cbfi_annual: Optional[float] = None
    revenue_per_cbfi_annual: Optional[float] = None
    total_revenues_annual: Optional[int] = None

    noi_annual: Optional[int] = None
    noi_per_cbfi_annual: Optional[float] = None
    ebitda_annual: Optional[int] = None
    ebitda_per_cbfi_annual: Optional[float] = None
    ffo_annual: Optional[int] = None
    affo_annual: Optional[int] = None
    total_distribution_annual: Optional[float] = None

    noi_margin_annual: Optional[float] = None
    ebitda_margin_annual: Optional[float] = None

    nav_per_cbfi: Optional[float] = None
    ltv: Optional[float] = None
    occupancy_rate: Optional[float] = None
    wale: Optional[float] = None
    top_tenant_pct: Optional[float] = None
    top10_tenants_pct: Optional[float] = None

    gross_leasable_area_m2: Optional[int] = None
    cbfis_outstanding: Optional[int] = None
    cbfis_per_m2: Optional[float] = None

    affo_payout_ratio_avg: Optional[float] = None
