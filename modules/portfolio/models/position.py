from enum import Enum

from pydantic import BaseModel


class PaymentFrequency(str, Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"


class Position(BaseModel):
    ticker: str
    name: str
    sector: str
    cbfis: int
    average_purchase_price: float
    payment_frequency: PaymentFrequency
