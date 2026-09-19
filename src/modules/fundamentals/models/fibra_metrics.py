from typing import Optional

from pydantic import BaseModel


class FibraMetrics(BaseModel):
    """Per-FIBRA aggregate metrics computed from the full historical series.

    All AFFO-related fields are None when fewer than 4 records are available for
    the ticker. periods_count and years_of_history are always populated.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        periods_count: Number of records used in calculations.
        years_of_history: Years between first and last period, expressed as a decimal
            using (year + (quarter - 1) / 4). Zero when periods_count is zero or one.

        affo_first: AFFO (MXN) in the earliest available period.
            None when fewer than 4 records exist or record.affo is None.
        affo_latest: AFFO (MXN) in the most recent period.
            None when fewer than 4 records exist or record.affo is None.
        cagr_affo_total: Compound annual growth rate of total AFFO:
            (affo_latest / affo_first) ** (1 / years_of_history) - 1.
            None if either affo value is None, fewer than 4 records exist,
            or years_of_history is zero.

        affo_per_cbfi_first: AFFO per CBFI in the earliest available period.
            None when fewer than 4 records exist or record.affo_per_cbfi is None.
        affo_per_cbfi_latest: AFFO per CBFI in the most recent period.
            None when fewer than 4 records exist or record.affo_per_cbfi is None.
        cagr_affo_per_cbfi: Compound annual growth rate of AFFO per CBFI:
            (affo_per_cbfi_latest / affo_per_cbfi_first) ** (1 / years_of_history) - 1.
            None if either value is None, fewer than 4 records exist,
            or years_of_history is zero.

        total_annual_years: Number of complete years (all four quarters present) in annual_records.
            None when no annual data is provided.
        years_with_distribution: Count of years where distribution_per_cbfi_annual is not None
            and greater than zero. None when no annual data is provided.
        years_distribution_grew: Count of year-over-year increases in distribution_per_cbfi_annual.
            First year is skipped (no prior year to compare); None pairs are also skipped.
            None when no annual data is provided.
        years_affo_per_cbfi_grew: Count of year-over-year increases in affo_per_cbfi_annual.
            Same skipping rules as years_distribution_grew.
            None when no annual data is provided.
        years_nav_per_cbfi_grew: Count of year-over-year increases in nav_per_cbfi (Q4 snapshot).
            Same skipping rules as years_distribution_grew.
            None when no annual data is provided.
        years_revenue_per_cbfi_grew: Count of year-over-year increases in revenue_per_cbfi_annual.
            Same skipping rules as years_distribution_grew.
            None when no annual data is provided.

        cagr_distribution_per_cbfi: Annual CAGR of distribution_per_cbfi_annual from first to last
            complete year: (last / first) ^ (1 / years) - 1.
            None if fewer than 2 annual records, either boundary value is None, or years is zero.
        cagr_revenue_per_cbfi: Annual CAGR of revenue_per_cbfi_annual from first to last complete year.
            Same None conditions as cagr_distribution_per_cbfi.
        cagr_inflation: Geometric mean annual Mexican inflation rate over the same year range as the
            ticker's annual records. Computed as compound_factor ^ (1 / years) - 1 where
            compound_factor = product of (1 + rate) for each year in [first_year, last_year).
            None if any year in the range is missing from inflation_records, or years is zero.
        distribution_vs_inflation: cagr_distribution_per_cbfi - cagr_inflation.
            None if either component is None.
    """

    ticker: str
    periods_count: int
    years_of_history: float

    affo_first: Optional[float] = None
    affo_latest: Optional[float] = None
    cagr_affo_total: Optional[float] = None

    affo_per_cbfi_first: Optional[float] = None
    affo_per_cbfi_latest: Optional[float] = None
    cagr_affo_per_cbfi: Optional[float] = None

    total_annual_years: Optional[int] = None
    years_with_distribution: Optional[int] = None
    years_distribution_grew: Optional[int] = None
    years_affo_per_cbfi_grew: Optional[int] = None
    years_nav_per_cbfi_grew: Optional[int] = None
    years_revenue_per_cbfi_grew: Optional[int] = None

    cagr_distribution_per_cbfi: Optional[float] = None
    cagr_revenue_per_cbfi: Optional[float] = None
    cagr_inflation: Optional[float] = None
    distribution_vs_inflation: Optional[float] = None
