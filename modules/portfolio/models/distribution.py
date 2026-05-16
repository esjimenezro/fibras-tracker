from datetime import date

from pydantic import BaseModel


class Distribution(BaseModel):
    """A single distribution payment received from a FIBRA.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        payment_date: Date the payment was credited by the broker.
        reimbursement_per_cbfi: Capital reimbursement per CBFI
            (not taxable when received).
        fiscal_result_per_cbfi: Fiscal result per CBFI
            (subject to 30% ISR withholding).
        cbfis_at_time: Number of CBFIs held at the time of payment.
    """

    ticker: str
    payment_date: date
    reimbursement_per_cbfi: float
    fiscal_result_per_cbfi: float
    cbfis_at_time: int
