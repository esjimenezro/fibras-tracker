"""Annual cross-FIBRA comparison chart with direct and base-1000 normalized modes."""

from typing import Any
from typing import Optional

import plotly.graph_objects as go
import streamlit as st

from modules.common.models import Fibra
from modules.common.models import InflationRecord
from modules.fundamentals.models import AnnualFundamentalsRecord
from ui.components.fundamentals.detail_chart import _add_threshold_bands
from ui.components.fundamentals.detail_chart import _apply_yaxis_format
from ui.components.fundamentals.detail_chart import _base_layout
from ui.components.fundamentals.detail_chart import KPI_CONFIG


# Flat ordered list of KPI entries for the selector.
# Direct entries reference a KPI_CONFIG key; field names and thresholds are resolved at
# render time so they stay in sync with KPI_CONFIG without duplication.
# Normalized entries carry the AnnualFundamentalsRecord field name directly.
_KPI_OPTIONS: list[dict[str, Any]] = [
    {"label": "Payout Ratio",                            "kind": "direct",     "config_key": "payout_ratio"},
    {"label": "LTV",                                     "kind": "direct",     "config_key": "ltv"},
    {"label": "Tasa de Ocupación",                       "kind": "direct",     "config_key": "ocupacion"},
    {"label": "Distribución por CBFI (normalizado)",     "kind": "normalized", "field": "distribution_per_cbfi_annual", "inflation_ref": True},
    {"label": "AFFO por CBFI (normalizado)",             "kind": "normalized", "field": "affo_per_cbfi_annual",         "inflation_ref": False},
    {"label": "Ingresos por CBFI (normalizado)",         "kind": "normalized", "field": "revenue_per_cbfi_annual",      "inflation_ref": False},
    {"label": "NAV por CBFI (normalizado)",              "kind": "normalized", "field": "nav_per_cbfi",                 "inflation_ref": False},
]


def _compute_base_year(
    selected_fibras: list[Fibra],
    annual_records: dict[str, list[AnnualFundamentalsRecord]],
) -> Optional[int]:
    """Determine the common base year for normalized comparison.

    The base year is the latest "earliest year" across all selected tickers, ensuring
    every FIBRA has data from that point. Capped so the window never exceeds 10 years.

    Args:
        selected_fibras: FIBRAs included in the current chart.
        annual_records: Annual records per ticker, each list sorted ascending by year.

    Returns:
        The common base year as an int, or None if no ticker has any records.
    """
    earliest_years: list[int] = []
    latest_years: list[int] = []
    for fibra in selected_fibras:
        records = annual_records.get(fibra.ticker, [])
        if records:
            earliest_years.append(records[0].year)
            latest_years.append(records[-1].year)
    if not earliest_years:
        return None
    common_base = max(earliest_years)
    most_recent = max(latest_years)
    if most_recent - common_base > 10:
        common_base = most_recent - 10
    return common_base


def _build_inflation_index(
    base_year: int,
    end_year: int,
    inflation_records: list[InflationRecord],
) -> dict[int, float]:
    """Compute a base-1000 inflation index from base_year forward.

    Starts at 1000 and compounds using annual Mexican inflation rates. Stops at the
    first year missing from inflation_records rather than raising an error.

    Args:
        base_year: Starting year; receives index value 1000.
        end_year: Latest year to attempt (inclusive).
        inflation_records: Full inflation history used for compounding.

    Returns:
        Dict mapping year to indexed value. May be shorter than base_year..end_year
        if inflation data is unavailable for some years.
    """
    inflation_by_year: dict[int, float] = {r.year: r.annual_inflation for r in inflation_records}
    result: dict[int, float] = {base_year: 1000.0}
    current: float = 1000.0
    for year in range(base_year + 1, end_year + 1):
        if year not in inflation_by_year:
            break
        current = current * (1.0 + inflation_by_year[year])
        result[year] = current
    return result


