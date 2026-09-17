# Git practice exercises

Suggested order. Nothing here can cause real damage — this repo is disposable.

## 0. One-time setup

Set who your commits are attributed to:

```bash
git config --global user.name "Ryan Pratt"
git config --global user.email "ryan.pratt@greatgulf.com"
```

## 1. The everyday loop

The 90% case, in order:

```bash
git status          # what have I changed?
git diff            # show me exactly what changed
git add -A          # stage everything
git commit -m "Describe the change"
git push            # send it to GitHub
```

`git status` is the single most useful command. When confused, run it.

## 2. Pull before you push

If you edited a file in the GitHub web UI, your local copy is now behind:

```bash
git pull            # fetch and merge what's on GitHub
```

Try this deliberately: edit `README.md` on github.com, commit it there, then
`git pull` locally and watch the change arrive.

## 3. Branching

Never a bad habit. Work on a branch, then merge:

```bash
git switch -c experiment/new-metric   # create and switch
# ... make changes, commit ...
git push -u origin experiment/new-metric
```

Then open a pull request on GitHub, and merge it there.

Back to main afterwards:

```bash
git switch main
git pull
```

## 4. Undoing things

| Situation | Command |
| --- | --- |
| Discard changes to one file | `git restore path/to/file` |
| Unstage a file, keep the edits | `git restore --staged path/to/file` |
| Fix the last commit message | `git commit --amend -m "Better message"` |
| Undo last commit, keep changes | `git reset --soft HEAD~1` |
| Throw away everything uncommitted | `git restore .` |
| See where you've been | `git log --oneline --graph --all` |

## 5. Deliberately cause a merge conflict

Worth doing once so it's not scary later:

1. On GitHub, edit the first line of `README.md` and commit.
2. Locally, edit that same first line differently and commit.
3. Run `git pull`. Git reports a conflict.
4. Open `README.md` — you'll see `<<<<<<<`, `=======`, `>>>>>>>` markers.
5. Delete the markers, keep the text you want.
6. `git add README.md` then `git commit`.

## 6. Things to try with Claude in this repo

Small, verifiable asks are the best way to get a feel for it:

- "Add a metric for average deposit structure by project, with a test."
- "Which exposure carries the biggest premium, and by how much?"
- "The 3B suites look underpriced — check them against the 2B+D $/sqft."
- "Add 5 more units to GG-07 in the inventory, then run the tests."
- "Create a branch, add a `--by municipality` report option, and push it."
- "Why did the test suite fail?" — after deliberately breaking a CSV.

Then review the diff yourself with `git diff` before committing. Reading the
diff is the habit that makes working with an agent safe.
