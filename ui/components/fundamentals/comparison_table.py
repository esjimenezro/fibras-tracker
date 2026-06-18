from typing import Optional

import streamlit as st

from modules.common.models import Fibra
from modules.fundamentals.models import AnnualFundamentalsRecord
from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FibraMetrics
from ui.components.fundamentals.detail_chart import LTV_LOWER
from ui.components.fundamentals.detail_chart import LTV_UPPER
from ui.components.fundamentals.detail_chart import OCC_LOWER
from ui.components.fundamentals.detail_chart import OCC_UPPER
from ui.styles.theme import format_pct

# Icon thresholds — single source of truth.
_THRESHOLD_FULL: float = 1.0
_THRESHOLD_WARN: float = 0.70

# Background colour values.
_GREEN_BG: str = "rgba(50,200,100,0.15)"
_YELLOW_BG: str = "rgba(255,200,50,0.15)"
_RED_BG: str = "rgba(255,99,99,0.15)"
_GRAY_BG: str = "rgba(200,200,200,0.15)"

_LOW_SAMPLE_CAPTION: str = (
    "* Esta FIBRA cuenta con menos de 3 años de historial completo. "
    "Los porcentajes de cumplimiento pueden no ser representativos."
)

_TOOLTIP_DIST_CONSTANTE: str = (
    "Porcentaje de años completos en los que la FIBRA repartió distribución. "
    "Un año sin distribución cuenta en contra."
)
_TOOLTIP_DIST_CRECIENTE: str = (
    "Porcentaje de años en los que la distribución por CBFI fue mayor a la del año anterior."
)
_TOOLTIP_DIST_VS_INFLACION: str = (
    "Compara el CAGR de la distribución por CBFI contra el CAGR de la inflación en el mismo "
    "periodo. Positivo significa que la distribución creció por encima de la inflación."
)
_TOOLTIP_NAV_CRECIENTE: str = (
    "Porcentaje de años en los que el NAV por CBFI fue mayor al del año anterior."
)
_TOOLTIP_INGRESOS_CRECIENTE: str = (
    "Porcentaje de años en los que los ingresos por CBFI fueron mayores a los del año anterior."
)
_TOOLTIP_AFFO_CRECIENTE: str = (
    "Porcentaje de años en los que el AFFO por CBFI fue mayor al del año anterior. "
    "No comparable en valor absoluto entre FIBRAs por diferencias metodológicas, "
    "pero el patrón de crecimiento sí es informativo."
)
_TOOLTIP_PAYOUT_RATIO: str = (
    "Distribución por CBFI entre AFFO por CBFI del último año completo. "
    "Por encima de 100% significa que la FIBRA distribuyó más de lo que generó ese año."
)
_TOOLTIP_OCUPACION: str = (
    "Tasa de ocupación del Área Bruta Rentable al cierre del último año completo."
)
_TOOLTIP_LTV: str = (
    "Deuda financiera entre activos totales al cierre del último año completo. "
    "Mide el apalancamiento."
)
_TOOLTIP_WALE: str = (
    "Plazo promedio ponderado de vigencia restante de los contratos de arrendamiento, en años. "
    "Dato del último trimestre reportado, no anual."
)
_TOOLTIP_TOP_CLIENTE: str = (
    "Porcentaje de ingresos (o renta, según metodología de cada FIBRA) que representa el "
    "arrendatario más grande. Dato del último trimestre reportado."
)
_TOOLTIP_TOP_10: str = (
    "Porcentaje acumulado de ingresos que representan los 10 arrendatarios más grandes. "
    "Dato del último trimestre reportado."
)

_TABLE_CSS: str = """
<style>
.fibras-cmp-table { border-collapse: collapse; width: 100%; font-size: 0.85em; }
.fibras-cmp-table th, .fibras-cmp-table td {
    border: 1px solid #ddd; padding: 6px 10px; text-align: center; white-space: nowrap;
}
.fibras-cmp-table th { background-color: #f0f2f6; font-weight: 600; }
.fibras-cmp-table td:first-child { text-align: left; font-weight: 500; }
</style>
"""


