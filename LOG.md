# Decision Log

Record of project decisions, newest at the bottom. Each entry says what was decided, why, and who decided it.

- **Decided by:** *Student* means the student chose it. *Agent → Student* means the agent proposed it and the student approved or changed it.
- **Pushback** marks moments where the student questioned, corrected, or redirected the agent (useful for the reflection report).

---

## 2026-11-23

### D1. Project guide (CLAUDE.md)
- **Decision:** Created `CLAUDE.md` from the homework brief. It sets out the requirements, the deliverables, and the split of responsibilities: the student owns the questions, choices, verification, and reflection; the agent writes Python only and proposes rather than decides.
- **Why:** Keep the agent aligned with the homework rules across sessions.
- **Decided by:** Student request; content drafted by agent.

### D2. Install the docstring skill
- **Decision:** Copied the course `SKILL.md` to `.claude/skills/python-docstrings/SKILL.md`. It is called with `/python-docstrings <path>`.
- **Why:** The homework requires installing the skill in the coding agent. A file in the project root is not picked up as a skill.
- **Decided by:** Agent → Student.

### D3. Project layout
- **Decision:** Created `src/`, `outputs/figures/`, `outputs/tables/`, `docs/`, `README.md`, a pinned `requirements.txt`, and `.gitignore`.
  - `src/load_data.py` loads and cleans all 8 sheets: it drops blank columns and the leftover `Cheap`/`NewPrice`/`IsCheap` columns, and parses dates.
  - `src/run_all.py` is the single entry point.
- **Why:** Reproducibility requirement. One command must regenerate every output.
- **Decided by:** Student request (layout proposed in CLAUDE.md).

### D4. Exploratory notebook
- **Decision:** Created `notebooks/01_exploration.ipynb` with an overview, time trends, markets, products, discounts, sales team, shipping, inventory, observations, and candidate questions. It is exploratory only; final code lives in `src/`.
- **Data checks made:**
  - Joins neither add nor drop rows, and all keys match.
  - The garbled characters in names are only a terminal display issue.
  - The odd 1–6% discounts all come from order #11077.
- **Decided by:** Student request.

### D5. Revenue definition: net of discount
- **Decision:** Revenue = `UnitPrice × Quantity × (1 − Discount)`.
  - Uses the price charged on the order line, not the catalogue price.
  - Excludes freight and includes unshipped orders.
  - `Discount` is rounded to 2 dp first, because of float noise such as 0.15000001.
  - Gross revenue is used only to measure the cost of discounting.
- **Why:** Net revenue is what Northwind actually receives and is the standard accounting measure. Discount rates vary a lot by market and customer (2% for Mexico vs 13% for Ireland; 2% to 15% across customers), so gross revenue would distort comparisons.
- **Decided by:** Agent default → **Pushback:** the student asked why discounts should be deducted → student confirmed after the explanation.
- **Implemented in:** `src/load_data.py` (`Revenue`, `GrossRevenue` columns).

### D6. Strengthening the student's first question set
- **Student's original five questions:**
  1. Customer with the biggest impact on growth
  2. Countries' customer concentration
  3. Country with the highest revenue increase
  4. Most "efficient" employee by average revenue
  5. Shipper with the most late orders
- **Assessment:** All five were "which X has the highest Y" lookups, matching the homework's "too simple" example.
- **Changes:**
  - Q1 and Q3 merged into one growth question (markets plus customers), since both asked where growth came from.
  - Q2 reframed as dependence on one or two customers (revenue at risk).
  - Q4 reframed from "efficiency" (not measurable: no hours or cost data) to whether top performers win more orders or bigger orders.
  - Q5: a count of late orders favours the busiest shipper, so a late rate is needed.
- **Data rule set here:** compare Jan–Apr 1997 with Jan–Apr 1998, because 1998 data ends on 6 May.
- **Constraint from the student:** enhance, but keep the analysis simple enough to design.
- **Decided by:** Agent → Student.

### D7. Shipping question dropped
- **Option A, the student's proposal:** "Which products are delayed the most, and how does this affect shipper revenue?" **Rejected**, because:
  - only 37 of 809 shipped orders are late, and no product appears on more than 5 of them;
  - lateness is a property of the whole order, not of one product;
  - shipper revenue and lost-sales data don't exist in the dataset.
