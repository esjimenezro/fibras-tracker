import os
from typing import Optional

import streamlit as st

import config  # noqa: F401 - ensures load_dotenv() has run before reading ANTHROPIC_API_KEY
from modules.common.schemas import ServiceStatus
from modules.fundamentals.models import AnnualFundamentalsRecord
from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FundamentalsHistory
from modules.fundamentals.schemas import FundamentalsDataRetrieverServiceSchema
from modules.fundamentals.services import FundamentalsDataRetrieverService
from modules.wiki.models import WikiChatMessage
from modules.wiki.models import WikiErrorCategory
from modules.wiki.models import WikiQueryRequest
from modules.wiki.models import WikiStreamEventType
from modules.wiki.schemas import WikiCatalogServiceSchema
from modules.wiki.services import WikiCatalogService
from modules.wiki.services import WikiQueryService
from ui.components.common import render_error_banner
from ui.components.common import render_page_header
from ui.components.fundamentals import render_citations
from ui.components.fundamentals import render_comparison_chart
from ui.components.fundamentals import render_comparison_table
from ui.components.fundamentals import render_detail_chart
from ui.components.fundamentals import render_detail_header


_WIKI_ERROR_MESSAGES = {
    WikiErrorCategory.AUTH: "Falta o es inválida la `ANTHROPIC_API_KEY`. Revisá tu archivo `.env`.",
    WikiErrorCategory.RATE_LIMIT: "Se alcanzó el límite de la API de Anthropic. Probá de nuevo en un momento.",
    WikiErrorCategory.CONNECTION: "No se pudo contactar la API de Anthropic. Revisá tu conexión.",
    WikiErrorCategory.INCOMPLETE: "No se pudo completar la respuesta. Probá reformular la pregunta.",
    WikiErrorCategory.INTERNAL: "Algo salió mal procesando la consulta.",
}


@st.cache_data(ttl=300, show_spinner="Cargando datos fundamentales...")
def _load_fundamentals() -> FundamentalsDataRetrieverServiceSchema:
    """Fetch and assemble the fundamentals history, cached for 5 minutes.

    Returns:
        FundamentalsDataRetrieverServiceSchema with status OK and data, or ERROR and error_message.
    """
    return FundamentalsDataRetrieverService().run()


@st.cache_data(ttl=300)
def _load_wiki_catalog() -> WikiCatalogServiceSchema:
    """Fetch which FIBRAs have a wiki, cached for 5 minutes.

    Returns:
        WikiCatalogServiceSchema with status OK and the BMV tickers, or ERROR and
            error_message.
    """
    return WikiCatalogService().run()


def _render_wiki_chat(ticker: str) -> None:
    """Render the per-ticker "Pregúntale a la wiki" chat below the detail chart.

    Conversation history is kept per ticker in ``st.session_state["wiki_chat"]`` so
    switching FIBRA preserves each thread. The WikiQueryService stream is consumed
    here (never cached): TEXT events grow a placeholder, STATUS events show a
    progress caption, and the terminal FINAL/ERROR event renders the answer with
    its sources line or an inline banner keyed by ``error_category``.

    Args:
        ticker: BMV ticker of the selected FIBRA (e.g. "DANHOS13").
    """
    threads: dict[str, list[WikiChatMessage]] = st.session_state.setdefault("wiki_chat", {})
    history = threads.setdefault(ticker, [])

    for message in history:
        with st.chat_message(message.role):
            st.markdown(message.content)

    question = st.chat_input(f"Pregunta sobre {ticker}…")
    if not question:
        return

    with st.chat_message("user"):
        st.markdown(question)

    request = WikiQueryRequest(ticker=ticker, question=question, history=list(history))
    with st.chat_message("assistant"):
        status_slot = st.empty()
        text_slot = st.empty()
        answer = ""
        terminal = None
        for event in WikiQueryService().stream(request=request):
            if event.type == WikiStreamEventType.TEXT:
                answer += event.text or ""
                text_slot.markdown(answer + " ▌")
            elif event.type == WikiStreamEventType.STATUS:
                status_slot.caption(f"🔎 {event.text}")
            elif event.type in (WikiStreamEventType.FINAL, WikiStreamEventType.ERROR):
                terminal = event

        status_slot.empty()
        if terminal is not None and terminal.type == WikiStreamEventType.FINAL:
            text_slot.markdown(terminal.data.answer_text)
            render_citations(citations=terminal.data.citations)
            history.append(WikiChatMessage(role="user", content=question))
            history.append(WikiChatMessage(role="assistant", content=terminal.data.answer_text))
        else:
            text_slot.empty()
            category = terminal.error_category if terminal is not None else WikiErrorCategory.INTERNAL
            st.error(_WIKI_ERROR_MESSAGES.get(category, _WIKI_ERROR_MESSAGES[WikiErrorCategory.INTERNAL]))


render_page_header(page_title="Fundamentales", page_icon="📋")

result = _load_fundamentals()
if result.status == ServiceStatus.ERROR:
    render_error_banner(error_message=result.error_message)
    st.stop()

history: FundamentalsHistory = result.data

annual_records_by_ticker: dict[str, list[AnnualFundamentalsRecord]] = {}
for _rec in history.annual_records:
    annual_records_by_ticker.setdefault(_rec.ticker, []).append(_rec)
for _ticker in annual_records_by_ticker:
    annual_records_by_ticker[_ticker].sort(key=lambda r: r.year)

[detalle_tab, comparativa_tab] = st.tabs(["Detalle", "Comparativa"])

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

    st.divider()
    ticker_records = [r for r in history.records if r.ticker == selected_ticker]
    annual_ticker_records = [r for r in history.annual_records if r.ticker == selected_ticker]
    render_detail_chart(
        records=ticker_records,
        annual_records=annual_ticker_records,
        inflation_records=history.inflation_records,
    )

    st.divider()
    st.subheader("💬 Pregúntale a la wiki")
    wiki_catalog = _load_wiki_catalog()
    if wiki_catalog.status == ServiceStatus.ERROR:
        st.error("No se pudo leer el catálogo de wikis.")
        st.caption(wiki_catalog.error_message)
    elif selected_ticker not in wiki_catalog.data:
        st.info("Esta FIBRA aún no tiene wiki.")
    elif not os.environ.get("ANTHROPIC_API_KEY"):
        st.info(
            "El chat de wiki necesita configurar `ANTHROPIC_API_KEY` en el archivo `.env` "
            "(copiá `.env.example` a `.env` y completá la clave)."
        )
    else:
        _render_wiki_chat(ticker=selected_ticker)

with comparativa_tab:
    render_comparison_table(
        latest_by_ticker=history.latest_by_ticker,
        fibras=history.fibras,
        fibra_metrics=history.fibra_metrics,
        annual_records=annual_records_by_ticker,
    )
    st.divider()
    render_comparison_chart(
        annual_records=annual_records_by_ticker,
        fibras=history.fibras,
        inflation_records=history.inflation_records,
    )
