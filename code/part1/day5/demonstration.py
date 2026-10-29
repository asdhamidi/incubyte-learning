"""Part 3 demos: test-first, contracts, data tests, managed-ingestion traps."""
import copy
import duckdb

def banner(t):
    print("\n" + "=" * 8, t, "=" * 8)

# ------------------------------------------------------------------ 1. test-first vs test-after
banner("1. Test-after copies the bug, test-first does not")

def line_total_buggy(qty, unit_price):
    return qty + unit_price                     # the bug

# Test written AFTER the code, by looking at the code: expected value is computed the same way
def test_after():
    return line_total_buggy(2, 9.99) == 2 + 9.99

# Test written BEFORE the code, from the business rule: 2 items at 9.99 cost 19.98
def test_first():
    return abs(line_total_buggy(2, 9.99) - 19.98) < 1e-9

print("test written after the code  ->", "PASS" if test_after() else "FAIL")
print("test written before the code ->", "PASS" if test_first() else "FAIL")

# ------------------------------------------------------------------ 2. contracts
banner("2. What counts as a breaking upstream change?")

CONTRACT = {                                      # dotted path -> expected type(s)
    "shipment_id": str, "status": str,
    "weight_kg": (int, float), "carrier.code": str,
}

def violations(payload):
    problems = []
    for path, expected in CONTRACT.items():
        node, ok = payload, True
        for part in path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                ok = False
                break
        if not ok:
            problems.append(f"missing '{path}'")
        elif not isinstance(node, expected):
            problems.append(f"'{path}' is {type(node).__name__}")
    return problems

GOOD = {"shipment_id": "S-1", "status": "IN_TRANSIT", "weight_kg": 12.5,
        "carrier": {"code": "DHL"}}

def variant(change):
    p = copy.deepcopy(GOOD)
    change(p)
    return p

CHANGES = [
    ("new field added (tracking_url)",       lambda p: p.update(tracking_url="x")),
    ("new status value ('LOST')",            lambda p: p.update(status="LOST")),
    ("field removed (status)",               lambda p: p.pop("status")),
    ("field renamed (weight_kg -> weight)",  lambda p: p.update(weight=p.pop("weight_kg"))),
    ("type changed (weight_kg '12.5')",      lambda p: p.update(weight_kg="12.5")),
    ("nested rename (carrier.code -> id)",   lambda p: p["carrier"].update(id=p["carrier"].pop("code"))),
    ("null value (status = None)",           lambda p: p.update(status=None)),
    ("unit changed silently (kg -> lb)",     lambda p: p.update(weight_kg=27.6)),
]
for label, change in CHANGES:
    v = violations(variant(change))
    print(f"{label:40} -> {'FAILS: ' + '; '.join(v) if v else 'passes'}")

banner("2b. Fail fast vs fail late")

def flatten(order):
    return [(order["order_id"], order["customer"]["id"], i, it["sku"])
            for i, it in enumerate(order["items"], 1)]

def order(n, renamed=False):
    cust = {"customer_id": f"C-{n}"} if renamed else {"id": f"C-{n}"}
    return {"order_id": f"O-{n}", "customer": cust, "items": [{"sku": "A"}, {"sku": "B"}]}

batch = [order(1), order(2), order(3, renamed=True), order(4)]

con = duckdb.connect()
con.execute("CREATE TABLE lines (order_id VARCHAR, customer_id VARCHAR, line_no INT, sku VARCHAR)")
try:
    for o in batch:                                   # no contract: load as you go
        for row in flatten(o):
            con.execute("INSERT INTO lines VALUES (?,?,?,?)", row)
except KeyError as e:
    n = con.execute("SELECT COUNT(DISTINCT order_id) FROM lines").fetchone()[0]
    print(f"no contract : crashed with KeyError {e} on order 3 -> table already holds {n} of 4 orders")

con2 = duckdb.connect()
con2.execute("CREATE TABLE lines (order_id VARCHAR, customer_id VARCHAR, line_no INT, sku VARCHAR)")
def has_id(o): return isinstance(o.get("customer"), dict) and "id" in o["customer"]
bad = [o["order_id"] for o in batch if not has_id(o)]
if bad:
    print(f"with contract: rejected batch before loading, bad orders {bad} -> table holds 0 orders")

# ------------------------------------------------------------------ 3. data tests
banner("3. Data tests, with the offending rows")

db = duckdb.connect()
db.execute("CREATE TABLE orders (order_id VARCHAR)")
db.execute("INSERT INTO orders VALUES ('O-1'), ('O-2')")
db.execute("""CREATE TABLE order_lines (order_id VARCHAR, line_no INT, currency VARCHAR, qty INT)""")
db.execute("""INSERT INTO order_lines VALUES
    ('O-1', 1, 'USD', 2),
    ('O-1', 2, 'USD', 1),
    ('O-1', 2, 'USD', 1),     -- duplicate of line 2
    (NULL,  1, 'EUR', 3),     -- missing order_id
    ('O-2', 1, 'XXX', 1),     -- currency not in the allowed list
    ('O-2', 2, NULL, 4),      -- missing currency
    ('O-9', 1, 'GBP', 1)      -- order O-9 does not exist
""")

def show(title, sql):
    rows = db.execute(sql).fetchall()
    print(f"{title:28} -> {len(rows)} offending row(s) {rows}")

show("not_null(order_id)",      "SELECT * FROM order_lines WHERE order_id IS NULL")
show("unique(order_id,line_no)","SELECT order_id, line_no, COUNT(*) FROM order_lines "
                                "GROUP BY 1,2 HAVING COUNT(*) > 1")
show("accepted_values (naive)", "SELECT * FROM order_lines WHERE currency NOT IN ('USD','EUR','GBP')")
show("accepted_values (fixed)", "SELECT * FROM order_lines WHERE currency IS NULL "
                                "OR currency NOT IN ('USD','EUR','GBP')")
show("relationships",           "SELECT l.* FROM order_lines l LEFT JOIN orders o ON l.order_id = o.order_id "
                                "WHERE l.order_id IS NOT NULL AND o.order_id IS NULL")

# ------------------------------------------------------------------ 4. managed ingestion traps
banner("4. What a managed ingestion tool leaves to you")

m = duckdb.connect()
m.execute("""CREATE TABLE orders_landed (
    order_id VARCHAR, amount DOUBLE, _fivetran_deleted BOOLEAN)""")
m.execute("""INSERT INTO orders_landed VALUES
    ('O-1', 100.0, false), ('O-2', 250.0, false), ('O-3', 75.0, true)""")   # O-3 deleted at source
naive = m.execute("SELECT SUM(amount) FROM orders_landed").fetchone()[0]
right = m.execute("SELECT SUM(amount) FROM orders_landed WHERE NOT _fivetran_deleted").fetchone()[0]
print(f"revenue, forgetting the delete flag : {naive}")
print(f"revenue, excluding deleted rows     : {right}")

EXPECTED = {"order_id", "amount", "currency"}                 # what our models read
actual = {r[0] for r in m.execute(
    "SELECT column_name FROM information_schema.columns WHERE table_name='orders_landed'").fetchall()}
print("landing table missing columns we rely on:", sorted(EXPECTED - actual))
print("new columns we never asked for          :", sorted(actual - EXPECTED - set()))
