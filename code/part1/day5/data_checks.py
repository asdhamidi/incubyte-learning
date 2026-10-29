def flatten_order(order):
    if "items" not in order:
        raise ValueError("order is missing required field: items")

    rows = []
    for line_no, item in enumerate(order["items"], start=1):
        rows.append({
            "order_id": order["order_id"],
            "customer_id": order["customer"]["id"],
            "created_at": order["created_at"],
            "currency": order["currency"],
            "line_no": line_no,
            "sku": item["sku"],
            "qty": item["qty"],
            "unit_price": item["unit_price"],
            "line_total": item["qty"] * item["unit_price"],
        })
    return rows
