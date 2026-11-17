"""
order_processor.py

Order processing for Lone Star Outfitters, a fictional online retailer.

A customer is a dict:  {"name": str, "email": str, "type": str}
An item is a dict:     {"name": str, "price": float, "quantity": int}
"""

# every order we process gets saved here
orders = []


def send_email(email, order_id, total):
    # we don't really send email, just print what we would send
    print("Sending confirmation email to " + email + "...")
    print("  Order #" + str(order_id) + " confirmed. Total charged: $" + format(total, ".2f"))


def save_order(order_id, customer, items, total):
    orders.append({
        "order_id": order_id,
        "customer": customer["name"],
        "email": customer["email"],
        "type": customer["type"],
        "items": len(items),
        "total": total,
    })


def process_order(customer, items):
    order_id = 1001 + len(orders)

    # add up the items
    x = 0
    for i in items:
        x = x + i["price"] * i["quantity"]

    # discounts
    if customer["type"] == "regular":
        d = x
    else:
        if customer["type"] == "premium":
            d = x * 0.9
        else:
            if customer["type"] == "employee":
                d = x * 0.8
            else:
                d = x

    # shipping
    if d < 50:
        s = 7.99
    else:
        s = 0

    # tax
    t = d + s
    total = round(t * 1.0825, 2)

    # make the receipt
    r = ""
    r += "=" * 44 + "\n"
    r += "LONE STAR OUTFITTERS".center(44) + "\n"
    r += ("Order #" + str(order_id)).center(44) + "\n"
    r += "=" * 44 + "\n"
    r += "Customer: " + customer["name"] + "\n"
    r += "Email:    " + customer["email"] + "\n"
    r += "-" * 44 + "\n"
    for i in items:
        line = i["price"] * i["quantity"]
        r += f"{i['name']:<20}{i['quantity']:>3} x {i['price']:>7.2f} = {line:>8.2f}\n"
    r += "-" * 44 + "\n"
    r += "Subtotal:".ljust(32) + ("$" + format(x, ".2f")).rjust(12) + "\n"
    if d != x:
        if customer["type"] == "premium":
            r += "Premium discount (10%):".ljust(32) + ("-$" + format(x - d, ".2f")).rjust(12) + "\n"
        else:
            if customer["type"] == "employee":
                r += "Employee discount (20%):".ljust(32) + ("-$" + format(x - d, ".2f")).rjust(12) + "\n"
    if s == 0:
        r += "Shipping:".ljust(32) + "FREE".rjust(12) + "\n"
    else:
        r += "Shipping:".ljust(32) + ("$" + format(s, ".2f")).rjust(12) + "\n"
    r += "Sales tax (8.25%):".ljust(32) + ("$" + format(total - t, ".2f")).rjust(12) + "\n"
    r += "TOTAL:".ljust(32) + ("$" + format(total, ".2f")).rjust(12) + "\n"
    r += "=" * 44 + "\n"
    r += "Thank you for shopping with us!\n"

    print(r)
    send_email(customer["email"], order_id, total)
    save_order(order_id, customer, items, total)

    return {
        "order_id": order_id,
        "subtotal": x,
        "discount": x - d,
        "shipping": s,
        "tax": total - t,
        "total": total,
        "receipt": r,
    }


def print_order_summary():
    # print all the orders processed so far
    r = ""
    r += "=" * 44 + "\n"
    r += "LONE STAR OUTFITTERS".center(44) + "\n"
    r += "Daily Order Summary".center(44) + "\n"
    r += "=" * 44 + "\n"
    g = 0
    for o in orders:
        r += ("#" + str(o["order_id"]) + " " + o["customer"]).ljust(32) + ("$" + format(o["total"], ".2f")).rjust(12) + "\n"
        g = g + o["total"]
    r += "-" * 44 + "\n"
    r += ("Orders processed: " + str(len(orders))).ljust(32) + "\n"
    r += "Grand total:".ljust(32) + ("$" + format(g, ".2f")).rjust(12) + "\n"
    r += "=" * 44 + "\n"
    print(r)
