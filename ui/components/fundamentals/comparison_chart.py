from typing import Optional

import plotly.graph_objects as go
import streamlit as st

from modules.common.models import Fibra
from modules.fundamentals.models import EnrichedFundamentalsRecord
from ui.components.fundamentals.detail_chart import _add_threshold_bands
from ui.components.fundamentals.detail_chart import _apply_yaxis_format
from ui.components.fundamentals.detail_chart import _FORMAT_SCALE
from ui.components.fundamentals.detail_chart import _base_layout
from ui.components.fundamentals.detail_chart import KPI_CONFIG


def _sort_key_period(period: str) -> tuple[int, int]:
    """Return (year, quarter) sort key from a period string like '1T2026'.

    Args:
        period: Period label (e.g. "3T2024").

    Returns:
        tuple[int, int]: (year, quarter) suitable for chronological sorting.
    """
    quarter_str, year_str = period.split("T")
    return (int(year_str), int(quarter_str))


def render_comparison_chart(
    records: list[EnrichedFundamentalsRecord],
    fibras: list[Fibra],
) -> None:
    """Render an interactive multi-FIBRA KPI trend chart with FIBRA and KPI selectors.

    Presents a multiselect to choose FIBRAs and a selectbox to choose any single-kind KPI
    from KPI_CONFIG. The chart shows one line per selected FIBRA, sorted chronologically.
    Null values appear as gaps (connectgaps=False). When the selected KPI has threshold
    bands defined in KPI_CONFIG, coloured background bands and dashed reference lines are
    rendered identically to the detail chart.

    Args:
        records: All enriched fundamentals records across all tickers, in any order.
        fibras: FIBRA catalog entries used to populate the FIBRA selector.
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

    single_keys = [k for k, v in KPI_CONFIG.items() if v["kind"] == "single"]
    selected_kpi: str = st.selectbox(
        label="Indicador",
        options=single_keys,
        format_func=lambda k: KPI_CONFIG[k]["label"],
    )
    config = KPI_CONFIG[selected_kpi]
    field: str = config["field_quarterly"]
    fmt: str = config["format"]

    selected_tickers = {f.ticker for f in selected_fibras}

    all_periods: list[str] = sorted(
        {r.period for r in records if r.ticker in selected_tickers},
        key=_sort_key_period,
    )

    fig = go.Figure()
    for fibra in selected_fibras:
        records_by_period: dict[str, EnrichedFundamentalsRecord] = {
            r.period: r for r in records if r.ticker == fibra.ticker
        }
        scale: float = _FORMAT_SCALE.get(fmt, 1.0)
        y_values: list[Optional[float]] = []
        for period in all_periods:
            record = records_by_period.get(period)
            raw: Optional[float] = getattr(record, field, None) if record is not None else None
            y_values.append(raw * scale if raw is not None else None)
        fig.add_trace(
            trace=go.Scatter(
                x=all_periods,
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
        **_base_layout(title=config["label"], show_legend=True),
        yaxis_title=config["label"],
    )

    st.plotly_chart(figure_or_data=fig, width="stretch")
