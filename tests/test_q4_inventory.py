"""Tests for Q4: stock-out risk and reorder levels vs demand."""
import numpy as np
import pandas as pd
import pytest

import q4_inventory
from load_data import DATA_PATH

# Hand-checked values: Camembert Pierrot (ProductID 60), confirmed by the
# student in Excel on 2026-11-24: stock 19, on order 0, reorder level 0 (Product sheet), and
# 540 units sold on orders dated Jan-Apr 1998 (Orders + Orders Details).
CAMEMBERT_ID = 60
CAMEMBERT_UNITS_JAN_APR_1998 = 540
CAMEMBERT_STOCK = 19


@pytest.fixture(scope="module")
def table(tables, lines):
    """Compute the Q4 inventory table once per test module.

    Args:
        tables (dict[str, pandas.DataFrame]): ``tables`` fixture.
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        pandas.DataFrame: Output of
            ``q4_inventory.inventory_table``.
    """
    return q4_inventory.inventory_table(tables, lines)


@pytest.fixture(scope="module")
def summary(table):
    """Compute the Q4 policy summary once per test module.

    Args:
        table (pandas.DataFrame): ``table`` fixture.

    Returns:
        dict[str, float]: Output of
            ``q4_inventory.policy_summary``.
    """
    return q4_inventory.policy_summary(table)


@pytest.fixture(scope="module")
def raw():
    """Rebuild Jan-Apr 1998 unit sales and products from Excel.

    Args:
        None.

    Returns:
        dict[str, pandas.Series | pandas.DataFrame]:
            ``"units_jan_apr_1998"`` (units sold, indexed by
            ``ProductID``) and ``"products"`` (raw Product sheet).
    """
    sheets = pd.read_excel(DATA_PATH, sheet_name=["Orders Details", "Orders", "Product"])
    details = sheets["Orders Details"].dropna(subset=["OrderID"])
    orders = sheets["Orders"][["OrderID", "OrderDate"]].assign(
        OrderDate=lambda d: pd.to_datetime(d["OrderDate"]))
    sold = details.merge(orders, on="OrderID")
    window = sold[(sold["OrderDate"] >= "1998-01-01") & (sold["OrderDate"] < "1998-05-01")]
    products = sheets["Product"].dropna(subset=["ProductID"])
    products = products.loc[:, ~products.columns.duplicated()]
    return {
        "units_jan_apr_1998": window.groupby("ProductID")["Quantity"].sum(),
        "products": products,
    }


def test_monthly_demand_matches_independent_calculation(table, raw):
    """Check every product's monthly demand against the rebuild.

    Args:
        table (pandas.DataFrame): ``table`` fixture.
        raw (dict[str, pandas.Series | pandas.DataFrame]): ``raw``
            fixture.

    Returns:
        None.
    """
    expected = raw["units_jan_apr_1998"].reindex(table["ProductID"]).fillna(0).values / 4
    assert table["MonthlyDemand"].values == pytest.approx(expected)


def test_camembert_matches_hand_checked_values(table):
    """Check Camembert Pierrot's demand, stock, and cover.

    Args:
        table (pandas.DataFrame): ``table`` fixture.

    Returns:
        None.
    """
    row = table.set_index("ProductID").loc[CAMEMBERT_ID]
    assert row["MonthlyDemand"] * 4 == CAMEMBERT_UNITS_JAN_APR_1998
    assert row["UnitsInStock"] == CAMEMBERT_STOCK
    assert row["MonthsOfCover"] == pytest.approx(19 / 135)


def test_only_active_products_are_included(table, raw):
    """Check the table holds exactly the 69 non-discontinued products.

    Args:
        table (pandas.DataFrame): ``table`` fixture.
        raw (dict[str, pandas.Series | pandas.DataFrame]): ``raw``
            fixture.

    Returns:
        None.
    """
    p = raw["products"]
    active_ids = set(p.loc[~p["Discontinued"].astype(bool), "ProductID"])
    assert set(table["ProductID"]) == active_ids
    assert len(table) == 69


def test_reorder_rule_statuses(table, summary):
    """Check status counts and that each status matches the rule.

    Args:
        table (pandas.DataFrame): ``table`` fixture.
        summary (dict[str, float]): ``summary`` fixture.

    Returns:
        None.
    """
    assert (summary["StatusOK"], summary["StatusRestockComing"], summary["StatusMissedReorder"]) == (51, 17, 1)
    missed = table[table["Status"] == "Missed reorder"]
    assert missed["ProductName"].tolist() == ["Nord-Ost Matjeshering"]
    ok = table["Status"] == "OK"
    assert (table.loc[ok, "UnitsInStock"] > table.loc[ok, "ReorderLevel"]).all()
    assert (table.loc[~ok, "UnitsInStock"] <= table.loc[~ok, "ReorderLevel"]).all()


def test_cover_and_risk_flag_follow_definitions(table):
    """Check months of cover and the at-risk flag by definition.

    Args:
        table (pandas.DataFrame): ``table`` fixture.

    Returns:
        None.
    """
    sold = table["MonthlyDemand"] > 0
    expected = (table["UnitsInStock"] + table["UnitsOnOrder"]) / table["MonthlyDemand"]
    assert table.loc[sold, "MonthsOfCover"].values == pytest.approx(expected[sold].values)
    assert table.loc[~sold, "MonthsOfCover"].isna().all()  # no sales -> blank, not infinite
    assert not np.isinf(table["MonthsOfCover"]).any()
    assert (table["AtRisk"] == (table["MonthsOfCover"] < 1)).all()  # LOG D10


def test_policy_summary_counts(summary):
    """Check the headline counts and the near-zero rank correlation.

    Args:
        summary (dict[str, float]): ``summary`` fixture.

    Returns:
        None.
    """
    assert summary["ActiveProducts"] == 69
    assert summary["AtRisk"] == 30
    assert summary["AtRiskButRulePasses"] == 29
    assert summary["ReorderLevelZero"] == 16
    assert summary["NoRecentSales"] == 3
    assert abs(summary["RankCorrReorderLevelDemand"]) < 0.1