def _render_direct_chart(
    selected_fibras: list[Fibra],
    kpi: dict[str, Any],
    annual_records: dict[str, list[AnnualFundamentalsRecord]],
) -> None:
    """Render a direct per-FIBRA comparison chart for a single annual KPI field.

    One line per selected FIBRA. Colored threshold bands are applied when the KPI_CONFIG
    entry defines lower/upper boundaries (LTV and Ocupación). Payout Ratio renders without
    bands. Null values produce gaps rather than raising errors.

    Args:
        selected_fibras: FIBRAs to plot.
        kpi: Entry from _KPI_OPTIONS with kind == "direct".
        annual_records: Annual records per ticker, each list sorted ascending by year.
    """
    config: dict[str, Any] = KPI_CONFIG[kpi["config_key"]]
    field: str = config["field_annual"]
    fmt: str = config["format"]

    all_years: list[int] = sorted({
        record.year
        for fibra in selected_fibras
        for record in annual_records.get(fibra.ticker, [])
    })

    fig = go.Figure()
    for fibra in selected_fibras:
        records_by_year: dict[int, AnnualFundamentalsRecord] = {
            r.year: r for r in annual_records.get(fibra.ticker, [])
        }
        y_values: list[Optional[float]] = [
            getattr(records_by_year[yr], field, None) if yr in records_by_year else None
            for yr in all_years
        ]
        fig.add_trace(
            trace=go.Scatter(
                x=[str(yr) for yr in all_years],
                y=y_values,
                mode="lines+markers",
                connectgaps=False,
                name=fibra.name,
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
        **_base_layout(title=kpi["label"], show_legend=True, x_title="Año", x_type="category"),
        yaxis_title=kpi["label"],
    )
    st.plotly_chart(figure_or_data=fig, width="stretch")


def _render_normalized_chart(
    selected_fibras: list[Fibra],
    kpi: dict[str, Any],
    annual_records: dict[str, list[AnnualFundamentalsRecord]],
    inflation_records: list[InflationRecord],
) -> None:
    """Render a base-1000 normalized comparison chart for a per-CBFI annual field.

    All selected FIBRAs are indexed to 1000 at the common base year, allowing
    trend comparison regardless of absolute value differences. For the distribution
    KPI, a dashed inflation reference line is added starting at 1000. FIBRAs
    missing data at the base year are skipped with a caption notice.

    Args:
        selected_fibras: FIBRAs to plot.
        kpi: Entry from _KPI_OPTIONS with kind == "normalized".
        annual_records: Annual records per ticker, each list sorted ascending by year.
        inflation_records: Annual inflation rates used for the reference line.
    """
    base_year: Optional[int] = _compute_base_year(
        selected_fibras=selected_fibras,
        annual_records=annual_records,
    )
    if base_year is None:
        st.warning(body="No hay datos anuales para las FIBRAs seleccionadas.")
        return

    field: str = kpi["field"]
    all_years_flat: list[int] = [
        record.year
        for fibra in selected_fibras
        for record in annual_records.get(fibra.ticker, [])
    ]
    end_year: int = max(all_years_flat) if all_years_flat else base_year

    fig = go.Figure()
    skipped_names: list[str] = []

    for fibra in selected_fibras:
        records_by_year: dict[int, AnnualFundamentalsRecord] = {
            r.year: r for r in annual_records.get(fibra.ticker, [])
        }
        base_record: Optional[AnnualFundamentalsRecord] = records_by_year.get(base_year)
        if base_record is None:
            skipped_names.append(fibra.name)
            continue
        base_value: Optional[float] = getattr(base_record, field, None)
        if base_value is None:
            skipped_names.append(fibra.name)
            continue

        years: list[int] = [yr for yr in sorted(records_by_year.keys()) if yr >= base_year]
        y_indexed: list[Optional[float]] = []
        for yr in years:
            raw: Optional[float] = getattr(records_by_year.get(yr), field, None) if yr in records_by_year else None
            y_indexed.append((raw / base_value) * 1000.0 if raw is not None else None)

        fig.add_trace(
            trace=go.Scatter(
                x=[str(yr) for yr in years],
                y=y_indexed,
                mode="lines+markers",
                connectgaps=False,
                name=fibra.name,
            )
        )

    if kpi.get("inflation_ref"):
        inflation_index: dict[int, float] = _build_inflation_index(
            base_year=base_year,
            end_year=end_year,
            inflation_records=inflation_records,
        )
        ref_years: list[int] = sorted(inflation_index.keys())
        fig.add_trace(
            trace=go.Scatter(
                x=[str(yr) for yr in ref_years],
                y=[inflation_index[yr] for yr in ref_years],
                mode="lines",
                line={"dash": "dash", "color": "gray"},
                name="Referencia: inflación acumulada",
            )
        )

    if skipped_names:
        st.caption(body=f"Sin datos en el año base ({base_year}): {', '.join(skipped_names)}.")

    fig.update_layout(
        **_base_layout(title=kpi["label"], show_legend=True, x_title="Año", x_type="category"),
        yaxis_title="Índice (base 1000)",
    )
    st.plotly_chart(figure_or_data=fig, width="stretch")


def render_comparison_chart(
    annual_records: dict[str, list[AnnualFundamentalsRecord]],
    fibras: list[Fibra],
    inflation_records: list[InflationRecord],
) -> None:
    """Render an interactive annual cross-FIBRA KPI comparison chart.

    Provides a FIBRA multiselect and a flat KPI selectbox with seven entries:
    three direct comparison KPIs (Payout Ratio, LTV, Tasa de Ocupación) and four
    base-1000 normalized KPIs (Distribución, AFFO, Ingresos, NAV per CBFI).

    Direct KPIs plot raw annual field values per FIBRA, with colored threshold bands
    where defined in KPI_CONFIG. Normalized KPIs index all series to 1000 at the
    common base year (the most restrictive earliest year across selected FIBRAs,
    capped to a 10-year window). The distribution normalized chart adds a dashed
    inflation reference line.

    Args:
        annual_records: Annual records per ticker, each list sorted ascending by year.
        fibras: FIBRA catalog entries used to populate the FIBRA multiselect.
        inflation_records: Annual inflation rates used for the normalized distribution
            reference line.
    """
    selected_fibras: list[Fibra] = st.multiselect(
        label="FIBRAs",
        options=fibras,
        default=fibras,
        format_func=lambda f: f.name,
    )
    if not selected_fibras:
        st.warning(body="Selecciona al menos una FIBRA para visualizar el gráfico.")
        return

    kpi: dict[str, Any] = st.selectbox(
        label="Indicador",
        options=_KPI_OPTIONS,
        format_func=lambda entry: entry["label"],
    )

    if kpi["kind"] == "direct":
        _render_direct_chart(
            selected_fibras=selected_fibras,
            kpi=kpi,
            annual_records=annual_records,
        )
    else:
        _render_normalized_chart(
            selected_fibras=selected_fibras,
            kpi=kpi,
            annual_records=annual_records,
            inflation_records=inflation_records,
        )
