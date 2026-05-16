from modules.portfolio.models.distribution import Distribution


class EnrichedDistribution(Distribution):
    """A distribution payment with all derived income and tax fields computed.

    Extends Distribution with five calculated fields produced by DistributionsProcessor.

    Attributes:
        total_reimbursement_income: Capital reimbursement received in MXN
            (reimbursement_per_cbfi * cbfis_at_time).
        total_fiscal_result_income: Fiscal result income in MXN
            (fiscal_result_per_cbfi * cbfis_at_time).
        total_income: Sum of reimbursement and fiscal result income in MXN.
        fiscal_result_withholding: ISR withheld at 30% of total_fiscal_result_income in MXN.
        net_income: Income after withholding in MXN (total_income - fiscal_result_withholding).
    """

    total_reimbursement_income: float
    total_fiscal_result_income: float
    total_income: float
    fiscal_result_withholding: float
    net_income: float
