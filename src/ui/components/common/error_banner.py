import streamlit as st


def render_error_banner(error_message: str) -> None:
    """Render a full-width error box with a fixed header and the raw exception message.

    Args:
        error_message: The exception message returned by the service.
    """
    st.error("No fue posible cargar la cartera.")
    st.caption(error_message)
