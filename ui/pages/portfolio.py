import streamlit as st

from modules.portfolio.models import Portfolio
from modules.common.schemas import ServiceStatus
from modules.portfolio.schemas import PortfolioDataRetrieverServiceSchema
from modules.portfolio.services import PortfolioDataRetrieverService
from ui.components.common import render_error_banner
from ui.components.common import render_page_header
from ui.components.portfolio import render_distributions_chart
from ui.components.portfolio import render_positions_table
from ui.components.portfolio import render_summary_card


@st.cache_data(ttl=300, show_spinner="Cargando datos del portafolio...")
def _load_portfolio() -> PortfolioDataRetrieverServiceSchema:
    """Fetch and assemble the portfolio, cached for 5 minutes to avoid live-price re-fetches.

    Returns:
        PortfolioDataRetrieverServiceSchema with status OK and data, or ERROR and error_message.
    """
    return PortfolioDataRetrieverService().run()


render_page_header(page_title="Mi Portafolio", page_icon="📊")

result = _load_portfolio()
if result.status == ServiceStatus.ERROR:
    render_error_banner(error_message=result.error_message)
    st.stop()

portfolio: Portfolio = result.data

st.divider()
render_summary_card(
    total_purchase_cost=portfolio.total_purchase_cost,
    total_market_value=portfolio.total_market_value,
    total_return=portfolio.total_return,
    total_return_pct=portfolio.total_return_pct,
    total_net_fiscal_result_received=portfolio.total_net_fiscal_result_received,
    total_return_including_distributions=portfolio.total_return_including_distributions,
    last_updated_at=portfolio.last_updated_at,
    positions_share=portfolio.positions_share,
)

st.divider()
st.subheader("Posiciones")
render_positions_table(positions=portfolio.portfolio_positions, positions_share=portfolio.positions_share)

st.divider()
st.subheader("Historial de Distribuciones")
render_distributions_chart(distributions_by_ticker={pos.ticker: pos.distributions for pos in portfolio.portfolio_positions})
