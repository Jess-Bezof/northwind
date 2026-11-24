"""Tests for Q3: sales reps' order counts and order sizes."""
import pandas as pd
import pytest

import q3_sales_team
from load_data import DATA_PATH

# Hand-checked values: Margaret Peacock's order count and revenue,
# confirmed by the student in Excel on 2026-11-24 (filter Orders to
# EmployeeID 4, count orders, apply the revenue formula to their lines).
PEACOCK_ORDERS = 156
PEACOCK_REVENUE = 232_890.85

EXPECTED_REPS = {"Nancy Davolio", "Janet Leverling", "Margaret Peacock",
                 "Michael Suyama", "Robert King", "Anne Dodsworth"}


@pytest.fixture(scope="module")
def everyone(lines, tables):
    """Compute the all-employee summary once per test module.

    Args:
        lines (pandas.DataFrame): ``lines`` fixture.
        tables (dict[str, pandas.DataFrame]): ``tables`` fixture.

    Returns:
        pandas.DataFrame: Output of
            ``q3_sales_team.employee_summary``.
    """
    return q3_sales_team.employee_summary(lines, tables["employees"])


@pytest.fixture(scope="module")
def reps(everyone):
    """Compute the sales-rep summary once per test module.

    Args:
        everyone (pandas.DataFrame): ``everyone`` fixture.

    Returns:
        pandas.DataFrame: Output of ``q3_sales_team.rep_summary``.
    """
    return q3_sales_team.rep_summary(everyone)


@pytest.fixture(scope="module")
def raw_by_employee():
    """Rebuild orders and revenue per employee straight from Excel.

    Args:
        None.

    Returns:
        pandas.DataFrame: Indexed by employee full name, with
            ``Orders`` (distinct order IDs) and net ``Revenue``.
    """
    sheets = pd.read_excel(DATA_PATH, sheet_name=["Orders Details", "Orders", "Employees"])
    d = sheets["Orders Details"].dropna(subset=["OrderID"])
    d = d.assign(Revenue=d["UnitPrice"] * d["Quantity"] * (1 - d["Discount"].round(2)))
    d = d.merge(sheets["Orders"][["OrderID", "EmployeeID"]], on="OrderID")
    emp = sheets["Employees"].dropna(subset=["EmployeeID"])
    names = (emp["FirstName"] + " " + emp["LastName"]).set_axis(emp["EmployeeID"])
    out = d.groupby("EmployeeID").agg(Orders=("OrderID", "nunique"), Revenue=("Revenue", "sum"))
    return out.set_axis(out.index.map(names))


def test_matches_independent_calculation_for_every_employee(everyone, raw_by_employee):
    """Check every employee's orders and revenue against the rebuild.

    Args:
        everyone (pandas.DataFrame): ``everyone`` fixture.
        raw_by_employee (pandas.DataFrame): ``raw_by_employee``
            fixture.

    Returns:
        None.
    """
    assert set(everyone.index) == set(raw_by_employee.index)
    for name, row in raw_by_employee.iterrows():
        assert everyone.loc[name, "Orders"] == row["Orders"]
        assert everyone.loc[name, "Revenue"] == pytest.approx(row["Revenue"], abs=0.01)


def test_peacock_matches_hand_checked_values(everyone):
    """Check Margaret Peacock's orders and revenue against hand checks.

    Args:
        everyone (pandas.DataFrame): ``everyone`` fixture.

    Returns:
        None.
    """
    assert everyone.loc["Margaret Peacock", "Orders"] == PEACOCK_ORDERS
    assert everyone.loc["Margaret Peacock", "Revenue"] == pytest.approx(PEACOCK_REVENUE, abs=0.01)


def test_only_the_six_sales_reps_are_compared(reps, everyone):
    """Check only the six reps are kept and the excluded share is ~29%.

    Args:
        reps (pandas.DataFrame): ``reps`` fixture.
        everyone (pandas.DataFrame): ``everyone`` fixture.

    Returns:
        None.
    """
    assert set(reps.index) == EXPECTED_REPS  # LOG D10
    assert (reps["Title"] == "Sales Representative").all()
    excluded = everyone.drop(reps.index)
    assert set(excluded.index) == {"Andrew Fuller", "Steven Buchanan", "Laura Callahan"}
    assert excluded["ShareOfCompanyRevenue"].sum() == pytest.approx(0.286, abs=0.005)


def test_revenue_equals_orders_times_average_order_value(reps):
    """Check revenue equals orders times average order value.

    Args:
        reps (pandas.DataFrame): ``reps`` fixture.

    Returns:
        None.
    """
    assert (reps["Orders"] * reps["AvgOrderValue"]).values == pytest.approx(reps["Revenue"].values)


def test_team_comparisons_are_relative_to_rep_average(reps):
    """Check the vs-team columns average to 1.0 over the reps.

    Args:
        reps (pandas.DataFrame): ``reps`` fixture.

    Returns:
        None.
    """
    assert reps["OrdersVsTeam"].mean() == pytest.approx(1.0)
    weighted_aov = (reps["AvgOrderValueVsTeam"] * reps["Orders"]).sum() / reps["Orders"].sum()
    assert weighted_aov == pytest.approx(1.0)


def test_driver_spreads_match_rep_extremes(reps):
    """Check the spreads equal max / min of the rep columns.

    Args:
        reps (pandas.DataFrame): ``reps`` fixture.

    Returns:
        None.
    """
    d = q3_sales_team.driver_summary(reps)
    assert d["Reps"] == 6
    assert d["OrdersSpread"] == pytest.approx(156 / 43)
    assert d["RevenueSpread"] == pytest.approx(reps["Revenue"].max() / reps["Revenue"].min())
    assert d["AvgOrderValueSpread"] == pytest.approx(
        reps["AvgOrderValue"].max() / reps["AvgOrderValue"].min())


def test_rank_comparison_matches_hand_ranking(reps):
    """Check the rank comparison against ranks written out by hand.

    Args:
        reps (pandas.DataFrame): ``reps`` fixture.

    Returns:
        None.
    """
    # Ranks written out by hand from the rep table (1 = highest):
    #   revenue: Peacock, Leverling, Davolio, King, Dodsworth, Suyama
    #   orders:  Peacock, Leverling, Davolio, King, Suyama, Dodsworth
    #   avg order value: Dodsworth, King, Leverling, Davolio, Peacock, Suyama
    d = q3_sales_team.driver_summary(reps)
    assert d["OrdersRankMatchesRevenueRank"] == 4
    assert d["OrdersRankMismatchReps"] == "Anne Dodsworth, Michael Suyama"
    assert d["BiggestOrdersRep"] == "Anne Dodsworth"
    assert d["BiggestOrdersRepRevenueRank"] == 5
    assert d["TopEarner"] == "Margaret Peacock"
    assert d["TopEarnerOrderSizeRank"] == 5
    assert "RankCorrRevenueOrders" not in d  # LOG D29: correlations dropped
