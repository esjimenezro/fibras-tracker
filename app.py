import streamlit as st

from config import PAGE_ICON, PAGE_TITLE

pg = st.navigation([
    st.Page("ui/pages/home.py",         title="Inicio",        icon="🏠"),
    st.Page("ui/pages/portfolio.py",    title="Mi Portafolio", icon="📊"),
    st.Page("ui/pages/fundamentals.py", title="Fundamentales", icon="📋"),
    st.Page("ui/pages/radar.py",        title="Radar",         icon="🔍"),
])
st.set_page_config(
    page_title=f"{PAGE_TITLE} · {pg.title}",
    page_icon=PAGE_ICON,
    layout="wide",
)
st.logo("ui/assets/fibralens_logo_light_v2.svg")
pg.run()
