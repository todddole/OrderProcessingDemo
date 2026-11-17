"""
Business-rule tests for the order processor.

Expected values in this file were calculated by hand from the rules in
docs/BUSINESS_RULES.md, not by re-running the production algorithm.

These tests use only the public interface:
    process_order(customer, items) -> dict
    orders                          (module-level list of recorded orders)
so they should keep passing after the implementation is refactored.
"""

import pytest

import order_processor
from order_processor import process_order


@pytest.fixture(autouse=True)
def reset_orders():
    """Give every test a clean in-memory order list."""
    order_processor.orders.clear()
    yield
    order_processor.orders.clear()


def customer(type_="regular", name="Test Customer", email="test@example.com"):
    return {"name": name, "email": email, "type": type_}


def item(name, price, quantity=1):
    return {"name": name, "price": price, "quantity": quantity}


# ---------------------------------------------------------------------------
# Customer discounts
# ---------------------------------------------------------------------------

def test_regular_customer_gets_no_discount():
    # 75.00, no discount, free shipping, 75.00 * 1.0825 = 81.1875 -> 81.19
    result = process_order(customer("regular"), [item("Lantern", 75.00)])

    assert result["subtotal"] == pytest.approx(75.00)
    assert result["discount"] == pytest.approx(0.00)
    assert result["total"] == 81.19


def test_premium_customer_gets_ten_percent_discount():
    # 120.00 - 12.00 = 108.00, free shipping, 108.00 * 1.0825 = 116.91
    result = process_order(customer("premium"), [item("Tent", 120.00)])

    assert result["discount"] == pytest.approx(12.00)
    assert result["shipping"] == 0
    assert result["total"] == 116.91


def test_employee_customer_gets_twenty_percent_discount():
    # 120.00 - 24.00 = 96.00, free shipping, 96.00 * 1.0825 = 103.92
    result = process_order(customer("employee"), [item("Rain Jacket", 120.00)])

    assert result["discount"] == pytest.approx(24.00)
    assert result["shipping"] == 0
    assert result["total"] == 103.92


def test_unknown_customer_type_gets_no_discount():
    # 30.00, no discount, +7.99 shipping = 37.99, * 1.0825 = 41.124175 -> 41.12
    result = process_order(customer("wholesale"), [item("Water Bottle", 15.00, 2)])

    assert result["discount"] == pytest.approx(0.00)
    assert result["shipping"] == 7.99
    assert result["total"] == 41.12


# ---------------------------------------------------------------------------
# Item handling
# ---------------------------------------------------------------------------

def test_single_item_order():
    # 24.99 + 7.99 shipping = 32.98, * 1.0825 = 35.70085 -> 35.70
    result = process_order(customer("regular"), [item("Canvas Tote", 24.99)])

    assert result["subtotal"] == pytest.approx(24.99)
    assert result["total"] == 35.70


def test_multiple_item_order_sums_price_times_quantity():
    # 89.99*1 + 12.50*2 + 3.00*4 = 89.99 + 25.00 + 12.00 = 126.99
    # regular, free shipping, 126.99 * 1.0825 = 137.466675 -> 137.47
    items = [
        item("Hiking Boots", 89.99, 1),
        item("Wool Socks", 12.50, 2),
        item("Bandana", 3.00, 4),
    ]
    result = process_order(customer("regular"), items)

    assert result["subtotal"] == pytest.approx(126.99)
    assert result["total"] == 137.47


# ---------------------------------------------------------------------------
# Shipping
# ---------------------------------------------------------------------------

def test_order_below_shipping_threshold_pays_shipping():
    # 49.99 < 50 -> shipping 7.99; 57.98 * 1.0825 = 62.76335 -> 62.76
    result = process_order(customer("regular"), [item("Daypack", 49.99)])

    assert result["shipping"] == 7.99
    assert result["total"] == 62.76


def test_order_exactly_at_threshold_after_discount_ships_free():
    # Employee: 5 x 12.50 = 62.50, 20% off = 50.00 exactly -> free shipping
    result = process_order(customer("employee"), [item("Trail Map", 12.50, 5)])

    assert result["subtotal"] - result["discount"] == pytest.approx(50.00)
    assert result["shipping"] == 0
    # The final total for this order is pinned in test_characterization.py,
    # because it lands exactly on a half cent (54.125).


