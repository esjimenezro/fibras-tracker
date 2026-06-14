from datetime import date
from typing import Optional

from pydantic import BaseModel


class FundamentalsRecord(BaseModel):
    """A single quarterly/annual fundamentals snapshot for a FIBRA.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        period: Reporting period label (e.g. "1T2026").
        report_date: Date the report was published.
        total_revenues: Total revenues in MXN.
        noi: Net Operating Income in MXN.
        ebitda: EBITDA in MXN.
        ffo: Funds From Operations in MXN.
        affo: Adjusted Funds From Operations in MXN.
        distribution_per_cbfi: Cash distributed per CBFI in MXN.
        gross_leasable_area_m2: Gross leasable area in square metres.
        cbfis_outstanding: Total CBFIs outstanding at quarter close.
        cbfis_with_rights: CBFIs with economic rights during the period. May differ from
            cbfis_outstanding in quarters with capital raises or buybacks.
        total_equity: Total equity (NAV) in MXN.
        total_debt: Total debt in MXN.
        financial_debt: Financial (interest-bearing) debt in MXN.
        total_assets: Total assets in MXN.
        occupancy_rate: Portfolio occupancy as a fraction (0–1).
        usd_mxn_exchange_rate: USD/MXN exchange rate at period end.
        wale: Weighted Average Lease Expiry in years. Null where not explicitly
            reported.
        top_tenant_pct: Percentage of the largest single tenant over the base
            reported by each FIBRA (decimal, e.g. 0.10 for 10 %).
        top10_tenants_pct: Cumulative percentage of the top 10 tenants over the
            same base (decimal).
    """

    ticker: str
    period: str
    report_date: date
    total_revenues: Optional[int] = None
    noi: Optional[int] = None
    ebitda: Optional[int] = None
    ffo: Optional[int] = None
    affo: Optional[int] = None
    distribution_per_cbfi: Optional[float] = None
    gross_leasable_area_m2: Optional[int] = None
    cbfis_outstanding: Optional[int] = None
    cbfis_with_rights: Optional[int] = None
    total_equity: Optional[int] = None
    total_debt: Optional[int] = None
    financial_debt: Optional[int] = None
    total_assets: Optional[int] = None
    occupancy_rate: Optional[float] = None
    usd_mxn_exchange_rate: Optional[float] = None
    wale: Optional[float] = None
    top_tenant_pct: Optional[float] = None
    top10_tenants_pct: Optional[float] = None
