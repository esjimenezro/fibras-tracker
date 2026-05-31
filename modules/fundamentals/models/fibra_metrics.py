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