def test_order_above_shipping_threshold_ships_free():
    # 100.00 >= 50 -> free shipping; 100.00 * 1.0825 = 108.25
    result = process_order(customer("regular"), [item("Sleeping Bag", 100.00)])

    assert result["shipping"] == 0
    assert result["total"] == 108.25


def test_discount_can_move_order_below_shipping_threshold():
    # 3 x 18.00 = 54.00 (would ship free), premium 10% off = 48.60 -> pays 7.99
    # 48.60 + 7.99 = 56.59, * 1.0825 = 61.258675 -> 61.26
    result = process_order(customer("premium"), [item("Camp Mug", 18.00, 3)])

    assert result["subtotal"] == pytest.approx(54.00)
    assert result["shipping"] == 7.99
    assert result["total"] == 61.26


# ---------------------------------------------------------------------------
# Tax and rounding
# ---------------------------------------------------------------------------

def test_tax_is_eight_and_a_quarter_percent():
    # 100.00 * 0.0825 = 8.25
    result = process_order(customer("regular"), [item("Sleeping Bag", 100.00)])

    assert result["tax"] == pytest.approx(8.25)


def test_tax_applies_to_discounted_subtotal_plus_shipping():
    # 20.00 + 7.99 = 27.99; tax 27.99 * 0.0825 = 2.309175; total 30.299175 -> 30.30
    # (If shipping were NOT taxed the total would be 20*1.0825 + 7.99 = 29.64.)
    result = process_order(customer("regular"), [item("Headlamp", 20.00)])

    assert result["total"] == 30.30
    assert result["tax"] == pytest.approx(2.31, abs=0.005)


def test_final_total_rounds_up_to_two_decimals():
    # premium: 114.99 * 0.9 = 103.491, * 1.0825 = 112.0290075 -> 112.03
    items = [item("Hiking Boots", 89.99, 1), item("Wool Socks", 12.50, 2)]
    result = process_order(customer("premium"), items)

    assert result["total"] == 112.03


def test_final_total_rounds_down_to_two_decimals():
    # 32.98 * 1.0825 = 35.70085 -> 35.70
    result = process_order(customer("regular"), [item("Canvas Tote", 24.99)])

    assert result["total"] == 35.70
    assert round(result["total"], 2) == result["total"]


# ---------------------------------------------------------------------------
# Receipt, notification, recording
# ---------------------------------------------------------------------------

def test_receipt_contains_order_details():
    c = customer("premium", name="Ben Carter", email="ben@example.com")
    items = [item("Hiking Boots", 89.99, 1), item("Wool Socks", 12.50, 2)]
    receipt = process_order(c, items)["receipt"]

    assert "Order #1001" in receipt
    assert "Ben Carter" in receipt
    assert "ben@example.com" in receipt
    assert "Hiking Boots" in receipt
    assert "Wool Socks" in receipt
    assert "$114.99" in receipt           # subtotal
    assert "-$11.50" in receipt           # 10% of 114.99, displayed to cents
    assert "FREE" in receipt              # shipping
    assert "$112.03" in receipt           # total


def test_receipt_is_printed(capsys):
    result = process_order(customer("regular"), [item("Canvas Tote", 24.99)])
    out = capsys.readouterr().out

    assert result["receipt"] in out


def test_notification_includes_email_and_total(capsys):
    process_order(customer("regular", email="alice@example.com"), [item("Canvas Tote", 24.99)])
    out = capsys.readouterr().out

    assert "Sending confirmation email to alice@example.com..." in out
    assert "Order #1001 confirmed. Total charged: $35.70" in out


def test_orders_are_recorded_in_memory():
    process_order(customer("regular", name="Alice"), [item("Canvas Tote", 24.99)])
    process_order(customer("employee", name="Carmen"), [item("Rain Jacket", 120.00)])

    assert len(order_processor.orders) == 2
    assert order_processor.orders[0]["customer"] == "Alice"
    assert order_processor.orders[0]["total"] == 35.70
    assert order_processor.orders[1]["customer"] == "Carmen"
    assert order_processor.orders[1]["total"] == 103.92


def test_order_ids_are_sequential_starting_at_1001():
    first = process_order(customer(), [item("A", 10.00)])
    second = process_order(customer(), [item("B", 10.00)])

    assert first["order_id"] == 1001
    assert second["order_id"] == 1002
