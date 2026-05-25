import pandas as pd
import plotly.express as px
import streamlit as st

from modules.portfolio.models import EnrichedDistribution


def render_distributions_chart(
    distributions_by_ticker: dict[str, list[EnrichedDistribution]],
) -> None:
    """Render a stacked bar chart of net distribution income over time, grouped by FIBRA,
    alongside a detailed summary table showing all income components.

    Distributions are aggregated by period (monthly or daily) and ticker before
    plotting. A granularity toggle above the chart controls the period for both the
    chart and the table. In monthly view, every month in the range from the first to
    the last payment date is shown on the x-axis, including months with no distributions.

    Args:
        distributions_by_ticker: Mapping of BMV ticker to its enriched distribution list.
    """
    rows = [
        {
            "payment_date": d.payment_date,
            "ticker": ticker,
            "gross_fiscal_result_income": d.gross_fiscal_result_income,
            "net_reimbursement_income": d.net_reimbursement_income,
            "fiscal_result_withholding": d.fiscal_result_withholding,
            "net_income": d.net_income,
        }
        for ticker, dists in distributions_by_ticker.items()
        for d in dists
    ]

    if not rows:
        st.info("No hay distribuciones registradas.")
        return

    granularity = st.radio(
        "Granularidad",
        options=["Mensual", "Diaria"],
        index=0,
        horizontal=True,
    )

    df = pd.DataFrame(rows)
    df["payment_date"] = pd.to_datetime(df["payment_date"])

    if granularity == "Mensual":
        df["period"] = df["payment_date"].dt.to_period("M").astype(str)
    else:
        df["period"] = df["payment_date"].astype(str)

    numeric_cols = [
        "gross_fiscal_result_income",
        "net_reimbursement_income",
        "fiscal_result_withholding",
        "net_income",
    ]
    df_grouped = (
        df.groupby(["period", "ticker"])[numeric_cols]
        .sum()
        .reset_index()
        .sort_values("period")
    )

    fig = px.bar(
        df_grouped,
        x="period",
        y="net_income",
        color="ticker",
        barmode="stack",
        labels={
            "period": "Período",
            "net_income": "Ingreso Neto (MXN)",
            "ticker": "FIBRA",
        },
        title="Distribuciones Recibidas por FIBRA",
    )
    fig.update_layout(legend_title_text="FIBRA")

    if granularity == "Mensual":
        all_periods = (
            pd.period_range(
                start=df_grouped["period"].min(),
                end=df_grouped["period"].max(),
                freq="M",
            )
            .astype(str)
            .tolist()
        )
        fig.update_xaxes(type="category", categoryorder="array", categoryarray=all_periods)
    else:
        fig.update_xaxes(type="date")

    df_display = df_grouped.rename(columns={
        "period": "Período",
        "ticker": "FIBRA",
        "gross_fiscal_result_income": "Ingreso Fiscal Bruto",
        "net_reimbursement_income": "Reembolso Neto",
        "fiscal_result_withholding": "Retención ISR",
        "net_income": "Ingreso Neto",
    })
    for col in ["Ingreso Fiscal Bruto", "Reembolso Neto", "Retención ISR", "Ingreso Neto"]:
        df_display[col] = df_display[col].map(lambda v: f"${v:,.2f}")

    chart_col, table_col = st.columns(2)
    with chart_col:
        st.plotly_chart(fig, width="stretch")
    with table_col:
        st.dataframe(df_display, width="stretch", hide_index=True)
