"""Tests for Q1: Jan-Apr revenue growth by country and customer."""
import numpy as np
import pytest

import q1_growth

# Hand-checked values: Denmark's Jan-Apr net revenue, confirmed by the
# student in Excel on 2026-11-24 (filter Orders to Danish customers, Jan-Apr,
# apply the revenue formula to their order lines).
DENMARK_1997 = 13_706.40
DENMARK_1998 = 4_284.00


@pytest.fixture(scope="module")
def countries(lines):
    """Compute the Q1 country table once per test module.

    Args:
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        pandas.DataFrame: Output of ``q1_growth.country_growth``.
    """
    return q1_growth.country_growth(lines)


def raw_jan_apr(raw_lines, year, country=None):
    """Sum independent Jan-Apr revenue for one year.

    Args:
        raw_lines (pandas.DataFrame): ``raw_lines`` fixture.
        year (int): Calendar year of the order date.
        country (str | None): Customer country; None for all.

    Returns:
        float: Net revenue in USD.
    """
    d = raw_lines[(raw_lines["OrderDate"].dt.year == year) & (raw_lines["OrderDate"].dt.month <= 4)]
    if country:
        d = d[d["Country"] == country]
    return d["Revenue"].sum()


def test_period_filter_keeps_only_jan_apr_of_both_years(lines):
    """Check the period filter keeps only Jan-Apr of 1997 and 1998.

    Args:
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        None.
    """
    period = q1_growth.jan_apr_lines(lines)
    assert set(period["Year"]) == {1997, 1998}
    assert set(period["Month"]) == {1, 2, 3, 4}


def test_yearly_totals_match_independent_calculation(countries, raw_lines):
    """Check yearly Jan-Apr totals against the independent rebuild.

    Args:
        countries (pandas.DataFrame): ``countries`` fixture.
        raw_lines (pandas.DataFrame): ``raw_lines`` fixture.

    Returns:
        None.
    """
    for year in (1997, 1998):
        assert countries[f"Revenue_{year}"].sum() == pytest.approx(raw_jan_apr(raw_lines, year), abs=0.01)


def test_denmark_matches_independent_and_hand_checked_values(countries, raw_lines):
    """Check Denmark against the rebuild and the hand-checked values.

    Args:
        countries (pandas.DataFrame): ``countries`` fixture.
        raw_lines (pandas.DataFrame): ``raw_lines`` fixture.

    Returns:
        None.
    """
    dk = countries.loc["Denmark"]
    assert dk["Revenue_1997"] == pytest.approx(raw_jan_apr(raw_lines, 1997, "Denmark"), abs=0.01)
    assert dk["Revenue_1998"] == pytest.approx(raw_jan_apr(raw_lines, 1998, "Denmark"), abs=0.01)
    assert dk["Revenue_1997"] == pytest.approx(DENMARK_1997, abs=0.01)
    assert dk["Revenue_1998"] == pytest.approx(DENMARK_1998, abs=0.01)


def test_country_changes_add_up_to_total_growth(countries):
    """Check country changes and growth shares reconcile to the total.

    Args:
        countries (pandas.DataFrame): ``countries`` fixture.

    Returns:
        None.
    """
    total = countries["Revenue_1998"].sum() - countries["Revenue_1997"].sum()
    assert countries["Change"].sum() == pytest.approx(total, abs=0.01)
    assert countries["ShareOfTotalGrowth"].sum() == pytest.approx(1.0)


def test_chart_shows_top10_by_revenue_plus_decliners(countries, lines):
    """Check the chart holds exactly the top 10 plus decliners.

    Args:
        countries (pandas.DataFrame): ``countries`` fixture.
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        None.
    """
    top10 = set(lines.groupby("Country")["Revenue"].sum().nlargest(10).index)
    decliners = set(countries.index[countries["Change"] < 0])
    in_chart = set(countries.index[countries["InChart"]])
    assert in_chart == top10 | decliners
    assert len(in_chart) == 13
    assert "Belgium" not in in_chart  # LOG D13


def test_new_market_has_blank_percentage_change(countries):
    """Check a zero-base market gets NaN, not inf, percentage change.

    Args:
        countries (pandas.DataFrame): ``countries`` fixture.

    Returns:
        None.
    """
    poland = countries.loc["Poland"]
    assert poland["Revenue_1997"] == 0
    assert np.isnan(poland["ChangePct"])
    assert not np.isinf(countries["ChangePct"]).any()


def test_customer_contributions_add_up_to_country_change(countries, lines):
    """Check customer changes reconcile to each top-3 country's change.

    Args:
        countries (pandas.DataFrame): ``countries`` fixture.
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        None.
    """
    top3 = countries.index[:3].tolist()
    contrib = q1_growth.customer_contributors(lines, top3)
    by_country = contrib.groupby("Country", observed=True)["Change"].sum()
    for country in top3:
        assert by_country[country] == pytest.approx(countries.loc[country, "Change"], abs=0.01)
        shares = contrib.loc[contrib["Country"] == country, "ShareOfCountryGrowth"]
        assert shares.sum() == pytest.approx(1.0)
