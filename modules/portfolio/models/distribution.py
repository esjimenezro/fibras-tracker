from datetime import date

from pydantic import BaseModel


class Distribution(BaseModel):
    """A single distribution payment received from a FIBRA.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        payment_date: Date the payment was credited by the broker.
        reimbursement_total: Total capital reimbursement received in MXN
            (not taxable when received).
        fiscal_result_total: Total fiscal result income received in MXN
            (subject to 30% ISR withholding).
    """

    ticker: str
    payment_date: date
    reimbursement_total: float
    fiscal_result_total: float
