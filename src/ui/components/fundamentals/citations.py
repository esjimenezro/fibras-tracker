import streamlit as st


def render_citations(citations: list[str]) -> None:
    """Render a plain-text sources line for the wiki pages an answer cited.

    Args:
        citations: Wikilink targets in first-appearance order (e.g. ["2024-Q1"]).
            When empty, nothing is rendered.
    """
    if not citations:
        return
    st.markdown("**Fuentes:** " + ", ".join(f"[[{citation}]]" for citation in citations))
