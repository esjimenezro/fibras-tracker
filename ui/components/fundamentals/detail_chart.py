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
    "distribucion_cbfi": {
        "label": "Distribución por CBFI",
        "kind": "single",
        "format": "mxn",
        "field_quarterly": "distribution_per_cbfi",
        "field_annual": "distribution_per_cbfi_annual",
    },
    "progresion_ingresos": {
        "label": "Ingresos, NOI y EBITDA",
        "kind": "combined",
        "toggle": ["Total", "Margen", "Por CBFI"],
        "format_total": "mxn_thousands",
        "format_margin": "pct",
        "format_per_cbfi": "mxn",
        "lines_total_quarterly": [
            {"field": "total_revenues", "label": "Ingresos"},
            {"field": "noi",            "label": "NOI"},
            {"field": "ebitda",         "label": "EBITDA"},
        ],
        "lines_total_annual": [
            {"field": "total_revenues_annual", "label": "Ingresos"},
            {"field": "noi_annual",            "label": "NOI"},
            {"field": "ebitda_annual",         "label": "EBITDA"},
        ],
        "lines_margin_quarterly": [
            {"field": "noi_margin",    "label": "Margen NOI"},
            {"field": "ebitda_margin", "label": "Margen EBITDA"},
        ],
        "lines_margin_annual": [
            {"field": "noi_margin_annual",    "label": "Margen NOI"},
            {"field": "ebitda_margin_annual", "label": "Margen EBITDA"},
        ],
        "lines_per_cbfi_quarterly": [
            {"field": "revenue_per_cbfi", "label": "Ingresos/CBFI"},
            {"field": "noi_per_cbfi",     "label": "NOI/CBFI"},
            {"field": "ebitda_per_cbfi",  "label": "EBITDA/CBFI"},
        ],
        "lines_per_cbfi_annual": [
            {"field": "revenue_per_cbfi_annual", "label": "Ingresos/CBFI"},
            {"field": "noi_per_cbfi_annual",     "label": "NOI/CBFI"},
            {"field": "ebitda_per_cbfi_annual",  "label": "EBITDA/CBFI"},
        ],
    },
    "progresion_ffo_affo": {
        "label": "FFO, AFFO y Distribución",
        "kind": "combined",
        "toggle": ["Total", "Por CBFI"],
        "format_total": "mxn_thousands",
        "format_per_cbfi": "mxn",
        "lines_total_quarterly": [
            {"field": "ffo",                "label": "FFO"},
            {"field": "affo",               "label": "AFFO"},
            {"field": "total_distribution", "label": "Distribución"},
        ],
        "lines_total_annual": [
            {"field": "ffo_annual",                "label": "FFO"},
            {"field": "affo_annual",               "label": "AFFO"},
            {"field": "total_distribution_annual", "label": "Distribución"},
        ],
        "lines_per_cbfi_quarterly": [
            {"field": "ffo_per_cbfi",          "label": "FFO/CBFI"},
            {"field": "affo_per_cbfi",         "label": "AFFO/CBFI"},
            {"field": "distribution_per_cbfi", "label": "Distribución/CBFI"},
        ],
        "lines_per_cbfi_annual": [
            {"field": "ffo_per_cbfi_annual",          "label": "FFO/CBFI"},
            {"field": "affo_per_cbfi_annual",         "label": "AFFO/CBFI"},
            {"field": "distribution_per_cbfi_annual", "label": "Distribución/CBFI"},
        ],
    },
    "payout_ratio": {
        "label": "Payout Ratio (AFFO)",
        "kind": "single",
        "format": "pct",
        "field_quarterly": "affo_payout_ratio",
        "field_annual": "affo_payout_ratio_avg",
    },
    "ltv": {
        "label": "LTV",
        "kind": "single",
        "format": "pct",
        "field_quarterly": "ltv",
        "field_annual": "ltv",
        "lower": _LTV_LOWER,
        "upper": _LTV_UPPER,
        "inverse": True,
    },
    "nav_per_cbfi": {
        "label": "NAV por CBFI",
        "kind": "single",
        "format": "mxn",
        "field_quarterly": "nav_per_cbfi",
        "field_annual": "nav_per_cbfi",
    },
    "ocupacion": {
        "label": "Tasa de Ocupación",
        "kind": "single",
        "format": "pct",
        "field_quarterly": "occupancy_rate",
        "field_annual": "occupancy_rate",
        "lower": _OCC_LOWER,
        "upper": _OCC_UPPER,
        "inverse": False,
    },
    "abr_cbfis": {
        "label": "ABR y CBFIs en Circulación",
        "kind": "dual_axis",
        "left_axis_quarterly": "gross_leasable_area_m2",
        "left_axis_annual": "gross_leasable_area_m2",
        "right_axis_quarterly": "cbfis_outstanding",
        "right_axis_annual": "cbfis_outstanding",
        "format_left": "float",
        "format_right": "float",
        "annotation_field_quarterly": "cbfis_per_m2",
        "annotation_field_annual": "cbfis_per_m2",
        "left_label": "ABR (m²)",
        "right_label": "CBFIs en Circulación",
    },
}

