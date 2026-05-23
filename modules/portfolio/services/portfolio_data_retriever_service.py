from modules.common.repositories.base import BaseCatalogReadRepository
from modules.common.repositories.base import BaseMarketPriceReadRepository
from modules.common.repositories import JsonCatalogReadRepository
from modules.common.repositories import YFinanceMarketPriceReadRepository

from modules.portfolio.processors import DistributionsProcessor
from modules.portfolio.processors import PortfolioProcessor
from modules.portfolio.processors import PositionsProcessor
from modules.portfolio.repositories.base import BaseDistributionsReadRepository
from modules.portfolio.repositories.base import BasePositionsReadRepository
from modules.portfolio.repositories import JsonDistributionsReadRepository
from modules.portfolio.repositories import JsonPositionsReadRepository
from modules.portfolio.schemas import PortfolioDataRetrieverServiceSchema
from modules.portfolio.schemas import PortfolioDataRetrieverStatus


class PortfolioDataRetrieverService:
    """Orchestrates repositories and processors to assemble a fully enriched Portfolio."""

    def __init__(
        self,
        position_repository: BasePositionsReadRepository | None = None,
        distribution_repository: BaseDistributionsReadRepository | None = None,
        market_price_repository: BaseMarketPriceReadRepository | None = None,
        catalog_repository: BaseCatalogReadRepository | None = None,
    ) -> None:
        """Initialise repositories and processors.

        Args:
            position_repository: Repository for raw positions. Defaults to JsonPositionsReadRepository.
            distribution_repository: Repository for raw distributions. Defaults to JsonDistributionsReadRepository.
            market_price_repository: Repository for live market prices. Defaults to YFinanceMarketPriceReadRepository.
            catalog_repository: Repository for the FIBRA catalog. Defaults to JsonCatalogReadRepository.
        """

        self._catalog_repository = catalog_repository or JsonCatalogReadRepository()
        self._position_repository = position_repository or JsonPositionsReadRepository()
        self._distribution_repository = distribution_repository or JsonDistributionsReadRepository()
        self._market_price_repository = market_price_repository or YFinanceMarketPriceReadRepository()

        self._distributions_processor = DistributionsProcessor()
        self._positions_processor = PositionsProcessor()
        self._portfolio_processor = PortfolioProcessor()

    def run(self) -> PortfolioDataRetrieverServiceSchema:
        """Fetch, enrich, and aggregate all portfolio data.

        Returns:
            PortfolioDataRetrieverServiceSchema: status=OK with the assembled Portfolio on
                success, or status=ERROR with the exception message on failure.
        """
        try:

            fibras = self._catalog_repository.retrieve_data()
            positions = self._position_repository.retrieve_data()
            distributions = self._distribution_repository.retrieve_data()

            tickers = [p.ticker for p in positions]
            market_prices = self._market_price_repository.retrieve_data(tickers=tickers)

            enriched_distributions = self._distributions_processor.process(distributions=distributions)
            enriched_positions = self._positions_processor.process(
                positions=positions,
                market_prices=market_prices,
                distributions=enriched_distributions,
                fibras=fibras,
            )
            portfolio = self._portfolio_processor.process(positions=enriched_positions)

            return PortfolioDataRetrieverServiceSchema(
                status=PortfolioDataRetrieverStatus.OK,
                data=portfolio
            )

        except Exception as e:

            return PortfolioDataRetrieverServiceSchema(
                status=PortfolioDataRetrieverStatus.ERROR,
                error_message=str(e)
            )
