from modules.portfolio.models.distribution import Distribution


class EnrichedDistribution(Distribution):
    """A distribution payment with all derived income and tax fields computed.

    Extends Distribution with six calculated fields produced by DistributionsProcessor.

    Attributes:
        gross_fiscal_result_income: Fiscal result income in MXN
            (equals fiscal_result_total).
        net_reimbursement_income: Capital reimbursement received in MXN
            (equals reimbursement_total). It is net as it is not subject to tax withholding.
        gross_income: Sum of reimbursement and fiscal result income in MXN.
        fiscal_result_withholding: ISR withheld at 30% of gross_fiscal_result_income in MXN.
        net_fiscal_result_income: Net fiscal result after ISR withholding, excluding capital
            reimbursement (gross_fiscal_result_income - fiscal_result_withholding).
        net_income: Income after withholding in MXN (gross_income - fiscal_result_withholding).
    """

    gross_fiscal_result_income: float
    net_reimbursement_income: float
    gross_income: float
    fiscal_result_withholding: float
    net_fiscal_result_income: float
    net_income: float
