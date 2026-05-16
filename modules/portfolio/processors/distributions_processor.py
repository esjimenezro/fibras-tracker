from config import FISCAL_RESULT_WITHHOLDING_RATE
from modules.portfolio.models.distribution import Distribution
from modules.portfolio.models.enriched_distribution import EnrichedDistribution


class DistributionsProcessor:
    """Enriches raw Distribution records into EnrichedDistribution output models.

    Transformation: Distribution → EnrichedDistribution

    Formulas implemented:
        gross_fiscal_result_income = fiscal_result_per_cbfi * cbfis_at_time
        net_reimbursement_income   = reimbursement_per_cbfi * cbfis_at_time
        gross_income               = gross_fiscal_result_income + net_reimbursement_income
        fiscal_result_withholding  = FISCAL_RESULT_WITHHOLDING_RATE * gross_fiscal_result_income
        net_fiscal_result_income   = gross_fiscal_result_income - fiscal_result_withholding
        net_income                 = gross_income - fiscal_result_withholding
    """

    def process(self, distributions: list[Distribution]) -> list[EnrichedDistribution]:
        """Compute all derived income and tax fields for each distribution.

        Args:
            distributions: Raw distribution records to enrich.

        Returns:
            list[EnrichedDistribution]: One enriched record per input distribution, in the same
                order. Derived fields for each record are computed by _enrich().
        """
        return [
            self._enrich(distribution=distribution)
            for distribution in distributions
        ]

    def _enrich(self, distribution: Distribution) -> EnrichedDistribution:
        """Compute derived fields for a single distribution record.

        Args:
            distribution: A raw distribution record.

        Returns:
            EnrichedDistribution with the following derived fields:
                gross_fiscal_result_income = fiscal_result_per_cbfi * cbfis_at_time
                net_reimbursement_income   = reimbursement_per_cbfi * cbfis_at_time
                gross_income               = gross_fiscal_result_income + net_reimbursement_income
                fiscal_result_withholding  = FISCAL_RESULT_WITHHOLDING_RATE * gross_fiscal_result_income
                net_fiscal_result_income   = gross_fiscal_result_income - fiscal_result_withholding
                net_income                 = gross_income - fiscal_result_withholding

            Note: net_fiscal_result_income is the fiscal portion only, net of withholding.
            Use this field — never net_income — when aggregating income received from the
            fiscal result.
        """
        gross_fiscal_result_income = distribution.fiscal_result_per_cbfi * distribution.cbfis_at_time
        net_reimbursement_income = distribution.reimbursement_per_cbfi * distribution.cbfis_at_time
        gross_income = net_reimbursement_income + gross_fiscal_result_income
        fiscal_result_withholding = FISCAL_RESULT_WITHHOLDING_RATE * gross_fiscal_result_income
        net_fiscal_result_income = gross_fiscal_result_income - fiscal_result_withholding
        net_income = gross_income - fiscal_result_withholding

        return EnrichedDistribution(
            **distribution.model_dump(),
            gross_fiscal_result_income=gross_fiscal_result_income,
            net_reimbursement_income=net_reimbursement_income,
            gross_income=gross_income,
            fiscal_result_withholding=fiscal_result_withholding,
            net_fiscal_result_income=net_fiscal_result_income,
            net_income=net_income,
        )

    def total_net_income(self, enriched: list[EnrichedDistribution]) -> float:
        """Sum net_income across all enriched distribution records.

        Args:
            enriched: Enriched distribution records.

        Returns:
            float: Total net income in MXN after ISR withholding.
        """
        return sum(e.net_income for e in enriched)

    def total_gross_income(self, enriched: list[EnrichedDistribution]) -> float:
        """Sum gross_income across all enriched distribution records.

        Args:
            enriched: Enriched distribution records.

        Returns:
            float: Total gross income in MXN before withholding.
        """
        return sum(e.gross_income for e in enriched)

    def total_withholding(self, enriched: list[EnrichedDistribution]) -> float:
        """Sum fiscal_result_withholding across all enriched distribution records.

        Args:
            enriched: Enriched distribution records.

        Returns:
            float: Total ISR withheld in MXN.
        """
        return sum(e.fiscal_result_withholding for e in enriched)