- **Finding:** `ShippedDate` is when the order leaves Northwind. Lateness therefore mostly measures Northwind's own dispatch speed, not shipper performance.
- **Option B, a freight-cost-by-shipper question:** **Considered, then dropped.**
  - Germany was chosen to control for distance: 122 orders in a compact country, so destinations vary little in distance. Single-customer cities (Cunewalde, Graz, Boise) were identified as a cross-check.
  - The cheapest shipper differs by country and city, so the finding would likely be "no consistent difference".
- **Decided by:** Student (question choice) with agent data checks.

### D8. Inventory question replaces shipping
- **Student's proposal:** "Which products are likely to stock out based on units in stock, reorder level, and units on order?"
- **Enhancement:** Using only those three fields, the answer is a filter that finds just one product (Nord-Ost Matjeshering), so demand (monthly sales) was added to calculate months of cover.
- **Final wording:** "Which products are at risk of stocking out, and are reorder levels set in line with how fast products actually sell?"
- **Supporting evidence:**
  - Reorder levels are unrelated to demand (Spearman ρ ≈ −0.04).
  - 16 active products have a reorder level of 0.
- **Caveat:** The stock snapshot is undated and looks low relative to sales, so present this as a reorder-policy finding, not an exact forecast.
- **Decided by:** Student → enhanced by agent → Student approved.

### D9. Final four questions and the analysis plan
- **Decision:** `ANALYSIS_PLAN.md` records the four questions, each with its rationale, analysis, visual, decision, caveats, and outputs:
  - Q1. Growth drivers (markets and customers)
  - Q2. Customer concentration risk
  - Q3. Sales team: more orders or bigger orders
  - Q4. Stock-out risk and reorder policy
- **Decided by:** Student.

### D10. Design choices for each question
- **Q1:** The chart shows the top 10 countries by total revenue plus any decliners. Four declined (Denmark, Canada, Mexico, Finland); Canada is already in the top 10, giving 13 countries.
- **Q2:** "Dependent" means the top customer brings in ≥ 50% of the country's revenue. The student's condition was to keep it if enough countries qualify; 12 of 21 do, so it is kept.
- **Q3:** Sales representatives only. The student's condition was that there must be enough of them; there are 6.
  - Excluded: Fuller (VP Sales), Buchanan (Sales Manager), and Callahan (Inside Sales Coordinator).
  - Together the excluded staff account for ~29% of revenue; state this on the page.
- **Q4:** Demand window Jan–Apr 1998; at risk means less than 1 month of cover.
- **Decided by:** Student, with agent checks of the conditions.

### D11. Build process
- **Decision:**
  1. Build a shared order-line preparation function first, with checks on the joins.
  2. Build one script per question (`q1_growth.py` … `q4_inventory.py`), with student review of each output before moving on.
  3. Wire them into `run_all.py`, then run everything from scratch to confirm it reproduces.
  4. Update the README, then build the webpage, then GitHub.
- **Decided by:** Agent → Student.

### D12. Docstring timing: hybrid
- **Decision:** Run `/python-docstrings` on each script after the student approves its output, then run it once more on all of `src/` at the end.
- **Why:**
  - The per-script runs give fresh context and catch unclear code early.
  - The final run fixes docstrings that no longer meet the skill's rules.
  - The final run will not catch a docstring that still meets the rules but describes old behaviour.
  - This was compared against "during development only" and "after development only" (comparison table in the conversation).
- **Decided by:** Student (the agent had recommended a single pass at the end).

### D13. Q1 chart: keep the rule, Belgium excluded
- **Context:**
  - The shared order-line step (`build_order_lines`) and `src/q1_growth.py` were built and run.
  - The Jan–Apr totals reconcile ($191,322 → $422,290, +121%).
  - Belgium grew +$10.0k (more than Venezuela) but is neither in the top 10 by total revenue nor a decliner.
- **Decision:** Keep the D10 rule. Belgium stays out of the chart and remains in `q1_growth_by_country.csv`.
- **Decided by:** Student.

### D14. Add a pytest test suite
- **Decision:** Add `pytest` (pinned in `requirements.txt`) and a `tests/` folder with one test file per question.
- **Why:**
  - The in-script assertions catch mechanical errors (joins, totals) but not logic errors, such as a wrong period filter.
  - Recomputing key numbers from the raw Excel file by an independent route catches those.
  - Tests also give concrete, repeatable evidence for the "what I verified" part of the reflection.
