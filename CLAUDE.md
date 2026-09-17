# CLAUDE.md

Instructions for Claude Code when working in this repository.

## What this repo is

A sandbox. All data is synthetic mock GTA high-rise sales data — see
[README.md](README.md). Do not treat any figure in `data/` as real.

The *data* carries no risk, but the repository is **public** and merging to
`main` publishes a **public website**
(https://ryanp15.github.io/Testing-Environment-Sales/). So experiment freely
with the code and the figures, and treat pushing and merging as the real
actions they are — see [Process instructions](#process-instructions).

## Running things

```bash
python3 -m src.report                  # portfolio summary
python3 -m src.build_site              # generate the HTML dashboard into site/
python3 -m unittest discover -s tests  # full test suite
```

Stock Python 3.9+, standard library only. Do not add third-party runtime
dependencies without being asked — keeping it dependency-free is deliberate.

## Branching — `main` is protected

**Never commit directly to `main`; the remote will reject it.** Always pull
first, then work on a branch and open a pull request:

```bash
git switch main && git pull
git switch -c fix/short-description
```

CI must pass before a PR can merge, and merging to `main` is what deploys the
live dashboard.

> **Pushing and merging both require confirmation first.** See
> [Process instructions](#process-instructions) below for the full rules, and
> [docs/the-loop.md](docs/the-loop.md) for the commands.

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

**These are hard rules, not suggestions.** They exist for two reasons: the local
clone can silently fall behind the remote, and a merge to `main` publishes to a
public website. Follow them in order, every session.

### 1. Start from current — always pull first

Before reading, analysing or changing anything, confirm the clone matches the
remote. Do not assume it is up to date, even if it was current an hour ago —
changes may have been made on GitHub, from another machine, or in another
session.

```bash
git status                 # confirm a clean tree BEFORE pulling
git switch main
git pull
```

- If `git status` is **not** clean, stop and say so. Show what is uncommitted
  and ask how to handle it. Never pull over uncommitted work, and never
  discard it to make the pull succeed.
- If the pull brings in changes, say what arrived before continuing.
- If a question can be answered from the code, still pull first — an answer
  based on a stale clone is a wrong answer.

### 2. Every change goes on its own branch

Never commit to `main`. Branch before the first edit, not after:

```bash
git switch -c <type>/<short-description>
```

Use `fix/`, `feature/`, `docs/`, `data/` or `report/` as the type. Name the
branch after what the change does.

### 3. Stop and confirm BEFORE pushing or committing

Do not push or commit on your own initiative. When the change is ready:

1. Run the full test suite and report the actual result.
2. Rebuild the dashboard if the change affects anything it renders.
3. **Show the diff and wait for explicit confirmation.**

Only push after Ryan has said to. "The work is finished" is not permission to
push it.

### 4. Stop and confirm BEFORE merging — and never merge silently

Opening a pull request is fine once the push is approved. **Merging is not.**

- **Never merge a PR without explicit, specific approval for that merge.**
- Approval to push is **not** approval to merge. Approval to merge one PR is
  **not** standing approval for the next.
- Merging to `main` triggers the live deploy, so a merge is a publish. Treat it
  as one.
- Report that CI is green and the PR is ready, then stop and wait.

Leave the merge to Ryan wherever practical — it is one click in the GitHub UI,
and it is the step where a human should be looking.

### 5. Never route around the gates

- Never use `--admin`, `--auto`, or any override flag on `gh pr merge`.
- Never force-push, and never push to `main` directly.
- Never weaken or remove branch protection to make something merge. If a gate
  is blocking legitimate work, say so and explain the options — do not quietly
  unlock the door.

### The gates, in one table

| Step | Who decides | Claude may act alone? |
| --- | --- | --- |
| Pull / read / analyse | — | yes |
| Create a branch | — | yes |
| Edit files, run tests, rebuild the site | — | yes |
| **Commit or push** | Ryan | **no — confirm first** |
| Open a pull request | Ryan (after push approval) | yes |
| **Merge to `main` / deploy** | Ryan | **no — confirm first, every time** |
| Change branch protection | Ryan | **no — propose only** |

### A note on what this does and does not guarantee

This file is an instruction Claude follows, not a lock. Claude operates through
Ryan's `gh` credentials, so GitHub cannot distinguish the two — any branch rule
that permits Ryan to merge also technically permits Claude to. Branch
protection guarantees that every change goes through a PR with a green test
run; **these rules are what guarantee nothing ships without Ryan saying so.**

If policy-level enforcement is ever wanted instead, it takes a second GitHub
account or a collaborator as a required reviewer. See
[docs/the-loop.md](docs/the-loop.md).
