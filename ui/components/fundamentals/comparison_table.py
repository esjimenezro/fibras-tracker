from typing import Optional

import pandas as pd
import streamlit as st

from modules.common.models import Fibra
from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FibraMetrics
from ui.components.fundamentals.detail_chart import KPI_CONFIG
from ui.styles.theme import format_mxn
from ui.styles.theme import format_pct

_RED = "background-color: rgba(255,99,99,0.15)"
_YELLOW = "background-color: rgba(255,200,50,0.15)"
_GREEN = "background-color: rgba(50,200,100,0.15)"
_AFFO_POSITIVE_BG = "background-color: rgba(46,125,50,0.15)"
_AFFO_NEGATIVE_BG = "background-color: rgba(198,40,40,0.15)"

# Thresholds for LTV and ocupación — still present in KPI_CONFIG.
# noi_margin and ebitda_margin were removed from KPI_CONFIG in the KPI unification;
# their thresholds are hardcoded here temporarily until comparison_table is redesigned.
_NOI_MARGIN_LOWER: float = 0.70
_NOI_MARGIN_UPPER: float = 0.80
_EBITDA_MARGIN_LOWER: float = 0.60
_EBITDA_MARGIN_UPPER: float = 0.70
_OCUPACION_LOWER: float = KPI_CONFIG["ocupacion"]["lower"]
_OCUPACION_UPPER: float = KPI_CONFIG["ocupacion"]["upper"]
_LTV_LOWER: float = KPI_CONFIG["ltv"]["lower"]
_LTV_UPPER: float = KPI_CONFIG["ltv"]["upper"]

# Thresholds for columns with no KPI_CONFIG entry — defined here as the single source of truth.
_CAGR_AFFO_PER_CBFI_LOWER: float = 0.03
_CAGR_AFFO_PER_CBFI_UPPER: float = 0.08
_CAGR_AFFO_TOTAL_LOWER: float = 0.05
_CAGR_AFFO_TOTAL_UPPER: float = 0.15
_P_AFFO_LOWER: float = 10.0
_P_AFFO_UPPER: float = 20.0
_DIV_YIELD_LOWER: float = 0.05
_DIV_YIELD_UPPER: float = 0.08

_CAPTION = (
    "* El AFFO/CBFI no es directamente comparable entre FIBRAs "
    "debido a diferencias metodológicas en su cálculo. Consulta "
    "el glosario de cada reporte trimestral."
)

_COLUMNS = [
    "FIBRA",
    "NOI Margin",
    "EBITDA Margin",
    "Ocupación",
    "LTV",
    "AFFO/CBFI *",
    "CAGR AFFO/CBFI",
    "CAGR AFFO Total",
    "P/AFFO",
    "Dividend Yield",
]


def _color_cell(value: Optional[float], lower: float, upper: float, inverse: bool) -> str:
    """Return a CSS background-color string for a table cell based on threshold comparisons.

    Args:
        value: Numeric value to evaluate. None returns an empty string (no colour).
        lower: Lower threshold boundary.
        upper: Upper threshold boundary.
        inverse: When True, green is below lower and red is above upper (e.g. LTV, P/AFFO).

    Returns:
        CSS background-color string, or empty string when value is None.
    """
    if value is None:
        return ""
    if not inverse:
        if value < lower:
            return _RED
        if value > upper:
            return _GREEN
        return _YELLOW
    else:
        if value < lower:
            return _GREEN
        if value > upper:
            return _RED
        return _YELLOW


