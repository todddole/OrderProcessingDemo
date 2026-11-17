# Instructor Guide

> **For the instructor only.** Do not share this file before the students' own
> code review and the Claude audit in Phase 2. If you hand the repository to
> students, remove or withhold `docs/INSTRUCTOR_GUIDE.md` and `docs/DEMO_SCRIPT.md`.
> Claude Code can also read these files, so see the "Keeping the AI audit honest"
> section below.

## Teaching objective

`order_processor.py` is **functionally correct and well tested** (35 passing
tests), yet it has clear design and maintainability problems. The demo shows
that passing tests are necessary but not sufficient, and that tests are
what make an AI-assisted refactoring safe.

## Public interface (must survive refactoring)

The tests depend only on these names. A refactoring that renames or removes
them will break the tests, and that would be an interface change, not a refactoring:

- `order_processor.process_order(customer, items)` returns a dict with keys
  `order_id, subtotal, discount, shipping, tax, total, receipt`
- `order_processor.orders`, the module-level list of recorded orders (tests call
  `.clear()` on it)
- `order_processor.print_order_summary()`
- `main.main()`

Everything else (`send_email`, `save_order`, local variable names, internal
structure) is fair game.

## Intentional code smells

Line numbers refer to the baseline commit of `order_processor.py`.

| # | Code smell | Location (approx.) | Explanation | Why it matters | Reasonable refactoring | Risk when refactoring |
|---|---|---|---|---|---|---|
| 1 | **Long method** | `process_order()`, lines 31–102 | One ~70-line function does everything: subtotal, discount, shipping, tax, receipt, printing, notification, recording, return value. | Hard to read, test, or change any one rule without understanding the whole function. | Extract `calculate_subtotal`, `apply_discount`, `calculate_shipping`, `calculate_total`, `format_receipt`; keep `process_order` as a short coordinator. | Accidentally reordering steps (e.g. shipping before discount) or changing what gets returned. |
| 2 | **Multiple responsibilities (SRP violation)** | `process_order()`; lines 34–59 business logic, 62–88 formatting, 90–92 I/O and persistence | Pricing rules, presentation, notification, and storage live in one unit. | Any change to receipt layout, email, or storage forces edits to the pricing function. Low cohesion. | Separate pure calculation, pure formatting (returns a string), and side effects (print, notify, record). | Moving `print`, notify, or record calls changes the **order of output**, which the characterization tests pin. |
| 3 | **Magic numbers** | `0.9` (l.44), `0.8` (l.47), `50` (l.52), `7.99` (l.53), `1.0825` (l.59), `44`/`32`/`12` widths throughout, `1001` (l.32) | Business rules are buried as unexplained literals. The tax rate also appears as text `"8.25%"`, and discounts as `"10%"`/`"20%"`. | Changing the tax rate means hunting for the number and keeping text labels in sync by hand. | Named constants (`PREMIUM_DISCOUNT_RATE`, `FREE_SHIPPING_THRESHOLD`, `SHIPPING_FEE`, `TAX_RATE`, `RECEIPT_WIDTH`), or a dict mapping type to rate. | `t + t * 0.0825` is not always the same float as `t * 1.0825` and occasionally changes a rounded cent. (`1 + 0.0825` happens to equal `1.0825` exactly, so `t * (1 + TAX_RATE)` is safe.) Keep the same expression shape. |
| 4 | **Duplicate code** | Money-line formatting `label.ljust(32) + ("$"+format(v,".2f")).rjust(12)` repeated 7× (lines 74–86, 114, 118); receipt header duplicated in `print_order_summary` (lines 63–66 vs 108–111); customer-type branching duplicated (lines 40–49 and 75–80) | The same formatting and the same type check appear in several places. | A layout change must be made in many places. The two type branches can drift apart (add a new type in one place, forget the other). | Extract `money_line(label, amount)` and `header(title)` helpers, and a single discount table that supplies both the rate and the label. | A helper that formats slightly differently (e.g. `f"${v:>11.2f}"` puts spaces *between* `$` and the number). The golden master catches this. |
| 5 | **Tight coupling / hidden dependencies** | Lines 90–92 call `print`, `send_email`, `save_order` directly; global `orders` (l.11) | `process_order` cannot be called without printing, "emailing", and mutating global state. | Unit testing requires capturing stdout and clearing globals. Swapping in a real email service means editing the pricing function. | Return data from calculation; have a thin coordinator perform side effects. Optionally accept `notify`/`record` callables with the current functions as defaults. | Changing the signature in a way that breaks existing callers, or dropping the default behavior. |
| 6 | **Poor naming** | `x` (subtotal), `d` (discounted), `s` (shipping), `t` (pre-tax), `r` (receipt), `g` (grand total), `i`/`o` loop vars | Single-letter names force the reader to reverse-engineer meaning. | Slows comprehension and makes errors like using `x` where `d` was meant easy to miss. | Rename: `subtotal`, `discounted_subtotal`, `shipping`, `pre_tax_total`, `receipt`, `grand_total`, `item`, `order`. | Low risk with tests, but note `discount` in the return dict is the **amount** (`x - d`), not the discounted subtotal. |
| 7 | **Mixed levels of abstraction** | Lines 62–88: `ljust`, `center`, `"=" * 44` sit next to discount and tax rules | Low-level string padding is interleaved with high-level business decisions. | The reader must constantly switch between "what is the price?" and "how many spaces?". | Format in a dedicated function that takes already-computed values. | Formatting functions that recompute values instead of receiving them can drift from the real totals. |
| 8 | **Unnecessary conditional complexity** | Lines 40–49 (3-deep nested `else: if`), lines 75–80 (nested again), `if d != x` | An `if/elif` chain or a lookup table would express the same rules flatly. | Deep nesting hides the simple rule "rate depends on type". | `DISCOUNT_RATES = {"premium": 0.10, "employee": 0.20}` with `.get(type, 0)`. | `x - x * 0.10` is **not always bitwise equal** to `x * 0.9` in floating point (it differs for roughly 1 in 5 prices). `x * (1 - 0.10)` is safe because `1 - 0.10 == 0.9` exactly. Storing the multipliers `0.9`/`0.8` is safest. Also, `"Premium"` must stay case-sensitive (unknown). |
| 9 | **Primitive obsession** (bonus) | Customers, items, and orders are raw dicts | No type or field documentation is enforced. | Typos in keys fail at runtime. | `dataclass`es *could* help, but they change the public input format, so this is out of scope for today. | Converting inputs to dataclasses breaks callers and tests that pass dicts. |