def _icon(pct: float) -> str:
    """Return a pass/warn/fail icon based on threshold comparison.

    Args:
        pct: Ratio value (0.0 – 1.0) to evaluate against thresholds.

    Returns:
        '✅' when pct equals _THRESHOLD_FULL, '⚠️' when pct >= _THRESHOLD_WARN, '❌' otherwise.
    """
    if pct == _THRESHOLD_FULL:
        return "✅"
    if pct >= _THRESHOLD_WARN:
        return "⚠️"
    return "❌"


def _format_fraction(count: Optional[int], total: Optional[int]) -> str:
    """Format count/total with a pass/warn/fail icon prefix.

    Used for 'Distribución constante' where both numerator and denominator
    come directly from annual year counts.

    Args:
        count: Numerator (e.g. years_with_distribution).
        total: Denominator (e.g. total_annual_years).

    Returns:
        Icon-prefixed fraction string (e.g. '✅ 4/4'), or 'N/D' when total is None or 0.
    """
    if count is None or total is None or total == 0:
        return "N/D"
    pct = count / total
    return f"{_icon(pct=pct)} {count}/{total}"


def _format_growth_fraction(count: Optional[int], total_annual_years: Optional[int]) -> str:
    """Format count/(total_annual_years - 1) with a pass/warn/fail icon prefix.

    Used for year-over-year growth metrics (distribution, NAV, revenue, AFFO per CBFI)
    where the denominator is the number of comparable year pairs.

    Args:
        count: Numerator (e.g. years_distribution_grew).
        total_annual_years: Total complete years; denominator is (total_annual_years - 1).

    Returns:
        Icon-prefixed fraction string (e.g. '⚠️ 2/3'), or 'N/D' when denominator <= 0.
    """
    if count is None or total_annual_years is None or total_annual_years - 1 <= 0:
        return "N/D"
    denom = total_annual_years - 1
    pct = count / denom
    return f"{_icon(pct=pct)} {count}/{denom}"


def _format_vs_inflation(value: Optional[float]) -> str:
    """Format distribution_vs_inflation as an icon + signed percentage-point difference.

    Args:
        value: Fractional difference (e.g. 0.032 means +3.2pp). Negative allowed.

    Returns:
        Icon-prefixed string (e.g. '✅ +3.2pp' or '❌ -1.5pp'), or 'N/D' when None.
    """
    if value is None:
        return "N/D"
    pp = value * 100
    icon = "✅" if value > 0 else "❌"
    sign = "+" if pp > 0 else ""
    return f"{icon} {sign}{pp:.1f}pp"


def _color_bg(value: Optional[float], lower: float, upper: float, inverse: bool) -> str:
    """Return a CSS background-color value string for threshold-based traffic-light colouring.

    Args:
        value: Metric value to evaluate. Returns '' when None.
        lower: Lower threshold boundary.
        upper: Upper threshold boundary.
        inverse: When True, lower is better (e.g. LTV): value < lower → green, > upper → red.

    Returns:
        CSS colour string (e.g. 'rgba(50,200,100,0.15)'), or '' when value is None.
    """
    if value is None:
        return ""
    if not inverse:
        if value < lower:
            return _RED_BG
        if value > upper:
            return _GREEN_BG
        return _YELLOW_BG
    else:
        if value < lower:
            return _GREEN_BG
        if value > upper:
            return _RED_BG
        return _YELLOW_BG


def _td(content: str, bg: str = "") -> str:
    """Build an HTML <td> element with optional inline background-color.

    Args:
        content: Cell text content (already formatted; not escaped — callers
            must not pass user-controlled strings here).
        bg: CSS background-color value string (e.g. 'rgba(50,200,100,0.15)').
            Empty string renders no inline style.

    Returns:
        HTML <td> string.
    """
    style = f' style="background-color: {bg};"' if bg else ""
    return f"<td{style}>{content}</td>"


