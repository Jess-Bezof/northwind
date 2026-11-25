# CLAUDE.md

Guidance for Claude Code (the AI agent) working in this project. The full brief is in [15.561 FA26 HW 3_ AI-Assisted Business Data Analysis.md](15.561%20FA26%20HW%203_%20AI-Assisted%20Business%20Data%20Analysis.md). If that file and this one disagree, the homework file wins. The brief is kept out of the public GitHub repo (`.gitignore`, LOG D38), so this link works only in the local project folder.

## Project goal

MIT 15.561 (Fall 2026), HW 3: AI-Assisted Business Data Analysis.

We are advising a manager who wants to understand the organization behind the Northwind dataset. The work is to ask useful business questions, choose suitable analyses and visualizations, check the results, and explain what the evidence means for the business. The findings are published on a public webpage, backed by reproducible Python code in a public GitHub repository.

Writing code is only part of the job. The point is the questions asked, the analytical choices, and correct, defensible conclusions.

## Roles and responsibilities

### The student (owner of the work)

The student is responsible for the questions, analytical choices, accuracy, and conclusions that are submitted. Specifically, the student:

- Chooses and approves the business questions (at least three).
- Approves the analytical approach and chart type for each question before the final build.
- Checks key numbers, figures, and tables before trusting them, for example by cross-checking against the Excel file or re-running the code.
- Pushes back, corrects the agent, or rejects suggestions where needed, and keeps a note of these moments for the reflection report.
- Writes the 1–2 page reflection report **personally, without AI help**.
- Creates and owns the public GitHub repository and the public webpage, and submits the Google Doc link on Canvas.
- Tests every public URL in an incognito/private browser window before submitting.

### Claude Code (the AI agent)

The agent may help with: inspecting the data, planning, writing and debugging code, building charts, drafting webpage text, and building the webpage. In doing so, the agent must:

- **Write Python only** for all analysis code. Do not use R, SQL files, notebooks in other languages, or JavaScript-based analysis. The webpage itself may use HTML/CSS, but every number, figure, and table on it must come from Python.
- **Propose, don't decide.** Offer candidate business questions, methods, and chart choices with short reasons, and let the student pick. Don't quietly settle analytical choices that change the conclusions (for example how revenue is defined, whether discounts are included, how dates are cut, how outliers are treated). State them and ask.
- **Show your checks.** For every key figure, report how it was computed and include a sanity check (row counts, totals that match, join cardinality, null counts). Flag anything surprising instead of hiding it.
- **Be honest about limitations.** Point out data-quality problems, small sample sizes, partial periods (for example a final month with incomplete data), and places where correlation is being read as causation.
- **Keep it reproducible.** Scripts must run end to end from the raw `Northwind Database.xlsx` with no manual steps and no hard-coded results.
- **Document all Python code with the `python-docstrings` skill** (see below).
- **Do not write the reflection report**, and do not draft, outline, or edit its prose. The agent may answer factual questions about what happened in the session (for example "which command did we run?").
- **Do not push to GitHub, publish the webpage, or make anything public** without the student's explicit go-ahead each time.

## Current analysis plan

The four agreed business questions, with their analyses, visuals, decisions, and open choices, are in [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md). Follow it when building the analysis, and update it when the student changes a choice.

## Decision log

[LOG.md](LOG.md) records every project decision. **Whenever a decision is made or changed** (questions, definitions, thresholds, methods, tooling, process), append a numbered entry under the current date with:
- the decision
- why it was made
- who decided (*Student*, or *Agent → Student*)
- **Pushback**, if the student questioned, corrected, or redirected the agent

Never rewrite past entries. If a decision is reversed, add a new entry that references the old one.

## Deliverables and requirements

### 1. Webpage (public URL)

- At least **three meaningful business questions**, each linked to a decision, opportunity, risk, or operational understanding. Questions must require analysis and interpretation, not simply looking up a value.
  - Too simple: "Which product has the most orders?"
  - Stronger: "Which customer markets are growing or declining over time, and where should sales attention be focused?"
- For **each** question, the page shows:
  1. The question
  2. Why it matters
  3. The analytical approach
  4. A visualization or table (at least one purposeful visual per question, unless a table communicates the result more clearly)
  5. The main finding
  6. The business implication / interpretation
- Visualization standards: label axes **with units**, use readable titles and legends, and match chart type to purpose:
  - Bar / grouped bar: comparisons and rankings
  - Line: change over time
  - Scatter (optionally with trend line): relationships between numeric variables
  - Histogram / box / violin: distributions, variation, outliers
  - Heatmap: patterns across two dimensions or among several variables
  - Table: when exact values matter more than shape
- The page must be viewable by someone with no access to this computer, with all charts loading.

### 2. Code (public GitHub repository)

- Python only, reproducible from the provided Northwind dataset.
- A `README.md` that explains how to reproduce every number, figure, and table on the webpage: environment setup, dependencies, the command(s) to run, and where outputs are written.
- Pin dependencies in `requirements.txt`.
- Every function, method, class, and module documented via the `python-docstrings` skill.