### Subtle details worth pointing out

- **Tax displayed is derived, not computed.** The receipt's tax line is
  `total - t` (final minus pre-tax), not `round(t * 0.0825, 2)`. A refactor that
  computes tax separately can produce a receipt whose lines differ by a cent.
- **Discount line is hidden when there is no discount** (`if d != x`), and
  for unknown types there is no label at all.
- **`items` in the recorded order is the number of line items**, not the total quantity.
- **Blank line after each receipt.** `print(r)` with `r` ending in `\n`
  produces an empty line before the email message.
- **Trailing spaces** in centered header lines and in `"Orders processed: N"`
  (it is `ljust(32)` with nothing after it). The golden master includes them.
- **54.125 rounds to 54.12** (see `test_half_cent_total_at_shipping_threshold_rounds_to_54_12`).
  This makes a good "gotcha" if Claude proposes `Decimal`.

## Expected refactoring opportunities

A good behavior-preserving refactoring would likely include:

1. Introduce named constants for rates, fees, thresholds, and widths.
2. Extract subtotal calculation (`calculate_subtotal(items)`).
3. Extract discount calculation, replacing the nested `if`s with a lookup.
4. Extract shipping calculation (`calculate_shipping(discounted_subtotal)`).
5. Extract tax/total calculation (`calculate_total(pre_tax)`).
6. Separate receipt formatting into a pure function returning a string.
7. Extract a `money_line()` helper and a `header()` helper to remove duplication.
8. Separate notification and recording from calculation, so `process_order`
   becomes a short coordinator.
9. Rename `x`, `d`, `s`, `t`, `r`, `g` to meaningful names.
10. Optionally reduce coupling by letting `process_order` accept `notify=` and
    `record=` callables that default to the existing behavior.

A good result is roughly the same length or a bit longer, with each function
doing one thing, and **all 35 tests passing unchanged**.

## Potential AI mistakes to watch for

| Suggestion | Why it is inappropriate *here* |
|---|---|
| Plugin / strategy-pattern architecture for discounts (`DiscountStrategy` classes, registries) | Over-engineering for three fixed rules. Adds indirection without benefit. |
| Abstract base classes (`ABC`) for notifier, repository, formatter | One implementation each. A function or default parameter is enough. |
| Rewriting as a web service (Flask/FastAPI) or CLI framework | Changes the product, adds dependencies, out of scope. |
| Adding an ORM, SQLite, or file persistence | Changes the side effects. The spec says in-memory only. |
| Changing the order of discount, shipping, and tax | **Changes totals**. E.g. checking shipping before the discount gives the premium $54 order free shipping. |
| A different rounding policy (`ROUND_HALF_UP`, rounding intermediate values) | Changes 54.125 → 54.13, and rounding the discount early can shift other totals. |
| Replacing `float` with `Decimal` | A good production decision, but it is a **behavior change**, not a refactoring. Do it as a separate, deliberate change with updated tests. |
| Changing receipt text, column widths, or "cleaning up" trailing whitespace | Visible output changes. The golden master fails. |
| Moving the notification before the receipt, or recording before printing | Changes the observable order of events. |
| Case-insensitive customer types (`type.lower()`) | Looks like a bug fix, but it changes behavior (`"Premium"` would start getting a discount). Flag it, don't silently "fix" it. |
| Editing the tests or the golden file to make them pass | Defeats the purpose. Ask: *did the tests change?* (`git diff --stat tests/`) |
| Adding type hints, docstrings, logging, `dataclasses` | Generally harmless (except dataclasses for inputs), but watch for scope creep. |

Many of these could be the right call in a **production redesign**. They are
out of scope for a **behavior-preserving** refactoring, where the rule is that
the externally observable behavior stays the same and only the structure changes.

## Keeping the AI audit honest

Claude Code reads files in the repository, including this guide. For a
"blind" audit in Phase 2, before class either:

- move `docs/INSTRUCTOR_GUIDE.md` and `docs/DEMO_SCRIPT.md` outside the repo
  folder (for example to your Desktop), **or**
- add to the Phase 2 prompt: *"Do not read anything in the docs/ folder."*

Moving the files makes the working tree "dirty" (`git status` shows them
as deleted). That is harmless; `git restore docs/` brings them back.

## Restoring the baseline between rehearsals or sections

```bash
git status                       # see what changed
git diff                         # review it
git stash push -u -m "demo run"  # save the refactored version, just in case
# or, to throw it away entirely:
git restore .                    # revert tracked files to the baseline commit
git clean -fdn                   # PREVIEW untracked files that would be deleted
git clean -fd                    # delete them (only after checking the preview)
python -m pytest                 # confirm: 35 passed
```

To keep a refactored run for later comparison, commit it on a branch instead:
`git switch -c refactor-section1 && git add -A && git commit -m "Live refactor"`,
then `git switch main` (or `master`) to return to the baseline.
