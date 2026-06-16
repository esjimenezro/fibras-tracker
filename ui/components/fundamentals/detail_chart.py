from typing import Optional
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from modules.common.models import InflationRecord
from modules.fundamentals.models import AnnualFundamentalsRecord
from modules.fundamentals.models import EnrichedFundamentalsRecord


_LTV_LOWER: float = 0.35
_LTV_UPPER: float = 0.45
_OCC_LOWER: float = 0.80
_OCC_UPPER: float = 0.85

KPI_CONFIG: dict[str, dict[str, Any]] = {
    "flujo_operativo": {
        "label": "Flujo Operativo (FFO / AFFO / Distribución)",
        "group": "Operación",
        "kind": "combined",
        "toggle": ["Por CBFI", "Miles MXN"],
        "lines_per_cbfi": [
            {"field": "ffo_per_cbfi",          "label": "FFO por CBFI"},
            {"field": "affo_per_cbfi",         "label": "AFFO por CBFI"},
            {"field": "distribution_per_cbfi", "label": "Distribución por CBFI"},
        ],
        "lines_absolute": [
            {"field": "ffo",                "label": "FFO"},
            {"field": "affo",               "label": "AFFO"},
            {"field": "total_distribution", "label": "Distribución Total"},
        ],
        "format_per_cbfi": "mxn",
        "format_absolute": "mxn_thousands",
    },
    "noi_margin": {
        "label": "Margen NOI",
        "group": "Operación",
        "kind": "single",
        "field": "noi_margin",
        "format": "pct",
        "lower": 0.70,
        "upper": 0.80,
        "inverse": False,
    },
    "ebitda_margin": {
        "label": "Margen EBITDA",
        "group": "Operación",
        "kind": "single",
        "field": "ebitda_margin",
        "format": "pct",
        "lower": 0.60,
        "upper": 0.70,
        "inverse": False,
    },
    "margenes": {
        "label": "Márgenes (NOI / EBITDA / Ingresos)",
        "group": "Operación",
        "kind": "combined",
        "toggle": ["Margen %", "Miles MXN"],
        "lines_pct": [
            {"field": "noi_margin",    "label": "Margen NOI"},
            {"field": "ebitda_margin", "label": "Margen EBITDA"},
        ],
        "lines_absolute": [
            {"field": "noi",            "label": "NOI"},
            {"field": "ebitda",         "label": "EBITDA"},
            {"field": "total_revenues", "label": "Ingresos Totales"},
        ],
        "format_pct": "pct",
        "format_absolute": "mxn_thousands",
    },
    "ocupacion": {
        "label": "Tasa de Ocupación",
        "group": "Operación",
        "kind": "single",
        "field": "occupancy_rate",
        "format": "pct",
        "lower": _OCC_LOWER,
        "upper": _OCC_UPPER,
        "inverse": False,
    },
    "nav_per_cbfi": {
        "label": "NAV por CBFI",
        "group": "Por CBFI",
        "kind": "single",
        "field": "nav_per_cbfi",
        "format": "mxn",
    },
    "affo_per_m2": {
        "label": "AFFO por m²",
        "group": "Por m²",
        "kind": "single",
        "field": "affo_per_m2",
        "format": "float",
    },
    "revenue_per_m2": {
        "label": "Ingresos por m²",
        "group": "Por m²",
        "kind": "single",
        "field": "revenue_per_m2",
        "format": "float",
    },
    "ltv": {
        "label": "LTV",
        "group": "Estructura de capital",
        "kind": "single",
        "field": "ltv",
        "format": "pct",
        "lower": _LTV_LOWER,
        "upper": _LTV_UPPER,
        "inverse": True,
    },
    "affo_payout_ratio": {
        "label": "Payout Ratio (AFFO)",
        "group": "Estructura de capital",
        "kind": "single",
        "field": "affo_payout_ratio",
        "format": "pct",
    },
    "abr_cbfis": {
        "label": "ABR y CBFIs en Circulación",
        "group": "Escala del portafolio",
        "kind": "dual_axis",
        "left_axis":  [{"field": "gross_leasable_area_m2", "label": "ABR (m²)"}],
        "right_axis": [{"field": "cbfis_outstanding",      "label": "CBFIs en Circulación"}],
        "format_left": "float",
        "format_right": "float",
    },
    "cbfis_per_m2": {
        "label": "CBFIs por m²",
        "group": "Escala del portafolio",
        "kind": "single",
        "field": "cbfis_per_m2",
        "format": "float",
    },
}

