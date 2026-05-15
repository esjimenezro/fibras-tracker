from datetime import date

from pydantic import BaseModel


class Distribution(BaseModel):
    ticker: str
    payment_date: date
    reimbursement_per_cbfi: float
    fiscal_result_per_cbfi: float
    cbfis_at_time: int
