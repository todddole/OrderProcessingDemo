"""
Characterization ("golden master") tests.

These tests pin down what the program CURRENTLY does -- exact stdout, exact
receipt layout, the order in which things are printed, what gets recorded, and
a couple of rounding/edge-case quirks. They are not a statement that the
current behavior is ideal; they exist so a refactoring can prove it changed
nothing observable.

They use only the public interface (process_order, print_order_summary,
orders, and main.main) and never inspect how the code is organized inside,
so they remain valid when process_order is split into smaller pieces.

Expected strings are written line by line so that trailing spaces (produced
by str.center and str.ljust) stay visible and survive editors that strip
trailing whitespace.
"""

import copy
from pathlib import Path

import pytest

import main
import order_processor
from order_processor import print_order_summary, process_order

GOLDEN_DIR = Path(__file__).parent / "golden"


@pytest.fixture(autouse=True)
def reset_orders():
    order_processor.orders.clear()
    yield
    order_processor.orders.clear()


BEN = {"name": "Ben Carter", "email": "ben@example.com", "type": "premium"}
BEN_ITEMS = [
    {"name": "Hiking Boots", "price": 89.99, "quantity": 1},
    {"name": "Wool Socks", "price": 12.50, "quantity": 2},
]

ALICE = {"name": "Alice Johnson", "email": "alice@example.com", "type": "regular"}
ALICE_ITEMS = [{"name": "Canvas Tote", "price": 24.99, "quantity": 1}]


def lines(*rows):
    return "\n".join(rows) + "\n"


# ---------------------------------------------------------------------------
# Exact console output
# ---------------------------------------------------------------------------

def test_full_stdout_for_a_discounted_free_shipping_order(capsys):
    process_order(BEN, BEN_ITEMS)

    assert capsys.readouterr().out == lines(
        "============================================",
        "            LONE STAR OUTFITTERS            ",
        "                Order #1001                 ",
        "============================================",
        "Customer: Ben Carter",
        "Email:    ben@example.com",
        "--------------------------------------------",
        "Hiking Boots          1 x   89.99 =    89.99",
        "Wool Socks            2 x   12.50 =    25.00",
        "--------------------------------------------",
        "Subtotal:                            $114.99",
        "Premium discount (10%):              -$11.50",
        "Shipping:                               FREE",
        "Sales tax (8.25%):                     $8.54",
        "TOTAL:                               $112.03",
        "============================================",
        "Thank you for shopping with us!",
        "",  # print() adds a newline after the receipt's own trailing newline
        "Sending confirmation email to ben@example.com...",
        "  Order #1001 confirmed. Total charged: $112.03",
    )


def test_full_stdout_for_a_regular_order_with_shipping(capsys):
    process_order(ALICE, ALICE_ITEMS)

    assert capsys.readouterr().out == lines(
        "============================================",
        "            LONE STAR OUTFITTERS            ",
        "                Order #1001                 ",
        "============================================",
        "Customer: Alice Johnson",
        "Email:    alice@example.com",
        "--------------------------------------------",
        "Canvas Tote           1 x   24.99 =    24.99",
        "--------------------------------------------",
        "Subtotal:                             $24.99",
        "Shipping:                              $7.99",
        "Sales tax (8.25%):                     $2.72",
        "TOTAL:                                $35.70",
        "============================================",
        "Thank you for shopping with us!",
        "",
        "Sending confirmation email to alice@example.com...",
        "  Order #1001 confirmed. Total charged: $35.70",
    )


def test_employee_discount_line_wording(capsys):
    process_order(
        {"name": "Carmen Lopez", "email": "carmen@example.com", "type": "employee"},
        [{"name": "Rain Jacket", "price": 120.00, "quantity": 1}],
    )
    out = capsys.readouterr().out

    assert "Employee discount (20%):             -$24.00\n" in out


def test_receipt_is_printed_before_the_notification(capsys):
    process_order(ALICE, ALICE_ITEMS)
    out = capsys.readouterr().out

    assert out.index("Thank you for shopping with us!") < out.index("Sending confirmation email")


def test_returned_receipt_matches_printed_receipt(capsys):
    result = process_order(BEN, BEN_ITEMS)
    out = capsys.readouterr().out

    assert out.startswith(result["receipt"] + "\n")
    assert "Sending confirmation" not in result["receipt"]


def test_long_product_names_are_not_truncated(capsys):
    process_order(
        ALICE,
        [{"name": "Ultralight Backpacking Tent", "price": 249.00, "quantity": 1}],
    )
    out = capsys.readouterr().out

    assert "Ultralight Backpacking Tent  1 x  249.00 =   249.00\n" in out


