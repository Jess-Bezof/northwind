"""Build the project webpage from the analysis results.

Fills ``site/template.html`` with numbers, tables, and Plotly charts
and writes ``docs/index.html``.
"""
from string import Template

import numpy as np
import plotly.graph_objects as go
import plotly.offline

import q1_growth
import q2_concentration
import q3_sales_team
import q4_inventory
from load_data import ROOT, build_order_lines, load_tables

TEMPLATE_PATH = ROOT / "site" / "template.html"
OUTPUT_PATH = ROOT / "docs" / "index.html"
REPO_URL = "https://github.com/Jess-Bezof/northwind"

# Same colours as the reviewed matplotlib charts.
LIGHT_BLUE, DARK_BLUE, RED = "#9ecae1", "#3182bd", "#c0392b"
ORANGE, GREY, PINK_BAND = "#e6550d", "#999999", "#fdecea"
CHART_CONFIG = {"displayModeBar": False, "responsive": True}
FONT = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"


# ---------- number formatting (every number on the page goes through these)

def usd(x):
    """Format an amount as whole US dollars.

    Args:
        x (float): Amount in USD.

    Returns:
        str: E.g. ``$104,875``.
    """
    return f"${x:,.0f}"


def usd_k(x):
    """Format an amount in thousands of dollars, no decimals.

    Args:
        x (float): Amount in USD.

    Returns:
        str: E.g. ``$422k``.
    """
    return f"${x / 1000:,.0f}k"


def usd_k1(x):
    """Format an amount in thousands of dollars, one decimal.

    Args:
        x (float): Amount in USD.

    Returns:
        str: E.g. ``$20.4k``.
    """
    return f"${x / 1000:,.1f}k"


def signed_usd_k1(x):
    """Format a change in thousands of dollars with its sign.

    Args:
        x (float): Change in USD.

    Returns:
        str: E.g. ``+$53.2k`` or ``−$9.4k`` (Unicode minus).
    """
    return f"{'+' if x >= 0 else '−'}${abs(x) / 1000:,.1f}k"


def pct(x):
    """Format a fraction as a whole percentage.

    Args:
        x (float): Fraction, e.g. 0.82.

    Returns:
        str: E.g. ``82%``.
    """
    return f"{x:.0%}"


def signed_pct(x):
    """Format a fractional change as a signed percentage.

    Args:
        x (float): Change as a fraction, e.g. -0.69.

    Returns:
        str: E.g. ``+121%`` or ``−69%`` (Unicode minus).
    """
    return f"{'+' if x >= 0 else '−'}{abs(x):.0%}"


NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve"]


def word(n):
    """Spell out a small whole number.

    Args:
        n (int): Count.

    Returns:
        str: ``zero`` to ``twelve``; digits for any other value.
    """
    return NUMBER_WORDS[n] if 0 <= n < len(NUMBER_WORDS) else str(n)


def ordinal(n):
    """Turn a rank into an ordinal such as ``1st`` or ``22nd``.

    Args:
        n (int): Positive rank.

    Returns:
        str: Rank with its suffix.
    """
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# Country names that need "the" in running text (tables and charts keep raw names).
PROSE_COUNTRY = {"USA": "the USA", "UK": "the UK"}


def prose_list(countries, capitalize=False):
    """Join country names for running text.

    Args:
        countries (Iterable[str]): Country names as in the data.
        capitalize (bool): Capitalise the first letter, for the
            start of a sentence.

    Returns:
        str: E.g. ``The USA, Germany and Brazil``; ``USA`` and
            ``UK`` become ``the USA`` and ``the UK``.
    """
    names = [PROSE_COUNTRY.get(c, c) for c in countries]
    text = names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" and {names[-1]}"
    return text[0].upper() + text[1:] if capitalize else text


def day_month_year(ts):
    """Format a date as day, short month, and year.

    Args:
        ts (pandas.Timestamp): Date.

    Returns:
        str: E.g. ``6 May 1998``.
    """
    return f"{ts.day} {ts:%b %Y}"


