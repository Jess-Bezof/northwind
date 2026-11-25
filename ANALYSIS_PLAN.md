# Analysis Plan

This plan covers the four business questions for the Northwind webpage. For each question it records why it matters, the analysis, the visual, and the decision it supports. Exploration behind these choices is in [notebooks/01_exploration.ipynb](notebooks/01_exploration.ipynb).

**Status:** questions and design choices agreed 2026-11-23. Analysis not yet built.

## Shared definitions

| Term | Definition |
|---|---|
| Revenue | Net revenue per order line: `UnitPrice × Quantity × (1 − Discount)`. Excludes freight; includes unshipped orders. |
| Data period | 4 Jul 1996 – 6 May 1998. Both end months are partial. |
| Like-for-like comparison | **Jan–Apr 1997 vs Jan–Apr 1998**, because 1998 data stops on 6 May. Never compare full-year 1997 with 1998. |
| Customer country | `Customers.Country` (where the customer is based), not `Orders.ShipCountry`. |
| Active product | `Product.Discontinued == 0` (69 of 77 products). |

---

## Q1. Growth drivers

> **Which markets and customers drove Northwind's growth from 1997 to 1998, and where should sales attention go next?**

**Why it matters:** Jan–Apr revenue more than doubled ($191k → $422k, +121%). Knowing which markets and accounts drove the increase shows where sales effort pays off, and which markets are falling behind.

**Analysis**
1. Filter order lines to Jan–Apr of 1997 and 1998.
2. Sum revenue by customer country and year, then compute the change in $ and %.
3. Rank countries by $ change, showing the biggest gainers and any decliners.
4. For the top 3 growth countries, break the change down by customer to show who drove it.

**Visuals**
- Grouped bar chart of Jan–Apr revenue by country, with 1997 and 1998 side by side (sorted by $ change).
- Table of the top customer contributors to growth: customer, country, 1997 revenue, 1998 revenue, $ change, and share of total growth.

**Decision it supports:** where to focus sales attention, i.e. whether to double down on markets that are growing or investigate markets that are flat or declining.

**Caveats:** four months per year is a short window, and a single large order can swing a small country.

**Outputs:** `outputs/figures/q1_growth_by_country.png`, `outputs/tables/q1_growth_by_country.csv`, `outputs/tables/q1_top_customer_contributors.csv`

---

## Q2. Customer concentration risk

> **Which markets depend on just one or two customers, and how much revenue is at risk if a key customer leaves?**

**Why it matters:** Austria is the #3 market ($128k) with only 2 customers, and Ireland ($50k) has 1. Losing a single account would remove most of a market's revenue.

**Analysis**
1. For each customer country (whole period), compute:
   - number of active customers
   - total revenue
   - the top customer's name and revenue
   - the top customer's share of country revenue
2. Revenue at risk = the top customer's revenue, i.e. what is lost if that one customer leaves.

**Visuals**
- Scatter of country revenue (x) against the top customer's share of that country (y), with countries labelled. The upper-right area (big markets that depend on one account) is the risk zone.
- Table of the riskiest markets: country, customers, revenue, top customer, top-customer share, revenue at risk.

**Decision it supports:** where to invest in key-account retention (high-share, high-revenue markets) and where to win more customers so a market is less dependent on one account.

**Caveats:** dependence on one customer is a risk, not a prediction that the customer will leave.

**Must say in the webpage text (LOG D17):** Germany (48.6%) and the USA (42.5%) fall just under the 50% threshold. Even so, they carry the largest single-customer dollar exposure: QUICK-Stop $110k and Save-a-lot Markets $104k, each more than all of Ireland.

**Outputs:** `outputs/figures/q2_concentration_scatter.png`, `outputs/tables/q2_concentration_by_country.csv`

---

## Q3. Sales team: volume vs order size

> **Do top-performing employees sell more because they win more orders or bigger orders, and what does that suggest for coaching?**

**Why it matters:** revenue per employee ranges from $69k to $233k. Whether top performers win on volume (more orders) or on order size points to different coaching (prospecting vs upselling).

**Analysis**
1. For each employee (whole period), compute:
   - number of orders
   - average order value
   - total revenue
2. Total revenue = orders × average order value. Across the 6 reps, compare how widely each driver varies (max ÷ min), and whether reps rank in the same order on each driver as on revenue. This is a whole-team view, not a top-vs-bottom split (LOG D20). With only six reps, ranks are compared directly rather than summarised as a Spearman correlation (LOG D29).
3. Show each employee's title and country (US vs UK office) alongside.

**Visuals**
- Scatter of number of orders (x) against average order value (y). Bubble size shows total revenue. Points are labelled by employee and coloured by office.
- Table: employee, title, office, orders, average order value, revenue.

**Decision it supports:** coaching focus (more prospecting or more upselling) and whether practices from the top performers can be shared across the team.

**Caveats**
- Andrew Fuller (VP Sales) and Laura Callahan (Inside Sales Coordinator) have different roles from the sales representatives.
- US and UK staff likely serve different territories.
- Employees with few orders have noisier averages.
- The data shows correlation, not skill.

**Outputs:** `outputs/figures/q3_employee_scatter.png`, `outputs/tables/q3_employee_summary.csv`, `outputs/tables/q3_drivers.csv`

---

## Q4. Stock-out risk and reorder policy

> **Which products are at risk of stocking out, and are reorder levels set in line with how fast products actually sell?**

