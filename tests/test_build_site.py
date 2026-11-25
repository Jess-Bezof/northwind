"""Tests for the webpage: structure, numbers, charts, and rules."""
import html as html_lib
import re

import plotly.offline
import pytest

import build_site
import q1_growth
import q2_concentration
import q3_sales_team
import q4_inventory


def visible_text(page):
    """Extract the text a reader sees on the page.

    Args:
        page (str): Page HTML.

    Returns:
        str: Text without scripts, styles, comments, or tags;
            whitespace collapsed and entities decoded.
    """
    # Page text as a reader sees it: no scripts, styles, comments, or tags.
    body = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", page, flags=re.S)
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)))


@pytest.fixture(scope="module")
def page(tables):
    """Render the page once per test module.

    Args:
        tables (dict[str, pandas.DataFrame]): ``tables`` fixture.

    Returns:
        str: Output of ``build_site.render_page``.
    """
    return build_site.render_page(tables)


@pytest.fixture(scope="module")
def text(page):
    """Extract the page's visible text once per test module.

    Args:
        page (str): ``page`` fixture.

    Returns:
        str: Output of ``visible_text``.
    """
    return visible_text(page)


# ---------- structure


def test_no_unfilled_placeholders(page):
    """Check no placeholder survives outside comments.

    Args:
        page (str): ``page`` fixture.

    Returns:
        None.
    """
    outside_comments = re.sub(r"<!--.*?-->", "", page, flags=re.S)
    assert not re.findall(r"\$\{?\w+\}?", re.sub(r"\$[\d,.]+k?", "", visible_text(outside_comments)))
    assert "${" not in outside_comments


def test_page_has_four_sections_charts_and_tables(page):
    """Check the four sections, charts, and tables exist.

    Args:
        page (str): ``page`` fixture.

    Returns:
        None.
    """
    for q in ("q1", "q2", "q3", "q4"):
        assert f'id="{q}-section"' in page
        assert f'id="{q}-chart"' in page
    assert page.count("<table>") == 4


def test_each_question_has_the_six_required_parts(page):
    """Check each section has the six parts the homework requires.

    Args:
        page (str): ``page`` fixture.

    Returns:
        None.
    """
    sections = re.findall(r'<section class="question".*?</section>', page, flags=re.S)
    assert len(sections) == 4
    for s in sections:
        for part in ("<h2>", "Why it matters", "Approach", "-chart", "Main finding",
                     "Business implication"):
            assert part in s


def test_table_row_counts(page):
    """Check each table has the agreed number of rows.

    Args:
        page (str): ``page`` fixture.

    Returns:
        None.
    """
    tables = re.findall(r"<tbody>(.*?)</tbody>", page, flags=re.S)
    rows = [t.count("<tr>") for t in tables]
    # Q1: 2 customers x 3 countries; Q2: 12 dependent markets (D10);
    # Q3: 6 reps (D10); Q4: 10 lowest-cover products.
    assert rows == [6, 12, 6, 10]


def test_plotly_js_version_matches_installed_plotly(page):
    """Check the page loads the plotly.js the charts were built for.

    Args:
        page (str): ``page`` fixture.

    Returns:
        None.
    """
    version = plotly.offline.get_plotlyjs_version()
    assert f"https://cdn.plot.ly/plotly-{version}.min.js" in page


def test_page_links_to_the_real_repository(page):
    """Check the page links to the published repository and README.

    Args:
        page (str): ``page`` fixture.

    Returns:
        None.
    """
    assert 'href="https://github.com/Jess-Bezof/northwind"' in page
    assert 'href="https://github.com/Jess-Bezof/northwind#readme"' in page
    assert "OWNER/REPO" not in page


# ---------- numbers on the page


def test_q1_totals_match_independent_calculation(text, raw_lines):
    """Check the Q1 totals sentence against the raw-data rebuild.

    Args:
        text (str): ``text`` fixture.
        raw_lines (pandas.DataFrame): ``raw_lines`` fixture.

    Returns:
        None.
    """
    window = raw_lines[raw_lines["OrderDate"].dt.month <= 4]
    base = window.loc[window["OrderDate"].dt.year == 1997, "Revenue"].sum()
    comp = window.loc[window["OrderDate"].dt.year == 1998, "Revenue"].sum()
    expected = f"from ${base / 1000:,.0f}k to ${comp / 1000:,.0f}k (+{comp / base - 1:.0%})"
    assert expected in text


def test_q2_austria_share_matches_independent_calculation(text, raw_lines):
    """Check Austria's top-customer share against the rebuild.

    Args:
        text (str): ``text`` fixture.
        raw_lines (pandas.DataFrame): ``raw_lines`` fixture.

    Returns:
        None.
    """
    at = raw_lines[raw_lines["Country"] == "Austria"].groupby("CustomerID")["Revenue"].sum()
    assert f"Ernst Handel alone provides {at.max() / at.sum():.0%}" in text


def test_hand_checked_values_appear_on_page(text):
    """Check the student's hand-checked values appear verbatim.

    Args:
        text (str): ``text`` fixture.

    Returns:
        None.
    """
    # Values the student confirmed in Excel on 2026-11-24 (LOG D25).
    assert "Margaret Peacock leads with 156 orders" in text
    assert "Camembert Pierrot: 19 units in stock" in text