_MODE_KEY_MAP: dict[str, str] = {
    "Total": "total",
    "Margen": "margin",
    "Por CBFI": "per_cbfi",
}

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


def _extract_values(
    records: list,
    field: str,
    fmt: str,
) -> list[Optional[float]]:
    """Extract field values from any record list with format-specific scaling.

    Works with both EnrichedFundamentalsRecord and AnnualFundamentalsRecord
    since both expose fields via attribute access.

    Args:
        records: Sorted list of records (quarterly or annual).
        field: Attribute name to extract via getattr.
        fmt: Format key; values in _FORMAT_SCALE are multiplied before return.

    Returns:
        List of scaled float values, with None where the source field is None.
    """
    scale = _FORMAT_SCALE.get(fmt, 1.0)
    result = []
    for r in records:
        v = getattr(r, field, None)
        result.append(v * scale if v is not None else None)
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


def _base_layout(
    title: str,
    show_legend: bool,
    x_title: str = "Trimestre",
    x_type: Optional[str] = None,
) -> dict[str, Any]:
    """Return common Plotly layout kwargs for title, axis grid style, and legend visibility.

    Args:
        title: Chart title string.
        show_legend: Whether the legend should be visible.
        x_title: X-axis label — 'Trimestre' for quarterly, 'Año' for annual.
        x_type: Optional Plotly axis type, e.g. 'category' for annual integer years.

    Returns:
        Dict of keyword arguments suitable for fig.update_layout(**...).
    """
    layout: dict[str, Any] = {
        "title": title,
        "xaxis_title": x_title,
        "xaxis_showgrid": False,
        "yaxis_showgrid": True,
        "yaxis_gridcolor": "rgba(200,200,200,0.3)",
        "legend": {"visible": show_legend},
    }
    if x_type is not None:
        layout["xaxis"] = {"type": x_type}
    return layout


