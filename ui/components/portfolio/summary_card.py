from datetime import datetime

import plotly.express as px
import streamlit as st

from modules.portfolio.models import PositionShare
from ui.styles.theme import format_mxn
from ui.styles.theme import format_pct


def render_summary_card(
    total_purchase_cost: float,
    total_market_value: float,
    total_return: float,
    total_return_pct: float,
    total_net_fiscal_result_received: float,
    total_return_including_distributions: float,
    last_updated_at: datetime,
    positions_share: list[PositionShare],
) -> None:
    """Render portfolio-level summary metrics and an allocation pie chart.

    Args:
        total_purchase_cost: Total invested amount in MXN.
        total_market_value: Current total market value in MXN.
        total_return: Unrealised gain or loss in MXN.
        total_return_pct: Unrealised return as a fraction of purchase cost.
        total_net_fiscal_result_received: Net fiscal distributions received in MXN.
        total_return_including_distributions: Total return including distributions in MXN.
        last_updated_at: UTC timestamp of the most recently fetched market price.
        positions_share: Portfolio weight per position; used for the allocation pie.
    """
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Valor de Mercado",
            value=format_mxn(value=total_market_value),
            delta=format_mxn(value=total_return),
        )
    with col2:
        st.metric(
            label="Costo de Compra",
            value=format_mxn(value=total_purchase_cost),
        )
    with col3:
        st.metric(
            label="Retorno Total %",
            value=format_pct(value=total_return_pct),
            delta=format_mxn(value=total_return),
        )
    with col4:
        st.metric(
            label="Distribuciones Netas",
            value=format_mxn(value=total_net_fiscal_result_received),
        )

    left, right = st.columns([0.6, 0.4])
    with left:
        st.metric(
            label="Retorno Incl. Distribuciones",
            value=format_mxn(value=total_return_including_distributions),
        )
    with right:
        fig = px.pie(
            names=[ps.ticker for ps in positions_share],
            values=[ps.share for ps in positions_share],
            title="Composición del Portafolio",
            hole=0.4,
        )
        fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=220)
        st.plotly_chart(fig, width="stretch")

    st.caption(f"Actualizado: {last_updated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
