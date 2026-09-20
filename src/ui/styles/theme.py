from typing import Literal

import streamlit as st


COLOR_POSITIVE = "#2E7D32"
COLOR_NEGATIVE = "#C62828"
COLOR_NEUTRAL = "#1565C0"

COLOR_MUTED_BG = "rgba(200,200,200,0.15)"

ThresholdZone = Literal["positive", "warning", "negative"]

_ZONE_RGB: dict[ThresholdZone, tuple[int, int, int]] = {
    "positive": (50, 200, 100),
    "warning": (255, 200, 50),
    "negative": (255, 99, 99),
}

_ZONE_EMOJI: dict[ThresholdZone, str] = {
    "positive": "🟢",
    "warning": "🟡",
    "negative": "🔴",
}


def zone_background(zone: ThresholdZone, alpha: float = 0.15) -> str:
    """Return an rgba() background-color string for a threshold zone at a given opacity.

    Args:
        zone: One of "positive", "warning", "negative" (see threshold_zone()).
        alpha: Opacity, 0-1. Defaults to 0.15, matching table-cell/metric-card usage;
            a chart background wash typically wants something lower (e.g. 0.06) so it
            doesn't overpower the plotted line.

    Returns:
        str: e.g. 'rgba(50,200,100,0.15)'.
    """
    r, g, b = _ZONE_RGB[zone]
    return f"rgba({r},{g},{b},{alpha})"


COLOR_POSITIVE_BG = zone_background(zone="positive")
COLOR_WARNING_BG = zone_background(zone="warning")
COLOR_NEGATIVE_BG = zone_background(zone="negative")


def threshold_zone(value: float, lower: float, upper: float, inverse: bool = False) -> ThresholdZone:
    """Classify a value into a red/yellow/green threshold zone.

    The single shared decision behind every traffic-light KPI in the app (occupancy,
    LTV, NOI/EBITDA margins, ...): previously reimplemented independently by
    detail_header's metric badges, detail_chart's chart background bands, and
    comparison_table's cell background colouring, with nothing enforcing the three
    stayed in agreement.

    Args:
        value: Metric value to classify.
        lower: Lower threshold boundary (boundary between the negative and warning
            zones for a normal, higher-is-better metric).
        upper: Upper threshold boundary (boundary between the warning and positive
            zones for a normal metric).
        inverse: When True the metric is lower-is-better (e.g. LTV): value < lower is
            the positive zone, value > upper is the negative zone. Defaults to False.

    Returns:
        ThresholdZone: "positive", "warning", or "negative". A value exactly on a
            boundary falls in the warning zone.
    """
    if not inverse:
        if value > upper:
            return "positive"
        if value < lower:
            return "negative"
        return "warning"
    if value < lower:
        return "positive"
    if value > upper:
        return "negative"
    return "warning"


def threshold_emoji(value: float, lower: float, upper: float, inverse: bool = False) -> str:
    """Traffic-light emoji for a value against threshold boundaries.

    Args:
        value: Metric value to classify.
        lower: Lower threshold boundary. See threshold_zone().
        upper: Upper threshold boundary. See threshold_zone().
        inverse: When True the metric is lower-is-better. See threshold_zone().

    Returns:
        str: '🟢', '🟡', or '🔴' per threshold_zone().
    """
    return _ZONE_EMOJI[threshold_zone(value=value, lower=lower, upper=upper, inverse=inverse)]


def threshold_background(value: float, lower: float, upper: float, inverse: bool = False) -> str:
    """Traffic-light CSS background-color for a value against threshold boundaries.

    Args:
        value: Metric value to classify.
        lower: Lower threshold boundary. See threshold_zone().
        upper: Upper threshold boundary. See threshold_zone().
        inverse: When True the metric is lower-is-better. See threshold_zone().

    Returns:
        str: One of COLOR_POSITIVE_BG / COLOR_WARNING_BG / COLOR_NEGATIVE_BG per
            threshold_zone().
    """
    zone = threshold_zone(value=value, lower=lower, upper=upper, inverse=inverse)
    return zone_background(zone=zone)


def format_mxn(value: float) -> str:
    """Format a float as a MXN currency string.

    Args:
        value: Numeric value in MXN.

    Returns:
        Formatted string, e.g. '$1,234.56 MXN'.
    """
    return f"${value:,.2f} MXN"


def format_mxn_label(value: float) -> str:
    """Format a float as a MXN currency string safe for use in Streamlit widget labels.

    Escapes the dollar sign to prevent Streamlit from interpreting it as LaTeX.

    Args:
        value: Numeric value in MXN.

    Returns:
        Formatted string with escaped dollar sign, e.g. '\\$1,234.56 MXN'.
    """
    return f"\\${value:,.2f} MXN"


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
    return format_mxn(value=value)


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
