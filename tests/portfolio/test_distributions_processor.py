from datetime import date

import pytest

from modules.portfolio.models.distribution import Distribution
from modules.portfolio.processors.distributions_processor import DistributionsProcessor


@pytest.fixture
def processor():
    """Return a DistributionsProcessor instance."""
    return DistributionsProcessor()


@pytest.fixture
def dist_fiscal_only():
    """Distribution with no reimbursement component — purely fiscal result."""
    return Distribution(
        ticker="FMTY14",
        payment_date=date(2026, 3, 6),
        reimbursement_per_cbfi=0.0,
        fiscal_result_per_cbfi=0.10,
        cbfis_at_time=1000,
    )


@pytest.fixture
def dist_reimbursement_only():
    """Distribution with no fiscal result component — purely capital reimbursement."""
    return Distribution(
        ticker="FMTY14",
        payment_date=date(2026, 3, 6),
        reimbursement_per_cbfi=0.05,
        fiscal_result_per_cbfi=0.0,
        cbfis_at_time=500,
    )


@pytest.fixture
def dist_mixed():
    """Distribution with both reimbursement and fiscal result components."""
    return Distribution(
        ticker="FMTY14",
        payment_date=date(2026, 3, 6),
        reimbursement_per_cbfi=0.0331,
        fiscal_result_per_cbfi=0.0483,
        cbfis_at_time=1500,
    )


def test_gross_fiscal_result_income(processor, dist_mixed):
    """gross_fiscal_result_income = fiscal_result_per_cbfi * cbfis_at_time."""
    result = processor._enrich(dist_mixed)
    assert result.gross_fiscal_result_income == pytest.approx(72.45, rel=1e-6)


def test_net_reimbursement_income(processor, dist_mixed):
    """net_reimbursement_income = reimbursement_per_cbfi * cbfis_at_time."""
    result = processor._enrich(dist_mixed)
    assert result.net_reimbursement_income == pytest.approx(49.65, rel=1e-6)


def test_gross_income(processor, dist_mixed):
    """gross_income = net_reimbursement_income + gross_fiscal_result_income."""
    result = processor._enrich(dist_mixed)
    assert result.gross_income == pytest.approx(122.10, rel=1e-6)


def test_fiscal_result_withholding(processor, dist_mixed):
    """fiscal_result_withholding = 0.30 * gross_fiscal_result_income."""
    result = processor._enrich(dist_mixed)
    assert result.fiscal_result_withholding == pytest.approx(21.735, rel=1e-6)


def test_net_fiscal_result_income(processor, dist_mixed):
    """net_fiscal_result_income = gross_fiscal_result_income - fiscal_result_withholding."""
    result = processor._enrich(dist_mixed)
    assert result.net_fiscal_result_income == pytest.approx(50.715, rel=1e-6)


def test_net_income(processor, dist_mixed):
    """net_income = gross_income - fiscal_result_withholding."""
    result = processor._enrich(dist_mixed)
    assert result.net_income == pytest.approx(100.365, rel=1e-6)


def test_fiscal_only_zero_reimbursement(processor, dist_fiscal_only):
    """When reimbursement_per_cbfi=0, net_reimbursement_income=0 and gross_income equals gross_fiscal_result_income."""
    result = processor._enrich(dist_fiscal_only)
    assert result.net_reimbursement_income == pytest.approx(0.0, abs=1e-9)
    assert result.gross_income == pytest.approx(result.gross_fiscal_result_income, rel=1e-6)


def test_reimbursement_only_zero_withholding(processor, dist_reimbursement_only):
    """When fiscal_result_per_cbfi=0, withholding=0 and net_income equals net_reimbursement_income."""
    result = processor._enrich(dist_reimbursement_only)
    assert result.fiscal_result_withholding == pytest.approx(0.0, abs=1e-9)
    assert result.net_income == pytest.approx(result.net_reimbursement_income, rel=1e-6)


def test_process_returns_one_per_input(processor, dist_mixed, dist_fiscal_only):
    """process() returns one EnrichedDistribution per input Distribution."""
    results = processor.process([dist_mixed, dist_fiscal_only])
    assert len(results) == 2


def test_process_empty_list(processor):
    """process() on an empty list returns an empty list."""
    assert processor.process([]) == []


def test_total_net_income(processor, dist_mixed, dist_fiscal_only):
    """total_net_income() sums net_income across all enriched distributions.

    dist_mixed: net_income = 100.365
    dist_fiscal_only: net_income = 0.10 * 1000 - 0.30 * (0.10 * 1000) = 100 - 30 = 70.0
    """
    enriched = processor.process([dist_mixed, dist_fiscal_only])
    assert processor.total_net_income(enriched) == pytest.approx(170.365, rel=1e-6)


def test_total_gross_income(processor, dist_mixed, dist_fiscal_only):
    """total_gross_income() sums gross_income across all enriched distributions.

    dist_mixed: gross_income = 122.10
    dist_fiscal_only: gross_income = 0 + 0.10 * 1000 = 100.0
    """
    enriched = processor.process([dist_mixed, dist_fiscal_only])
    assert processor.total_gross_income(enriched) == pytest.approx(222.10, rel=1e-6)


def test_total_withholding(processor, dist_mixed, dist_fiscal_only):
    """total_withholding() sums fiscal_result_withholding across all enriched distributions.

    dist_mixed: withholding = 21.735
    dist_fiscal_only: withholding = 0.30 * 100 = 30.0
    """
    enriched = processor.process([dist_mixed, dist_fiscal_only])
    assert processor.total_withholding(enriched) == pytest.approx(51.735, rel=1e-6)