def html_table(rows, headers, numeric_cols=()):
    """Build an HTML table inside a horizontally scrollable div.

    Args:
        rows (list[list]): Cell values, already formatted;
            inserted without HTML escaping.
        headers (list[str]): Column headings.
        numeric_cols (Iterable[int]): Zero-based columns to
            right-align.

    Returns:
        str: Table HTML.
    """
    head = "".join(
        f'<th class="num">{h}</th>' if i in numeric_cols else f"<th>{h}</th>"
        for i, h in enumerate(headers)
    )
    body = "".join(
        "<tr>" + "".join(
            f'<td class="num">{v}</td>' if i in numeric_cols else f"<td>{v}</td>"
            for i, v in enumerate(row)
        ) + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def chart_html(fig, div_id, title):
    """Wrap a Plotly figure with an HTML title for the page.

    Args:
        fig (plotly.graph_objects.Figure): Chart to embed.
        div_id (str): HTML id of the chart's div.
        title (str): Chart title, shown as HTML above the
            chart so it wraps on narrow screens.

    Returns:
        str: Title div plus a ``chart`` div holding the chart,
            without plotly.js (the page loads it once).
    """
    # The title is HTML above the chart (not a Plotly title) so it wraps on
    # narrow screens instead of colliding with the legend.
    chart = fig.to_html(full_html=False, include_plotlyjs=False, config=CHART_CONFIG, div_id=div_id)
    return f'<div class="chart-title">{title}</div><div class="chart">{chart}</div>'


def base_layout(fig, height):
    """Apply the shared page style to a chart.

    Args:
        fig (plotly.graph_objects.Figure): Chart; modified in
            place.
        height (int): Chart height in pixels.

    Returns:
        plotly.graph_objects.Figure: The same ``fig``, with no
            title and the legend at the top left.
    """
    fig.update_layout(
        height=height, margin={"l": 70, "r": 20, "t": 40, "b": 60},
        font={"family": FONT, "size": 13}, plot_bgcolor="white", paper_bgcolor="white",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        hoverlabel={"font": {"family": FONT}},
    )
    fig.update_yaxes(gridcolor="#e5e5e5", zerolinecolor="#999")
    return fig


# ---------- Q1

Q1_TABLE_PER_COUNTRY = 2  # customers shown per fast-growing country
Q1_SOLO_DRIVER_SHARE = 0.6  # name one customer alone above this growth share

def q1_chart(countries):
    """Build the interactive Q1 grouped bar chart.

    Args:
        countries (pandas.DataFrame): Output of
            ``q1_growth.country_growth``; rows with ``InChart``
            are plotted.

    Returns:
        plotly.graph_objects.Figure: Jan-Apr revenue by country
            for both years, with change labels.
    """
    data = countries[countries["InChart"]].sort_values("Change", ascending=False)
    labels = [f"{c}*" if d else c for c, d in zip(data.index, data["Declined"])]
    base, comp = f"Revenue_{q1_growth.BASE_YEAR}", f"Revenue_{q1_growth.COMPARE_YEAR}"
    pct_text = [("new market" if p != p else signed_pct(p)) for p in data["ChangePct"]]
    hover = [
        f"<b>{c}</b><br>Jan–Apr {q1_growth.BASE_YEAR}: {usd(b)}<br>"
        f"Jan–Apr {q1_growth.COMPARE_YEAR}: {usd(n)}<br>Change: {signed_usd_k1(ch)} ({p})"
        for c, b, n, ch, p in zip(data.index, data[base], data[comp], data["Change"], pct_text)
    ]

    fig = go.Figure()
    fig.add_bar(x=labels, y=data[base], name=f"Jan–Apr {q1_growth.BASE_YEAR}",
                marker_color=LIGHT_BLUE, hovertext=hover, hoverinfo="text")
    fig.add_bar(x=labels, y=data[comp], name=f"Jan–Apr {q1_growth.COMPARE_YEAR}",
                marker_color=DARK_BLUE, hovertext=hover, hoverinfo="text")
    for label, top, ch in zip(labels, data[[base, comp]].max(axis=1), data["Change"]):
        fig.add_annotation(x=label, y=top, text=signed_usd_k1(ch), showarrow=False, yshift=10,
                           font={"size": 11, "color": RED if ch < 0 else "#333"})
    fig.update_layout(barmode="group", bargap=0.25)
    fig.update_yaxes(title_text="Revenue, net of discounts (USD)", tickprefix="$", tickformat=",.0f")
    fig.update_xaxes(title_text="Customer country (sorted by change in revenue; * = declined)",
                     tickangle=-40)
    return base_layout(fig, 480)


def q1_context(lines):
    """Compute the Q1 placeholder values for the template.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.

    Returns:
        dict[str, object]: Formatted text and numbers, the
            customer table HTML, and the chart HTML, keyed by
            placeholder name.
    """
    countries = q1_growth.country_growth(lines)
    top = countries.index[:q1_growth.TOP_GROWTH_COUNTRIES].tolist()
    contrib = q1_growth.customer_contributors(lines, top)
    base, comp = f"Revenue_{q1_growth.BASE_YEAR}", f"Revenue_{q1_growth.COMPARE_YEAR}"

    total_base, total_comp = countries[base].sum(), countries[comp].sum()
    top_share = countries["ShareOfTotalGrowth"].iloc[:len(top)].sum()

    def driver_bullet(country):
        """Describe which customers drove one country's growth.

        Args:
            country (str): One of the top growth countries.

        Returns:
            str: Sentence naming the top customer alone if its
                share is at least ``Q1_SOLO_DRIVER_SHARE``,
                otherwise the top two.
        """
        # Name the top customer alone if it delivered most of the country's
        # growth on its own; otherwise name the top two.
        rows = contrib[contrib["Country"] == country]
        n = 1 if rows["ShareOfCountryGrowth"].iloc[0] >= Q1_SOLO_DRIVER_SHARE else 2
        rows = rows.head(n)
        names = " and ".join(rows["Customer"]) + (" alone" if n == 1 else "")
        return (f"{country} ({signed_usd_k1(countries.loc[country, 'Change'])}): {names}, "
                f"{pct(rows['ShareOfCountryGrowth'].sum())} of the country's growth.")

    c = {}
    c["q1_base_year"], c["q1_comp_year"] = q1_growth.BASE_YEAR, q1_growth.COMPARE_YEAR
    c["q1_total_base"], c["q1_total_comp"] = usd_k(total_base), usd_k(total_comp)
    c["q1_growth_usd"] = usd_k(total_comp - total_base)
    c["q1_growth_pct"] = signed_pct(total_comp / total_base - 1)
    c["q1_orders_base"] = lines[(lines["Year"] == q1_growth.BASE_YEAR)
                                & lines["Month"].isin(q1_growth.MONTHS)]["OrderID"].nunique()
    c["q1_orders_comp"] = lines[(lines["Year"] == q1_growth.COMPARE_YEAR)
                                & lines["Month"].isin(q1_growth.MONTHS)]["OrderID"].nunique()
    c["q1_top_countries"] = prose_list(top, capitalize=True)
    c["q1_top_share"] = pct(top_share)
    c["q1_driver_bullets"] = "".join(f"<li>{driver_bullet(country)}</li>" for country in top)
    c["q1_n_top_word"] = word(len(top))
    c["q1_top_n_word"] = word(q1_growth.TOP_N_COUNTRIES)
    c["q1_n_months_word"] = word(len(q1_growth.MONTHS))
    c["q1_table_per_country_word"] = word(Q1_TABLE_PER_COUNTRY)

    sweden = countries.loc["Sweden"]
    c["q1_sweden_base"], c["q1_sweden_comp"] = usd_k1(sweden[base]), usd_k1(sweden[comp])
    c["q1_sweden_multiple"] = f"{sweden[comp] / sweden[base]:.0f}"
    c["q1_france_pct"] = signed_pct(countries.loc["France", "ChangePct"])
    c["q1_france_total"] = usd_k(countries.loc["France", "TotalRevenue"])
    decl = countries[countries["Declined"]].sort_values("Change")
    c["q1_decliners"] = ", ".join(
        f"{name} ({signed_usd_k1(r['Change'])}, {signed_pct(r['ChangePct'])})" for name, r in decl.iterrows())
    c["q1_biggest_decliner"] = decl.index[0]
    c["q1_n_decliners_word"] = word(len(decl))
    c["q1_n_decliners_word_cap"] = word(len(decl)).capitalize()
    c["q1_n_chart"] = int(countries["InChart"].sum())

    top_rows = contrib.groupby("Country", observed=True).head(Q1_TABLE_PER_COUNTRY)
    c["q1_table"] = html_table(
        [[r["Customer"], r["Country"], usd(r[base]), usd(r[comp]), signed_usd_k1(r["Change"]),
          pct(r["ShareOfCountryGrowth"])] for _, r in top_rows.iterrows()],
        ["Customer", "Country", f"Jan–Apr {q1_growth.BASE_YEAR}", f"Jan–Apr {q1_growth.COMPARE_YEAR}",
         "Change", "Share of country's growth"],
        numeric_cols=(2, 3, 4, 5),
    )
    c["q1_chart"] = chart_html(
        q1_chart(countries), "q1-chart",
        f"Revenue by country, Jan–Apr {q1_growth.BASE_YEAR} vs Jan–Apr {q1_growth.COMPARE_YEAR}")
    return c


# ---------- Q2

Q2_DIVERSIFIED_SHOWN = 3  # markets with the lowest top-customer share
Q2_BIG_EXPOSURES_SHOWN = 2  # non-dependent markets with the largest top customer
# Label positions for bubbles whose default (right-hand) label would collide.
Q2_LABEL_POSITIONS = {"Portugal": "top center", "UK": "middle left"}


def q2_chart(table):
    """Build the interactive Q2 dependence scatter.

    Args:
        table (pandas.DataFrame): Output of
            ``q2_concentration.concentration_by_country``.

    Returns:
        plotly.graph_objects.Figure: Country revenue (log
            scale) against top-customer share.
    """
    threshold = q2_concentration.DEPENDENCE_THRESHOLD
    fig = go.Figure()
    fig.add_hrect(y0=threshold, y1=1.05, fillcolor=PINK_BAND, line_width=0, layer="below")
    fig.add_hline(y=threshold, line={"color": RED, "dash": "dash", "width": 1})
    for dependent, colour, name in [(True, RED, f"Dependent (top customer ≥ {pct(threshold)})"),
                                    (False, DARK_BLUE, "Not dependent")]:
        d = table[table["Dependent"] == dependent]
        hover = [
            f"<b>{c}</b><br>Revenue: {usd(r['Revenue'])}<br>Customers: {r['Customers']}<br>"
            f"Top customer: {r['TopCustomer']}<br>Top customer's share: {pct(r['TopCustomerShare'])}<br>"
            f"Revenue at risk: {usd(r['RevenueAtRisk'])}"
            for c, r in d.iterrows()
        ]
        fig.add_scatter(
            x=d["Revenue"], y=d["TopCustomerShare"], mode="markers+text", name=name,
            text=[f"{c} ({n})" for c, n in zip(d.index, d["Customers"])],
            textposition=[Q2_LABEL_POSITIONS.get(c, "middle right") for c in d.index],
            textfont={"size": 10},
            marker={"size": 8 + 2.2 * d["Customers"], "color": colour, "opacity": 0.8,
                    "line": {"color": "white", "width": 1}},
            hovertext=hover, hoverinfo="text", cliponaxis=False,
        )
    ticks = [2_000, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000, 500_000]
    fig.update_xaxes(type="log", title_text="Country revenue (USD, log scale)",
                     tickvals=ticks, ticktext=[usd_k(t) for t in ticks], gridcolor="#e5e5e5",
                     range=[np.log10(table["Revenue"].min() * 0.7), np.log10(table["Revenue"].max() * 2.2)])
    fig.update_yaxes(title_text="Top customer's share of country revenue", tickformat=".0%",
                     range=[0, 1.05])
    return base_layout(fig, 540)


def q2_context(lines):
    """Compute the Q2 placeholder values for the template.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.

    Returns:
        dict[str, object]: Formatted text and numbers, the
            dependent-markets table HTML, and the chart HTML,
            keyed by placeholder name.
    """
    table = q2_concentration.concentration_by_country(lines)
    risky = q2_concentration.riskiest_markets(table)
    total = table["Revenue"].sum()
    c = {}
    c["q2_threshold"] = pct(q2_concentration.DEPENDENCE_THRESHOLD)
    c["q2_n_countries"] = len(table)
    c["q2_n_customers"] = int(table["Customers"].sum())
    c["q2_n_dependent"] = len(risky)
    c["q2_dependent_share"] = pct(risky["Revenue"].sum() / total)
    c["q2_total_at_risk"] = usd_k(risky["RevenueAtRisk"].sum())

    top_risk = risky.iloc[0]
    rank = list(table.index).index(risky.index[0]) + 1
    c["q2_top_risk_country"] = risky.index[0]
    c["q2_top_risk_rank"] = f"#{rank}"
    c["q2_top_risk_revenue"] = usd_k(top_risk["Revenue"])
    c["q2_top_risk_customers_word"] = word(int(top_risk["Customers"]))
    c["q2_top_risk_customer"] = top_risk["TopCustomer"]
    c["q2_top_risk_share"] = pct(top_risk["TopCustomerShare"])
    c["q2_top_risk_at_risk"] = usd_k(top_risk["RevenueAtRisk"])

    single = table[table["Customers"] == 1].sort_values("Revenue", ascending=False)
    biggest_single = single.iloc[0]
    c["q2_n_single_word"] = word(len(single))
    c["q2_single_list"] = prose_list(single.index, capitalize=True)
    c["q2_biggest_single"] = single.index[0]
    c["q2_biggest_single_customer"] = biggest_single["TopCustomer"]
    c["q2_biggest_single_revenue"] = usd_k(biggest_single["Revenue"])

    big = table[~table["Dependent"]].nlargest(Q2_BIG_EXPOSURES_SHOWN, "TopCustomerRevenue")
    c["q2_big_exposures"] = " and ".join(
        f"{r['TopCustomer']} in {prose_list([country])} ({usd_k(r['TopCustomerRevenue'])}, "
        f"{pct(r['TopCustomerShare'])} of that market)" for country, r in big.iterrows())
    c["q2_big_exposure_countries"] = prose_list(big.index)
    c["q2_big_exposure_countries_cap"] = prose_list(big.index, capitalize=True)

    div = table.nsmallest(Q2_DIVERSIFIED_SHOWN, "TopCustomerShare")
    c["q2_diversified"] = prose_list(div.index, capitalize=True)
    c["q2_diversified_customers"] = f"{div['Customers'].min()}–{div['Customers'].max()}"
    c["q2_diversified_max_share"] = pct(div["TopCustomerShare"].max())

    c["q2_table"] = html_table(
        [[country, r["Customers"], usd(r["Revenue"]), r["TopCustomer"], pct(r["TopCustomerShare"]),
          usd(r["RevenueAtRisk"])] for country, r in risky.iterrows()],
        ["Market", "Customers", "Revenue", "Top customer", "Top customer's share", "Revenue at risk"],
        numeric_cols=(1, 2, 4, 5),
    )
    c["q2_chart"] = chart_html(
        q2_chart(table), "q2-chart",
        "How dependent is each market on its largest customer? "
        "Bubble size and (n) = number of customers.")
    return c


# ---------- Q3

# Label positions for reps whose bubbles sit close together.
Q3_LABEL_POSITIONS = {"Nancy Davolio": "bottom center"}

def q3_chart(reps):
    """Build the interactive Q3 sales-rep scatter.

    Args:
        reps (pandas.DataFrame): Output of
            ``q3_sales_team.rep_summary``.

    Returns:
        plotly.graph_objects.Figure: Orders against average
            order value, with equal-revenue curves.
    """
    fig = go.Figure()
    x = np.linspace(reps["Orders"].min() * 0.8, reps["Orders"].max() * 1.15, 200)
    for level in (100_000, 150_000, 200_000, 250_000):
        fig.add_scatter(x=x, y=level / x, mode="lines", line={"color": GREY, "dash": "dot", "width": 1},
                        hoverinfo="skip", showlegend=False)
        fig.add_annotation(x=x[-1], y=level / x[-1], text=f"{usd_k(level)} total", showarrow=False,
                           xanchor="left", xshift=4, font={"size": 10, "color": GREY})
    colours = {"USA": DARK_BLUE, "UK": ORANGE}
    for office, d in reps.groupby("Office"):
        hover = [
            f"<b>{name}</b> ({office} office, hired {r['HireDate']:%Y})<br>Orders: {r['Orders']}<br>"
            f"Average order: {usd(r['AvgOrderValue'])}<br>Revenue: {usd(r['Revenue'])}"
            for name, r in d.iterrows()
        ]
        fig.add_scatter(
            x=d["Orders"], y=d["AvgOrderValue"], mode="markers+text", name=f"{office} office",
            text=[f"{n}<br>{usd_k(v)}" for n, v in zip(d.index, d["Revenue"])],
            textposition=[Q3_LABEL_POSITIONS.get(n, "top center") for n in d.index],
            textfont={"size": 10},
            marker={"size": d["Revenue"] / 6000, "color": colours.get(office, GREY), "opacity": 0.8,
                    "line": {"color": "white", "width": 1}},
            hovertext=hover, hoverinfo="text",
        )
    fig.update_xaxes(title_text="Number of orders, whole period", range=[0, reps["Orders"].max() * 1.3],
                     gridcolor="#e5e5e5")
    fig.update_yaxes(title_text="Average order value (USD, net of discounts)", tickprefix="$",
                     tickformat=",.0f", range=[0, reps["AvgOrderValue"].max() * 1.35])
    return base_layout(fig, 540)


def q3_context(lines, tables):
    """Compute the Q3 placeholder values for the template.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``; uses ``employees``.

    Returns:
        dict[str, object]: Formatted text and numbers, the rep
            table HTML, and the chart HTML, keyed by
            placeholder name.
    """
    everyone = q3_sales_team.employee_summary(lines, tables["employees"])
    reps = q3_sales_team.rep_summary(everyone)
    d = q3_sales_team.driver_summary(reps)
    excluded = everyone[everyone["Title"] != q3_sales_team.REP_TITLE]

    def span(series, fmt=str):
        """Format a column's range as ``min–max``.

        Args:
            series (pandas.Series): Values to span.
            fmt (Callable[[object], str]): Formatter for each end.

        Returns:
            str: E.g. ``43–156``.
        """
        return f"{fmt(series.min())}–{fmt(series.max())}"

    c = {}
    c["q3_n_reps_word"] = word(d["Reps"])
    c["q3_excluded"] = "; ".join(f"{n} ({t})" for n, t in zip(excluded.index, excluded["Title"]))
    c["q3_n_excluded_word"] = word(len(excluded))
    c["q3_excluded_share"] = pct(excluded["ShareOfCompanyRevenue"].sum())
    c["q3_revenue_span"] = span(reps["Revenue"], usd_k)
    c["q3_orders_span"] = span(reps["Orders"])
    c["q3_aov_span"] = span(reps["AvgOrderValue"], usd)
    c["q3_revenue_spread"] = f"{d['RevenueSpread']:.1f}"
    c["q3_orders_spread"] = f"{d['OrdersSpread']:.1f}"
    c["q3_aov_spread"] = f"{d['AvgOrderValueSpread']:.1f}"
    c["q3_rank_match"] = d["OrdersRankMatchesRevenueRank"]
    c["q3_n_reps"] = d["Reps"]
    c["q3_rank_mismatch"] = d["OrdersRankMismatchReps"].replace(", ", " and ")
    c["q3_biggest_orders_rep"] = d["BiggestOrdersRep"]
    c["q3_biggest_orders_rep_revenue_rank"] = ordinal(d["BiggestOrdersRepRevenueRank"])
    c["q3_top_earner_order_size_rank"] = ordinal(d["TopEarnerOrderSizeRank"])

    top = reps["Revenue"].idxmax()
    c["q3_top_rep"] = top
    c["q3_top_rep_revenue"] = usd_k(reps.loc[top, "Revenue"])
    c["q3_top_rep_orders"] = reps.loc[top, "Orders"]

    for office in ("USA", "UK"):
        o = reps[reps["Office"] == office]
        key = office.lower()
        c[f"q3_{key}_reps"] = ", ".join(o.index[:-1]) + f" and {o.index[-1]}"
        c[f"q3_{key}_orders_span"] = span(o["Orders"])
        c[f"q3_{key}_hired_span"] = span(o["HireDate"].dt.year)

    biggest_orders = reps.nlargest(2, "AvgOrderValue")
    c["q3_biggest_orders_reps"] = " and ".join(biggest_orders.index)
    c["q3_biggest_orders_office"] = biggest_orders["Office"].iloc[0]
    low = reps.loc[reps["Revenue"].idxmin()]
    c["q3_lowest_rep"] = reps["Revenue"].idxmin()
    c["q3_lowest_rep_aov"] = usd(low["AvgOrderValue"])

    c["q3_table"] = html_table(
        [[name, r["Office"], f"{r['HireDate']:%Y}", r["Orders"], usd(r["AvgOrderValue"]), usd(r["Revenue"])]
         for name, r in reps.iterrows()],
        ["Sales rep", "Office", "Hired", "Orders", "Average order", "Revenue"],
        numeric_cols=(3, 4, 5),
    )
    c["q3_chart"] = chart_html(
        q3_chart(reps), "q3-chart",
        "Sales representatives: more orders or bigger orders? "
        "Bubble size = revenue; dotted curves = equal total revenue.")
    return c


# ---------- Q4

def q4_chart(table):
    """Build the interactive Q4 reorder-level scatter.

    Args:
        table (pandas.DataFrame): Output of
            ``q4_inventory.inventory_table``.

    Returns:
        plotly.graph_objects.Figure: Reorder level (jittered as
            in the PNG) against monthly demand, coloured by risk.
    """
    rng = np.random.default_rng(q4_inventory.JITTER_SEED)
    x = table["ReorderLevel"] + rng.uniform(-1.2, 1.2, len(table))  # same jitter as the PNG
    no_sales = table["MonthlyDemand"] == 0
    groups = [
        (~table["AtRisk"] & ~no_sales, DARK_BLUE, "≥ 1 month of cover"),
        (table["AtRisk"], RED, "< 1 month of cover (at risk)"),
        (no_sales, GREY, f"No sales Jan–Apr {q4_inventory.DEMAND_YEAR}"),
    ]
    fig = go.Figure()
    fig.add_vrect(x0=-2.5, x1=2.5, fillcolor=PINK_BAND, line_width=0, layer="below")
    fig.add_annotation(x=0, y=1, yref="paper", text="Reorder level 0:<br>never triggers a reorder",
                       showarrow=False, yanchor="top", font={"size": 10, "color": RED})
    for mask, colour, name in groups:
        d = table[mask]
        cover = ["n/a" if v != v else f"{v:.1f} months" for v in d["MonthsOfCover"]]
        hover = [
            f"<b>{r['ProductName']}</b> ({r['CategoryName']})<br>In stock: {r['UnitsInStock']}, "
            f"on order: {r['UnitsOnOrder']}<br>Reorder level: {r['ReorderLevel']}<br>"
            f"Sells per month: {r['MonthlyDemand']:.0f}<br>Cover: {cv}<br>Reorder rule: {r['Status']}"
            for (_, r), cv in zip(d.iterrows(), cover)
        ]
        fig.add_scatter(x=x[mask], y=d["MonthlyDemand"], mode="markers", name=name,
                        marker={"size": 10, "color": colour, "opacity": 0.8,
                                "line": {"color": "white", "width": 1}},
                        hovertext=hover, hoverinfo="text")
    # Name the fastest sellers that never trigger a reorder (as in the PNG).
    fastest_zero = table[table["ReorderLevelZero"]].nlargest(4, "MonthlyDemand").index
    for k, i in enumerate(fastest_zero):
        fig.add_annotation(x=x[i], y=table.loc[i, "MonthlyDemand"], text=table.loc[i, "ProductName"],
                           showarrow=False, xanchor="left", xshift=8, yshift=7 if k % 2 == 0 else -7,
                           font={"size": 10})
    levels = sorted(table["ReorderLevel"].unique())
    fig.update_xaxes(title_text="Reorder level (units)", tickvals=levels, range=[-3, max(levels) + 4],
                     showgrid=False, zeroline=False)
    fig.update_yaxes(title_text=f"Average units sold per month, Jan–Apr {q4_inventory.DEMAND_YEAR}")
    return base_layout(fig, 520)


def q4_context(lines, tables):
    """Compute the Q4 placeholder values for the template.

    Args:
        lines (pandas.DataFrame): All order lines from
            ``build_order_lines``.
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``; uses ``products`` and
            ``categories``.

    Returns:
        dict[str, object]: Formatted text and numbers, the
            lowest-cover table HTML, and the chart HTML, keyed
            by placeholder name.
    """
    table = q4_inventory.inventory_table(tables, lines)
    s = q4_inventory.policy_summary(table)
    c = {}
    c["q4_n_active"] = s["ActiveProducts"]
    c["q4_n_discontinued_word"] = word(int(tables["products"]["Discontinued"].sum()))
    c["q4_ok"] = s["StatusOK"]
    c["q4_restock"] = s["StatusRestockComing"]
    c["q4_missed"] = s["StatusMissedReorder"]
    c["q4_missed_word"] = word(s["StatusMissedReorder"])
    c["q4_missed_names"] = ", ".join(table.loc[table["Status"] == "Missed reorder", "ProductName"])
    c["q4_at_risk"] = s["AtRisk"]
    c["q4_at_risk_pass"] = s["AtRiskButRulePasses"]
    c["q4_zero"] = s["ReorderLevelZero"]
    c["q4_zero_at_risk_word"] = word(s["AtRiskWithReorderLevelZero"])
    c["q4_corr"] = f"{s['RankCorrReorderLevelDemand']:.2f}".replace("-", "−")
    c["q4_median_cover"] = f"{s['MedianMonthsOfCover']:.1f}"
    c["q4_no_sales_word"] = word(s["NoRecentSales"])
    c["q4_demand_year"] = q4_inventory.DEMAND_YEAR
    c["q4_threshold_word"] = word(int(q4_inventory.COVER_THRESHOLD_MONTHS))
    c["q4_n_months_word"] = word(len(q4_inventory.DEMAND_MONTHS))

    worst = table.iloc[0]
    c["q4_worst"] = worst["ProductName"]
    c["q4_worst_stock"] = worst["UnitsInStock"]
    c["q4_worst_demand"] = f"{worst['MonthlyDemand']:.0f}"
    c["q4_worst_reorder"] = worst["ReorderLevel"]
    c["q4_worst_days"] = f"{worst['MonthsOfCover'] * 30:.0f}"

    # The at-risk product that matters most for revenue.
    product_revenue = lines.groupby("ProductID")["Revenue"].sum()
    at_risk = table[table["AtRisk"]].assign(Rev=lambda d: d["ProductID"].map(product_revenue))
    key = at_risk.loc[at_risk["Rev"].idxmax()]
    c["q4_key_product"] = key["ProductName"]
    c["q4_key_product_share"] = pct(key["Rev"] / lines["Revenue"].sum())
    c["q4_key_product_cover_days"] = f"{key['MonthsOfCover'] * 30:.0f}"

    rows = table.head(q4_inventory.LOWEST_COVER_ROWS)
    c["q4_table_rows_word"] = word(q4_inventory.LOWEST_COVER_ROWS)
    c["q4_table"] = html_table(
        [[r["ProductName"], r["CategoryName"], r["UnitsInStock"], r["UnitsOnOrder"], r["ReorderLevel"],
          f"{r['MonthlyDemand']:.0f}", f"{r['MonthsOfCover']:.2f}", r["Status"]] for _, r in rows.iterrows()],
        ["Product", "Category", "In stock", "On order", "Reorder level", "Sold / month",
         "Months of cover", "Reorder rule says"],
        numeric_cols=(2, 3, 4, 5, 6),
    )
    c["q4_chart"] = chart_html(
        q4_chart(table), "q4-chart",
        f"Reorder levels vs actual demand ({len(table)} active products)")
    return c


# ---------- page

def build_context(tables):
    """Compute every placeholder value for the page template.

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``.

    Returns:
        dict[str, object]: plotly.js CDN URL, repo URL, data
            period, and the Q1-Q4 values.
    """
    lines = build_order_lines(tables)
    context = {
        "plotly_js_url": f"https://cdn.plot.ly/plotly-{plotly.offline.get_plotlyjs_version()}.min.js",
        "repo_url": REPO_URL,
        "data_start": day_month_year(lines["OrderDate"].min()),
        "data_end": day_month_year(lines["OrderDate"].max()),
    }
    context.update(q1_context(lines))
    context.update(q2_context(lines))
    context.update(q3_context(lines, tables))
    context.update(q4_context(lines, tables))
    return context


def render_page(tables):
    """Fill the page template with the analysis results.

    Args:
        tables (dict[str, pandas.DataFrame]): Output of
            ``load_tables``.

    Returns:
        str: Complete HTML page.

    Raises:
        KeyError: The template uses a placeholder that has no
            value.
    """
    # substitute() (not safe_substitute) raises KeyError on any unfilled
    # placeholder, so a missing number can never reach the page silently.
    return Template(TEMPLATE_PATH.read_text(encoding="utf-8")).substitute(build_context(tables))


def main(tables=None):
    """Build the page and write it to ``docs/index.html``.

    Args:
        tables (dict[str, pandas.DataFrame] | None): Output of
            ``load_tables``; loaded from the workbook if None.

    Returns:
        None. Writes the page and prints its size.
    """
    tables = tables if tables is not None else load_tables()
    html = render_page(tables)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Site | wrote {OUTPUT_PATH.relative_to(ROOT)} ({len(html) / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
