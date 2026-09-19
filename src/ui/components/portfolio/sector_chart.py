import plotly.express as px
import streamlit as st

from modules.portfolio.models import SectorShare


SECTOR_CHART_MIN_WEIGHT = 0.02


def render_sector_chart(sector_shares: list[SectorShare]) -> None:
    """Render a donut chart showing the portfolio's real-estate sector allocation.

    Sectors with a weight below SECTOR_CHART_MIN_WEIGHT are grouped into a single
    "Otros" slice appended after the remaining sectors, which are sorted descending
    by weight.

    Args:
        sector_shares: Portfolio weight per real-estate sector.
    """
    main = sorted(
        [ss for ss in sector_shares if ss.weight >= SECTOR_CHART_MIN_WEIGHT],
        key=lambda ss: ss.weight,
        reverse=True,
    )
    otros_weight = sum(ss.weight for ss in sector_shares if ss.weight < SECTOR_CHART_MIN_WEIGHT)

    labels = [ss.sector.value for ss in main]
    values = [ss.weight for ss in main]

    if otros_weight > 0:
        labels.append("Otros")
        values.append(otros_weight)

    fig = px.pie(
        names=labels,
        values=values,
        title="Composición Sectorial",
        hole=0.4,
    )
    fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=220)
    st.plotly_chart(fig, width="stretch")
