from abc import ABC, abstractmethod

from modules.portfolio.models.market_price import MarketPrice


class BaseMarketPriceReadRepository(ABC):
    """Abstract interface for fetching live market prices from any data source."""

    @abstractmethod
    def retrieve_data(self, tickers: list[str]) -> list[MarketPrice]:
        """Return market prices for the given tickers.

        Args:
            tickers: BMV tickers without the .MX suffix (e.g. ["FMTY14", "DANHOS13"]).

        Returns:
            list[MarketPrice]: One entry per ticker, in the same order as tickers.
        """
        ...