def _build_table_html(
    fibras: list[Fibra],
    fibra_metrics: dict[str, FibraMetrics],
    latest_by_ticker: dict[str, Optional[EnrichedFundamentalsRecord]],
    annual_records: dict[str, list[AnnualFundamentalsRecord]],
) -> tuple[str, bool]:
    """Build the HTML string for the full comparison table.

    Args:
        fibras: FIBRA catalog entries defining row order.
        fibra_metrics: Per-FIBRA aggregate metrics keyed by ticker.
        latest_by_ticker: Most recent EnrichedFundamentalsRecord per ticker.
        annual_records: Annual records per ticker, each list sorted by year ascending.

    Returns:
        Tuple of (html_string, has_low_sample) where has_low_sample is True when at
        least one ticker has total_annual_years not None and < 3.
    """
    has_low_sample = False
    rows_html = ""

    for fibra in fibras:
        metrics: Optional[FibraMetrics] = fibra_metrics.get(fibra.ticker)
        latest: Optional[EnrichedFundamentalsRecord] = latest_by_ticker.get(fibra.ticker)
        ticker_annual: list[AnnualFundamentalsRecord] = annual_records.get(fibra.ticker, [])
        most_recent_annual: Optional[AnnualFundamentalsRecord] = ticker_annual[-1] if ticker_annual else None

        total_annual_years: Optional[int] = metrics.total_annual_years if metrics else None
        is_low_sample: bool = total_annual_years is not None and total_annual_years < 3
        if is_low_sample:
            has_low_sample = True

        row_style = f' style="background-color: {_GRAY_BG};"' if is_low_sample else ""
        ticker_display = f"{fibra.ticker}*" if is_low_sample else fibra.ticker

        # ── Propósito ──────────────────────────────────────────────────────────
        dist_constante = _format_fraction(
            count=metrics.years_with_distribution if metrics else None,
            total=total_annual_years,
        )
        dist_creciente = _format_growth_fraction(
            count=metrics.years_distribution_grew if metrics else None,
            total_annual_years=total_annual_years,
        )
        dist_vs_inflation = _format_vs_inflation(
            value=metrics.distribution_vs_inflation if metrics else None,
        )

        # ── Predictibilidad ────────────────────────────────────────────────────
        nav_creciente = _format_growth_fraction(
            count=metrics.years_nav_per_cbfi_grew if metrics else None,
            total_annual_years=total_annual_years,
        )
        ingresos_creciente = _format_growth_fraction(
            count=metrics.years_revenue_per_cbfi_grew if metrics else None,
            total_annual_years=total_annual_years,
        )
        affo_creciente = _format_growth_fraction(
            count=metrics.years_affo_per_cbfi_grew if metrics else None,
            total_annual_years=total_annual_years,
        )

        payout_val: Optional[float] = most_recent_annual.affo_payout_ratio_avg if most_recent_annual else None
        payout_str = format_pct(value=payout_val, include_sign=False) if payout_val is not None else "N/D"

        ocup_val: Optional[float] = most_recent_annual.occupancy_rate if most_recent_annual else None
        ocup_str = format_pct(value=ocup_val, include_sign=False) if ocup_val is not None else "N/D"
        ocup_bg = _color_bg(value=ocup_val, lower=OCC_LOWER, upper=OCC_UPPER, inverse=False)

        ltv_val: Optional[float] = most_recent_annual.ltv if most_recent_annual else None
        ltv_str = format_pct(value=ltv_val, include_sign=False) if ltv_val is not None else "N/D"
        ltv_bg = _color_bg(value=ltv_val, lower=LTV_LOWER, upper=LTV_UPPER, inverse=True)

        # ── Contratos ──────────────────────────────────────────────────────────
        wale_val: Optional[float] = latest.wale if latest else None
        wale_str = f"{wale_val:.1f} años" if wale_val is not None else "N/D"

        top1_val: Optional[float] = latest.top_tenant_pct if latest else None
        top1_str = format_pct(value=top1_val, include_sign=False) if top1_val is not None else "N/D"

        top10_val: Optional[float] = latest.top10_tenants_pct if latest else None
        top10_str = format_pct(value=top10_val, include_sign=False) if top10_val is not None else "N/D"

        rows_html += f"""        <tr{row_style}>
            <td>{ticker_display}</td>
            {_td(content=dist_constante)}
            {_td(content=dist_creciente)}
            {_td(content=dist_vs_inflation)}
            {_td(content=nav_creciente)}
            {_td(content=ingresos_creciente)}
            {_td(content=affo_creciente)}
            {_td(content=payout_str)}
            {_td(content=ocup_str, bg=ocup_bg)}
            {_td(content=ltv_str, bg=ltv_bg)}
            {_td(content=wale_str)}
            {_td(content=top1_str)}
            {_td(content=top10_str)}
        </tr>\n"""

    html = (
        f"{_TABLE_CSS}"
        f'<table class="fibras-cmp-table">\n'
        f"  <thead>\n"
        f"    <tr>\n"
        f'      <th rowspan="2">FIBRA</th>\n'
        f'      <th colspan="3">Propósito</th>\n'
        f'      <th colspan="6">Predictibilidad</th>\n'
        f'      <th colspan="3">Contratos</th>\n'
        f"    </tr>\n"
        f"    <tr>\n"
        f'      <th title="{_TOOLTIP_DIST_CONSTANTE}">Dist. constante</th>\n'
        f'      <th title="{_TOOLTIP_DIST_CRECIENTE}">Dist. creciente</th>\n'
        f'      <th title="{_TOOLTIP_DIST_VS_INFLACION}">Dist. vs inflación</th>\n'
        f'      <th title="{_TOOLTIP_NAV_CRECIENTE}">NAV/CBFI creciente</th>\n'
        f'      <th title="{_TOOLTIP_INGRESOS_CRECIENTE}">Ing./CBFI creciente</th>\n'
        f'      <th title="{_TOOLTIP_AFFO_CRECIENTE}">AFFO/CBFI creciente</th>\n'
        f'      <th title="{_TOOLTIP_PAYOUT_RATIO}">Payout ratio</th>\n'
        f'      <th title="{_TOOLTIP_OCUPACION}">Ocupación</th>\n'
        f'      <th title="{_TOOLTIP_LTV}">LTV</th>\n'
        f'      <th title="{_TOOLTIP_WALE}">WALE</th>\n'
        f'      <th title="{_TOOLTIP_TOP_CLIENTE}">Top Cliente</th>\n'
        f'      <th title="{_TOOLTIP_TOP_10}">Top 10</th>\n'
        f"    </tr>\n"
        f"  </thead>\n"
        f"  <tbody>\n"
        f"{rows_html}"
        f"  </tbody>\n"
        f"</table>"
    )

    return html, has_low_sample


