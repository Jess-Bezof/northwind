# Northwind Business Analysis (15.561 HW 3)

Reproducible Python analysis of the Northwind dataset. It answers four business questions for a manager and produces every number, chart, and table shown on the project webpage.

- **Webpage:** https://jess-bezof.github.io/northwind/
- **Repository:** https://github.com/Jess-Bezof/northwind
- **Data:** `Northwind Database.xlsx` (provided with the course; included in this repo, never modified)

## Reproduce the results

Tested with Python 3.13 on Windows. Any Python 3.11+ should work.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python src/run_all.py
```

`run_all.py` does four things:

1. loads the workbook once;
2. runs the four question scripts in order, printing the key numbers for each question;
3. writes the charts and tables to `outputs/` (recreating the folder if it is missing);
4. rebuilds the webpage, `docs/index.html`.

Every number on the webpage can be traced to this printout or to the CSV tables below.

### Check the results

```bash
python -m pytest
```

There are 40 tests: one file per question, plus one for the webpage.

The question tests:

- recompute key numbers directly from the Excel file, by a route independent of the `src/` code, and compare them with the scripts' results;
- check that the rules are applied correctly (thresholds, which rows are included) and that totals reconcile;
- check edge cases, such as a market with no revenue in the base year;
- include one value per question that was hand-checked in Excel.

The webpage tests check:

- **Structure:** every question section has the six required parts.
- **Numbers:** key figures in the page text match independent calculations and the hand-checked values.
- **Charts:** the charts plot exactly the analysed data.
- **Navigation:** every tab and Previous/Next link points to a real question.
- **No hand-typed figures:** the page template contains no numbers typed by hand.

The repository was verified by a clean run: a fresh virtual environment built from `requirements.txt` produced identical outputs and webpage, and passed all tests.

## How the webpage is built

The webpage is generated, not hand-written:

- `src/build_site.py` takes every number, table, and chart from the analysis functions and fills them into the page template `site/template.html`. The result is `docs/index.html`, which GitHub Pages serves.
- To change the wording, edit `site/template.html` and rerun `python src/run_all.py`. Do not edit `docs/index.html` directly; it is overwritten on every run.
- Each `${name}` placeholder in the template is filled by Python. The build stops with an error if any placeholder has no value.
- The webpage charts are interactive Plotly charts. They are built from the same tested data as the static matplotlib charts in `outputs/figures/`, with the same encodings. The page loads plotly.js from the Plotly CDN, so viewing it needs an internet connection.
- The page shows one question at a time, using tabs in a menu that stays at the top of the screen. A short script at the end of the template switches tabs; it is the only hand-written JavaScript in the project, and all analysis is Python.
  - Each question has its own link: `index.html#q1` to `#q4`.
  - Without JavaScript, all four questions are shown one after another.
  - On narrow screens, charts and tables keep a readable width and scroll sideways.

## The four questions and where their outputs come from

| # | Business question | Script | Static figure (`outputs/figures/`) | Tables (`outputs/tables/`) |
|---|---|---|---|---|
| Q1 | Which markets and customers drove growth from 1997 to 1998, and where should sales attention go next? | `src/q1_growth.py` | `q1_growth_by_country.png` | `q1_growth_by_country.csv`, `q1_top_customer_contributors.csv` |
| Q2 | Which markets depend on just one or two customers, and how much revenue is at risk if a key customer leaves? | `src/q2_concentration.py` | `q2_concentration_scatter.png` | `q2_concentration_by_country.csv`, `q2_riskiest_markets.csv` |
| Q3 | Do top-performing sales reps sell more because they win more orders or bigger orders? | `src/q3_sales_team.py` | `q3_employee_scatter.png` | `q3_employee_summary.csv`, `q3_drivers.csv` |
| Q4 | Which products are at risk of stocking out, and are reorder levels set in line with demand? | `src/q4_inventory.py` | `q4_reorder_vs_demand.png` | `q4_lowest_cover.csv`, `q4_inventory_all_active.csv` |

Each script can also be run on its own, e.g. `python src/q2_concentration.py`.

### Key analytical choices