# ---------------------------------------------------------------------------
# Return value and recorded side effects
# ---------------------------------------------------------------------------

def test_return_value_shape():
    result = process_order(BEN, BEN_ITEMS)

    assert set(result) == {"order_id", "subtotal", "discount", "shipping", "tax", "total", "receipt"}
    assert result["order_id"] == 1001
    assert result["subtotal"] == pytest.approx(114.99)
    assert result["discount"] == pytest.approx(11.499)
    assert result["shipping"] == 0
    assert result["tax"] == pytest.approx(8.5390075)
    assert result["total"] == 112.03


def test_recorded_order_contents():
    process_order(BEN, BEN_ITEMS)

    assert order_processor.orders == [
        {
            "order_id": 1001,
            "customer": "Ben Carter",
            "email": "ben@example.com",
            "type": "premium",
            "items": 2,  # number of line items, not total quantity
            "total": 112.03,
        }
    ]


def test_order_is_recorded_only_once_per_call():
    process_order(ALICE, ALICE_ITEMS)
    process_order(ALICE, ALICE_ITEMS)

    assert [o["order_id"] for o in order_processor.orders] == [1001, 1002]


def test_inputs_are_not_modified():
    customer = copy.deepcopy(BEN)
    items = copy.deepcopy(BEN_ITEMS)

    process_order(customer, items)

    assert customer == BEN
    assert items == BEN_ITEMS


# ---------------------------------------------------------------------------
# Edge cases and quirks that a refactoring must not silently change
# ---------------------------------------------------------------------------

def test_half_cent_total_at_shipping_threshold_rounds_to_54_12():
    # Employee: 62.50 * 0.8 = 50.00 -> free shipping -> 50.00 * 1.0825 = 54.125.
    # Python's round() on this float gives 54.12, not 54.13. Switching to
    # Decimal with ROUND_HALF_UP (or any other rounding policy) changes this.
    result = process_order(
        {"name": "Pat", "email": "pat@example.com", "type": "employee"},
        [{"name": "Trail Map", "price": 12.50, "quantity": 5}],
    )

    assert result["shipping"] == 0
    assert result["total"] == 54.12


def test_customer_type_matching_is_case_sensitive(capsys):
    # "Premium" (capital P) is not "premium", so it is treated as unknown.
    result = process_order(
        {"name": "Ben Carter", "email": "ben@example.com", "type": "Premium"},
        BEN_ITEMS,
    )
    out = capsys.readouterr().out

    assert result["discount"] == 0
    assert result["total"] == 124.48  # 114.99 * 1.0825 = 124.476675
    assert "discount" not in out.lower()


def test_no_discount_line_for_regular_or_unknown_customers(capsys):
    process_order(ALICE, ALICE_ITEMS)
    process_order({"name": "Erin", "email": "erin@example.com", "type": "wholesale"}, ALICE_ITEMS)
    out = capsys.readouterr().out

    assert "discount" not in out.lower()


# ---------------------------------------------------------------------------
# Order summary
# ---------------------------------------------------------------------------

def test_order_summary_output(capsys):
    process_order(ALICE, ALICE_ITEMS)
    process_order(BEN, BEN_ITEMS)
    capsys.readouterr()  # discard receipts

    print_order_summary()

    assert capsys.readouterr().out == lines(
        "============================================",
        "            LONE STAR OUTFITTERS            ",
        "            Daily Order Summary             ",
        "============================================",
        "#1001 Alice Johnson                   $35.70",
        "#1002 Ben Carter                     $112.03",
        "--------------------------------------------",
        "Orders processed: 2             ",
        "Grand total:                         $147.73",
        "============================================",
        "",
    )


def test_order_summary_with_no_orders(capsys):
    print_order_summary()

    assert capsys.readouterr().out == lines(
        "============================================",
        "            LONE STAR OUTFITTERS            ",
        "            Daily Order Summary             ",
        "============================================",
        "--------------------------------------------",
        "Orders processed: 0             ",
        "Grand total:                           $0.00",
        "============================================",
        "",
    )


# ---------------------------------------------------------------------------
# Whole-program golden master
# ---------------------------------------------------------------------------

def test_main_output_matches_golden_master(capsys):
    main.main()
    actual = capsys.readouterr().out

    expected = (GOLDEN_DIR / "main_output.txt").read_text(encoding="utf-8")
    assert actual == expected
