from datetime import datetime, timezone

import yfinance as yf

from config import TICKER_SUFFIX
from modules.portfolio.models.market_price import MarketPrice
from modules.portfolio.repositories.base.base_market_price_read_repository import BaseMarketPriceReadRepository


class YFinanceMarketPriceReadRepository(BaseMarketPriceReadRepository):
    """Fetches live market prices from Yahoo Finance via yfinance (>=1.0.0)."""

    def retrieve_data(self) -> list[MarketPrice]:
        """Return the latest market price for each configured ticker.

        Returns:
            list[MarketPrice]: One entry per ticker, using the .MX suffix internally
                to query BMV prices via Yahoo Finance.
        """
        retrieved_at = datetime.now(timezone.utc)
        return [self._fetch(ticker, retrieved_at) for ticker in self.tickers]

    def _fetch(self, ticker: str, retrieved_at: datetime) -> MarketPrice:
        """Fetch price and currency for a single ticker from Yahoo Finance.

        Args:
            ticker: BMV ticker without the .MX suffix (e.g. "FMTY14").
            retrieved_at: UTC timestamp to record on the returned model.

        Returns:
            MarketPrice: Populated model with the latest price data.
        """
        info = yf.Ticker(f"{ticker}{TICKER_SUFFIX}").fast_info
        last_price = info.last_price
        if last_price is None:
            raise ValueError(f"Failed to fetch price for ticker {ticker} from Yahoo Finance.")
        return MarketPrice(
            ticker=ticker,
            price=last_price,
            currency=info.currency,
            retrieved_at=retrieved_at,
        )