def test_headline_counts_match_analysis(text, lines, tables):
    """Check Q2-Q4 headline figures match the analysis.

    Args:
        text (str): ``text`` fixture.
        lines (pandas.DataFrame): ``lines`` fixture.
        tables (dict[str, pandas.DataFrame]): ``tables``
            fixture.

    Returns:
        None.
    """
    deps = q2_concentration.riskiest_markets(q2_concentration.concentration_by_country(lines))
    assert f"{len(deps)} of 21 markets depend on a single customer" in text

    reps = q3_sales_team.rep_summary(q3_sales_team.employee_summary(lines, tables["employees"]))
    d = q3_sales_team.driver_summary(reps)
    assert f"varies {d['OrdersSpread']:.1f}×" in text
    assert f"for {d['OrdersRankMatchesRevenueRank']} of the {d['Reps']} reps" in text

    s = q4_inventory.policy_summary(q4_inventory.inventory_table(tables, lines))
    assert f"{s['AtRisk']} of {s['ActiveProducts']} products have less than" in text
    assert f"{s['AtRiskButRulePasses']} of them still pass the reorder rule" in text


# ---------- charts show the analysed data


def test_q1_chart_bars_equal_analysis(lines):
    """Check the Q1 bar heights equal the analysed revenue.

    Args:
        lines (pandas.DataFrame): ``lines`` fixture.

    Returns:
        None.
    """
    countries = q1_growth.country_growth(lines)
    fig = build_site.q1_chart(countries)
    shown = countries[countries["InChart"]].sort_values("Change", ascending=False)
    assert list(fig.data[0].y) == pytest.approx(list(shown["Revenue_1997"]))
    assert list(fig.data[1].y) == pytest.approx(list(shown["Revenue_1998"]))
    assert len(fig.layout.annotations) == len(shown) == 13


def test_scatter_charts_plot_every_unit(lines, tables):
    """Check the Q2-Q4 charts plot every market, rep, and product.

    Args:
        lines (pandas.DataFrame): ``lines`` fixture.
        tables (dict[str, pandas.DataFrame]): ``tables``
            fixture.

    Returns:
        None.
    """
    def points(fig):
        """Count the plotted points in a figure.

        Args:
            fig (plotly.graph_objects.Figure): Chart.

        Returns:
            int: Points across marker traces; line-only traces
                are excluded.
        """
        return sum(len(t.x) for t in fig.data if t.mode and "markers" in t.mode)

    q2 = q2_concentration.concentration_by_country(lines)
    reps = q3_sales_team.rep_summary(q3_sales_team.employee_summary(lines, tables["employees"]))
    q4 = q4_inventory.inventory_table(tables, lines)
    assert points(build_site.q2_chart(q2)) == 21
    assert points(build_site.q3_chart(reps)) == 6
    assert points(build_site.q4_chart(q4)) == 69


# ---------- the "no hand-typed numbers" rule (LOG D27)


def test_template_prose_has_no_hand_typed_numbers():
    """Check the template text contains no hand-typed figures.

    Args:
        None.

    Returns:
        None.
    """
    template = build_site.TEMPLATE_PATH.read_text(encoding="utf-8")
    prose = re.sub(r"<head>.*?</head>|<!--.*?-->|<script.*?</script>", " ", template, flags=re.S)
    prose = re.sub(r"\$\{\w+\}", " ", re.sub(r"<[^>]+>", " ", prose))
    tokens = re.findall(r"\S*\d\S*", prose)
    # Allowed: section labels ("Question 2", "1 · Growth"), "reorder level of 0",
    # and the formula's "(1 − discount)". Any multi-digit number or figure
    # such as "57%" or "$104k" means a number was typed by hand.
    assert all(re.fullmatch(r"\(?[0-4]\)?[.,]?\)?\.?", t) for t in tokens), tokens


# ---------- tab navigation (LOG D35)


def test_tabs_and_pager_links_point_to_real_sections(page):
    """Check tab and Previous/Next links target real sections.

    Args:
        page (str): ``page`` fixture.

    Returns:
        None.
    """
    sections = re.findall(r'<section class="question" id="(q\d)-section"', page)
    assert sections == ["q1", "q2", "q3", "q4"]
    tabs = re.findall(r'<a class="tab" href="#(q\d)"', page)
    assert tabs == sections
    pager_targets = re.findall(r'<a class="(?:prev|next)" href="#(q\d)"', page)
    assert set(pager_targets) <= set(sections)
    # q1 has only "next", q4 only "prev", q2 and q3 both: 6 links.
    assert len(pager_targets) == 6
    # Hash targets (#q1) must not match any element id, or the browser would
    # jump past the header when a question is opened by link.
    assert not re.search(r'id="q\d"', page)
    # Without JavaScript every section stays visible; the tabs need the "js" class.
    assert 'classList.add("js")' in page
    assert ".js section.question { display: none" in page


# ---------- formatting helpers


def test_formatting_helpers():
    """Check the number and text formatting helpers.

    Args:
        None.

    Returns:
        None.
    """
    assert build_site.usd(104_874.98) == "$104,875"
    assert build_site.usd_k(422_290) == "$422k"
    assert build_site.signed_usd_k1(-9_422.4) == "−$9.4k"
    assert build_site.signed_pct(-0.687) == "−69%"
    assert build_site.signed_pct(1.207) == "+121%"
    assert [build_site.ordinal(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22)] == \
        ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd"]
    assert build_site.word(4) == "four" and build_site.word(16) == "16"
    assert build_site.prose_list(["USA", "Germany", "Brazil"], capitalize=True) == \
        "The USA, Germany and Brazil"