ANNUAL_KPI_CONFIG: dict[str, dict[str, Any]] = {
    "distribucion_cbfi_anual": {
        "label": "Distribución por CBFI",
        "field": "distribution_per_cbfi_annual",
        "format": "mxn",
    },
    "nav_cbfi_anual": {
        "label": "NAV por CBFI",
        "field": "nav_per_cbfi",
        "format": "mxn",
    },
    "ingresos_cbfi_anual": {
        "label": "Ingresos por CBFI",
        "field": "revenue_per_cbfi_annual",
        "format": "mxn",
    },
    "affo_cbfi_anual": {
        "label": "AFFO por CBFI",
        "field": "affo_per_cbfi_annual",
        "format": "mxn",
    },
    "ltv_anual": {
        "label": "LTV",
        "field": "ltv",
        "format": "pct",
        "lower": _LTV_LOWER,
        "upper": _LTV_UPPER,
        "inverse": True,
    },
    "ocupacion_anual": {
        "label": "Tasa de Ocupación",
        "field": "occupancy_rate",
        "format": "pct",
        "lower": _OCC_LOWER,
        "upper": _OCC_UPPER,
        "inverse": False,
    },
}

_GROUP_ORDER: list[str] = [
    "Operación",
    "Por CBFI",
    "Por m²",
    "Estructura de capital",
    "Escala del portafolio",
]

_FORMAT_SCALE: dict[str, float] = {
    "mxn_thousands": 1 / 1_000,
}

_YAXIS_FORMAT: dict[str, dict[str, str]] = {
    "pct":           {"tickformat": ".1%"},
    "mxn":           {"tickprefix": "$", "ticksuffix": " MXN", "tickformat": ",.2f"},
    "float":         {"tickformat": ",.2f"},
    "mxn_thousands": {"tickprefix": "$", "ticksuffix": " K MXN", "tickformat": ",.0f"},
    "m2":            {"tickformat": ",d", "ticksuffix": " m²"},
    "cbfis":         {"tickformat": ",d"},
}


def _get_annual_values(
    sorted_annual: list[AnnualFundamentalsRecord],
    field: str,
) -> list[Optional[float]]:
    """Extract field values from annual records; None preserved as None.

    Args:
        sorted_annual: Annual records sorted ascending by year.
        field: Attribute name on AnnualFundamentalsRecord to extract.

    Returns:
        List of float values, with None where the source field is None.
    """
    result = []
    for r in sorted_annual:
        v = getattr(r, field, None)
        result.append(float(v) if v is not None else None)
    return result


def _compute_inflation_reference(
    sorted_annual: list[AnnualFundamentalsRecord],
    inflation_records: list[InflationRecord],
) -> tuple[list[int], list[float]]:
    """Compute the inflation-adjusted reference series for distribution_per_cbfi_annual.

    Starts at the first year's distribution value and compounds it forward using the
    annual Mexican inflation rate for each subsequent year. Stops at the last year
    for which inflation data is available; missing years truncate the series rather
    than raising an error.

    Args:
        sorted_annual: Annual records sorted ascending by year; must be non-empty.
        inflation_records: Full inflation history; lookup is by year.

    Returns:
        Tuple of (years, values) lists for the reference line. Both lists are empty
        when the first record's distribution_per_cbfi_annual is None.
    """
    if not sorted_annual or sorted_annual[0].distribution_per_cbfi_annual is None:
        return [], []

    inflation_by_year: dict[int, float] = {
        r.year: r.annual_inflation for r in inflation_records
    }

    ref_years: list[int] = [sorted_annual[0].year]
    ref_values: list[float] = [sorted_annual[0].distribution_per_cbfi_annual]

    for record in sorted_annual[1:]:
        year = record.year
        if year not in inflation_by_year:
            break
        ref_values.append(ref_values[-1] * (1.0 + inflation_by_year[year]))
        ref_years.append(year)

    return ref_years, ref_values


def _period_sort_key(record: EnrichedFundamentalsRecord) -> tuple[int, int]:
    """Return (year, quarter) for chronological sorting from a period string like '1T2026'."""
    quarter, year = record.period.split("T")
    return (int(year), int(quarter))


def _get_values(
    records: list[EnrichedFundamentalsRecord],
    field: str,
    fmt: str,
) -> list[Optional[float]]:
    """Extract field values from records applying format-specific scaling; None preserved as None.

    Args:
        records: Sorted enriched fundamentals records to read from.
        field: Attribute name on EnrichedFundamentalsRecord to extract.
        fmt: Format key from _FORMAT_SCALE; determines scaling factor (default 1.0).

    Returns:
        List of scaled float values, with None where the source field is None.
    """
    scale = _FORMAT_SCALE.get(fmt, 1.0)
    result = []
    for r in records:
        v = getattr(r, field, None)
        result.append(v * scale if v is not None else None)
    return result


