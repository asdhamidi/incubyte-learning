REQUIRED_ORDER_FIELDS = {
    "order_id": str,
    "created_at": str,
    "currency": str,
    "customer": dict,
    "items": list,
}
REQUIRED_CUSTOMER_FIELDS = {"id": str}
REQUIRED_ITEM_FIELDS = {"sku": str, "qty": int, "unit_price": (int, float)}


def _check(obj, spec, where):
    problems = []
    for field, expected in spec.items():
        if field not in obj:
            problems.append(f"{where}: missing field '{field}'")
        elif not isinstance(obj[field], expected):
            problems.append(
                f"{where}: field '{field}' has type {type(obj[field]).__name__}"
            )
    return problems


def validate_order(order):
    problems = _check(order, REQUIRED_ORDER_FIELDS, "order")
    if isinstance(order.get("customer"), dict):
        problems += _check(order["customer"], REQUIRED_CUSTOMER_FIELDS, "customer")
    if isinstance(order.get("items"), list):
        for i, item in enumerate(order["items"]):
            problems += _check(item, REQUIRED_ITEM_FIELDS, f"items[{i}]")
    return problems
