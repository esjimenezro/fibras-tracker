import streamlit as st

from config import PAGE_ICON
from config import PAGE_LEGEND
from config import PAGE_TITLE
from ui.styles.theme import load_custom_css


def render_page_header(page_title: str, page_icon: str) -> None:
    """Render the shared app header with logo, brand, and the current page title.

    Args:
        page_title: Name of the current page (e.g. 'Mi Portafolio').
        page_icon: Emoji icon for the current page (e.g. '📊').
    """
    load_custom_css()

    logo_col, brand_col, _ = st.columns(3)
    with logo_col:
        st.image(PAGE_ICON, width="content")
    with brand_col:
        st.markdown(
            f"<h1 style='margin-top: 20px; margin-bottom: 4px;'>{PAGE_TITLE}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='color: #6c757d; font-size: 1rem; margin-top: 0;'>{PAGE_LEGEND}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h2 style='margin-top: 24px; text-align: left; color: #262730;'>"
            f"{page_icon}&nbsp;{page_title}</h2>",
            unsafe_allow_html=True,
        )
