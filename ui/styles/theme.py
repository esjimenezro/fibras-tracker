import streamlit as st


COLOR_POSITIVE = "#2E7D32"
COLOR_NEGATIVE = "#C62828"
COLOR_NEUTRAL = "#1565C0"


def format_mxn(value: float) -> str:
    """Format a float as a MXN currency string.

    Args:
        value: Numeric value in MXN.

    Returns:
        Formatted string, e.g. '$1,234.56 MXN'.
    """
    return f"${value:,.2f} MXN"


def format_mxn_compact(value: float) -> str:
    """Format large MXN values in compact notation.

    Args:
        value: Numeric value in MXN.

    Returns:
        Compact string, e.g. '$1.23 M MXN' or '$1.23 K MXN'.
    """
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:,.2f} M MXN"
    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:,.2f} K MXN"
    return format_mxn(value)


def format_pct(value: float, include_sign: bool = True) -> str:
    """Format a fractional float as a percentage string.

    Args:
        value: Fractional value (e.g. 0.0523 for 5.23%).
        include_sign: Prepend '+' for non-negative values when True.

    Returns:
        Formatted string, e.g. '+5.23%' or '-2.10%'.
    """
    pct = value * 100
    if include_sign and pct >= 0:
        return f"+{pct:.2f}%"
    return f"{pct:.2f}%"


def color_return(value: float) -> str:
    """Return a CSS color string for use with pandas Styler.map().

    Args:
        value: Numeric return value; non-negative maps to green, negative to red.

    Returns:
        CSS property string, e.g. 'color: #2E7D32'.
    """
    return f"color: {COLOR_POSITIVE}" if value >= 0 else f"color: {COLOR_NEGATIVE}"


def load_custom_css() -> None:
    """Inject minimal CSS via st.markdown() to polish metric cards and spacing."""
    st.markdown(
        """
        <style>
        [data-testid="stMetric"] {
            background-color: #f0f2f6;
            border-radius: 8px;
            padding: 12px 16px;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
