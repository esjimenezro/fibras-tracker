from pydantic import BaseModel


class Position(BaseModel):
    """A single FIBRA position held in the portfolio.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        cbfis: Number of CBFIs held.
        average_purchase_cost: Weighted average purchase cost per CBFI in MXN.
    """

    ticker: str
    cbfis: int
    average_purchase_cost: float
