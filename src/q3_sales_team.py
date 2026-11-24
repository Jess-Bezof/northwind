"""Q3: whether top sales reps win more orders or bigger orders.

Writes the rep scatter and two CSV tables to ``outputs/``.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

from load_data import FIGURES_DIR, TABLES_DIR, build_order_lines, load_tables

# Only sales representatives are compared; managers and the inside sales
# coordinator have different roles (LOG D10).
REP_TITLE = "Sales Representative"
OFFICE_COLORS = {"USA": "#3182bd", "UK": "#e6550d"}
# Label offsets (points) for reps whose bubbles sit close together.
LABEL_OFFSETS = {"Janet Leverling": (6, 14), "Nancy Davolio": (-20, -34)}


def employee_summary(lines, employees):
    """Summarise orders and revenue for every employee.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.
        employees (pandas.DataFrame): Cleaned ``employees`` table
            from ``load_tables``.

    Returns:
        pandas.DataFrame: Indexed by employee name, sorted by
            ``Revenue`` descending, with ``Orders``, ``Revenue``,
            ``AvgOrderValue`` (USD per order), ``Title``, ``Office``,
            ``HireDate``, and ``ShareOfCompanyRevenue`` (fraction).

    Raises:
        AssertionError: Employee totals don't match total revenue or
            the number of orders.
    """
    orders = lines.groupby(["OrderID", "Employee"], as_index=False)["Revenue"].sum()
    table = orders.groupby("Employee").agg(Orders=("OrderID", "size"), Revenue=("Revenue", "sum"))
    table["AvgOrderValue"] = table["Revenue"] / table["Orders"]

    info = employees.assign(Employee=employees["FirstName"] + " " + employees["LastName"])
    info = info.set_index("Employee")[["Title", "Country", "HireDate"]]
    table = table.join(info.rename(columns={"Country": "Office"}))
    table["ShareOfCompanyRevenue"] = table["Revenue"] / table["Revenue"].sum()

    assert abs(table["Revenue"].sum() - lines["Revenue"].sum()) < 0.01
    assert table["Orders"].sum() == lines["OrderID"].nunique()
    return table.sort_values("Revenue", ascending=False)


def rep_summary(table):
    """Keep sales reps and compare each with the rep-team average.

    Args:
        table (pandas.DataFrame): Output of ``employee_summary``.

    Returns:
        pandas.DataFrame: Copy of the sales-rep rows plus
            ``OrdersVsTeam`` (vs mean orders per rep) and
            ``AvgOrderValueVsTeam`` (vs total rep revenue / total
            rep orders); 1.0 equals the team level.
    """
    reps = table[table["Title"] == REP_TITLE].copy()
    team_orders = reps["Orders"].mean()
    team_aov = reps["Revenue"].sum() / reps["Orders"].sum()
    # Each rep vs the rep-team average: 1.20 means 20% above average.
    reps["OrdersVsTeam"] = reps["Orders"] / team_orders
    reps["AvgOrderValueVsTeam"] = reps["AvgOrderValue"] / team_aov
    return reps


def driver_summary(reps):
    """Compare how orders and order size line up with rep revenue.

    Args:
        reps (pandas.DataFrame): Output of ``rep_summary``.

    Returns:
        dict[str, int | float | str]: ``Reps`` (count);
            ``RevenueSpread``, ``OrdersSpread``,
            ``AvgOrderValueSpread`` (max / min); and rank checks
            (1 = highest): ``OrdersRankMatchesRevenueRank`` (count),
            ``OrdersRankMismatchReps`` (comma-separated names),
            ``BiggestOrdersRep`` with its
            ``BiggestOrdersRepRevenueRank``, and ``TopEarner`` with
            its ``TopEarnerOrderSizeRank``.
    """
    # Whole-team view (LOG D20, D29): how widely each driver varies across
    # reps (max / min), and whether reps rank in the same order on a driver
    # as on revenue. With only six reps, ranks are compared directly rather
    # than summarised as a correlation coefficient.
    def spread(col):
        """Return the max-to-min ratio of a rep column.

        Args:
            col (str): Column of ``reps`` to measure.

        Returns:
            float: Largest value divided by smallest.
        """
        return reps[col].max() / reps[col].min()

    # Rank 1 = highest value.
    revenue_rank = reps["Revenue"].rank(ascending=False, method="min").astype(int)
    orders_rank = reps["Orders"].rank(ascending=False, method="min").astype(int)
    aov_rank = reps["AvgOrderValue"].rank(ascending=False, method="min").astype(int)
    biggest_orders = reps["AvgOrderValue"].idxmax()
    top_earner = reps["Revenue"].idxmax()

    return {
        "Reps": len(reps),
        "RevenueSpread": spread("Revenue"),
        "OrdersSpread": spread("Orders"),
        "AvgOrderValueSpread": spread("AvgOrderValue"),
        "OrdersRankMatchesRevenueRank": int((orders_rank == revenue_rank).sum()),
        "OrdersRankMismatchReps": ", ".join(sorted(revenue_rank.index[orders_rank != revenue_rank])),
        "BiggestOrdersRep": biggest_orders,
        "BiggestOrdersRepRevenueRank": int(revenue_rank[biggest_orders]),
        "TopEarner": top_earner,
        "TopEarnerOrderSizeRank": int(aov_rank[top_earner]),
    }


def plot_reps(reps, path):
    """Draw orders against average order value for each sales rep.

    Args:
        reps (pandas.DataFrame): Output of ``rep_summary``.
        path (pathlib.Path): Destination PNG; overwritten if present.

    Returns:
        None. Saves the chart to ``path``.
    """
    fig, ax = plt.subplots(figsize=(9, 6))

    # Dotted curves of equal total revenue (orders x average order value).
    x = np.linspace(reps["Orders"].min() * 0.8, reps["Orders"].max() * 1.15, 200)
    for level in (100_000, 150_000, 200_000, 250_000):
        ax.plot(x, level / x, color="gray", lw=0.8, ls=":", zorder=0)
        ax.annotate(f"${level / 1000:.0f}k total", (x[-1], level / x[-1]), fontsize=8,
                    color="gray", xytext=(3, 0), textcoords="offset points", va="center")

    for office, group in reps.groupby("Office"):
        ax.scatter(group["Orders"], group["AvgOrderValue"], s=group["Revenue"] / 400,
                   color=OFFICE_COLORS.get(office, "gray"), alpha=0.8, edgecolor="white",
                   label=f"{office} office", zorder=2)
    for name, row in reps.iterrows():
        ax.annotate(f"{name}\n${row['Revenue'] / 1000:,.0f}k", (row["Orders"], row["AvgOrderValue"]),
                    textcoords="offset points", xytext=LABEL_OFFSETS.get(name, (10, -4)),
                    fontsize=8, zorder=3)

    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.set_ylim(0, reps["AvgOrderValue"].max() * 1.35)
    ax.set_xlim(0, reps["Orders"].max() * 1.3)
    ax.set_xlabel("Number of orders, Jul 1996 – May 1998")
    ax.set_ylabel("Average order value (USD, net of discounts)")
    ax.set_title("Sales representatives: more orders or bigger orders?\n"
                 "Bubble size = total revenue; dotted curves = equal total revenue")
    ax.legend(loc="lower right", frameon=True, markerscale=0.4)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(tables=None):
    """Run the Q3 analysis and write its chart and tables.

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

    everyone = employee_summary(lines, tables["employees"])
    reps = rep_summary(everyone)
    drivers = driver_summary(reps)

    plot_reps(reps, FIGURES_DIR / "q3_employee_scatter.png")
    out = reps.copy()
    out["HireDate"] = out["HireDate"].dt.date
    out.round(4).to_csv(TABLES_DIR / "q3_employee_summary.csv")
    rounded = {k: round(v, 4) if isinstance(v, float) else v for k, v in drivers.items()}
    pd.Series(rounded).to_csv(TABLES_DIR / "q3_drivers.csv", header=["Value"])

    excluded = everyone[everyone["Title"] != REP_TITLE]
    print(f"Q3 | {len(reps)} sales reps compared; excluded {', '.join(excluded.index)} "
          f"({excluded['ShareOfCompanyRevenue'].sum():.0%} of revenue)")
    print(f"Q3 | Rep revenue ${reps['Revenue'].min():,.0f} to ${reps['Revenue'].max():,.0f}; "
          f"orders {reps['Orders'].min()} to {reps['Orders'].max()}; "
          f"avg order ${reps['AvgOrderValue'].min():,.0f} to ${reps['AvgOrderValue'].max():,.0f}")
    print(f"Q3 | Spread (max/min): revenue {drivers['RevenueSpread']:.1f}x, "
          f"orders {drivers['OrdersSpread']:.1f}x, avg order {drivers['AvgOrderValueSpread']:.1f}x")
    print(f"Q3 | Orders rank = revenue rank for {drivers['OrdersRankMatchesRevenueRank']} of "
          f"{drivers['Reps']} reps (swapped: {drivers['OrdersRankMismatchReps']})")
    print(f"Q3 | Biggest orders: {drivers['BiggestOrdersRep']} (revenue rank "
          f"{drivers['BiggestOrdersRepRevenueRank']}); top earner {drivers['TopEarner']} "
          f"(order-size rank {drivers['TopEarnerOrderSizeRank']})")


if __name__ == "__main__":
    main()
