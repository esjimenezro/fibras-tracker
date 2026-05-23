import streamlit as st

from ui.components.common.page_header import render_page_header


render_page_header(page_title="Inicio", page_icon="🏠")


st.divider()


col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("ui/pages/portfolio.py", label="Mi Portafolio", icon="📊")
    st.markdown("Valor de mercado, retornos y distribuciones de tu cartera de FIBRAs.")
with col2:
    st.page_link("ui/pages/fundamentals.py", label="Fundamentales", icon="📋")
    st.markdown("Métricas fundamentales por FIBRA: FFO, distribución por CBFI y más.")
with col3:
    st.page_link("ui/pages/radar.py", label="Radar", icon="🔍")
    st.markdown("Detecta oportunidades comparando FIBRAs por sector, rendimiento y precio.")
