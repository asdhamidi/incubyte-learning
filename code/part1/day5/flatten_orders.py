REQUIRED_ORDER_FIELDS = {
    "order_id": str,
    "created_at": str,
    "currency": str,
    "customer": dict,
    "items": list,
}
REQUIRED_CUSTOMER_FIELDS = {"id": str}
REQUIRED_ITEM_FIELDS = {"sku": str, "qty": int, "unit_price": (int, float)}


def validate_order(order):
    problems = []
    for order_field in REQUIRED_ORDER_FIELDS:
        if order_field not in order:
            problems.append(f"order: missing field '{order_field}'")

    for customer_field in REQUIRED_CUSTOMER_FIELDS:
        if customer_field not in order["customer"]:
            problems.append(f"customer: missing field '{customer_field}'")

    return problems
