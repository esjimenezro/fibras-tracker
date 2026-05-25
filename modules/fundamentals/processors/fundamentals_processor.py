from typing import Optional

from modules.common.models import MarketPrice

from modules.fundamentals.models import EnrichedFundamentalsRecord
from modules.fundamentals.models import FundamentalsRecord


class FundamentalsProcessor:
    """Enriches raw FundamentalsRecord instances with derived financial and market metrics.

    Transformation: list[FundamentalsRecord] + list[MarketPrice] → list[EnrichedFundamentalsRecord]

    Formulas implemented:
        noi_margin              = noi / total_revenues
        ebitda_margin           = ebitda / total_revenues
        revenue_per_m2          = total_revenues / gross_leasable_area_m2
        affo_per_m2             = affo / gross_leasable_area_m2

        ffo_per_cbfi            = ffo / cbfis_with_rights
        affo_per_cbfi           = affo / cbfis_with_rights
        nav_per_cbfi            = total_equity / cbfis_outstanding

        ltv                     = financial_debt / total_assets
        affo_payout_ratio       = (distribution_per_cbfi * cbfis_outstanding) / affo

        market_cap              = market_price * cbfis_outstanding
        price_to_ffo            = market_price / ffo_per_cbfi
        price_to_affo           = market_price / affo_per_cbfi
        dividend_yield          = distribution_per_cbfi * 4 / market_price
        price_to_nav            = market_price / nav_per_cbfi

    Any field whose inputs contain None or whose denominator is zero is set to None.
    Market metrics are None when the ticker has no matching entry in market_prices.
    """

    def process(
        self,
        records: list[FundamentalsRecord],
        market_prices: list[MarketPrice],
    ) -> list[EnrichedFundamentalsRecord]:
        """Compute all derived fields for each fundamentals record.

        Args:
            records: Raw fundamentals records to enrich. Must not be empty.
            market_prices: Live market prices used to compute market-based metrics.
                Converted internally to a dict keyed by ticker for O(1) lookup.
                Records whose ticker is not present receive None for all market metrics.

        Returns:
            list[EnrichedFundamentalsRecord]: One enriched record per input record,
                in the same order, with the following derived fields:

                noi_margin              = noi / total_revenues
                ebitda_margin           = ebitda / total_revenues
                revenue_per_m2          = total_revenues / gross_leasable_area_m2
                affo_per_m2             = affo / gross_leasable_area_m2

                ffo_per_cbfi            = ffo / cbfis_with_rights
                affo_per_cbfi           = affo / cbfis_with_rights
                nav_per_cbfi            = total_equity / cbfis_outstanding

                ltv                     = financial_debt / total_assets
                affo_payout_ratio       = (distribution_per_cbfi * cbfis_outstanding) / affo

                market_cap              = market_price * cbfis_outstanding
                price_to_ffo            = market_price / ffo_per_cbfi
                price_to_affo           = market_price / affo_per_cbfi
                dividend_yield          = distribution_per_cbfi * 4 / market_price
                price_to_nav            = market_price / nav_per_cbfi

        Raises:
            ValueError: If records is empty.
        """
        if not records:
            raise ValueError("Cannot enrich an empty list of FundamentalsRecord instances.")

        prices_by_ticker: dict[str, float] = {mp.ticker: mp.price for mp in market_prices}

        return [
            self._enrich(
                record=record,
                market_price=prices_by_ticker.get(record.ticker),
            )
            for record in records
        ]

    def _enrich(
        self,
        record: FundamentalsRecord,
        market_price: Optional[float],
    ) -> EnrichedFundamentalsRecord:
        """Compute all derived fields for a single fundamentals record.

        Args:
            record: A raw fundamentals record.
            market_price: Resolved market price per CBFI in MXN, or None if unavailable.

        Returns:
            EnrichedFundamentalsRecord with all derived fields set, or None for any field
            whose inputs are None or would produce a division by zero.
        """
        ffo_per_cbfi = self._safe_div(
            numerator=record.ffo,
            denominator=record.cbfis_with_rights,
        )
        affo_per_cbfi = self._safe_div(
            numerator=record.affo,
            denominator=record.cbfis_with_rights,
        )
        nav_per_cbfi = self._safe_div(
            numerator=record.total_equity,
            denominator=record.cbfis_outstanding,
        )

        affo_payout_numerator = (
            record.distribution_per_cbfi * record.cbfis_outstanding
            if record.distribution_per_cbfi is not None and record.cbfis_outstanding is not None
            else None
        )

        return EnrichedFundamentalsRecord(
            **record.model_dump(),
            market_price=market_price,
            noi_margin=self._safe_div(
                numerator=record.noi,
                denominator=record.total_revenues,
            ),
            ebitda_margin=self._safe_div(
                numerator=record.ebitda,
                denominator=record.total_revenues,
            ),
            revenue_per_m2=self._safe_div(
                numerator=record.total_revenues,
                denominator=record.gross_leasable_area_m2,
            ),
            affo_per_m2=self._safe_div(
                numerator=record.affo,
                denominator=record.gross_leasable_area_m2,
            ),
            ffo_per_cbfi=ffo_per_cbfi,
            affo_per_cbfi=affo_per_cbfi,
            nav_per_cbfi=nav_per_cbfi,
            ltv=self._safe_div(
                numerator=record.financial_debt,
                denominator=record.total_assets,
            ),
            affo_payout_ratio=self._safe_div(
                numerator=affo_payout_numerator,
                denominator=record.affo,
            ),
            market_cap=(
                market_price * record.cbfis_outstanding
                if market_price is not None and record.cbfis_outstanding is not None
                else None
            ),
            price_to_ffo=self._safe_div(
                numerator=market_price,
                denominator=ffo_per_cbfi,
            ),
            price_to_affo=self._safe_div(
                numerator=market_price,
                denominator=affo_per_cbfi,
            ),
            dividend_yield=self._safe_div(
                numerator=(
                    record.distribution_per_cbfi * 4
                    if record.distribution_per_cbfi is not None
                    else None
                ),
                denominator=market_price,
            ),
            price_to_nav=self._safe_div(
                numerator=market_price,
                denominator=nav_per_cbfi,
            ),
        )

    @staticmethod
    def _safe_div(
        numerator: Optional[float],
        denominator: Optional[float],
    ) -> Optional[float]:
        """Divide numerator by denominator, returning None on missing data or zero denominator.

        Args:
            numerator: Dividend value, or None.
            denominator: Divisor value, or None.

        Returns:
            float: numerator / denominator, or None if either argument is None or
                denominator is zero.
        """
        if numerator is None or denominator is None or denominator == 0:
            return None
        return numerator / denominator
