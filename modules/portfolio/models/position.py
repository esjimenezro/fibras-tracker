from enum import Enum

from pydantic import BaseModel


class PaymentFrequency(str, Enum):
    """Distribution payment frequency for a FIBRA position."""

    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"


class Position(BaseModel):
    """A single FIBRA position held in the portfolio."""

    ticker: str
    name: str
    sector: str
    cbfis: int
    average_purchase_price: float
    payment_frequency: PaymentFrequency