def render_comparison_table(
    latest_by_ticker: dict[str, Optional[EnrichedFundamentalsRecord]],
    prior_year_by_ticker: dict[str, Optional[EnrichedFundamentalsRecord]],
    fibras: list[Fibra],
    fibra_metrics: dict[str, FibraMetrics],
) -> None:
    """Render a styled cross-FIBRA comparison table with traffic-light background colours.

    One row per FIBRA in fibras order. Each KPI column uses threshold-based background
    colours: green above upper threshold, yellow in the middle band, red below lower
    threshold. The LTV and P/AFFO columns use inverse logic (lower is better).
    The AFFO/CBFI column is coloured by year-over-year growth instead of thresholds.
    None values display as "N/D" with no background colour.

    Args:
        latest_by_ticker: Most recent EnrichedFundamentalsRecord per ticker; None if no data.
        prior_year_by_ticker: Same-quarter prior-year record per ticker; None if unavailable.
        fibras: FIBRA catalog entries defining row order and tickers.
        fibra_metrics: Per-FIBRA aggregate metrics keyed by ticker.
    """
    display_rows: list[dict] = []
    style_rows: list[dict] = []

    for fibra in fibras:
        latest: Optional[EnrichedFundamentalsRecord] = latest_by_ticker.get(fibra.ticker)
        prior: Optional[EnrichedFundamentalsRecord] = prior_year_by_ticker.get(fibra.ticker)
        metrics: Optional[FibraMetrics] = fibra_metrics.get(fibra.ticker)

        noi_margin: Optional[float] = latest.noi_margin if latest else None
        ebitda_margin: Optional[float] = latest.ebitda_margin if latest else None
        occupancy_rate: Optional[float] = latest.occupancy_rate if latest else None
        ltv: Optional[float] = latest.ltv if latest else None
        affo_per_cbfi: Optional[float] = latest.affo_per_cbfi if latest else None
        price_to_affo: Optional[float] = latest.price_to_affo if latest else None
        dividend_yield: Optional[float] = latest.dividend_yield if latest else None
        cagr_affo_per_cbfi: Optional[float] = metrics.cagr_affo_per_cbfi if metrics else None
        cagr_affo_total: Optional[float] = metrics.cagr_affo_total if metrics else None
        prior_affo_per_cbfi: Optional[float] = prior.affo_per_cbfi if prior else None

        display_rows.append({
            "FIBRA": fibra.ticker,
            "NOI Margin": format_pct(value=noi_margin, include_sign=False) if noi_margin is not None else "N/D",
            "EBITDA Margin": format_pct(value=ebitda_margin, include_sign=False) if ebitda_margin is not None else "N/D",
            "Ocupación": format_pct(value=occupancy_rate, include_sign=False) if occupancy_rate is not None else "N/D",
            "LTV": format_pct(value=ltv, include_sign=False) if ltv is not None else "N/D",
            "AFFO/CBFI *": format_mxn(value=affo_per_cbfi) if affo_per_cbfi is not None else "N/D",
            "CAGR AFFO/CBFI": format_pct(value=cagr_affo_per_cbfi) if cagr_affo_per_cbfi is not None else "N/D",
            "CAGR AFFO Total": format_pct(value=cagr_affo_total) if cagr_affo_total is not None else "N/D",
            "P/AFFO": f"{price_to_affo:.2f}" if price_to_affo is not None else "N/D",
            "Dividend Yield": format_pct(value=dividend_yield, include_sign=False) if dividend_yield is not None else "N/D",
        })

        affo_css = ""
        if affo_per_cbfi is not None and prior_affo_per_cbfi is not None:
            affo_css = _AFFO_POSITIVE_BG if affo_per_cbfi >= prior_affo_per_cbfi else _AFFO_NEGATIVE_BG

        style_rows.append({
            "FIBRA": "",
            "NOI Margin": _color_cell(value=noi_margin, lower=_NOI_MARGIN_LOWER, upper=_NOI_MARGIN_UPPER, inverse=False),
            "EBITDA Margin": _color_cell(value=ebitda_margin, lower=_EBITDA_MARGIN_LOWER, upper=_EBITDA_MARGIN_UPPER, inverse=False),
            "Ocupación": _color_cell(value=occupancy_rate, lower=_OCUPACION_LOWER, upper=_OCUPACION_UPPER, inverse=False),
            "LTV": _color_cell(value=ltv, lower=_LTV_LOWER, upper=_LTV_UPPER, inverse=True),
            "AFFO/CBFI *": affo_css,
            "CAGR AFFO/CBFI": _color_cell(value=cagr_affo_per_cbfi, lower=_CAGR_AFFO_PER_CBFI_LOWER, upper=_CAGR_AFFO_PER_CBFI_UPPER, inverse=False),
            "CAGR AFFO Total": _color_cell(value=cagr_affo_total, lower=_CAGR_AFFO_TOTAL_LOWER, upper=_CAGR_AFFO_TOTAL_UPPER, inverse=False),
            "P/AFFO": _color_cell(value=price_to_affo, lower=_P_AFFO_LOWER, upper=_P_AFFO_UPPER, inverse=True),
            "Dividend Yield": _color_cell(value=dividend_yield, lower=_DIV_YIELD_LOWER, upper=_DIV_YIELD_UPPER, inverse=False),
        })

    df = pd.DataFrame(data=display_rows, columns=_COLUMNS)
    styles_df = pd.DataFrame(data=style_rows, columns=_COLUMNS)

    styled = df.style.apply(func=lambda _: styles_df.values, axis=None)
    st.dataframe(data=styled, hide_index=True, width="stretch")
    st.caption(body=_CAPTION)
