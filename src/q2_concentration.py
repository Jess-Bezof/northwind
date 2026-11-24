"""Q2: how dependent each market is on its largest customer.

Writes the concentration scatter and two CSV tables to ``outputs/``.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.lines import Line2D

from load_data import FIGURES_DIR, TABLES_DIR, build_order_lines, load_tables

# A market is "dependent" when its largest customer brings in at least this
# share of the country's revenue (LOG D10).
DEPENDENCE_THRESHOLD = 0.50


def concentration_by_country(lines):
    """Measure each country's reliance on its top customer.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``; the full period is used.

    Returns:
        pandas.DataFrame: One row per customer country, sorted by
            ``Revenue`` descending, with ``Customers`` (count with
            orders), ``Revenue``, ``TopCustomer``,
            ``TopCustomerRevenue``, ``TopCustomerShare`` (fraction),
            ``RevenueAtRisk`` (USD), ``Dependent``, and
            ``ShareOfCompanyRevenue`` (fraction).

    Raises:
        AssertionError: Country revenue doesn't add up to the total.
    """
    by_customer = lines.groupby(["Country", "Customer"])["Revenue"].sum()

    table = by_customer.groupby(level="Country").agg(
        Customers="size", Revenue="sum", TopCustomerRevenue="max"
    )
    top_idx = by_customer.groupby(level="Country").idxmax()
    table["TopCustomer"] = top_idx.map(lambda key: key[1])
    table["TopCustomerShare"] = table["TopCustomerRevenue"] / table["Revenue"]
    # Revenue at risk = what the country loses if its top customer leaves.
    table["RevenueAtRisk"] = table["TopCustomerRevenue"]
    table["Dependent"] = table["TopCustomerShare"] >= DEPENDENCE_THRESHOLD
    table["ShareOfCompanyRevenue"] = table["Revenue"] / table["Revenue"].sum()

    assert abs(table["Revenue"].sum() - lines["Revenue"].sum()) < 0.01
    cols = ["Customers", "Revenue", "TopCustomer", "TopCustomerRevenue",
            "TopCustomerShare", "RevenueAtRisk", "Dependent", "ShareOfCompanyRevenue"]
    return table[cols].sort_values("Revenue", ascending=False)


def riskiest_markets(table):
    """Select dependent markets, largest revenue at risk first.

    Args:
        table (pandas.DataFrame): Output of
            ``concentration_by_country``.

    Returns:
        pandas.DataFrame: Rows where ``Dependent`` is True, sorted by
            ``RevenueAtRisk`` descending.
    """
    return table[table["Dependent"]].sort_values("RevenueAtRisk", ascending=False)


def plot_concentration(table, path):
    """Draw country revenue against top-customer share.

    Args:
        table (pandas.DataFrame): Output of
            ``concentration_by_country``; all rows are plotted.
        path (pathlib.Path): Destination PNG; overwritten if present.

    Returns:
        None. Saves the chart to ``path``.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axhspan(DEPENDENCE_THRESHOLD, 1.05, color="#fdecea", zorder=0)
    ax.axhline(DEPENDENCE_THRESHOLD, color="#c0392b", lw=1, ls="--", zorder=1)
    legend = [
        Line2D([], [], marker="o", ls="", color="#c0392b",
               label=f"Dependent (top customer ≥ {DEPENDENCE_THRESHOLD:.0%})"),
        Line2D([], [], marker="o", ls="", color="#3182bd", label="Not dependent"),
        Line2D([], [], color="#c0392b", ls="--", lw=1,
               label=f"{DEPENDENCE_THRESHOLD:.0%} threshold"),
    ]
    ax.legend(handles=legend, loc="lower left", frameon=True, fontsize=9)

    colors = table["Dependent"].map({True: "#c0392b", False: "#3182bd"})
    ax.scatter(table["Revenue"], table["TopCustomerShare"], s=table["Customers"] * 25 + 20,
               c=colors, alpha=0.8, edgecolor="white", zorder=2)
    for country, row in table.iterrows():
        ax.annotate(f"{country} ({row['Customers']})", (row["Revenue"], row["TopCustomerShare"]),
                    textcoords="offset points", xytext=(6, -3), fontsize=8, zorder=3)

    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v / 1000:,.0f}k"))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Country revenue, Jul 1996 – May 1998 (USD, net of discounts; log scale)")
    ax.set_ylabel("Top customer's share of country revenue")
    ax.set_title("How dependent is each market on its largest customer?\n"
                 "Bubble size and (n) = number of customers in the country")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(tables=None):
    """Run the Q2 analysis and write its chart and tables.

    Args:
        tables (dict[str, pandas.DataFrame] | None): Output of
            ``load_tables``; loaded from the workbook if None.

    Returns:
        None. Writes files to ``outputs/`` and prints key numbers.
    """
    tables = tables if tables is not None else load_tables()
    lines = build_order_lines(tables)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    table = concentration_by_country(lines)
    risky = riskiest_markets(table)

    plot_concentration(table, FIGURES_DIR / "q2_concentration_scatter.png")
    table.round(4).to_csv(TABLES_DIR / "q2_concentration_by_country.csv")
    risky.round(4).to_csv(TABLES_DIR / "q2_riskiest_markets.csv")

    print(f"Q2 | {len(table)} countries, {table['Customers'].sum()} customers with orders")
    print(f"Q2 | {len(risky)} dependent markets (top customer >= {DEPENDENCE_THRESHOLD:.0%}), "
          f"together {risky['Revenue'].sum() / table['Revenue'].sum():.0%} of company revenue; "
          f"revenue at risk ${risky['RevenueAtRisk'].sum():,.0f}")
    for country, row in risky.head(5).iterrows():
        print(f"Q2 |   {country}: {row['TopCustomer']} = {row['TopCustomerShare']:.0%} "
              f"of ${row['Revenue']:,.0f} (customers: {row['Customers']})")


if __name__ == "__main__":
    main()
