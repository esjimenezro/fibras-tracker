import pandas as pd
import streamlit as st

from modules.portfolio.models import EnrichedPosition
from modules.portfolio.models import PositionShare
from ui.styles.theme import color_return
from ui.styles.theme import format_mxn
from ui.styles.theme import format_pct


RETURN_COLS = ["Retorno/CBFI", "Retorno %", "Retorno Total", "Retorno + Distrib."]


def render_positions_table(
    positions: list[EnrichedPosition],
    positions_share: list[PositionShare],
) -> None:
    """Render a per-position breakdown table with color-coded return columns.

    Joins positions with their portfolio weight on ticker and renders a styled DataFrame.

    Args:
        positions: Enriched FIBRA positions with market data and distribution history.
        positions_share: Portfolio weight per position; joined on ticker.
    """
    share_map = {ps.ticker: ps.share for ps in positions_share}

    rows = [
        {
            "Ticker": pos.ticker,
            "FIBRA": pos.name,
            "Sector": (
                f"{(dom := max(pos.sector_exposure, key=lambda se: se.weight)).sector} ({dom.weight:.0%})"
                if pos.sector_exposure else "N/D"
            ),
            "CBFIs": pos.cbfis,
            "Frec. Pago": pos.payment_frequency.value,
            "Costo Promedio": pos.average_purchase_cost,
            "Precio Mercado": pos.market_price,
            "Costo Total": pos.purchase_cost,
            "Valor Mercado": pos.market_value,
            "Retorno/CBFI": pos.return_per_cbfi,
            "Retorno %": pos.return_pct,
            "Retorno Total": pos.total_return,
            "Distrib. Netas": pos.total_net_fiscal_result_received,
            "Retorno + Distrib.": pos.total_return_including_distributions,
            "Peso": share_map.get(pos.ticker, 0.0),
        }
        for pos in positions
    ]

    df = pd.DataFrame(rows)

    styled = (
        df.style
        .map(color_return, subset=RETURN_COLS)
        .format({
            "Precio Promedio": format_mxn,
            "Precio Mercado": format_mxn,
            "Costo Total": format_mxn,
            "Valor Mercado": format_mxn,
            "Retorno/CBFI": format_mxn,
            "Retorno %": format_pct,
            "Retorno Total": format_mxn,
            "Distrib. Netas": format_mxn,
            "Retorno + Distrib.": format_mxn,
            "Peso": lambda v: format_pct(value=v, include_sign=False),
        })
    )

    st.dataframe(styled, width="content", hide_index=True)
