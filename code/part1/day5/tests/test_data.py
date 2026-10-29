import json
from pathlib import Path

import duckdb
import pytest

from ..data_checks import flatten_order

COLUMNS = ["order_id", "customer_id", "created_at", "currency",
           "line_no", "sku", "qty", "unit_price", "line_total"]


@pytest.fixture
def con():
    con = duckdb.connect()
    con.execute("""
        CREATE TABLE order_lines (
            order_id VARCHAR, customer_id VARCHAR, created_at VARCHAR, currency VARCHAR,
            line_no INTEGER, sku VARCHAR, qty INTEGER,
            unit_price DOUBLE, line_total DOUBLE)""")
    for path in sorted(Path("sample_orders").glob("*.json")):
        order = json.loads(path.read_text())
        for row in flatten_order(order):
            con.execute("INSERT INTO order_lines VALUES (?,?,?,?,?,?,?,?,?)",
                        [row[c] for c in COLUMNS])
    return con

def test_order_id_is_not_null(con):
    bad = con.execute("SELECT COUNT(*) FROM order_lines WHERE order_id IS NULL").fetchone()[0]
    assert bad == 0
