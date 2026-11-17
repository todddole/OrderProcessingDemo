# Live Demonstration Script (about 18 minutes)

## Before class (5 minutes, the day of)

```bash
cd order-refactoring-demo
git status                 # must say "nothing to commit, working tree clean"
git log --oneline          # baseline: "Initial working implementation with intentional code smells"
python main.py             # sanity check
python -m pytest -q        # expect: 35 passed
```

- **Hide the answer key from Claude** (see INSTRUCTOR_GUIDE.md, "Keeping the
  AI audit honest"): move `docs/INSTRUCTOR_GUIDE.md` and `docs/DEMO_SCRIPT.md`
  out of the folder, or open this script from a copy elsewhere.
- Increase the terminal font size. Receipts are 44 characters wide.
- Have `order_processor.py` open in your editor.
- Start Claude Code in the project folder: `claude`.

---

## Phase 1: Introduction (2 min)

1. Run the program:

   ```bash
   python main.py
   ```

   Point out the five orders: regular, premium (free shipping), employee,
   premium whose discount drops it **below** $50 (pays shipping), and an
   unknown customer type. Then the daily summary.

2. *"It works. Is it good?"* Open `order_processor.py`.

3. Ask the class (about 60 seconds): **What would make this hard to change?**
   Collect a few answers on the board (expect: long function, `x`/`d`/`s`,
   magic numbers, repeated formatting).

---

## Phase 2: AI quality audit (4 min)

Paste this prompt exactly:

> Review this order-processing application for code quality and maintainability. Identify code smells, violations of cohesion or coupling principles, unnecessary complexity, and potential technical debt. Rank the issues by importance. Do not modify any files. Explain why each issue matters and recommend appropriate refactoring steps.

(If you did not move the docs, append: *"Do not read anything in the docs/ folder."*)

While it runs, keep the instructor guide's smell table at hand. Afterwards:

- Check off what Claude found against the 8 intentional smells.
- Did it find anything **we didn't plan**? (It often flags floats for money,
  dicts instead of dataclasses, and no input validation.) Discuss: *real
  issues, but are they refactorings or behavior changes?*
- Did it rank anything oddly? Is "use Decimal" really priority #1 for a
  *behavior-preserving* change?

Confirm nothing changed: `git status` (should be clean).

---

## Phase 3: Test baseline (4 min)

1. Run the tests:

   ```bash
   python -m pytest -v
   ```

   35 passing tests. Point out the two files: business rules vs.
   characterization (golden master, including `tests/golden/main_output.txt`).

2. Paste:

   > Review the existing tests and identify any important gaps in behavioral coverage. Add appropriate characterization tests before any refactoring. Preserve the current observable behavior, including calculation order, rounding, receipt formatting, notification output, and order-recording side effects. Run the full test suite.

3. Review what it added (`git diff --stat`, then `git diff tests/`). Ask:
   - Do the new tests describe **behavior** or **implementation**? (Tests that
     call private helpers or mock internals will break during refactoring.)
   - Did it change any existing test? It should not have.

4. Discussion point: **All tests passed before we touched anything, and the
   code is still poorly designed.** Tests show *what* the code does, not
   whether the code is easy to maintain. Their job today is to make the
   refactoring safe.

5. Optional: commit the new tests as a checkpoint so the refactor diff
   shows only production code:

   ```bash
   git add tests && git commit -m "Add characterization tests"
   ```

---

## Phase 4: Refactoring (5 min)

Paste:

> Refactor the order-processing application to improve readability, cohesion, coupling, and maintainability. Preserve existing externally observable behavior, including calculation order, rounding, receipt formatting, notification behavior, and order-recording side effects. Prefer simple, focused functions over unnecessary abstractions. Do not introduce new dependencies. Run the tests after making changes and summarize the modifications.

While it works, narrate what it is doing: extracting functions, naming
constants, removing duplication. If it proposes something from the "Potential AI
mistakes" table (ABCs, Decimal, a strategy registry), pause and ask the class
whether that is in scope.

When it finishes, run the tests yourself. Don't take the summary's word for it:

```bash
python -m pytest -q
python main.py
```

---

## Phase 5: Evaluation (3 min)

Show the changes:

```bash
git diff --stat                       # which files changed?
git diff --stat tests/                # did the TESTS change? (they should not, except Phase 3 additions)
git diff order_processor.py           # the refactor itself
git diff --word-diff order_processor.py   # alternative, easier to read for renames
```

If you committed the tests in Phase 3, compare against the original baseline
with `git diff HEAD~1 -- order_processor.py`. To view the baseline file side by
side: `git show HEAD:order_processor.py` (or `HEAD~1:` if you committed tests).

Ask the class:

- Did all tests pass, **without the tests being edited**?
- Did the design improve? Count responsibilities in `process_order` now.
- Is it easier to understand? Could you change the tax rate in one place?
- Did Claude add unnecessary complexity (classes, ABCs, patterns)?
- Did any observable behavior change? (Golden master test + `python main.py`)
- Would future maintenance be easier? Try: *"How would we add a 'student'
  type with 15% off?"* Count how many places must change, before vs. after.

---

## Resetting after the demo (or between sections)

```bash
git status
git stash push -u -m "section 1 refactor"   # keep it, or...
git restore .                               # ...discard tracked changes
git clean -fdn                              # preview untracked files to delete
git clean -fd                               # delete them
git log --oneline                           # if you committed in Phase 3:
git reset --hard <baseline-hash>            #   return to the baseline commit
python -m pytest -q                         # 35 passed
```

`git reset --hard` discards uncommitted work. Run `git status` first and
stash anything you want to keep.

Put the docs back if you moved them out of the folder (or `git restore docs/`).

## Fallback plan

If Claude is slow or the network fails, talk through the smell table from
INSTRUCTOR_GUIDE.md and refactor one piece by hand (e.g. extract
`calculate_shipping()` and replace `7.99`/`50` with constants), running
`python -m pytest -q` after each step.
