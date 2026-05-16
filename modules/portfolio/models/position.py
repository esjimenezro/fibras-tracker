from enum import Enum

from pydantic import BaseModel


class PaymentFrequency(str, Enum):
    """Distribution payment frequency for a FIBRA position.

    Attributes:
        MONTHLY: Distributions are paid once a month.
        QUARTERLY: Distributions are paid once per quarter.
    """

    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"


class Position(BaseModel):
    """A single FIBRA position held in the portfolio.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        name: Full name of the FIBRA (e.g. "Fibra Mty").
        sector: Market sector (e.g. "Industrial / Offices").
        cbfis: Number of CBFIs held.
        average_purchase_price: Weighted average purchase price per CBFI in MXN.
        payment_frequency: Distribution payment frequency.
    """

    ticker: str
    name: str
    sector: str
    cbfis: int
    average_purchase_price: float
    payment_frequency: PaymentFrequency