def _add_threshold_bands(
    fig: go.Figure,
    lower: float,
    upper: float,
    inverse: bool,
) -> None:
    """Add coloured background bands and dashed reference lines at threshold boundaries.

    Args:
        fig: Plotly figure to mutate.
        lower: Lower threshold boundary (boundary between red/yellow zones for normal metrics).
        upper: Upper threshold boundary (boundary between yellow/green zones for normal metrics).
        inverse: When True, green is below lower and red is above upper (e.g. LTV).
    """
    red_fill = "rgba(255, 99, 99, 0.06)"
    yellow_fill = "rgba(255, 200, 50, 0.06)"
    green_fill = "rgba(50, 200, 100, 0.06)"

    if not inverse:
        bands = [(0, lower, red_fill), (lower, upper, yellow_fill), (upper, 1.0, green_fill)]
    else:
        bands = [(0, lower, green_fill), (lower, upper, yellow_fill), (upper, 1.0, red_fill)]

    for y0, y1, color in bands:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=color, line_width=0)

    for threshold in [lower, upper]:
        fig.add_hline(
            y=threshold,
            line_color="rgba(150, 150, 150, 0.6)",
            line_dash="dash",
        )


def _apply_yaxis_format(fig: go.Figure, fmt: str, axis: str = "yaxis") -> None:
    """Apply Plotly Y-axis tick formatting from _YAXIS_FORMAT to the specified axis.

    Args:
        fig: Plotly figure to mutate.
        fmt: Format key matching a _YAXIS_FORMAT entry.
        axis: Plotly layout axis key, e.g. 'yaxis' or 'yaxis2'.
    """
    fig.update_layout({axis: _YAXIS_FORMAT.get(fmt, {})})


def _base_layout(title: str, show_legend: bool) -> dict[str, Any]:
    """Return common Plotly layout kwargs for title, axis grid style, and legend visibility.

    Args:
        title: Chart title string.
        show_legend: Whether the legend should be visible.

    Returns:
        Dict of keyword arguments suitable for fig.update_layout(**...).
    """
    return {
        "title": title,
        "xaxis_title": "Trimestre",
        "xaxis_showgrid": False,
        "yaxis_showgrid": True,
        "yaxis_gridcolor": "rgba(200,200,200,0.3)",
        "legend": {"visible": show_legend},
    }


def _render_single(
    sorted_records: list[EnrichedFundamentalsRecord],
    config: dict[str, Any],
) -> go.Figure:
    """Build a single-line Plotly figure with optional traffic-light threshold bands.

    Args:
        sorted_records: Records sorted chronologically for the selected ticker.
        config: KPI_CONFIG entry with kind='single'.

    Returns:
        Plotly Figure ready for st.plotly_chart.
    """
    periods = [r.period for r in sorted_records]
    values = _get_values(records=sorted_records, field=config["field"], fmt=config["format"])
    fig = go.Figure(
        data=go.Scatter(
            x=periods,
            y=values,
            mode="lines+markers",
            connectgaps=False,
            name=config["label"],
        )
    )
    if "lower" in config:
        _add_threshold_bands(
            fig=fig,
            lower=config["lower"],
            upper=config["upper"],
            inverse=config.get("inverse", False),
        )
    _apply_yaxis_format(fig=fig, fmt=config["format"])
    fig.update_layout(**_base_layout(title=config["label"], show_legend=False))
    return fig


