# CLAUDE.md

Instructions for Claude Code when working in this repository.

## What this repo is

A sandbox. All data is synthetic mock GTA high-rise sales data — see
[README.md](README.md). Nothing here is production, so there is no risk in
experimenting. Do not treat any figure in `data/` as real.

## Running things

```bash
python3 -m src.report                  # portfolio summary
python3 -m unittest discover -s tests  # full test suite
```

Stock Python 3.9+, standard library only. Do not add third-party runtime
dependencies without being asked — keeping it dependency-free is deliberate.

## Conventions

- **Data lives in `data/`** as CSV. Source of truth. Never write generated
  output back into `data/`.
- **Metrics go in `src/metrics.py`** as pure functions taking plain
  lists/dicts, so they stay unit-testable. Formatting belongs in `report.py`,
  never in `metrics.py`.
- **$/sqft always uses `interior_sqft`**, never interior + balcony. This
  matches how GTA pre-construction is actually priced.
- **Every new metric gets a test** in `tests/test_metrics.py`.
- Money is whole Canadian dollars, no cents. Dates are ISO `YYYY-MM-DD`.

## After making changes

Always run the test suite before reporting a change complete. The
`TestDataIntegrity` tests will catch a broken foreign key if a CSV was edited
by hand.

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
