"""Q4: stock-out risk and whether reorder levels match demand.

Writes the reorder-vs-demand chart and two CSV tables to ``outputs/``.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from load_data import FIGURES_DIR, TABLES_DIR, build_order_lines, load_tables

# Demand window: the latest full months (LOG D10). 1998 data ends on 6 May.
DEMAND_YEAR = 1998
DEMAND_MONTHS = [1, 2, 3, 4]
COVER_THRESHOLD_MONTHS = 1.0  # less than this = at risk of stocking out
LOWEST_COVER_ROWS = 10
JITTER_SEED = 0  # fixed seed so the chart is reproducible


def reorder_status(row):
    """Classify one product under the reorder rule.

    Args:
        row (pandas.Series): Product with ``UnitsInStock``,
            ``ReorderLevel``, and ``UnitsOnOrder``.

    Returns:
        str: ``"OK"`` (stock above reorder level), ``"Restock
            coming"`` (at or below, units on order), or ``"Missed
            reorder"`` (at or below, nothing on order).
    """
    # The reorder rule: at or below the reorder level means "buy more".
    if row["UnitsInStock"] > row["ReorderLevel"]:
        return "OK"
    if row["UnitsOnOrder"] > 0:
        return "Restock coming"
    return "Missed reorder"


def monthly_demand(lines):
    """Compute average units sold per month in the demand window.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.

    Returns:
        pandas.Series: Units per month, indexed by ``ProductID``;
            products with no sales in the window are absent.
    """
    window = lines[(lines["Year"] == DEMAND_YEAR) & lines["Month"].isin(DEMAND_MONTHS)]
    return window.groupby("ProductID")["Quantity"].sum() / len(DEMAND_MONTHS)


def inventory_table(tables, lines):
    """Build the stock, demand, and cover table for active products.

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``; uses ``products`` and ``categories``.
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.

    Returns:
        pandas.DataFrame: One row per active product, sorted by
            ``MonthsOfCover`` ascending (blanks last), with stock
            fields, ``Status``, ``MonthlyDemand`` (units/month),
            ``StockPosition`` (units), ``MonthsOfCover`` (NaN when
            there were no sales), ``AtRisk``, and
            ``ReorderLevelZero``.
    """
    products = tables["products"].merge(
        tables["categories"][["CategoryID", "CategoryName"]], on="CategoryID", how="left"
    )
    active = products[~products["Discontinued"]].copy()

    active["Status"] = active.apply(reorder_status, axis=1)
    active["MonthlyDemand"] = active["ProductID"].map(monthly_demand(lines)).fillna(0)
    active["StockPosition"] = active["UnitsInStock"] + active["UnitsOnOrder"]
    # Products with no sales in the window have no meaningful cover (left blank).
    active["MonthsOfCover"] = (active["StockPosition"] / active["MonthlyDemand"]).where(
        active["MonthlyDemand"] > 0
    )
    active["AtRisk"] = active["MonthsOfCover"] < COVER_THRESHOLD_MONTHS
    active["ReorderLevelZero"] = active["ReorderLevel"] == 0

    cols = ["ProductID", "ProductName", "CategoryName", "UnitsInStock", "UnitsOnOrder",
            "ReorderLevel", "Status", "MonthlyDemand", "StockPosition", "MonthsOfCover",
            "AtRisk", "ReorderLevelZero"]
    return active[cols].sort_values("MonthsOfCover").reset_index(drop=True)


def policy_summary(table):
    """Count reorder statuses and stock-out risk across products.

    Args:
        table (pandas.DataFrame): Output of ``inventory_table``.

    Returns:
        dict[str, float]: Product counts by status, at risk, at
            risk but passing the rule, reorder level 0, and no
            recent sales; plus ``RankCorrReorderLevelDemand``
            (Spearman) and ``MedianMonthsOfCover`` (products with
            sales only).
    """
    at_risk = table[table["AtRisk"]]
    return {
        "ActiveProducts": len(table),
        "StatusOK": int((table["Status"] == "OK").sum()),
        "StatusRestockComing": int((table["Status"] == "Restock coming").sum()),
        "StatusMissedReorder": int((table["Status"] == "Missed reorder").sum()),
        "NoRecentSales": int((table["MonthlyDemand"] == 0).sum()),
        "AtRisk": len(at_risk),
        "AtRiskButRulePasses": int((at_risk["Status"] != "Missed reorder").sum()),
        "ReorderLevelZero": int(table["ReorderLevelZero"].sum()),
        "AtRiskWithReorderLevelZero": int(at_risk["ReorderLevelZero"].sum()),
        "RankCorrReorderLevelDemand": table["ReorderLevel"].corr(table["MonthlyDemand"],
                                                                  method="spearman"),
        "MedianMonthsOfCover": table["MonthsOfCover"].median(),
    }


def plot_reorder_vs_demand(table, path):
    """Draw reorder level against monthly demand, coloured by risk.

    Args:
        table (pandas.DataFrame): Output of ``inventory_table``.
        path (pathlib.Path): Destination PNG; overwritten if present.

    Returns:
        None. Saves the chart to ``path``.
    """
    rng = np.random.default_rng(JITTER_SEED)
    # Reorder levels are multiples of 5, so points overlap; spread them a little.
    x = table["ReorderLevel"] + rng.uniform(-1.2, 1.2, len(table))

    fig, ax = plt.subplots(figsize=(10, 6))
    risk = table["AtRisk"]
    no_sales = table["MonthlyDemand"] == 0
    ok = ~risk & ~no_sales
    ax.scatter(x[ok], table.loc[ok, "MonthlyDemand"], color="#3182bd", alpha=0.75,
               edgecolor="white", s=55, label=f"≥ {COVER_THRESHOLD_MONTHS:.0f} month of cover")
    ax.scatter(x[risk], table.loc[risk, "MonthlyDemand"], color="#c0392b", alpha=0.85,
               edgecolor="white", s=55, label=f"< {COVER_THRESHOLD_MONTHS:.0f} month of cover (at risk)")
    ax.scatter(x[no_sales], table.loc[no_sales, "MonthlyDemand"], color="#999999", alpha=0.85,
               edgecolor="white", s=55, label=f"No sales Jan–Apr {DEMAND_YEAR}")

    # Name the fastest sellers that never trigger a reorder; alternate the
    # label offsets so labels of products with similar demand don't overlap.
    fastest_zero = table[table["ReorderLevelZero"]].nlargest(4, "MonthlyDemand").index
    for k, i in enumerate(fastest_zero):
        ax.annotate(table.loc[i, "ProductName"], (x[i], table.loc[i, "MonthlyDemand"]),
                    textcoords="offset points", xytext=(8, 6 if k % 2 == 0 else -8),
                    fontsize=8, va="center")

    ax.axvspan(-2.5, 2.5, color="#fdecea", zorder=0)
    ax.text(0, ax.get_ylim()[1] * 0.98, "Reorder level 0:\nnever triggers a reorder",
            ha="center", va="top", fontsize=8, color="#c0392b")
    ax.set_xticks(sorted(table["ReorderLevel"].unique()))
    ax.set_xlim(-3, table["ReorderLevel"].max() + 4)
    ax.set_xlabel("Reorder level (units)")
    ax.set_ylabel(f"Average units sold per month, Jan–Apr {DEMAND_YEAR}")
    ax.set_title("Reorder levels vs actual demand (69 active products)\n"
                 "Reorder levels are not set in line with how fast products sell")
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(tables=None):
    """Run the Q4 analysis and write its chart and tables.

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

    table = inventory_table(tables, lines)
    summary = policy_summary(table)

    plot_reorder_vs_demand(table, FIGURES_DIR / "q4_reorder_vs_demand.png")
    table.head(LOWEST_COVER_ROWS).round(2).to_csv(TABLES_DIR / "q4_lowest_cover.csv", index=False)
    table.round(4).to_csv(TABLES_DIR / "q4_inventory_all_active.csv", index=False)

    s = summary
    print(f"Q4 | {s['ActiveProducts']} active products: {s['StatusOK']} OK, "
          f"{s['StatusRestockComing']} restock coming, {s['StatusMissedReorder']} missed reorder")
    print(f"Q4 | {s['AtRisk']} at risk (< {COVER_THRESHOLD_MONTHS:.0f} month of cover incl. on order); "
          f"{s['AtRiskButRulePasses']} of them pass the reorder rule; "
          f"{s['NoRecentSales']} had no sales Jan-Apr {DEMAND_YEAR}")
    print(f"Q4 | Reorder level 0: {s['ReorderLevelZero']} products ({s['AtRiskWithReorderLevelZero']} at risk); "
          f"rank corr(reorder level, demand) = {s['RankCorrReorderLevelDemand']:.2f}; "
          f"median cover {s['MedianMonthsOfCover']:.1f} months")


if __name__ == "__main__":
    main()
