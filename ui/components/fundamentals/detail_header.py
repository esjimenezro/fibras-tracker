from typing import Optional

import streamlit as st

from modules.common.models import Fibra
from modules.fundamentals.models import EnrichedFundamentalsRecord
from ui.styles.theme import format_mxn
from ui.styles.theme import format_pct


def _pct(value: Optional[float]) -> str:
    """Format a fractional value as a percentage, or return 'N/D' if None.

    Args:
        value: Fractional value (e.g. 0.75 for 75%), or None.

    Returns:
        Formatted percentage string without sign, or 'N/D'.
    """
    return format_pct(value=value, include_sign=False) if value is not None else "N/D"


def _mxn(value: Optional[float]) -> str:
    """Format a float as MXN currency, or return 'N/D' if None.

    Args:
        value: Numeric value in MXN, or None.

    Returns:
        Formatted MXN string, or 'N/D'.
    """
    return format_mxn(value=value) if value is not None else "N/D"


def _float2(value: Optional[float]) -> str:
    """Format a float to two decimal places, or return 'N/D' if None.

    Args:
        value: Numeric value, or None.

    Returns:
        Two-decimal string, or 'N/D'.
    """
    return f"{value:.2f}" if value is not None else "N/D"


def _yoy_delta(current: Optional[float], prior: Optional[float]) -> Optional[str]:
    """Compute a year-over-year growth percentage string for st.metric delta.

    Returns None when either operand is absent or the prior value is zero,
    suppressing the delta indicator entirely.

    Args:
        current: Current period value.
        prior: Same-quarter prior-year value.

    Returns:
        Formatted percentage string with sign (e.g. '+12.34%'), or None.
    """
    if current is None or prior is None or prior == 0:
        return None
    growth = (current - prior) / prior
    return format_pct(value=growth, include_sign=True)


def render_detail_header(
    record: EnrichedFundamentalsRecord,
    fibra: Fibra,
    prior_year_record: Optional[EnrichedFundamentalsRecord],
) -> None:
    """Render a three-section KPI header for a single FIBRA and quarter.

    Displays operational metrics, per-CBFI generation/distribution metrics,
    and market valuation metrics as st.metric cards grouped by section.
    Year-over-year deltas are shown for FFO and AFFO per CBFI when prior-year
    data is available. The NAV delta indicates premium or discount vs. market price.
    All null values display 'N/D' without raising exceptions.

    Args:
        record: Enriched fundamentals record for the selected FIBRA and quarter.
        fibra: Catalog entry for the FIBRA, used for name and ticker display.
        prior_year_record: Enriched record for the same quarter one year prior,
            used to compute year-over-year deltas. Pass None to suppress deltas.
    """
    st.markdown(f"### {fibra.name} ({fibra.ticker})")

    st.markdown("**Operación y deuda**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Margen NOI",
            value=_pct(value=record.noi_margin),
            help=(
                "Ingreso Operativo Neto / Ingresos Totales. Mide qué proporción de los ingresos "
                "se convierte en flujo operativo después de gastos directos. Márgenes superiores "
                "al 70% son sólidos en FIBRAs mexicanas."
            ),
        )
    with col2:
        st.metric(
            label="Margen EBITDA",
            value=_pct(value=record.ebitda_margin),
            help=(
                "EBITDA / Ingresos Totales. Aproxima la eficiencia operativa antes de "
                "financiamiento e impuestos."
            ),
        )
    with col3:
        st.metric(
            label="Ocupación",
            value=_pct(value=record.occupancy_rate),
            help=(
                "Porcentaje del Área Bruta Rentable efectivamente arrendada. "
                "Por encima del 90% se considera saludable."
            ),
        )
    with col4:
        st.metric(
            label="LTV",
            value=_pct(value=record.ltv),
            help=(
                "Deuda financiera / Activos totales. Mide el apalancamiento. "
                "Por debajo del 40% se considera conservador en FIBRAs mexicanas."
            ),
        )

    prior = prior_year_record
    yoy_ffo = _yoy_delta(current=record.ffo_per_cbfi, prior=prior.ffo_per_cbfi if prior else None)
    yoy_affo = _yoy_delta(current=record.affo_per_cbfi, prior=prior.affo_per_cbfi if prior else None)

    st.markdown("**Generación y distribución por CBFI**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="FFO por CBFI",
            value=_mxn(value=record.ffo_per_cbfi),
            delta=yoy_ffo,
            help=(
                "Funds From Operations / CBFIs en circulación. Mide la generación de flujo "
                "operativo por certificado. El crecimiento sostenido en el tiempo es la señal "
                "más importante de salud de una FIBRA."
            ),
        )
    with col2:
        st.metric(
            label="AFFO por CBFI",
            value=_mxn(value=record.affo_per_cbfi),
            delta=yoy_affo,
            help=(
                "AFFO / CBFIs en circulación. Métrica ajustada de generación de flujo por certificado. "
                "La metodología de cálculo puede variar entre FIBRAs según su glosario de reportes."
            ),
        )
    with col3:
        st.metric(
            label="Payout ratio",
            value=_pct(value=record.affo_payout_ratio),
            help=(
                "Distribución por CBFI × CBFIs en circulación / AFFO. Indica qué porcentaje "
                "del AFFO se distribuye a los tenedores. Por encima del 100% la FIBRA distribuye "
                "más de lo que genera."
            ),
        )
    with col4:
        st.metric(
            label="Distribución por CBFI",
            value=_mxn(value=record.distribution_per_cbfi),
            help=(
                "Monto en pesos distribuido por certificado en el trimestre. Multiplicado por 4 "
                "aproxima la distribución anualizada."
            ),
        )

    nav_delta = None
    nav_delta_color = "normal"
    if (
        record.market_price is not None
        and record.nav_per_cbfi is not None
        and record.nav_per_cbfi != 0
    ):
        diff_pct = abs((record.market_price - record.nav_per_cbfi) / record.nav_per_cbfi)
        if record.market_price > record.nav_per_cbfi:
            nav_delta = f"Prima de {format_pct(value=diff_pct, include_sign=False)}"
            nav_delta_color = "inverse"
        else:
            nav_delta = f"Descuento de {format_pct(value=diff_pct, include_sign=False)}"
            nav_delta_color = "normal"

    st.markdown("**Valoración de mercado**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Precio de mercado",
            value=_mxn(value=record.market_price),
            help=(
                "Precio de cierre actual del CBFI en la BMV, obtenido en tiempo real "
                "vía Yahoo Finance."
            ),
        )
    with col2:
        st.metric(
            label="NAV por CBFI",
            value=_mxn(value=record.nav_per_cbfi),
            delta=nav_delta,
            delta_color=nav_delta_color,
            help=(
                "Patrimonio total / CBFIs en circulación. Valor contable por certificado. "
                "Cotizar por debajo del NAV indica un posible descuento sobre el valor de "
                "los activos."
            ),
        )
    with col3:
        st.metric(
            label="P/AFFO",
            value=_float2(value=record.price_to_affo),
            help=(
                "Precio de mercado / AFFO por CBFI. Indica cuántos pesos paga el mercado "
                "por cada peso de AFFO. Valores menores implican mayor potencial de retorno."
            ),
        )
    with col4:
        st.metric(
            label="Dividend yield",
            value=_pct(value=record.dividend_yield),
            help=(
                "Distribución por CBFI anualizada (×4) / precio de mercado. Rendimiento "
                "por distribuciones sobre el precio actual."
            ),
        )