- **Q1 tests (`tests/test_q1_growth.py`), 7 tests, all passing:**
  - period filter is Jan–Apr only
  - yearly totals match an independent calculation
  - Denmark matches both the independent calculation and hand-checked values
  - country changes add up to total growth
  - the chart includes exactly the top 10 plus decliners (13 countries, no Belgium)
  - a new market (Poland) gets a blank % change
  - customer contributions add up to each country's change
- **Check that the tests work:** with a deliberately planted bug (May included in the period), 4 of the 7 tests failed as expected.
- **Open:** the student still has to confirm the Denmark values ($13,706.40 and $4,284.00) in Excel.
- **Decided by:** Agent proposed → Student approved.

### D15. Q1 docstrings accepted (first per-script skill pass)
- **What happened:** The student ran `/python-docstrings src/load_data.py src/q1_growth.py tests/`. The skill wrote 25 Google-style docstrings (modules, functions, fixtures, and tests) and rewrote one incomplete docstring (`raw_lines`).
- **Skill report:** 6 assumptions to check and 4 "also noticed" items, all accepted without corrections. One noteworthy item: `raw_lines` reuses the revenue formula, so the independent check covers filtering and joins, not the formula itself.
- **Verified after the pass:** code unchanged; 7/7 tests pass; `run_all.py` gives the same numbers.
- **Decided by:** Student.

### D16. Q2 built (awaiting student review)
- **What was built:** `src/q2_concentration.py`, which writes `q2_concentration_scatter.png`, `q2_concentration_by_country.csv`, and `q2_riskiest_markets.csv`. It also added `tests/test_q2_concentration.py`: 6 tests, all passing.
- **Planted-bug checks:**
  - Using gross instead of net revenue failed 3 tests.
  - A changed threshold failed 1 test.
- **Agent presentation choices (for student review):**
  - The x-axis uses a log scale, because country revenue ranges from $3.5k to $246k and a linear axis bunches the small markets together.
  - Bubble size shows the number of customers.
  - A legend replaces the in-chart threshold label, which overlapped Portugal.
- **Open issue raised by the agent:** Germany (48.6%) and the USA (42.5%) fall just under the 50% threshold. Yet they have the largest single-customer exposure in dollars: QUICK-Stop $110k and Save-a-lot $104k. The share-based rule misses them.
- **Open:** the student to confirm the Austria values (revenue $128,003.84; Ernst Handel $104,874.98) in Excel.

### D17. Q2: keep the 50% share rule; note Germany and the USA in the text
- **Options considered:**
  1. Keep the rule and mention the large dollar exposures in the text.
  2. Add a second rule based on share of company revenue.
  3. Rank the risk table by dollars at risk across all countries.
