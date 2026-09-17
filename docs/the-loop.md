# The loop

How a change gets from "someone noticed something" to "the live site shows it".
This is the cycle a production repository runs on, and it is what this repo now
lets you practise end to end.

```
  someone looks at the dashboard
            │
            ▼
      files an Issue          ← GitHub, using a template
            │
            ▼
   you pull + branch          ← git switch -c fix/...
            │
            ▼
      make the change         ← src/, data/, or tests/
            │
            ▼
       push + open a PR       ← gh pr create
            │
            ▼
        CI runs               ← 36 tests + a build; red blocks the merge
            │
            ▼
       review + merge         ← main is protected, so this step is mandatory
            │
            ▼
   Pages redeploys itself     ← ~40 seconds, no action from you
            │
            ▼
   the reporter refreshes and confirms
```

## Why `main` is protected

You cannot push to `main` in this repo. That is deliberate, and it is the
single biggest difference between a practice repo and a real one.

It means every change is forced through a pull request, which means every
change gets a CI run and a diff someone can read before it ships. The
protection is not there because your changes are untrustworthy — it is there so
that the *process* doesn't depend on anyone remembering to follow it.

If you try to push straight to `main` you will get:

```
! [remote rejected] main -> main (protected branch hook declined)
```

That is the gate working, not a problem to route around.

## The commands, in order

Someone has filed issue #7 saying the leaderboard looks upside down.

```bash
# 1. Start from an up-to-date main
git switch main
git pull

# 2. Branch. Name it after what it does.
git switch -c fix/leaderboard-sort-order

# 3. Make the change, then check your own work
git diff

# 4. Run the tests before you push, not after
python3 -m unittest discover -s tests

# 5. Preview it locally
python3 -m src.build_site && python3 -m http.server 8765 --directory site

# 6. Commit and push
git add -A
git commit -m "Sort the leaderboard by revenue descending

Closes #7"
git push -u origin fix/leaderboard-sort-order

# 7. Open the pull request
gh pr create --fill
```

Then watch CI, and merge when it's green:

```bash
gh pr checks --watch
gh pr merge --squash --delete-branch
```

The deploy runs on its own from there. Watch it land:

```bash
gh run watch
```

## Closing issues from a commit

Putting `Closes #7` in the commit message or PR body means GitHub closes the
issue automatically when the PR merges. Worth the habit — it keeps the issue
list honest without anyone tidying it up.

## What CI actually checks

`.github/workflows/ci.yml` runs on every pull request:

1. **The full test suite** — 36 tests. The `TestDataIntegrity` ones will catch a
   broken foreign key if you hand-edited a CSV.
2. **A dashboard build** — catches a generator that crashes on real data.
3. **A page-count assertion** — every project in `projects.csv` must produce a
   page, so adding a ninth development can't silently skip it.
4. **An uploaded artifact** — download the built site from the PR's Checks tab
   to see exactly what would ship.

Only after all of that passes can the PR merge, and only a merge deploys.

## Things worth breaking on purpose

The repo is disposable, so cause these deliberately once each:

- **Break a foreign key.** Change a `project_id` in `unit_inventory.csv` to
  `GG-99`, push it, and watch CI fail on the PR rather than on the live site.
- **Try to push to main.** See the rejection above with your own eyes.
- **Merge a PR and time the deploy.** Open the Actions tab and watch the
  dashboard update without you touching anything.
- **File an issue against yourself** from the live site, then work it through
  the whole loop above.
- **Add a ninth project** to `projects.csv` with no matching units, and see
  which test complains first.