def render_comparison_table(
    latest_by_ticker: dict[str, Optional[EnrichedFundamentalsRecord]],
    fibras: list[Fibra],
    fibra_metrics: dict[str, FibraMetrics],
    annual_records: dict[str, list[AnnualFundamentalsRecord]],
) -> None:
    """Render a cross-FIBRA evaluative comparison table with grouped supercolumn headers.

    One row per FIBRA in fibras order. Three supercolumn groups: Propósito (distribution
    consistency and growth vs inflation), Predictibilidad (NAV/revenue/AFFO growth trends,
    payout ratio, occupancy, LTV), and Contratos (WALE, tenant concentration).

    Growth-pattern columns display an icon-prefixed fraction (✅/⚠️/❌ count/denominator).
    Ocupación and LTV cells receive traffic-light background colours. Rows for FIBRAs with
    fewer than 3 complete annual years receive a light gray background and a '*' ticker suffix;
    a caption explaining this indicator appears below the table when at least one such row exists.
    All None values render as 'N/D' without raising exceptions.

    Args:
        latest_by_ticker: Most recent EnrichedFundamentalsRecord per ticker; None if no data.
            Used only for WALE, top_tenant_pct, and top10_tenants_pct.
        fibras: FIBRA catalog entries defining row order and ticker strings.
        fibra_metrics: Per-FIBRA aggregate metrics keyed by ticker.
        annual_records: Annual records per ticker keyed by ticker string, each list sorted
            by year ascending so that the last entry is the most recent complete year.
            Used for affo_payout_ratio_avg, occupancy_rate, and ltv.
    """
    html, has_low_sample = _build_table_html(
        fibras=fibras,
        fibra_metrics=fibra_metrics,
        latest_by_ticker=latest_by_ticker,
        annual_records=annual_records,
    )
    st.markdown(body=html, unsafe_allow_html=True)
    if has_low_sample:
        st.caption(body=_LOW_SAMPLE_CAPTION)
    all_years = [rec.year for records in annual_records.values() for rec in records]
    if all_years:
        min_year = min(all_years)
        max_year = max(all_years)
        st.caption(
            body=(
                f"Datos anuales calculados sobre el periodo {min_year}–{max_year}. "
                "Indicadores de contratos (WALE, concentración) corresponden al trimestre más reciente reportado."
            )
        )
