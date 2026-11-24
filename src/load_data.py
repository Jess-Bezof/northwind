"""Load and clean the Northwind workbook and build the order-line table.

Also defines the project paths for the raw data and generated outputs.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "Northwind Database.xlsx"
FIGURES_DIR = ROOT / "outputs" / "figures"
TABLES_DIR = ROOT / "outputs" / "tables"

SHEETS = {
    "categories": "Categories",
    "customers": "Customers",
    "employees": "Employees",
    "order_details": "Orders Details",
    "orders": "Orders",
    "shippers": "Shippers",
    "products": "Product",
    "suppliers": "Suppliers",
}

# Leftover derived columns from earlier homework; not part of the source data.
PRODUCT_DROP_PREFIXES = ("Cheap", "NewPrice", "IsCheap")


def _clean(df):
    """Drop blank and unnamed columns and blank rows from a sheet.

    Args:
        df (pandas.DataFrame): One sheet as read from the workbook.

    Returns:
        pandas.DataFrame: Cleaned copy with a fresh 0..n-1 index.
    """
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
    return df.dropna(axis=0, how="all").reset_index(drop=True)


def load_tables(path=DATA_PATH):
    """Load all eight Northwind sheets as cleaned DataFrames.

    Drops leftover derived product columns, parses order dates,
    rounds ``Discount`` to 2 dp, and adds ``GrossRevenue``
    (price x quantity) and net ``Revenue`` to the order details.

    Args:
        path (pathlib.Path | str): Northwind Excel workbook.

    Returns:
        dict[str, pandas.DataFrame]: Tables keyed by the ``SHEETS``
            keys (e.g. ``"orders"``, ``"order_details"``).
    """
    raw = pd.read_excel(path, sheet_name=list(SHEETS.values()))
    tables = {key: _clean(raw[sheet]) for key, sheet in SHEETS.items()}

    products = tables["products"]
    keep = [
        c for c in products.columns
        if not str(c).startswith(PRODUCT_DROP_PREFIXES)
    ]
    tables["products"] = products[keep]

    for col in ("OrderDate", "RequiredDate", "ShippedDate"):
        tables["orders"][col] = pd.to_datetime(tables["orders"][col])

    details = tables["order_details"]
    details["Discount"] = details["Discount"].round(2)
    details["GrossRevenue"] = details["UnitPrice"] * details["Quantity"]
    details["Revenue"] = details["GrossRevenue"] * (1 - details["Discount"])
    return tables


def build_order_lines(tables):
    """Join order lines to orders, customers, staff, and products.

    Adds ``Year`` and ``Month`` of the order date. Checks that the
    joins keep one row per order line and that every key matches.

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``.

    Returns:
        pandas.DataFrame: One row per order line, with net
            ``Revenue``, customer ``Country``, ``Employee`` name,
            ``Office`` country, product, and category columns.

    Raises:
        pandas.errors.MergeError: A lookup table has duplicate keys.
        AssertionError: Joins changed the row count, a key had no
            match, or total revenue changed.
    """
    details = tables["order_details"]
    orders = tables["orders"][[
        "OrderID", "CustomerID", "EmployeeID", "OrderDate", "RequiredDate",
        "ShippedDate", "ShipVia", "Freight", "ShipCountry",
    ]]
    customers = tables["customers"][["CustomerID", "CompanyName", "Country"]]
    customers = customers.rename(columns={"CompanyName": "Customer"})
    employees = tables["employees"].assign(
        Employee=lambda d: d["FirstName"] + " " + d["LastName"],
        Office=lambda d: d["Country"],
    )[["EmployeeID", "Employee", "Title", "Office"]]
    products = tables["products"][
        ["ProductID", "ProductName", "CategoryID", "Discontinued"]
    ]
    categories = tables["categories"][["CategoryID", "CategoryName"]]

    # validate= raises if a lookup table has duplicate keys (which would
    # silently duplicate order lines).
    lines = (
        details
        .merge(orders, on="OrderID", how="left", validate="many_to_one")
        .merge(customers, on="CustomerID", how="left", validate="many_to_one")
        .merge(employees, on="EmployeeID", how="left", validate="many_to_one")
        .merge(products, on="ProductID", how="left", validate="many_to_one")
        .merge(categories, on="CategoryID", how="left", validate="many_to_one")
    )

    # Sanity checks: joins must neither add nor drop rows, and every key must
    # find a match.
    assert len(lines) == len(details), "join changed the number of order lines"
    key_cols = ["OrderDate", "Customer", "Employee", "ProductName", "CategoryName"]
    unmatched = lines[key_cols].isna().sum()
    assert unmatched.sum() == 0, f"unmatched keys:\n{unmatched[unmatched > 0]}"
    assert abs(lines["Revenue"].sum() - details["Revenue"].sum()) < 0.01

    lines["Year"] = lines["OrderDate"].dt.year
    lines["Month"] = lines["OrderDate"].dt.month
    return lines


if __name__ == "__main__":
    tables = load_tables()
    for name, df in tables.items():
        print(f"{name:14s} {df.shape}  {list(df.columns)}")
    lines = build_order_lines(tables)
    print(f"\norder lines: {len(lines)} rows, revenue ${lines['Revenue'].sum():,.2f}")
