# Testing Environment — Sales

A **practice repository**. Everything in here is synthetic mock data built to look
like GTA high-rise pre-construction sales reporting. It exists so that git
workflows, branching, and Claude Code can be experimented with safely.

> ⚠️ **No real data.** Project names, agents, brokerages, suites and prices are
> all invented. Nothing here comes from a real CRM, a real project, or a real
> deal. Break it, delete it, force-push over it — nothing of value is at risk.

## The live dashboard

**https://ryanp15.github.io/Testing-Environment-Sales/**

Rebuilt and republished automatically every time `main` moves. Because `main`
is protected, that only happens when a pull request is merged — so the live
site always reflects reviewed, tested code.

See [docs/the-loop.md](docs/the-loop.md) for the full issue → branch → PR →
deploy cycle, which is the thing this repo exists to practise.

## What's in here

A small sales analytics project covering eight fictional high-rise developments
across Toronto, Vaughan, Mississauga and Pickering.

```
├── data/                      CSV source data
│   ├── projects.csv           8 developments: location, storeys, launch, occupancy
│   ├── unit_inventory.csv     64 suites: model, size, exposure, list price, status
│   └── sales_transactions.csv 28 firm/closed deals: price, agent, incentives
├── src/
│   ├── loader.py              reads the CSVs into dicts
│   ├── metrics.py             $/sqft, absorption, discount, days-on-market
│   ├── report.py              command-line reporting
│   └── build_site.py          generates the static HTML dashboard
├── tests/
│   ├── test_metrics.py        18 tests — maths plus data integrity checks
│   └── test_build_site.py     18 tests — formatters plus generated-site checks
├── docs/
│   ├── data_dictionary.md     every column, explained
│   ├── practice-git.md        suggested git exercises
│   └── the-loop.md            the full issue → PR → deploy cycle
└── .github/
    ├── workflows/ci.yml       tests + build on every PR (required to merge)
    ├── workflows/deploy.yml   publishes to GitHub Pages on merge to main
    └── ISSUE_TEMPLATE/        bug report and change request forms
```

## Running it

Stock Python 3 — no packages to install.

```bash
python3 -m src.report
```

Other views:

```bash
python3 -m src.report --by model       # pricing by suite type
python3 -m src.report --by agent       # sales leaderboard
python3 -m src.report --by exposure    # the south-facing premium
python3 -m src.report --project GG-02  # single project, suite by suite
```

## Previewing the dashboard locally

Build it, then serve it — opening the HTML directly with `file://` breaks the
stylesheet, so use the little web server:

```bash
python3 -m src.build_site && python3 -m http.server 8765 --directory site
```

Then open http://localhost:8765. The `site/` directory is generated and
git-ignored; CI rebuilds it from `data/` on every deploy.

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

## The metrics, briefly

| Metric | Meaning |
| --- | --- |
| **$/sqft** | Price ÷ interior square feet. Balconies excluded — GTA pre-construction prices on interior area. |
| **Absorption** | Share of tracked units that are firm or closed. The headline health number for a launch. |
| **Discount** | How far below list a suite actually traded. |
| **Days on market** | Launch date → firm date. |
| **Exposure premium** | The uplift buyers pay for south and southeast views. |

## Unit statuses

| Status | Meaning |
| --- | --- |
| `available` | Still sellable |
| `held` | Temporarily off-market (broker hold, pending paperwork) |
| `firm` | Sold, past the rescission period |
| `closed` | Sold and title transferred |
