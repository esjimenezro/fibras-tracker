from typing import Optional

import streamlit as st

from modules.common.schemas import ServiceStatus
from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FundamentalsHistory
from modules.fundamentals.schemas import FundamentalsDataRetrieverServiceSchema
from modules.fundamentals.services import FundamentalsDataRetrieverService
from ui.components.common.error_banner import render_error_banner
from ui.components.common.page_header import render_page_header
from ui.components.fundamentals.detail_header import render_detail_header


@st.cache_data(ttl=300, show_spinner="Cargando datos fundamentales...")
def _load_fundamentals() -> FundamentalsDataRetrieverServiceSchema:
    """Fetch and assemble the fundamentals history, cached for 5 minutes.

    Returns:
        FundamentalsDataRetrieverServiceSchema with status OK and data, or ERROR and error_message.
    """
    return FundamentalsDataRetrieverService().run()


render_page_header(page_title="Fundamentales", page_icon="📋")

result = _load_fundamentals()
if result.status == ServiceStatus.ERROR:
    render_error_banner(error_message=result.error_message)
    st.stop()

history: FundamentalsHistory = result.data

[detalle_tab, comparativo_tab] = st.tabs(["Detalle", "Comparativo (próximamente)"])

with detalle_tab:
    fibra = st.selectbox(
        label="FIBRA",
        options=history.fibras,
        format_func=lambda f: f.name,
    )
    selected_ticker = fibra.ticker

    latest_record: Optional[EnrichedFundamentalsRecord] = history.latest_by_ticker.get(selected_ticker)
    if latest_record is None:
        st.info("No hay datos disponibles para esta FIBRA.")
        st.stop()

    prior_year_record = history.prior_year_by_ticker.get(selected_ticker)

    st.divider()
    render_detail_header(
        record=latest_record,
        fibra=fibra,
        prior_year_record=prior_year_record,
    )

with comparativo_tab:
    st.info("Esta sección estará disponible próximamente. ¡Mantente atento a las actualizaciones!")
