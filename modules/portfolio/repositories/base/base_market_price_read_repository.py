from abc import ABC, abstractmethod

from modules.portfolio.models.market_price import MarketPrice


class BaseMarketPriceReadRepository(ABC):
    """Abstract interface for fetching live market prices from any data source."""

    def __init__(self, tickers: list[str]) -> None:
        """Store the list of BMV tickers to fetch prices for.

        Args:
            tickers: BMV tickers without the .MX suffix
                (e.g. ["FMTY14", "DANHOS13"]).
        """
        self.tickers = tickers

    @abstractmethod
    def retrieve_data(self) -> list[MarketPrice]:
        """Return market prices for all configured tickers.

        Returns:
            list[MarketPrice]: One entry per ticker, in the same order
                as the tickers passed at construction time.
        """
        ...
