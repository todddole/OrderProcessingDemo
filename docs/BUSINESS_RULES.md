# Business Rules: Lone Star Outfitters Order Processing

## Inputs

**Customer:** a dict with `name`, `email`, and `type`.

**Items:** a list of one or more dicts, each with `name`, `price` (unit price,
in dollars), and `quantity` (a positive integer).

## Customer types and discounts

| `type` value | Discount |
|---|---|
| `"regular"` | none |
| `"premium"` | 10% |
| `"employee"` | 20% |
| anything else | none (unknown types are treated like regular) |

Type matching is **exact and case-sensitive**: `"Premium"` is an unknown type
and gets no discount. That is how the original program behaves.

## Calculation sequence

The steps always run in this order:

1. **Merchandise subtotal** = sum of `price × quantity` over all items.
2. **Discounted subtotal** = subtotal × (1 − discount rate).
3. **Shipping** = $7.99 if the discounted subtotal is **strictly less than**
   $50.00; otherwise $0.00 (free).
4. **Pre-tax total** = discounted subtotal + shipping.
5. **Total with tax** = pre-tax total × 1.0825 (8.25% sales tax; shipping is taxed).
6. **Final total** = total with tax rounded to 2 decimal places using Python's
   built-in `round()`.

The shipping threshold is checked **after** the discount. A discount can
therefore push an order from free shipping to paid shipping.

The tax shown on the receipt is `final total − pre-tax total`, so the receipt's
tax line and total always agree.

## Worked examples

| Customer | Items | Subtotal | After discount | Shipping | Pre-tax | Final total |
|---|---|---|---|---|---|---|
| regular | 1 × $24.99 | 24.99 | 24.99 | 7.99 | 32.98 | **35.70** (35.70085) |
| premium | 1 × $89.99, 2 × $12.50 | 114.99 | 103.491 | 0.00 | 103.491 | **112.03** (112.0290075) |
| employee | 1 × $120.00 | 120.00 | 96.00 | 0.00 | 96.00 | **103.92** |
| premium | 3 × $18.00 | 54.00 | 48.60 | 7.99 | 56.59 | **61.26** (61.258675) |
| unknown | 2 × $15.00 | 30.00 | 30.00 | 7.99 | 37.99 | **41.12** (41.124175) |
| employee | 5 × $12.50 | 62.50 | 50.00 | 0.00 | 50.00 | **54.12** (54.125, see below) |

### A note on rounding and money

The program uses ordinary Python `float` arithmetic and `round()`. This keeps
the classroom example simple, but it has consequences. For example, an exact
half-cent total such as 54.125 rounds to **54.12** rather than the 54.13 a
cashier would expect. This is the current, tested behavior.

A real production system should represent money with `decimal.Decimal` and an
explicit rounding policy (for example `ROUND_HALF_UP`). Making that change is a
**behavior change**, not a refactoring, and it is deliberately out of scope for
the behavior-preserving exercise.

## Outputs and side effects

For each processed order, in this order:

1. A formatted **receipt** is printed to stdout.
2. A **confirmation message** containing the customer's email address is printed
   (no email is actually sent).
3. The order is **recorded** in the in-memory list `order_processor.orders`
   (order ID, customer name, email, type, number of line items, final total).

`process_order()` also returns a dict with `order_id`, `subtotal`, `discount`,
`shipping`, `tax`, `total`, and `receipt`.

Order IDs start at 1001 and increase by one per recorded order.

`print_order_summary()` prints every recorded order and a grand total.
