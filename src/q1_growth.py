"""Q1: which markets and customers drove Jan-Apr 1997->1998 growth.

Writes the country growth chart and two CSV tables to ``outputs/``.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from load_data import FIGURES_DIR, TABLES_DIR, build_order_lines, load_tables

BASE_YEAR, COMPARE_YEAR = 1997, 1998
# 1998 data ends on 6 May, so compare the same full months (Jan-Apr) each year.
MONTHS = [1, 2, 3, 4]
TOP_N_COUNTRIES = 10
TOP_GROWTH_COUNTRIES = 3


def jan_apr_lines(lines):
    """Keep order lines from the comparison months of both years.

    Args:
        lines (pandas.DataFrame): Order lines from
            ``build_order_lines``.

    Returns:
        pandas.DataFrame: Rows dated in ``MONTHS`` of ``BASE_YEAR``
            or ``COMPARE_YEAR``.
    """
    mask = lines["Year"].isin([BASE_YEAR, COMPARE_YEAR]) & lines["Month"].isin(MONTHS)
    return lines[mask]


def growth_by(lines, keys):
    """Compare revenue between the two years for each group.

    Args:
        lines (pandas.DataFrame): Order lines, already limited to the
            comparison period.
        keys (str | list[str]): Column(s) to group by.

    Returns:
        pandas.DataFrame: Indexed by ``keys``, with ``Revenue_<year>``
            for both years, ``Change`` in USD, and ``ChangePct`` as a
            fraction (NaN when base-year revenue is 0).
    """
    table = lines.pivot_table(
        index=keys, columns="Year", values="Revenue", aggfunc="sum", fill_value=0
    )
    table = table.reindex(columns=[BASE_YEAR, COMPARE_YEAR], fill_value=0)
    table.columns = [f"Revenue_{BASE_YEAR}", f"Revenue_{COMPARE_YEAR}"]
    table["Change"] = table.iloc[:, 1] - table.iloc[:, 0]
    # Percentage change is undefined when the base year is zero (new market).
    table["ChangePct"] = (table["Change"] / table.iloc[:, 0]).where(table.iloc[:, 0] > 0)
    return table


def country_growth(lines):
    """Build the Jan-Apr revenue comparison by customer country.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``; the full period is used for
            ``TotalRevenue``.

    Returns:
        pandas.DataFrame: One row per country, sorted by ``Change``
            descending, with the ``growth_by`` columns plus
            ``TotalRevenue``, ``TopByRevenue``, ``Declined``,
            ``InChart``, and ``ShareOfTotalGrowth``.

    Raises:
        AssertionError: Country totals don't add up to the period
            totals.
    """
    period = jan_apr_lines(lines)
    table = growth_by(period, "Country")
    table["TotalRevenue"] = lines.groupby("Country")["Revenue"].sum()
    top = table["TotalRevenue"].nlargest(TOP_N_COUNTRIES).index
    table["TopByRevenue"] = table.index.isin(top)
    table["Declined"] = table["Change"] < 0
    table["InChart"] = table["TopByRevenue"] | table["Declined"]
    table["ShareOfTotalGrowth"] = table["Change"] / table["Change"].sum()

    # Country totals must add up to the overall Jan-Apr totals.
    for year in (BASE_YEAR, COMPARE_YEAR):
        expected = period.loc[period["Year"] == year, "Revenue"].sum()
        assert abs(table[f"Revenue_{year}"].sum() - expected) < 0.01
    return table.sort_values("Change", ascending=False)


def customer_contributors(lines, countries):
    """Break each country's Jan-Apr revenue change down by customer.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.
        countries (list[str]): Countries to break down, in display
            order.

    Returns:
        pandas.DataFrame: One row per customer, with the ``growth_by``
            columns plus ``ShareOfCountryGrowth`` and
            ``ShareOfTotalGrowth`` (fractions of the country's and of
            all countries' net change). Sorted by country order, then
            ``Change`` descending.
    """
    period = jan_apr_lines(lines)
    total_growth = growth_by(period, "Country")["Change"].sum()
    table = growth_by(period[period["Country"].isin(countries)], ["Country", "Customer"])
    table["ShareOfCountryGrowth"] = table["Change"] / table.groupby(level="Country")["Change"].transform("sum")
    table["ShareOfTotalGrowth"] = table["Change"] / total_growth
    table = table.reset_index()
    table["Country"] = pd.Categorical(table["Country"], categories=countries, ordered=True)
    return table.sort_values(["Country", "Change"], ascending=[True, False])


def plot_country_growth(table, path):
    """Draw the grouped bar chart of Jan-Apr revenue by country.

    Args:
        table (pandas.DataFrame): Output of ``country_growth``; only
            rows with ``InChart`` are plotted.
        path (pathlib.Path): Destination PNG; overwritten if present.

    Returns:
        None. Saves the chart to ``path``.
    """
    data = table[table["InChart"]].sort_values("Change", ascending=False)
    x = range(len(data))
    width = 0.4

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar([i - width / 2 for i in x], data[f"Revenue_{BASE_YEAR}"], width,
           label=f"Jan–Apr {BASE_YEAR}", color="#9ecae1")
    ax.bar([i + width / 2 for i in x], data[f"Revenue_{COMPARE_YEAR}"], width,
           label=f"Jan–Apr {COMPARE_YEAR}", color="#3182bd")

    for i, (_, row) in enumerate(data.iterrows()):
        top = max(row[f"Revenue_{BASE_YEAR}"], row[f"Revenue_{COMPARE_YEAR}"])
        color = "#c0392b" if row["Change"] < 0 else "#333333"
        ax.annotate(f"{row['Change'] / 1000:+,.1f}k", (i, top), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=8, color=color)

    labels = [f"{c}*" if d else c for c, d in zip(data.index, data["Declined"])]
    ax.set_xticks(list(x), labels, rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"${v / 1000:,.0f}k"))
    ax.set_ylabel("Revenue, net of discounts (USD)")
    ax.set_xlabel("Customer country (sorted by change in revenue)")
    ax.set_title(f"Revenue by country, Jan–Apr {BASE_YEAR} vs Jan–Apr {COMPARE_YEAR}\n"
                 f"Top {TOP_N_COUNTRIES} countries by total revenue, plus countries that declined (*)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main(tables=None):
    """Run the Q1 analysis and write its chart and tables.

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

    countries = country_growth(lines)
    top_growth = countries.index[:TOP_GROWTH_COUNTRIES].tolist()
    contributors = customer_contributors(lines, top_growth)

    plot_country_growth(countries, FIGURES_DIR / "q1_growth_by_country.png")
    countries.round(4).to_csv(TABLES_DIR / "q1_growth_by_country.csv")
    contributors.round(4).to_csv(TABLES_DIR / "q1_top_customer_contributors.csv", index=False)

    base = countries[f"Revenue_{BASE_YEAR}"].sum()
    comp = countries[f"Revenue_{COMPARE_YEAR}"].sum()
    print(f"Q1 | Jan-Apr revenue: {BASE_YEAR} ${base:,.0f} -> {COMPARE_YEAR} ${comp:,.0f} "
          f"(+${comp - base:,.0f}, {comp / base - 1:+.0%})")
    print(f"Q1 | Top {TOP_GROWTH_COUNTRIES} growth countries: "
          + ", ".join(f"{c} +${v:,.0f} ({s:.0%} of growth)" for c, v, s in
                      zip(top_growth, countries["Change"][:TOP_GROWTH_COUNTRIES],
                          countries["ShareOfTotalGrowth"][:TOP_GROWTH_COUNTRIES])))
    print("Q1 | Decliners: " + ", ".join(
        f"{c} ${v:,.0f}" for c, v in countries.loc[countries["Declined"], "Change"].items()))


if __name__ == "__main__":
    main()
