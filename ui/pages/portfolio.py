import streamlit as st

from modules.portfolio.schemas.portfolio_schemas import PortfolioDataRetrieverServiceSchema, PortfolioDataRetrieverStatus
from modules.portfolio.services.portfolio_data_retriever_service import PortfolioDataRetrieverService
from ui.components.common.error_banner import render_error_banner
from ui.components.common.page_header import render_page_header
from ui.components.portfolio.distributions_chart import render_distributions_chart
from ui.components.portfolio.positions_table import render_positions_table
from ui.components.portfolio.summary_card import render_summary_card


@st.cache_data(ttl=300)
def _load_portfolio() -> PortfolioDataRetrieverServiceSchema:
    """Fetch and assemble the portfolio, cached for 5 minutes to avoid live-price re-fetches.

    Returns:
        PortfolioDataRetrieverServiceSchema with status OK and data, or ERROR and error_message.
    """
    return PortfolioDataRetrieverService().run()


render_page_header("Mi Portafolio", "📊")

result = _load_portfolio()
if result.status == PortfolioDataRetrieverStatus.ERROR:
    render_error_banner(result.error_message)
    st.stop()

portfolio = result.data

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
render_positions_table(portfolio.portfolio_positions, portfolio.positions_share)

st.divider()
st.subheader("Historial de Distribuciones")
render_distributions_chart({pos.ticker: pos.distributions for pos in portfolio.portfolio_positions})
