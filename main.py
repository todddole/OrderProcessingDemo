"""
main.py

Runs a handful of sample orders through the order processor so you can see
the discount, shipping, tax, receipt, and notification behavior in action.

Usage:
    python main.py
"""

from order_processor import print_order_summary, process_order


SAMPLE_ORDERS = [
    # Regular customer, small order: no discount, pays shipping
    (
        {"name": "Alice Johnson", "email": "alice@example.com", "type": "regular"},
        [
            {"name": "Canvas Tote", "price": 24.99, "quantity": 1},
        ],
    ),
    # Premium customer, large order: 10% off, free shipping
    (
        {"name": "Ben Carter", "email": "ben@example.com", "type": "premium"},
        [
            {"name": "Hiking Boots", "price": 89.99, "quantity": 1},
            {"name": "Wool Socks", "price": 12.50, "quantity": 2},
        ],
    ),
    # Employee: 20% off, free shipping
    (
        {"name": "Carmen Lopez", "email": "carmen@example.com", "type": "employee"},
        [
            {"name": "Rain Jacket", "price": 120.00, "quantity": 1},
        ],
    ),
    # Premium customer whose discount drops the order below the $50 threshold
    (
        {"name": "Dev Patel", "email": "dev@example.com", "type": "premium"},
        [
            {"name": "Camp Mug", "price": 18.00, "quantity": 3},
        ],
    ),
    # Unknown customer type: treated as no discount
    (
        {"name": "Erin Walsh", "email": "erin@example.com", "type": "wholesale"},
        [
            {"name": "Water Bottle", "price": 15.00, "quantity": 2},
        ],
    ),
]


def main():
    for customer, items in SAMPLE_ORDERS:
        process_order(customer, items)
    print_order_summary()


if __name__ == "__main__":
    main()