def _render_combined(
    sorted_records: list[EnrichedFundamentalsRecord],
    config: dict[str, Any],
    chart_key: str,
) -> go.Figure:
    """Build a multi-line Plotly figure with a view-mode radio toggle rendered above the chart.

    Args:
        sorted_records: Records sorted chronologically for the selected ticker.
        config: KPI_CONFIG entry with kind='combined'.
        chart_key: Unique key suffix for the Streamlit radio widget.

    Returns:
        Plotly Figure ready for st.plotly_chart.
    """
    mode = st.radio(
        label="Modo",
        options=config["toggle"],
        horizontal=True,
        key=f"chart_mode_{chart_key}",
    )
    periods = [r.period for r in sorted_records]
    primary_mode = mode == config["toggle"][0]
    if primary_mode:
        if "lines_per_cbfi" in config:
            line_defs = config["lines_per_cbfi"]
            fmt = config["format_per_cbfi"]
        else:
            line_defs = config["lines_pct"]
            fmt = config["format_pct"]
    else:
        line_defs = config["lines_absolute"]
        fmt = config["format_absolute"]
    fig = go.Figure()
    for line in line_defs:
        fig.add_trace(
            trace=go.Scatter(
                x=periods,
                y=_get_values(records=sorted_records, field=line["field"], fmt=fmt),
                mode="lines+markers",
                connectgaps=False,
                name=line["label"],
            )
        )
    if primary_mode:
        first_with_thresholds = next(
            (line for line in line_defs if "lower" in line),
            None,
        )
        if first_with_thresholds is not None:
            _add_threshold_bands(
                fig=fig,
                lower=first_with_thresholds["lower"],
                upper=first_with_thresholds["upper"],
                inverse=False,
            )
    _apply_yaxis_format(fig=fig, fmt=fmt)
    fig.update_layout(**_base_layout(title=config["label"], show_legend=True))
    return fig


def _render_dual_axis(
    sorted_records: list[EnrichedFundamentalsRecord],
    config: dict[str, Any],
) -> go.Figure:
    """Build a dual-Y-axis Plotly figure with a CBFIs/m² text annotation at top-left.

    Args:
        sorted_records: Records sorted chronologically for the selected ticker.
        config: KPI_CONFIG entry with kind='dual_axis'.

    Returns:
        Plotly Figure ready for st.plotly_chart.
    """
    periods = [r.period for r in sorted_records]
    left_def = config["left_axis"][0]
    right_def = config["right_axis"][0]
    left_trace = go.Scatter(
        x=periods,
        y=_get_values(records=sorted_records, field=left_def["field"], fmt=config["format_left"]),
        name=left_def["label"],
        yaxis="y1",
        mode="lines+markers",
        connectgaps=False,
    )
    right_trace = go.Scatter(
        x=periods,
        y=_get_values(records=sorted_records, field=right_def["field"], fmt=config["format_right"]),
        name=right_def["label"],
        yaxis="y2",
        mode="lines+markers",
        connectgaps=False,
    )
    fig = go.Figure(data=[left_trace, right_trace])
    _apply_yaxis_format(fig=fig, fmt=config["format_left"], axis="yaxis")
    _apply_yaxis_format(fig=fig, fmt=config["format_right"], axis="yaxis2")
    fig.update_layout(
        yaxis2={"overlaying": "y", "side": "right"},
        **_base_layout(title=config["label"], show_legend=True),
    )
    latest_cbfis_per_m2: Optional[float] = sorted_records[-1].cbfis_per_m2 if sorted_records else None
    if latest_cbfis_per_m2 is not None:
        fig.add_annotation(
            text=f"CBFIs/m²: {latest_cbfis_per_m2:.1f}",
            xref="paper",
            yref="paper",
            x=0.01,
            y=0.99,
            showarrow=False,
            align="left",
        )
    return fig


def render_detail_chart(
    records: list[EnrichedFundamentalsRecord],
) -> None:
    """Render an interactive historical KPI chart for a single FIBRA's fundamentals.

    Presents a KPI selectbox with entries sorted by domain group. The selected KPI
    determines the chart type: single-line with optional traffic-light bands, multi-line
    with a view-mode radio toggle, or dual-Y-axis with a CBFIs/m² annotation. Records
    are sorted chronologically by (year, quarter) before plotting; None values appear
    as gaps rather than zeros.

    Args:
        records: Enriched fundamentals records pre-filtered to selected_ticker, in any
            order; sorted internally before plotting.
    """
    if not records:
        st.info(body="No hay datos históricos disponibles.")
        return

    sorted_records = sorted(records, key=_period_sort_key)

    options = sorted(
        KPI_CONFIG.keys(),
        key=lambda k: (_GROUP_ORDER.index(KPI_CONFIG[k]["group"]), KPI_CONFIG[k]["label"]),
    )
    selected_key: str = st.selectbox(
        label="Indicador",
        options=options,
        format_func=lambda k: KPI_CONFIG[k]["label"],
    )
    config = KPI_CONFIG[selected_key]

    if config["kind"] == "single":
        fig = _render_single(sorted_records=sorted_records, config=config)
    elif config["kind"] == "combined":
        fig = _render_combined(sorted_records=sorted_records, config=config, chart_key=selected_key)
    else:
        fig = _render_dual_axis(sorted_records=sorted_records, config=config)

    st.plotly_chart(figure_or_data=fig, width="stretch")