- **Decision:** Option 1. The rule and the code are unchanged. The webpage text for Q2 must say that Germany (QUICK-Stop, $110k) and the USA (Save-a-lot Markets, $104k) fall just under 50% yet carry the largest single-customer dollar exposure.
- **Why:** Keeps the analysis simple, and the scatter already shows both countries in the bottom-right.
- **Presentation choices accepted by default:** log-scale x-axis, bubble size showing the number of customers, legend.
- **Decided by:** Student (option 1 was also the agent's recommendation).

### D18. Q2 docstrings accepted (second per-script skill pass)
- **What happened:** The student ran `/python-docstrings src/q2_concentration.py tests/test_q2_concentration.py`. The skill wrote 13 docstrings.
- **Skill report:** 3 assumptions to check and 3 "also noticed" items, all accepted without corrections:
  - customers are grouped by name rather than ID (the tests confirm there are no clashes)
  - `RevenueAtRisk` duplicates `TopCustomerRevenue`
  - ties in top revenue would be broken silently
- **Verified after the pass:** 13/13 tests pass.
- **Decided by:** Student.

### D19. Q3 built (awaiting student review)
- **What was built:** `src/q3_sales_team.py`, which writes `q3_employee_scatter.png` and `q3_employee_summary.csv`. It also added `tests/test_q3_sales_team.py`: 6 tests, 19/19 passing overall.
- **Planted-bug check:** counting order lines instead of orders failed 2 tests.
- **Agent method choices (for student review):**
  - **"Top vs bottom" gap:** compares the highest- and lowest-revenue reps (Peacock vs Suyama). Revenue ratio = orders ratio × average-order-value ratio. A log split gives each driver's share of the gap.
  - **"Vs team" columns:** each rep is compared with the rep-team average. For orders this is the mean number of orders. For average order value it is total rep revenue ÷ total rep orders.
  - **Chart:** dotted curves mark equal total revenue, bubbles are coloured by office, and two labels were moved because they overlapped.
- **Decided by:** pending student review (resolved in D20).

### D20. Q3: whole-team pattern instead of a top-vs-bottom percentage split
- **Issue raised by the agent:**
  - The "74% of the gap comes from number of orders" figure (Peacock vs Suyama) depends on which two reps are compared.
  - Against Dodsworth, who has a *larger* average order than Peacock, number of orders explains more than 100% of the gap.
- **Options:**
  1. Keep the top-vs-bottom split and add a caveat.
  2. Drop it and describe the whole team.
- **Decision:** Option 2.
  - Removed `explain_gap`.
  - Added `driver_summary`: the spread (max ÷ min) of revenue, orders, and average order value across the 6 reps, plus each driver's Spearman rank correlation with revenue.
  - Writes `q3_drivers.csv`.
- **Result:**
  - Orders vary 3.6x and average order value 1.6x.
  - Rank correlation with revenue: orders 0.94, average order value −0.09.
  - Revenue ranking follows order count; order size is unrelated.
- **Tests:** the gap test was replaced by a spread test and a rank-correlation test. The rank-correlation test checks against values worked out by hand with Spearman's formula. 20/20 pass.
- **Accepted by default:** the "vs team" average-order-value definition, the dotted equal-revenue curves, and the label positions.
- **Decided by:** Student (option 2 was also the agent's recommendation).

### D21. Q3 docstrings accepted (third per-script skill pass)
- **What happened:** The student ran `/python-docstrings src/q3_sales_team.py tests/test_q3_sales_team.py`. The skill wrote 18 docstrings, including the nested `spread` helper.
- **Skill report:** 3 assumptions to check and 4 "also noticed" items, all accepted without corrections:
  - `Office` is derived twice
  - employees with no orders would drop out silently
  - two tests hard-code values from the current data
- **Verified after the pass:** 20/20 tests pass.
- **Decided by:** Student.

## 2026-11-24

### D22. Q4 built (awaiting student review)
- **What was built:** `src/q4_inventory.py`, which writes:
  - `q4_reorder_vs_demand.png`
  - `q4_lowest_cover.csv` (10 rows)
  - `q4_inventory_all_active.csv`

  It also added `tests/test_q4_inventory.py`: 6 tests, 26/26 passing overall. `run_all.py` now runs all four questions.
- **Planted-bug check:** a demand window of Jan–May (including the partial May) failed 3 tests.
- **Agent method choices (for student review):**
  - The 3 active products with no Jan–Apr 1998 sales get a blank months-of-cover. They are not counted as at risk, and they appear grey on the chart.
  - Reorder levels are multiples of 5, so points get a small horizontal jitter (fixed seed 0) to stop them overlapping.
  - The chart labels the 4 fastest sellers that have a reorder level of 0.
- **Decided by:** pending student review (resolved in D23).

### D23. Q4 accepted; Q4 and run_all docstrings accepted (fourth per-script skill pass)
- **Q4 method choices from D22:** accepted without change (blank cover for the no-sales products, jitter, labels).
- **What happened:** The student ran `/python-docstrings src/q4_inventory.py tests/test_q4_inventory.py src/run_all.py`. The skill wrote 19 docstrings.
- **Skill report:** 4 assumptions to check and 4 "also noticed" items, all accepted without corrections. One item (`q4_inventory_all_active.csv` missing from `ANALYSIS_PLAN.md`) was fixed in the plan.
- **Verified after the pass:** 26/26 tests pass.
- **Next:** the final hybrid docstring pass over all of `src/` and `tests/` (LOG D12).
- **Decided by:** Student.

### D24. Final docstring pass (hybrid approach complete)
- **What happened:** Ran `/python-docstrings src/ tests/` at the student's request. The skill checked 75 docstrings against the rules and the current code. 72 were left unchanged and 3 were rewritten:
  - the Q3 module summary ended with "?"
  - two Q4 tests used a bare `dict` type for `raw`, inconsistent with the fixture
- **Result:** no new assumptions to check. Code unchanged: 26/26 tests pass and the `run_all.py` output is identical.
- **What it showed about the hybrid approach:** none of the per-script docstrings had gone stale, because the code didn't change after each pass. The final pass mainly caught formatting and consistency slips.
- **Decided by:** Student.

### D25. Hand checks confirmed; clean reproduction found a missing dependency
- **Hand checks:** the student confirmed all four hand-checked values in Excel. The test comments now say "confirmed by the student in Excel on 2026-11-24".
  - Q1 Denmark: $13,706.40 / $4,284.00
  - Q2 Austria: $128,003.84, with Ernst Handel at $104,874.98
  - Q3 Peacock: 156 orders, $232,890.85
  - Q4 Camembert Pierrot: stock 19, 540 units sold Jan–Apr 1998
- **Clean reproduction:**
  - Method: copied only what the repo will contain (`src/`, `tests/`, `requirements.txt`, the Excel file) to a scratch folder, created a fresh virtual environment, installed `requirements.txt`, and ran `run_all.py` and `pytest`.
  - Problem found: the first attempt **failed**. pandas needs `scipy` for Spearman correlations (Q3, Q4), and `scipy` was installed on the student's machine but missing from `requirements.txt`.
  - Fix: added `scipy==1.18.1`.
  - Result: 26/26 tests pass; the printed output and all 8 CSV tables are byte-identical to the originals.
- **Why it matters:** this is exactly the kind of "works on my machine" error the reproducibility requirement is meant to catch.
- **Decided by:** Student (hand checks); agent (dependency fix, a mechanical correction).

### D26. README finished; webpage plan agreed
- **README:** finished. It now has:
  - a table mapping each question to its script and output files
  - the key analytical choices
  - data cleaning and the revenue definition
  - limitations
  - the full repository layout
  - how the docstrings were produced with the skill
  - a note that the clean reproduction was verified
- **Webpage decisions (student):**
  1. **Numbers:** Python fills an HTML template (`src/build_site.py`), so the page text can't drift from the analysis. (Agent recommendation.)
  2. **Charts: interactive Plotly** rather than the existing static PNGs. This was against the agent's recommendation of static PNGs.
     - Cost: a new dependency, four charts to re-verify, and plotly.js loaded from a CDN.
     - Mitigation: the Plotly charts keep the reviewed matplotlib encodings and are built from the same tested DataFrames; the PNGs stay in the repo.
  3. **Text:** the agent drafts and the student edits section by section. (Agent recommendation.)
  4. **Author:** no name on the page.
- **Plan recorded in:** `ANALYSIS_PLAN.md`, "Webpage plan".
- **Decided by:** Student.

### D27. Webpage step 1 built: skeleton plus Q1 (awaiting student review)
- **Built:**
  - `src/build_site.py`: number formatting, HTML tables, Plotly charts, and template filling.
  - `site/template.html`: the page text and CSS.
  - `docs/index.html`: generated output.
  - `docs/.nojekyll`
  - `plotly==7.1.0` pinned in `requirements.txt`. plotly.js 4.1.1 is loaded from cdn.plot.ly.
  - `run_all.py` now builds the site last.
- **No hand-typed numbers:** every figure in the text comes from the code, including counts written as words ("four months", "ten largest", "three markets"). The only digits left in the template are section labels and the revenue formula.
  - One fix came from this: the first draft had "the four shrinking markets" and "Hanari Carnes alone" typed by hand. Both are now generated.
- **Correction to an earlier chat figure:** the top 3 countries delivered **57%** of the growth (exact sum, 57.4%). The agent had earlier quoted 58% by adding rounded shares. The page uses the exact figure.
- **Q1 chart (Plotly):** same encoding as the reviewed PNG (13 countries, colours, starred decliners, change labels). Hover shows both years and the change.
- **Agent writing choices for student review:**
  - The text is in the first person ("I compared…").
  - The page title is "Northwind: where to focus next".
  - The Q1 implication recommends protecting the growth accounts and investigating France and Denmark.
- **Checks:** 26/26 tests pass; the page has no unfilled placeholders.
- **Decided by:** Student approved Q1 ("looks fine") → resolved.

### D28. Webpage step 2 built: Q2–Q4 sections (awaiting student review)
- **Built:** Q2, Q3, and Q4 sections in `site/template.html`, plus their context functions and Plotly charts in `src/build_site.py`. Each section has the six required parts, a chart, and a table:
  - Q2: all 12 dependent markets.
  - Q3: the 6 reps.
  - Q4: the 10 products with the least cover.
- **Notes required by earlier decisions are in the text:**
  - Q2: Germany and the USA fall under the threshold yet carry the largest dollar exposure (D17).
  - Q3: the 3 excluded employees and 29% of revenue; territory, seniority, and skill can't be separated (D10, D20).
  - Q4: framed as a reorder-policy finding, not a forecast (D8).
- **No hand-typed numbers:**
  - The at-risk threshold ("one month") now comes from `COVER_THRESHOLD_MONTHS`.
  - Which countries, customers, reps, and products the text names is chosen by rule, not typed. For example: the market with the most revenue at risk, the 3 markets with the lowest top-customer share, and the at-risk product with the most revenue.
- **Prose fix:** "USA" and "UK" become "the USA" and "the UK" in running text; tables and charts keep the raw names.
- **Visual check of the charts:** all four were rendered to PNG with kaleido (installed only in a scratch environment, not a project dependency) and inspected. Fixes made:
  - Q2: clipped "Germany (11)" label, Portugal label on the threshold line, cluttered log-axis ticks, UK label touching France.
  - Q3: overlapping Leverling and Davolio labels.
  - Q4: stray zero line; added the 4 fast-seller labels shown in the reviewed PNG.
- **Agent writing choices for student review:** each implication's recommendations.
  - Q2: named account plans; win extra customers in fragile markets.
  - Q3: coach for volume, especially in the UK; don't read revenue rankings as skill.
  - Q4: reset reorder levels to ≥ 1 month of demand, starting with reorder-level-0 fast sellers and Côte de Blaye.
- **Checks:** 26/26 tests pass; 4 charts, 4 tables, no unfilled placeholders.
- **Decided by:** Student approved Q2–Q4, including the implications ("look good"), on 2026-11-24 → resolved.

### D29. Q3: drop the Spearman rank correlations (partly reverses D20)
- **Pushback:** the student questioned using a Spearman rank correlation in Q3, given there are only 6 sales reps.
- **Agent's assessment:** agreed.
  - With n = 6, one coefficient summarising six people is more abstract than showing their ranking.
  - "0.94" looks more precise than it is; it really means "the bottom two swap places".
  - The page's table already shows all six reps.
  - Sample size doesn't make the statistic *wrong* here (it was descriptive, not a test), but it adds false precision without adding insight.
- **Decision:** remove both correlations and state the rank comparison directly.
  - Ranking by orders matches ranking by revenue for 4 of 6 reps; only Dodsworth and Suyama swap.
  - The rep with the largest orders (Dodsworth) is 5th in revenue; the top earner (Peacock) has the 5th-largest orders.
  - The spreads (orders 3.6×, average order value 1.6×) are kept.
- **Changes:**
  - `driver_summary` now returns the rank comparison; its old docstring was deleted, to be rewritten by the skill.
  - `q3_drivers.csv` updated.
  - The hand-computed Spearman test was replaced by a test against ranks written out by hand.
  - Page text (Approach and Main finding) and `ANALYSIS_PLAN.md` updated.
- **Unchanged:** Q4 keeps its Spearman correlation (reorder level vs demand, n = 69), so `scipy` stays in `requirements.txt`.
- **Checks:** 26/26 tests pass; no correlation is mentioned in Q3 on the page.
- **Decided by:** Student (raised it) → agent agreed → Student approved.

### D30. Q3 docstrings refreshed after D29 (fifth skill pass)
- **What happened:** The student ran `/python-docstrings src/q3_sales_team.py tests/test_q3_sales_team.py`.
  - The skill wrote 2 docstrings: `driver_summary` (whose old Spearman docstring had been deleted in D29) and the new rank-comparison test.
  - It left the other 17 unchanged.
- **Skill report:** 2 assumptions to check (rank direction; mismatch names are one string) and 2 "also noticed" items (ties would share a rank; the comment refers to log numbers).
- **Why it matters:** this is the hybrid approach working as intended. A code change made one docstring stale, and it was removed and regenerated rather than left wrong.
- **Checks:** 26/26 tests pass.
- **Decided by:** Student.

### D31. No manager summary and no data-and-method section on the page
- **Context:** the student asked whether these sections are required. They are not: the homework requires, per question, the question, why it matters, approach, visual, finding, and implication. All four sections already have these.
- **Agent's view:** the summary would be cheap and useful for a manager. The data-and-method section would mostly repeat each section's Approach and caveats, the footer, and the README.
- **Decision:** add neither. The student judged that they don't add enough value.
- **Decided by:** Student (partly against the agent's suggestion to add a short summary).

### D32. Webpage tests added
- **Refactor:** `build_site.render_page(tables)` builds the page in memory, so tests don't overwrite `docs/index.html`. `main` uses it.
- **New file `tests/test_build_site.py`, 13 tests (39/39 passing overall):**
  - **Structure:** no unfilled placeholders; 4 sections, each with the 6 required homework parts; 4 charts; table row counts 6/12/6/10; the plotly.js CDN version matches the installed plotly.
  - **Numbers on the page:**
    - Q1 totals and the Q2 Austria share are recomputed independently from the raw Excel file and matched against the page text.
    - The student's hand-checked values appear on the page (Peacock 156 orders; Camembert 19 in stock).
    - Q2–Q4 headline counts match the analysis functions.
  - **Charts:** the Q1 bar heights equal the analysis values; the Q2, Q3, and Q4 scatters plot all 21 / 6 / 69 units.
  - **The D27 rule:** the template prose contains no hand-typed numbers. Only section labels, "reorder level of 0", and "(1 − discount)" are allowed.
  - **Formatting helpers:** signs, minus character, ordinals, number words, "the USA".
- **Planted-bug checks** (each run in memory; no project files changed):
  - "57%" typed into the template → 1 failure.
  - Percentage formatter drops the sign → 2 failures.
  - Q2 table cut to 5 rows → 1 failure.
- **Not yet tested:** the GitHub repo link. It is still the placeholder `OWNER/REPO` until the repo exists; a test will be added at the publish step.
- **Decided by:** Student requested the tests; the content is the agent's design.

### D33. Webpage docstrings accepted (sixth skill pass)
- **What happened:** The student ran `/python-docstrings src/build_site.py tests/test_build_site.py`. The skill wrote 45 docstrings: 2 modules, 26 functions in `build_site.py` including 2 nested helpers, and 17 in the tests.
- **Verified:** the code with docstrings removed is identical before and after the pass, in both files. 39/39 tests pass.
- **Skill report:** 5 assumptions to check and 6 "also noticed" items, all accepted without corrections. Notable items:
  - **Correction to D28:** D28 said the named items on the page are chosen by rule. Sweden and France are in fact picked by name in `q1_context`. The numbers about them are still computed, but which countries get mentioned is an editorial choice from the exploration. Left as is.
  - 7 computed context values are unused by the template.
  - `html_table` doesn't escape HTML; no names in the data need it.
- **Decided by:** Student.

### D34. README updated; second clean reproduction passes
- **README changes:**
  - `run_all.py` now also builds the webpage.
  - The test count is now 39, with a summary of what the webpage tests check.
  - New section "How the webpage is built": template, then `build_site.py`, then `docs/index.html`; edit the template, never the output; Plotly loaded from its CDN.
  - The Q3 analytical choice now notes that ranks are compared rather than correlated (D29).
  - Repository layout now includes `build_site.py`, `site/`, `docs/`, and `test_build_site.py`.
  - The documentation note now says the skill was rerun on any file whose code changed.
- **Clean reproduction #2:**
  - Method: a brand-new virtual environment (the first one had extra packages from the chart checks), containing only what the repo will hold: `src/`, `tests/`, `site/`, `requirements.txt`, and the Excel file. No `outputs/` and no `docs/`.
  - Installed exactly the 8 pinned packages.
  - `run_all.py` succeeded and 39/39 tests pass.
  - The printed output, all 8 CSVs, the 4 PNGs, and `docs/index.html` are **byte-identical** to the originals.
- **Decided by:** Student requested; agent executed.

### D35. Webpage: one question at a time (tabs)
- **Student's request:** avoid long scrolling. Show questions one at a time, with the top area acting as a menu.
- **Options presented:**
  - (A) Separate pages `q1.html`–`q4.html`. No custom JavaScript, but more rework. The agent recommended this.
  - (B) Tabs on one page. The smallest change, but it adds hand-written JavaScript and needs a fix for charts drawn while hidden.
- **Decision:** (B) tabs, with Question 1 shown first. This was against the agent's recommendation.
- **How it was built:**
  - The menu stays at the top while scrolling, and the active tab is highlighted.
  - Previous/Next links sit at the bottom of each question.
  - Switching tabs scrolls back to the top.
  - Charts are resized when their tab opens, because charts drawn while hidden come out the wrong width.
  - **Progressive enhancement:** without JavaScript, all four questions show one after another.
  - Each question still has its own link (`#q1`–`#q4`).
- **Found through headless-Chrome screenshots, then fixed:**
  1. **Direct links jumped past the header.** A first fix (scroll to top on load) did not work, because the browser jumps after that runs. Final fix: sections are renamed `q1-section`…`q4-section`, so the `#q1` links match no element and the browser has nothing to jump to. A test now enforces this.
  2. **At a true 390 px phone width** (tested inside a 390 px iframe, because desktop Chrome will not shrink its window that far), the Plotly titles collided with the legends and labels were clipped.
     - Chart titles moved out of Plotly into HTML headings (`chart_html` now takes the title; `base_layout` no longer does), and legends moved to the top-left.
     - The Q2 axis title was shortened, and Q2 labels may draw outside the plot area (`cliponaxis=False`).
     - Charts get a minimum width of 640 px and scroll sideways on phones, like the tables.
- **Code changes:**
  - The template's CSS, menu, pager links, and script.
  - `build_site.py`: the `chart_html` and `base_layout` signatures changed. Their docstrings were deleted, to be regenerated by the skill.
  - The tests: section ids updated, and a new test for the tab and pager links.
- **Checks:** 40/40 tests pass; screenshots taken at desktop and phone width, each opened by its direct link.
- **Decided by:** Student (layout and front page); agent (fixes found during the visual checks).

### D36. Docstrings refreshed after D35 (seventh skill pass); clean reproduction #3 passes
- **Skill pass:** The student ran `/python-docstrings src/build_site.py tests/test_build_site.py`.
  - The skill wrote 3 docstrings: `chart_html` and `base_layout` (deleted in D35 after their signatures changed) and the new tab-link test.
  - The other 43 were unchanged. The code is identical apart from docstrings.
  - Report: 2 assumptions to check and 2 "also noticed" items, all accepted. Notable: the chart's minimum width now depends on `chart_html` producing the `chart` wrapper div.
- **Clean reproduction #3:** a fresh virtual environment with only the repo contents (`src/`, `tests/`, `site/`, `requirements.txt`, the Excel file).
  - Exactly the 8 pinned packages were installed (kaleido absent, as intended).
  - `run_all.py` succeeded and 40/40 tests pass.
  - The printed output, 8 CSVs, 4 PNGs, and `docs/index.html` are byte-identical to the originals (13/13 files).
- **Decided by:** Student.

### D37. Duplicate SKILL.md removed
- **What happened:** the student deleted the course-provided `SKILL.md` from the project root. The installed skill at `.claude/skills/python-docstrings/SKILL.md` remains the only copy.
- **Follow-up:** the agent had asked about it again without re-checking the folder, and fixed the now-broken link in `CLAUDE.md`. The `README.md` already pointed only to the installed copy.
- **Decided by:** Student.

### D38. Published to GitHub
- **Repository:** https://github.com/Jess-Bezof/northwind (created by the student; public, empty before the push).
- **Real links:**
  - `REPO_URL` in `build_site.py` points to the repository.
  - The README lists the webpage (https://jess-bezof.github.io/northwind/) and the repository.
  - New test: the page links to the real repository and no `OWNER/REPO` placeholder remains (41/41 pass). It awaits a docstring from the skill.
- **Kept out of the repo:** the course homework brief (`.gitignore`), so course materials are not republished. `CLAUDE.md` notes that its link to the brief works only locally.
- **Already ignored:** `.claude/settings.local.json`, caches, virtual environments, and Excel lock files.
- **Pushed:** the first commit on `main`, with the student's approval.
- **Decided by:** Student (keep the brief out; push now).