def _render_single(
    x_values: list,
    records: list,
    config: dict[str, Any],
    field: str,
    is_annual: bool,
    inflation_ref: Optional[tuple[list[int], list[float]]],
) -> go.Figure:
    """Build a single-line Plotly figure with optional threshold bands or inflation reference.

    Args:
        x_values: Pre-computed X-axis values (period strings or year ints).
        records: Sorted records matching x_values (quarterly or annual).
        config: KPI_CONFIG entry; provides format, label, and optional threshold keys.
        field: Pre-resolved field name on the records (field_quarterly or field_annual).
        is_annual: When True, applies category x-axis and 'Año' label.
        inflation_ref: Optional (years, values) tuple for a dashed reference line.
            Only passed for 'distribucion_cbfi' in annual mode.

    Returns:
        Plotly Figure ready for st.plotly_chart.
    """
    fmt = config["format"]
    values = _extract_values(records=records, field=field, fmt=fmt)
    show_legend = inflation_ref is not None
    fig = go.Figure()
    fig.add_trace(
        trace=go.Scatter(
            x=x_values,
            y=values,
            mode="lines+markers",
            connectgaps=False,
            name=config["label"],
        )
    )
    if inflation_ref is not None:
        ref_years, ref_values = inflation_ref
        if ref_years:
            fig.add_trace(
                trace=go.Scatter(
                    x=ref_years,
                    y=ref_values,
                    mode="lines+markers",
                    connectgaps=False,
                    name="Distribución ajustada a inflación",
                    line={"dash": "dash", "color": "rgba(255, 150, 50, 0.9)"},
                )
            )
    if "lower" in config:
        _add_threshold_bands(
            fig=fig,
            lower=config["lower"],
            upper=config["upper"],
            inverse=config.get("inverse", False),
        )
    _apply_yaxis_format(fig=fig, fmt=fmt)
    fig.update_layout(
        **_base_layout(
            title=config["label"],
            show_legend=show_legend,
            x_title="Año" if is_annual else "Trimestre",
            x_type="category" if is_annual else None,
        )
    )
    return fig


def _render_combined(
    x_values: list,
    records: list,
    config: dict[str, Any],
    line_defs: list[dict[str, str]],
    fmt: str,
    is_annual: bool,
) -> go.Figure:
    """Build a multi-line Plotly figure.

    No threshold bands are drawn — multiple lines with different natural thresholds
    make bands ambiguous in a combined chart.

    Args:
        x_values: Pre-computed X-axis values (period strings or year ints).
        records: Sorted records matching x_values (quarterly or annual).
        config: KPI_CONFIG entry; provides label.
        line_defs: Pre-resolved list of {field, label} dicts for the active mode.
        fmt: Pre-resolved format key for this mode.
        is_annual: When True, applies category x-axis and 'Año' label.

    Returns:
        Plotly Figure ready for st.plotly_chart.
    """
    fig = go.Figure()
    for line in line_defs:
        fig.add_trace(
            trace=go.Scatter(
                x=x_values,
                y=_extract_values(records=records, field=line["field"], fmt=fmt),
                mode="lines+markers",
                connectgaps=False,
                name=line["label"],
            )
        )
    _apply_yaxis_format(fig=fig, fmt=fmt)
    fig.update_layout(
        **_base_layout(
            title=config["label"],
            show_legend=True,
            x_title="Año" if is_annual else "Trimestre",
            x_type="category" if is_annual else None,
        )
    )
    return fig


