"""Shared pytest fixtures: project tables and an independent rebuild.

Puts ``src/`` on the import path so tests can import the scripts.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from load_data import DATA_PATH, build_order_lines, load_tables  # noqa: E402


@pytest.fixture(scope="session")
def tables():
    """Load the cleaned Northwind tables once per test session.

    Args:
        None.

    Returns:
        dict[str, pandas.DataFrame]: Output of ``load_tables``.
    """
    return load_tables()


@pytest.fixture(scope="session")
def lines(tables):
    """Build the project's order-line table once per test session.

    Args:
        tables (dict[str, pandas.DataFrame]): ``tables`` fixture.

    Returns:
        pandas.DataFrame: Output of ``build_order_lines``.
    """
    return build_order_lines(tables)


@pytest.fixture(scope="session")
def raw_lines():
    """Rebuild order lines straight from the workbook, without src/.

    Tests compare against this to check the scripts by an
    independent route.

    Args:
        None.

    Returns:
        pandas.DataFrame: One row per order line with ``OrderID``,
            price, quantity, discount, ``CustomerID``, parsed
            ``OrderDate``, customer ``Country``, and net ``Revenue``.
    """
    sheets = pd.read_excel(DATA_PATH, sheet_name=["Orders Details", "Orders", "Customers"])
    details = sheets["Orders Details"][["OrderID", "UnitPrice", "Quantity", "Discount"]]
    orders = sheets["Orders"][["OrderID", "CustomerID", "OrderDate"]]
    customers = sheets["Customers"][["CustomerID", "Country"]]
    df = details.dropna(subset=["OrderID"]).merge(orders, on="OrderID").merge(customers, on="CustomerID")
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["Revenue"] = df["UnitPrice"] * df["Quantity"] * (1 - df["Discount"].round(2))
    return df
