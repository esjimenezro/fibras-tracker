import pandas as pd
import plotly.express as px
import streamlit as st

from modules.portfolio.models import EnrichedDistribution
from ui.styles.theme import format_mxn
from ui.styles.theme import format_mxn_label


def render_distributions_chart(
    distributions_by_ticker: dict[str, list[EnrichedDistribution]],
) -> None:
    """Render a stacked bar chart of net distribution income over time, grouped by FIBRA,
    followed by an expandable monthly breakdown section.

    Distributions are always aggregated by month and ticker. Every month in the range
    from the first to the last payment date is shown on the x-axis, including months
    with no distributions. Below the chart, one st.expander is rendered per period
    (most recent first), each containing a per-FIBRA breakdown table with a styled
    totals row.

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

    df = pd.DataFrame(rows)
    df["payment_date"] = pd.to_datetime(df["payment_date"])
    df["period"] = df["payment_date"].dt.to_period("M").astype(str)

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

    st.plotly_chart(fig, width="stretch")

    def _highlight_total(data: pd.DataFrame) -> pd.DataFrame:
        """Return a styles DataFrame that bolds and highlights the last (totals) row.

        Args:
            data: The full display DataFrame passed by Styler.apply.

        Returns:
            DataFrame of CSS property strings with the same shape as data.
        """
        styles = pd.DataFrame("", index=data.index, columns=data.columns)
        styles.iloc[-1] = "font-weight: bold; background-color: #e8eaf6"
        return styles

    periods_sorted = sorted(df_grouped["period"].unique(), reverse=True)

    for period in periods_sorted:
        period_df = df_grouped[df_grouped["period"] == period].copy()

        total_net = period_df["net_income"].sum()
        total_fiscal = period_df["gross_fiscal_result_income"].sum()
        total_reimbursement = period_df["net_reimbursement_income"].sum()
        total_isr = period_df["fiscal_result_withholding"].sum()

        label = (
            f"{period}  —  "
            f"Neto: {format_mxn_label(value=total_net)}  |  "
            f"Fiscal: {format_mxn_label(value=total_fiscal)}  |  "
            f"Reembolso: {format_mxn_label(value=total_reimbursement)}  |  "
            f"ISR: {format_mxn_label(value=total_isr)}"
        )

        with st.expander(label=label):
            display_df = period_df[
                [
                    "ticker", "gross_fiscal_result_income",
                    "net_reimbursement_income", "fiscal_result_withholding",
                    "net_income"
                ]
            ].copy()

            for col in numeric_cols:
                display_df[col] = display_df[col].map(
                    lambda v: format_mxn(value=v) if pd.notna(v) else "N/D"
                )

            totals_row = pd.DataFrame([{
                "ticker": "Total",
                "gross_fiscal_result_income": format_mxn(value=total_fiscal),
                "net_reimbursement_income": format_mxn(value=total_reimbursement),
                "fiscal_result_withholding": format_mxn(value=total_isr),
                "net_income": format_mxn(value=total_net),
            }])

            display_df = pd.concat([display_df, totals_row], ignore_index=True)
            display_df = display_df.rename(columns={
                "ticker": "FIBRA",
                "gross_fiscal_result_income": "Ingreso Fiscal Bruto",
                "net_reimbursement_income": "Reembolso Neto",
                "fiscal_result_withholding": "Retención ISR",
                "net_income": "Ingreso Neto",
            })

            styled = display_df.style.apply(_highlight_total, axis=None)
            st.dataframe(styled, width="stretch", hide_index=True)