def _render_dual_axis(
    x_values: list,
    records: list,
    config: dict[str, Any],
    left_field: str,
    right_field: str,
    annotation_field: str,
    is_annual: bool,
) -> go.Figure:
    """Build a dual-Y-axis Plotly figure with a CBFIs/m² annotation at top-left.

    Args:
        x_values: Pre-computed X-axis values (period strings or year ints).
        records: Sorted records matching x_values (quarterly or annual).
        config: KPI_CONFIG entry; provides label, format_left, format_right,
            left_label, right_label.
        left_field: Pre-resolved field name for the left Y-axis.
        right_field: Pre-resolved field name for the right Y-axis.
        annotation_field: Pre-resolved field name for the latest-value annotation.
        is_annual: When True, applies category x-axis and 'Año' label.

    Returns:
        Plotly Figure ready for st.plotly_chart.
    """
    left_trace = go.Scatter(
        x=x_values,
        y=_extract_values(records=records, field=left_field, fmt=config["format_left"]),
        name=config["left_label"],
        yaxis="y1",
        mode="lines+markers",
        connectgaps=False,
    )
    right_trace = go.Scatter(
        x=x_values,
        y=_extract_values(records=records, field=right_field, fmt=config["format_right"]),
        name=config["right_label"],
        yaxis="y2",
        mode="lines+markers",
        connectgaps=False,
    )
    fig = go.Figure(data=[left_trace, right_trace])
    _apply_yaxis_format(fig=fig, fmt=config["format_left"], axis="yaxis")
    _apply_yaxis_format(fig=fig, fmt=config["format_right"], axis="yaxis2")
    fig.update_layout(
        yaxis2={"overlaying": "y", "side": "right"},
        **_base_layout(
            title=config["label"],
            show_legend=True,
            x_title="Año" if is_annual else "Trimestre",
            x_type="category" if is_annual else None,
        ),
    )
    latest_annotation: Optional[float] = getattr(records[-1], annotation_field, None) if records else None
    if latest_annotation is not None:
        fig.add_annotation(
            text=f"CBFIs/m²: {latest_annotation:.1f}",
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
    annual_records: list[AnnualFundamentalsRecord],
    inflation_records: list[InflationRecord],
) -> None:
    """Render an interactive historical KPI chart for a single FIBRA's fundamentals.

    A toggle switches between quarterly and annual views. The KPI selectbox is
    identical in both views — only the underlying fields and x-axis change.

    For the 'distribucion_cbfi' KPI in annual mode, a second dashed line shows
    the inflation-adjusted reference series.

    None values appear as gaps (connectgaps=False) in all chart types.

    Args:
        records: Enriched quarterly records pre-filtered to the selected ticker,
            any order; sorted internally by (year, quarter) before plotting.
        annual_records: Annual records pre-filtered to the selected ticker, any
            order; sorted internally by year ascending before plotting.
        inflation_records: Full annual Mexican inflation history; used only for
            the 'distribucion_cbfi' KPI in annual mode.
    """
    is_annual: bool = st.toggle(
        label="Vista anual",
        key="annual_view_toggle",
    )

    if is_annual and not annual_records:
        st.info(body="No hay datos anuales disponibles.")
        return
    if not is_annual and not records:
        st.info(body="No hay datos históricos disponibles.")
        return

    sorted_quarterly = sorted(records, key=_period_sort_key)
    sorted_annual = sorted(annual_records, key=lambda r: r.year)

    if is_annual:
        active_records: list = sorted_annual
        x_values: list = [r.year for r in sorted_annual]
    else:
        active_records = sorted_quarterly
        x_values = [r.period for r in sorted_quarterly]

    selected_key: str = st.selectbox(
        label="Indicador",
        options=list(KPI_CONFIG.keys()),
        format_func=lambda k: KPI_CONFIG[k]["label"],
        key="kpi_selector",
    )
    config = KPI_CONFIG[selected_key]

    suffix = "annual" if is_annual else "quarterly"

    if config["kind"] == "single":
        field = config[f"field_{suffix}"]
        inflation_ref: Optional[tuple[list[int], list[float]]] = None
        if is_annual and selected_key == "distribucion_cbfi":
            inflation_ref = _compute_inflation_reference(
                sorted_annual=sorted_annual,
                inflation_records=inflation_records,
            )
        fig = _render_single(
            x_values=x_values,
            records=active_records,
            config=config,
            field=field,
            is_annual=is_annual,
            inflation_ref=inflation_ref,
        )

    elif config["kind"] == "combined":
        mode: str = st.radio(
            label="Modo",
            options=config["toggle"],
            horizontal=True,
            key=f"chart_mode_{selected_key}",
        )
        mk = _MODE_KEY_MAP[mode]
        line_defs = config[f"lines_{mk}_{suffix}"]
        fmt = config[f"format_{mk}"]
        fig = _render_combined(
            x_values=x_values,
            records=active_records,
            config=config,
            line_defs=line_defs,
            fmt=fmt,
            is_annual=is_annual,
        )

    else:  # dual_axis
        fig = _render_dual_axis(
            x_values=x_values,
            records=active_records,
            config=config,
            left_field=config[f"left_axis_{suffix}"],
            right_field=config[f"right_axis_{suffix}"],
            annotation_field=config[f"annotation_field_{suffix}"],
            is_annual=is_annual,
        )

    st.plotly_chart(figure_or_data=fig, width="stretch")
