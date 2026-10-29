import json
import copy
from pathlib import Path

import pytest

from ..flatten_orders import validate_order

SAMPLES = sorted(Path("sample_orders").glob("*.json"))

sample_order = {
    "order_id": "O-1001",
    "created_at": "2026-10-27T10:15:00Z",
    "currency": "USD",
    "customer": {"id": "C-1", "email": "asha@example.com"},
    "items": [
        {"sku": "A1", "qty": 2, "unit_price": 9.99},
        {"sku": "B2", "qty": 1, "unit_price": 24.5},
    ],
}

def test_there_are_sample_orders():
    assert SAMPLES, "no sample orders found in sample_orders/"

def test_validator_exists():
    assert validate_order(sample_order) == []

@pytest.mark.parametrize("path", SAMPLES, ids=lambda p: p.name)
def test_sample_orders_meet_the_contract(path):
    order = json.loads(path.read_text())
    assert validate_order(order) == []

def test_missing_field_is_reported():
    order = copy.deepcopy(sample_order)
    del order["currency"]
    assert "order: missing field 'currency'" in validate_order(order)

def test_nested_missing_field_is_reported():
    order = copy.deepcopy(sample_order)
    del order["customer"]["id"]
    assert "customer: missing field 'id'" in validate_order(order)
