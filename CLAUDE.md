# CLAUDE.md

Instructions for Claude Code when working in this repository.

## What this repo is

A sandbox. All data is synthetic mock GTA high-rise sales data — see
[README.md](README.md). Nothing here is production, so there is no risk in
experimenting. Do not treat any figure in `data/` as real.

## Running things

```bash
python3 -m src.report                  # portfolio summary
python3 -m src.build_site              # generate the HTML dashboard into site/
python3 -m unittest discover -s tests  # full test suite
```

Stock Python 3.9+, standard library only. Do not add third-party runtime
dependencies without being asked — keeping it dependency-free is deliberate.

## Branching — `main` is protected

**Never commit directly to `main`; the remote will reject it.** Always work on
a branch and open a pull request:

```bash
git switch -c fix/short-description
```

CI must pass before a PR can merge, and merging to `main` is what deploys the
live dashboard. See [docs/the-loop.md](docs/the-loop.md).

## Conventions

- **Data lives in `data/`** as CSV. Source of truth. Never write generated
  output back into `data/`.
- **Metrics go in `src/metrics.py`** as pure functions taking plain
  lists/dicts, so they stay unit-testable. Formatting belongs in `report.py`
  or `build_site.py`, never in `metrics.py`.
- **`site/` is generated output.** It is git-ignored and rebuilt by CI. Edit
  `src/build_site.py`, never the HTML/CSS/JS it emits.
- **The dashboard and the CLI report must agree.** Both read the same
  `metrics.py`; if a figure differs between them, that is a bug in whichever
  one re-implements the calculation.
- **$/sqft always uses `interior_sqft`**, never interior + balcony. This
  matches how GTA pre-construction is actually priced.
- **Every new metric gets a test** in `tests/test_metrics.py`.
- Money is whole Canadian dollars, no cents. Dates are ISO `YYYY-MM-DD`.

## After making changes

Always run the test suite before reporting a change complete. The
`TestDataIntegrity` tests will catch a broken foreign key if a CSV was edited
by hand.

If the change touches anything the dashboard renders, rebuild it and look at
the result before saying it works:

```bash
python3 -m src.build_site && python3 -m http.server 8765 --directory site
```

Opening `site/index.html` over `file://` breaks the stylesheet — serve it.

---

## Process instructions

<!--
    Ryan: this is the section to fill in later.

    This is where a repeatable process gets written down so Claude follows the
    same steps every time. Write it as plain numbered instructions — Claude
    reads this file automatically at the start of every session in this repo.

    Example shape:

    ### Monthly sales reporting
    1. Confirm which month is being reported on.
    2. Read the new figures from <source>.
    3. Append rows to data/sales_transactions.csv, matching existing format.
    4. Run the test suite to confirm referential integrity.
    5. Run `python3 -m src.report` and summarise what moved vs last month.
    6. Commit on a branch named `report/YYYY-MM`, never directly on main.
-->

_Not written yet._
