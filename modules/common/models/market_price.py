from datetime import datetime

from pydantic import BaseModel


class MarketPrice(BaseModel):
    """Last known market price for a FIBRA ticker, fetched from a live data source.

    Attributes:
        ticker: BMV ticker without the .MX suffix (e.g. "FMTY14").
        price: Last market price in MXN.
        currency: Currency of the price (e.g. "MXN"). Captured from the data source
            to detect unexpected cross-listed prices.
        retrieved_at: UTC timestamp of when the price was fetched.
    """

    ticker: str
    price: float
    currency: str
    retrieved_at: datetime