### 3. Skill use (`python-docstrings`)

- The skill is installed at [.claude/skills/python-docstrings/SKILL.md](.claude/skills/python-docstrings/SKILL.md) (the course-provided file; the original copy in the project root was removed by the student to avoid duplication) and is called with `/python-docstrings <file or folder>`. It writes PEP 8 / PEP 257 docstrings (Google style by default) in one pass, then reports the docstrings written and any **assumptions to check**.
- **Timing (hybrid, LOG D12):** run it on each script right after the student approves that script's output, then once more on all of `src/` at the end. Don't add docstrings while writing new code; the skill writes them.
- When it runs, keep its report (docstrings written, assumptions, "also noticed") in the conversation so the student can review it and describe in the reflection what the skill does and how it was called.
- Per the skill's rules, docstring passes change **only docstrings**, never code.

### 4. Reflection report (student only, no AI)

A 1–2 page Google Doc written by the student. For reference only, so the agent knows what to keep traceable. It covers:

- What the student asked the agent to do and how the approach changed over time
- Which parts the agent did (inspection, planning, coding, debugging, charting, writing, webpage)
- What the student checked personally before trusting results
- At least one instance of pushing back, correcting, or rejecting the agent's suggestion, linked to lecture concepts
- What the student learned about the analysis and about working with an AI coding agent
- A paragraph on the `python-docstrings` skill: what it does and how it was called

Short excerpts or screenshots may go in an appendix.

### Submission

One Canvas URL to the Google Doc. **At the start of the doc:** the public webpage URL and the public GitHub repository URL. Test all URLs in an incognito window.

## Data notes

Source: `Northwind Database.xlsx` (8 sheets). Read it with `pandas.read_excel(..., sheet_name=...)` (requires `openpyxl`).

| Sheet | Key columns |
|---|---|
| `Categories` | CategoryID, CategoryName, Description |
| `Customers` | CustomerID, CompanyName, City, Region, Country |
| `Employees` | EmployeeID, LastName, FirstName, Title, HireDate, Country, ReportsTo |
| `Orders` | OrderID, CustomerID, EmployeeID, OrderDate, RequiredDate, ShippedDate, ShipVia, Freight, ShipCountry |
| `Orders Details` | OrderID, ProductID, UnitPrice, Quantity, Discount |
| `Product` | ProductID, ProductName, SupplierID, CategoryID, Price, UnitsInStock, UnitsOnOrder, ReorderLevel, Discontinued |
| `Shippers` | ShipperID, CompanyName |
| `Suppliers` | SupplierID, CompanyName, Country |

Known quirks to handle explicitly and mention in the README:

- The sheet name is `Orders Details` (with a space) and the product sheet is `Product` (singular).
- `Product` has leftover derived columns from earlier homework (`Cheap`, `NewPrice`, `IsCheap`, with duplicate headers) plus many blank trailing columns. Drop them; don't analyse them.
- Several sheets have empty trailing columns. Drop all-null columns after loading.
- **Revenue definition (confirmed by the student, 2026-11-23):** net revenue = `UnitPrice * Quantity * (1 - Discount)` from `Orders Details`. It uses the price charged on the order line, not the catalogue `Price`. It excludes freight and includes unshipped orders. Round `Discount` to 2 dp first (stored values have float noise, e.g. 0.15000001). Use gross revenue (`UnitPrice * Quantity`) only to measure the cost of discounting.
- `ShippedDate` can be missing (orders not yet shipped). Handle this explicitly in any lead-time or late-delivery analysis.
- Check the date range and whether the first and last months are partial before drawing trend conclusions.

## Suggested project layout

```
northwind-project/
├── CLAUDE.md
├── README.md               # reproduction guide (required)
├── requirements.txt
├── Northwind Database.xlsx # raw data, never modified
├── src/                    # Python analysis modules / scripts
├── outputs/
│   ├── figures/            # generated charts
│   └── tables/             # generated CSV/HTML tables
└── docs/                   # webpage (index.html, hosted on Netlify)
```

- **Tests (LOG D14):** every question script gets `tests/test_qN_*.py` (pytest). Each test file should include:
  - at least one independent recomputation from the raw Excel file (the `raw_lines` fixture), not the `src/` code
  - rule, reconciliation, and edge-case checks
  - one value hand-checked by the student

  Run `python -m pytest` before asking the student to approve a question.
- Never modify the raw Excel file. Write all derived data to `outputs/`.
- One command (for example `python src/run_all.py`) should regenerate every output used on the webpage.
- Use fixed random seeds wherever randomness is involved.

## Working conventions

- Use Windows paths carefully. Build file paths with `pathlib` relative to the repo root, never absolute user paths.
- Before building charts, show the student a short summary of the data (shapes, date ranges, nulls) and the proposed questions.
- After each analysis step, give a brief summary: what was computed, key numbers, sanity checks, open choices for the student.
- Don't commit or push without being asked. Don't commit secrets or large generated files that aren't needed.
