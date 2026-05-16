from modules.portfolio.models.distribution import Distribution
from modules.portfolio.models.enriched_distribution import EnrichedDistribution


class DistributionsProcessor:
    """Processes raw distribution records into enriched output models with derived financial fields."""

    def process(self, distributions: list[Distribution]) -> list[EnrichedDistribution]:
        """Compute all derived income and tax fields for each distribution.

        Args:
            distributions: Raw distribution records to enrich.

        Returns:
            list[EnrichedDistribution]: One enriched record per input distribution,
                in the same order.
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
            EnrichedDistribution: The distribution with all calculated fields populated.
        """
        total_reimbursement_income = distribution.reimbursement_per_cbfi * distribution.cbfis_at_time
        total_fiscal_result_income = distribution.fiscal_result_per_cbfi * distribution.cbfis_at_time
        total_income = total_reimbursement_income + total_fiscal_result_income
        fiscal_result_withholding = 0.30 * total_fiscal_result_income
        net_income = total_income - fiscal_result_withholding

        return EnrichedDistribution(
            **distribution.model_dump(),
            total_reimbursement_income=total_reimbursement_income,
            total_fiscal_result_income=total_fiscal_result_income,
            total_income=total_income,
            fiscal_result_withholding=fiscal_result_withholding,
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
        """Sum total_income across all enriched distribution records.

        Args:
            enriched: Enriched distribution records.

        Returns:
            float: Total gross income in MXN before withholding.
        """
        return sum(e.total_income for e in enriched)

    def total_withholding(self, enriched: list[EnrichedDistribution]) -> float:
        """Sum fiscal_result_withholding across all enriched distribution records.

        Args:
            enriched: Enriched distribution records.

        Returns:
            float: Total ISR withheld in MXN.
        """
        return sum(e.fiscal_result_withholding for e in enriched)