| Question | Choice |
|---|---|
| All | Revenue is net of discounts (see the next section). |
| Q1 | Compares **Jan–Apr 1997 with Jan–Apr 1998**, because the data ends on 6 May 1998. The chart shows the top 10 countries by total revenue plus every country that declined. |
| Q2 | Covers the whole period (Jul 1996 – May 1998), by customer country. A market is "dependent" when its largest customer brings in ≥ 50% of the country's revenue. |
| Q3 | Compares the 6 sales representatives only. The VP Sales, the Sales Manager, and the Inside Sales Coordinator are excluded; together they account for 29% of revenue. With only six reps, their rankings by orders, order size, and revenue are compared directly rather than summarised with a correlation coefficient. |
| Q4 | Covers the 69 active (not discontinued) products. Monthly demand = units sold in Jan–Apr 1998 ÷ 4. Months of cover = (units in stock + units on order) ÷ monthly demand. "At risk" means less than 1 month of cover. |

The full reasoning behind each choice, including options that were considered and rejected, is in `ANALYSIS_PLAN.md` and `LOG.md`.

## Data cleaning

Applied in `src/load_data.py`:

- All-blank columns and rows are dropped from every sheet.
- In the `Product` sheet, leftover derived columns from earlier coursework (`Cheap`, `NewPrice`, `IsCheap`) are removed.
- `OrderDate`, `RequiredDate`, and `ShippedDate` are parsed as dates. A missing `ShippedDate` means the order has not shipped.
- `Discount` is rounded to 2 decimals (stored values carry float noise, e.g. 0.15000001).
- `build_order_lines` joins order lines to orders, customers, employees, products, and categories. It stops with an error if a join adds or drops rows, or if a key has no match.

## Revenue definition

**Revenue** means net revenue per order line: `UnitPrice × Quantity × (1 − Discount)`.

- It uses the price charged on the order, not the catalogue price in `Product`.
- It excludes freight.
- It includes orders that have not yet shipped.

`GrossRevenue` (`UnitPrice × Quantity`) is used only to measure how much revenue discounts cost.

## Limitations

- The dataset covers 22 months, and both end months are partial. Trends rest on a single like-for-like Jan–Apr comparison.
- The stock figures in `Product` are an undated snapshot (assumed current as of May 1998). Stock is low relative to sales across most products, so Q4 is presented as a finding about the reorder policy, not an exact stock-out forecast.
- The dataset contains no costs, so the analysis covers revenue, not profit.
- Q3 shows associations only. The office (US vs UK), territory, and hire date overlap, so the data cannot separate skill from territory.

## Repository layout

```
├── Northwind Database.xlsx  # raw data
├── requirements.txt         # pinned dependencies
├── src/
│   ├── load_data.py         # loads and cleans all 8 sheets; builds the order-line table
│   ├── q1_growth.py         # Q1: growth drivers by market and customer
│   ├── q2_concentration.py  # Q2: dependence of each market on its top customer
│   ├── q3_sales_team.py     # Q3: sales reps, number of orders vs order size
│   ├── q4_inventory.py      # Q4: stock-out risk and reorder levels vs demand
│   ├── build_site.py        # fills the page template with numbers, tables, and Plotly charts
│   └── run_all.py           # single entry point that regenerates every output and the webpage
├── site/
│   └── template.html        # webpage text and styling, with ${placeholders} for every number
├── tests/                   # pytest checks: conftest.py, one file per question, test_build_site.py
├── outputs/
│   ├── figures/             # generated static charts (PNG)
│   └── tables/              # generated tables (CSV)
├── docs/                    # generated webpage served by GitHub Pages (index.html, .nojekyll)
├── notebooks/
│   └── 01_exploration.ipynb # initial exploration used to choose the questions
├── ANALYSIS_PLAN.md         # the four questions: rationale, method, visuals, decisions
├── LOG.md                   # dated log of every project decision
└── CLAUDE.md                # instructions for the AI coding agent used on this project
```

The exploration notebook is not part of the reproducible pipeline. To open it, also install Jupyter (`pip install jupyter`).

## Documentation

All Python code in `src/` and `tests/` has Google-style docstrings (PEP 257). They were generated with the course-provided `python-docstrings` skill (installed at `.claude/skills/python-docstrings/SKILL.md`) and reviewed by the author. The skill was run on each script after its results were approved, once more over the whole codebase, and again on any file whose code changed afterwards.
