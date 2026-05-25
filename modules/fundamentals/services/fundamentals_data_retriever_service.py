from typing import Optional

from modules.common.repositories.base import BaseCatalogReadRepository
from modules.common.repositories.base import BaseMarketPriceReadRepository
from modules.common.repositories import JsonCatalogReadRepository
from modules.common.repositories import YFinanceMarketPriceReadRepository
from modules.common.schemas import ServiceStatus

from modules.fundamentals.processors import FundamentalsHistoryProcessor
from modules.fundamentals.processors import FundamentalsProcessor
from modules.fundamentals.repositories.base import BaseFundamentalsReadRepository
from modules.fundamentals.repositories import JsonFundamentalsReadRepository
from modules.fundamentals.schemas import FundamentalsDataRetrieverServiceSchema


class FundamentalsDataRetrieverService:
    """Orchestrates repositories and processors to assemble a FundamentalsHistory aggregate."""

    def __init__(
        self,
        fundamentals_repository: Optional[BaseFundamentalsReadRepository] = None,
        market_price_repository: Optional[BaseMarketPriceReadRepository] = None,
        catalog_repository: Optional[BaseCatalogReadRepository] = None,
    ) -> None:
        """Initialise repositories and processors.

        Args:
            fundamentals_repository: Repository for raw fundamentals records.
                Defaults to JsonFundamentalsReadRepository.
            market_price_repository: Repository for live market prices.
                Defaults to YFinanceMarketPriceReadRepository.
            catalog_repository: Repository for the FIBRA catalog.
                Defaults to JsonCatalogReadRepository.
        """
        self._fundamentals_repository = fundamentals_repository or JsonFundamentalsReadRepository()
        self._market_price_repository = market_price_repository or YFinanceMarketPriceReadRepository()
        self._catalog_repository = catalog_repository or JsonCatalogReadRepository()

        self._fundamentals_processor = FundamentalsProcessor()
        self._history_processor = FundamentalsHistoryProcessor()

    def run(self) -> FundamentalsDataRetrieverServiceSchema:
        """Fetch, enrich, and aggregate all fundamentals data.

        Returns:
            FundamentalsDataRetrieverServiceSchema: status=OK with the assembled
                FundamentalsHistory on success, or status=ERROR with the exception
                message on failure.
        """
        try:

            records = self._fundamentals_repository.retrieve_data()
            fibras = self._catalog_repository.retrieve_data()

            tickers = sorted({r.ticker for r in records})
            market_prices = self._market_price_repository.retrieve_data(tickers=tickers)

            enriched_records = self._fundamentals_processor.process(
                records=records,
                market_prices=market_prices,
            )
            history = self._history_processor.process(
                records=enriched_records,
                fibras=fibras,
            )

            return FundamentalsDataRetrieverServiceSchema(
                status=ServiceStatus.OK,
                data=history,
            )

        except Exception as e:

            return FundamentalsDataRetrieverServiceSchema(
                status=ServiceStatus.ERROR,
                error_message=str(e),
            )