**Why it matters:** stock-outs lose sales on fast-moving products. Exploration found that reorder levels are unrelated to demand (Spearman ρ ≈ −0.04). In addition, 16 active products have a reorder level of 0, so they never trigger a reorder, and some of them are top sellers.

**How the fields relate**
- `UnitsInStock` is what is on hand now.
- `ReorderLevel` is the trigger point: stock at or below it means buy more.
- `UnitsOnOrder` is stock already ordered from suppliers but not yet received.
- Stock position = `UnitsInStock + UnitsOnOrder`.

**Analysis**
1. Keep the 69 active products.
2. Apply the reorder rule:
   - OK: stock above reorder level
   - Restock coming: at or below reorder level, with units on order
   - Missed reorder: at or below reorder level, nothing on order
3. Monthly demand = units sold in Jan–Apr 1998 ÷ 4.
4. Months of cover = (stock + on order) ÷ monthly demand.
5. Flag products with under 1 month of cover. Note how many of them still pass the reorder rule.

**Visuals**
- Scatter of reorder level (x) against monthly demand (y). It shows the lack of relationship, and products with a reorder level of 0 are highlighted.
- Table of the 10 products with the least cover: product, category, stock, on order, reorder level, monthly demand, months of cover.

**Decision it supports:** reset reorder levels in line with demand (e.g. at least 1 month of average sales), starting with fast sellers that currently have a reorder level of 0.

**Caveats**
- The stock figures are an undated snapshot, assumed to be current as of May 1998.
- Stock looks low relative to sales across the board, which suggests the inventory and sales data are not fully consistent.
- Present this as evidence that reorder rules don't reflect demand, not as an exact stock-out forecast.

**Outputs:** `outputs/figures/q4_reorder_vs_demand.png`, `outputs/tables/q4_lowest_cover.csv`, `outputs/tables/q4_inventory_all_active.csv`

---

## Decisions (confirmed by the student, 2026-11-23)

- [x] **Q1 chart scope:** the top 10 countries by total revenue (whole period), plus any country whose Jan–Apr revenue declined.
  - Checked: 4 countries declined (Denmark −$9.4k, Canada −$3.7k, Mexico −$3.1k, Finland −$1.9k).
  - Canada is already in the top 10, so the chart shows 13 countries.
- [x] **Q2 dependence threshold:** the top customer brings in ≥ 50% of the country's revenue.
  - Checked: 12 of 21 countries qualify, so the threshold is kept.
  - Three of them (Ireland, Norway, Poland) have only one customer, so they are 100% by definition.
  - Several qualifying markets are tiny (Poland $3.5k, Norway $5.7k), so the scatter's revenue axis is what separates real risk.
- [x] **Q3 population:** sales representatives only.
  - Checked: there are 6 (Davolio, Leverling, Peacock, Suyama, King, Dodsworth), which is enough for the chart.
  - Fuller (VP Sales), Buchanan (Sales Manager), and Callahan (Inside Sales Coordinator) are excluded. Together they account for ~$362k (29% of revenue); state this on the page.
- [x] **Q4:** demand window Jan–Apr 1998; at-risk threshold < 1 month of cover.

## Webpage plan (agreed 2026-11-24, LOG D26)

**Build:** `src/build_site.py`, run at the end of `run_all.py`, writes `docs/index.html`, the public webpage (hosted on Netlify at https://northwind-hw3.netlify.app/).
- It fills an HTML template (`site/template.html`) with numbers taken directly from the analysis functions. No number in the page text is typed by hand.
- It builds four **interactive Plotly charts** from the same DataFrames the question scripts produce, and embeds them in the page. plotly.js is loaded once, from its CDN.
- The tested matplotlib PNGs in `outputs/figures/` stay as static versions for the repo and README.

**Page outline**
1. Header: title, the brief in one line, and links to the GitHub repo and README. No author name.
2. ~~Summary for the manager~~: dropped (LOG D31).
3. Q1–Q4 sections, each with labelled parts: Question · Why it matters · Approach · interactive chart (plus a small table where useful) · Main finding · Business implication.
   - Q1: top-customer contributors table.
   - Q2: note on Germany and the USA (LOG D17), plus the riskiest-markets table.
   - Q3: the 3 excluded employees (29% of revenue); office, territory, and hire date overlap.
   - Q4: present as a reorder-policy finding, not a forecast; lowest-cover table.
4. ~~Data & method~~: dropped (LOG D31). The footer keeps the revenue definition and the link to the code.
5. Footer: data source; built with Python and an AI coding agent.

**Layout (LOG D35):** one question at a time.
- Tabs in a menu that stays at the top of the screen, opening on Q1. Each question has its own link (`#q1`–`#q4`) and Previous/Next links at the bottom.
- Chart titles are HTML headings so they wrap on small screens.
- On phones, charts and tables keep a minimum width and scroll sideways.

**Interactive chart design:** keep each matplotlib chart's encoding (same axes, colours, thresholds, labels), and add hover text with exact values.

**Text:** the agent drafts every section from this plan and the verified results; the student reviews and edits section by section.

**Design:** plain HTML and CSS (no CSS framework), readable on a phone, and it must work in a private browser window.

## Code structure (planned)

| Script | Produces |
|---|---|
| `src/load_data.py` | Cleaned tables and revenue columns (done). |
| `src/q1_growth.py` | Q1 figure and tables. |
| `src/q2_concentration.py` | Q2 figure and table. |
| `src/q3_sales_team.py` | Q3 figure and table. |
| `src/q4_inventory.py` | Q4 figure and table. |
| `src/run_all.py` | Runs all four. |
