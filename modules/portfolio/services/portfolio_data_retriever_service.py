from modules.portfolio.processors.distributions_processor import DistributionsProcessor
from modules.portfolio.processors.portfolio_processor import PortfolioProcessor
from modules.portfolio.processors.positions_processor import PositionsProcessor
from modules.portfolio.repositories.base.base_distributions_read_repository import BaseDistributionsReadRepository
from modules.portfolio.repositories.base.base_market_price_read_repository import BaseMarketPriceReadRepository
from modules.portfolio.repositories.base.base_positions_read_repository import BasePositionsReadRepository
from modules.portfolio.repositories.json_distributions_read_repository import JsonDistributionsReadRepository
from modules.portfolio.repositories.json_positions_read_repository import JsonPositionsReadRepository
from modules.portfolio.repositories.yfinance_market_price_read_repository import YFinanceMarketPriceReadRepository
from modules.portfolio.schemas.portfolio_schemas import PortfolioDataRetrieverServiceSchema, PortfolioDataRetrieverStatus


class PortfolioDataRetrieverService:
    """Orchestrates repositories and processors to assemble a fully enriched Portfolio."""

    def __init__(
        self,
        position_repository: BasePositionsReadRepository | None = None,
        distribution_repository: BaseDistributionsReadRepository | None = None,
        market_price_repository: BaseMarketPriceReadRepository | None = None,
    ) -> None:
        """Initialise repositories and processors.

        Args:
            position_repository: Repository for raw positions. Defaults to JsonPositionsReadRepository.
            distribution_repository: Repository for raw distributions. Defaults to JsonDistributionsReadRepository.
            market_price_repository: Repository for live market prices. Defaults to YFinanceMarketPriceReadRepository.
        """

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

            positions = self._position_repository.retrieve_data()
            distributions = self._distribution_repository.retrieve_data()
            tickers = [p.ticker for p in positions]
            market_prices = self._market_price_repository.retrieve_data(tickers=tickers)

            enriched_distributions = self._distributions_processor.process(distributions)
            enriched_positions = self._positions_processor.process(positions, market_prices, enriched_distributions)
            portfolio = self._portfolio_processor.process(enriched_positions)

            return PortfolioDataRetrieverServiceSchema(
                status=PortfolioDataRetrieverStatus.OK,
                data=portfolio
            )

        except Exception as e:

            return PortfolioDataRetrieverServiceSchema(
                status=PortfolioDataRetrieverStatus.ERROR,
                error_message=str(e)
            )
