import pytest

from modules.common.models import InflationRecord
from modules.common.processors import InflationIndexProcessor


@pytest.fixture
def processor():
    """A fresh InflationIndexProcessor for each test."""
    return InflationIndexProcessor()


@pytest.fixture
def inflation_records():
    """Three consecutive years of inflation, with a gap after 2022."""
    return [
        InflationRecord(year=2020, annual_inflation=0.04),
        InflationRecord(year=2021, annual_inflation=0.05),
        InflationRecord(year=2022, annual_inflation=0.08),
    ]


def test_series_starts_with_unchanged_base_entry(processor, inflation_records):
    """The first entry is always (base_year, base_value), with no rate applied."""
    series = processor.process(
        base_year=2020, base_value=1000.0, rate_years=[], inflation_records=inflation_records,
    )
    assert series == [(2020, 1000.0)]


def test_series_compounds_consecutive_rate_years_in_order(processor, inflation_records):
    """Each rate_years entry multiplies the running value by (1 + that year's rate)."""
    series = processor.process(
        base_year=2020, base_value=1000.0, rate_years=[2021, 2022], inflation_records=inflation_records,
    )
    expected_2021 = 1000.0 * 1.05
    expected_2022 = expected_2021 * 1.08
    assert series == [(2020, 1000.0), (2021, pytest.approx(expected_2021)), (2022, pytest.approx(expected_2022))]


def test_rate_years_may_skip_years_and_repeat_a_years_own_rate(processor, inflation_records):
    """rate_years is an arbitrary caller-chosen sequence, not necessarily base_year + 1 ...end_year."""
    series = processor.process(
        base_year=2020, base_value=1.0, rate_years=[2020, 2022], inflation_records=inflation_records,
    )
    expected_first = 1.0 * 1.04
    expected_second = expected_first * 1.08
    assert series == [(2020, 1.0), (2020, pytest.approx(expected_first)), (2022, pytest.approx(expected_second))]


def test_series_truncates_before_first_missing_rate_year(processor, inflation_records):
    """A rate_years entry absent from inflation_records stops the series, not an error."""
    series = processor.process(
        base_year=2020, base_value=1000.0, rate_years=[2021, 2025, 2022], inflation_records=inflation_records,
    )
    assert [year for year, _ in series] == [2020, 2021]


def test_empty_inflation_records_yields_only_the_base_entry(processor):
    """No inflation data at all truncates immediately, leaving only the base entry."""
    series = processor.process(
        base_year=2020, base_value=1000.0, rate_years=[2021], inflation_records=[],
    )
    assert series == [(2020, 1000.0)]
