# order-refactoring-demo

A small order-processing program for **Lone Star Outfitters**, a fictional online
retailer. It is used in an AI-Assisted Software Engineering lecture as a
**classroom refactoring exercise**.

The program works, and its tests pass. Whether it is *well designed* is a
separate question, and that is the point of the exercise. Read `order_processor.py`
and decide for yourself.

## Requirements

- Python 3.11 or later
- pytest (the only dependency, and only needed for the tests)

There is no database, web framework, network access, or configuration.

## Installation

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
```

## Run the application

```bash
python main.py
```

This processes five sample orders, printing a receipt and a confirmation
message for each, followed by a daily order summary.

## Run the tests

```bash
python -m pytest
```

Add `-v` to see each test by name.

- `tests/test_order_processor.py`: business-rule tests
- `tests/test_characterization.py`: characterization ("golden master") tests that
  pin down the current output and side effects exactly. One of them compares
  the full output of `main.py` to `tests/golden/main_output.txt`.

## Business rules (summary)

| Rule | Value |
|---|---|
| Customer discounts | regular 0%, premium 10%, employee 20%, any other type 0% |
| Shipping | $7.99 if the **discounted** subtotal is under $50, otherwise free |
| Sales tax | 8.25% of (discounted subtotal + shipping) |
| Rounding | final total rounded to 2 decimal places |

The order of operations is subtotal, then discount, then shipping, then tax,
then rounding. See [`docs/BUSINESS_RULES.md`](docs/BUSINESS_RULES.md) for details and worked examples.

Confirmation "emails" are only printed. Orders are kept in an in-memory list
and are lost when the program exits.

## Working with Git

```bash
git status                 # what has changed?
git diff                   # see the changes line by line
git diff --stat            # which files changed, and how much
git restore .              # discard changes to tracked files (back to the last commit)
```

## Note

Money is stored as Python `float` here to keep the example simple. A real
production system should use `decimal.Decimal` for currency.
