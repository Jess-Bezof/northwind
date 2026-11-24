"""Tests for Q2: market dependence on the largest customer."""
import pytest

import q2_concentration

# Hand-checked value: Austria's revenue and its top customer (Ernst Handel),
# confirmed by the student in Excel on 2026-11-24 (filter Orders to Austrian
# customers, apply the revenue formula to their order lines).
AUSTRIA_REVENUE = 128_003.84
AUSTRIA_TOP_CUSTOMER = "Ernst Handel"
AUSTRIA_TOP_REVENUE = 104_874.98


@pytest.fixture(scope="module")
def table(lines):
    """Compute the Q2 country table once per test module.

    Args:
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        pandas.DataFrame: Output of
            ``q2_concentration.concentration_by_country``.
    """
    return q2_concentration.concentration_by_country(lines)


def test_matches_independent_calculation_for_every_country(table, raw_lines):
    """Check every country's totals against the independent rebuild.

    Args:
        table (pandas.DataFrame): ``table`` fixture.
        raw_lines (pandas.DataFrame): ``raw_lines`` fixture.

    Returns:
        None.
    """
    by_customer = raw_lines.groupby(["Country", "CustomerID"])["Revenue"].sum()
    raw = by_customer.groupby(level="Country").agg(["sum", "max", "size"])
    assert set(raw.index) == set(table.index)
    for country, row in raw.iterrows():
        assert table.loc[country, "Revenue"] == pytest.approx(row["sum"], abs=0.01)
        assert table.loc[country, "TopCustomerRevenue"] == pytest.approx(row["max"], abs=0.01)
        assert table.loc[country, "Customers"] == row["size"]


def test_austria_matches_hand_checked_values(table):
    """Check Austria's revenue and top customer against hand checks.

    Args:
        table (pandas.DataFrame): ``table`` fixture.

    Returns:
        None.
    """
    at = table.loc["Austria"]
    assert at["Revenue"] == pytest.approx(AUSTRIA_REVENUE, abs=0.01)
    assert at["TopCustomer"] == AUSTRIA_TOP_CUSTOMER
    assert at["TopCustomerRevenue"] == pytest.approx(AUSTRIA_TOP_REVENUE, abs=0.01)


def test_country_revenue_adds_up_to_company_revenue(table, lines):
    """Check revenue, shares, and customer counts reconcile.

    Args:
        table (pandas.DataFrame): ``table`` fixture.
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        None.
    """
    assert table["Revenue"].sum() == pytest.approx(lines["Revenue"].sum(), abs=0.01)
    assert table["ShareOfCompanyRevenue"].sum() == pytest.approx(1.0)
    assert table["Customers"].sum() == lines["CustomerID"].nunique() == 89


def test_shares_are_valid_and_single_customer_markets_are_100pct(table):
    """Check shares lie in [0, 1] and one-customer markets are 100%.

    Args:
        table (pandas.DataFrame): ``table`` fixture.

    Returns:
        None.
    """
    assert table["TopCustomerShare"].between(0, 1).all()
    single = table[table["Customers"] == 1]
    assert set(single.index) == {"Ireland", "Norway", "Poland"}
    assert (single["TopCustomerShare"] == 1.0).all()


def test_dependent_flag_follows_threshold(table):
    """Check the dependent flag applies the threshold (12 markets).

    Args:
        table (pandas.DataFrame): ``table`` fixture.

    Returns:
        None.
    """
    expected = table["TopCustomerShare"] >= q2_concentration.DEPENDENCE_THRESHOLD
    assert (table["Dependent"] == expected).all()
    assert table["Dependent"].sum() == 12  # LOG D10


def test_riskiest_markets_are_dependent_and_sorted(table):
    """Check the risk table holds only dependent markets, sorted.

    Args:
        table (pandas.DataFrame): ``table`` fixture.

    Returns:
        None.
    """
    risky = q2_concentration.riskiest_markets(table)
    assert risky["Dependent"].all()
    assert risky["RevenueAtRisk"].is_monotonic_decreasing
