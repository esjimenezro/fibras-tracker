from typing import Optional

from modules.fundamentals.models.fundamentals_record import FundamentalsRecord


class EnrichedFundamentalsRecord(FundamentalsRecord):
    """A fundamentals snapshot enriched with all derived financial and market metrics.

    Extends FundamentalsRecord with computed fields produced by FundamentalsProcessor.

    Attributes:
        market_price: Last known market price per CBFI in MXN (injected by the processor).

        noi_margin: NOI as a fraction of total revenues (noi / total_revenues).
        ebitda_margin: EBITDA as a fraction of total revenues (ebitda / total_revenues).
        revenue_per_m2: Total revenues per square metre of GLA (total_revenues / gross_leasable_area_m2).
        affo_per_m2: AFFO per square metre of GLA (affo / gross_leasable_area_m2).
        cbfis_per_m2: CBFI emission density — CBFIs outstanding per square metre of GLA
            (cbfis_outstanding / gross_leasable_area_m2).

        ffo_per_cbfi: FFO per CBFI (ffo / cbfis_with_rights).
        affo_per_cbfi: AFFO per CBFI (affo / cbfis_with_rights).
        nav_per_cbfi: Net Asset Value per CBFI (total_equity / cbfis_outstanding).

        ltv: Loan-to-Value ratio (financial_debt / total_assets).
        affo_payout_ratio: Fraction of AFFO distributed to holders
            (distribution_per_cbfi / affo_per_cbfi).
        total_distribution: Total cash distributed to holders in the period
            (distribution_per_cbfi * cbfis_with_rights).

        market_cap: Total market capitalisation in MXN (market_price * cbfis_outstanding).
        price_to_ffo: Price-to-FFO multiple (market_price / ffo_per_cbfi).
        price_to_affo: Price-to-AFFO multiple (market_price / affo_per_cbfi).
        dividend_yield: Annualised distribution yield (distribution_per_cbfi * 4 / market_price).
        price_to_nav: Premium or discount to NAV (market_price / nav_per_cbfi).
    """

    market_price: Optional[float] = None

    noi_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    revenue_per_m2: Optional[float] = None
    affo_per_m2: Optional[float] = None
    cbfis_per_m2: Optional[float] = None

    ffo_per_cbfi: Optional[float] = None
    affo_per_cbfi: Optional[float] = None
    nav_per_cbfi: Optional[float] = None

    ltv: Optional[float] = None
    affo_payout_ratio: Optional[float] = None
    total_distribution: Optional[float] = None

    market_cap: Optional[float] = None
    price_to_ffo: Optional[float] = None
    price_to_affo: Optional[float] = None
    dividend_yield: Optional[float] = None
    price_to_nav: Optional[float] = None
