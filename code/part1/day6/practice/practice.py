"""Day 6 practice solution: one definition of 'active customers', in plain DuckDB views."""
import duckdb

con = duckdb.connect()

# ------------------------------------------------------------------ RAW
con.execute("""CREATE TABLE raw_orders (
    order_id VARCHAR, customer_id VARCHAR, email VARCHAR, status VARCHAR,
    amount DOUBLE, order_ts TIMESTAMP)""")        # order_ts is UTC
con.execute("""INSERT INTO raw_orders VALUES
  ('O-1' ,'C-1','a@x.com'        ,'completed',100,'2026-10-20 10:00'),
  ('O-2' ,'C-2','b@x.com'        ,'cancelled', 60,'2026-10-15 09:00'),
  ('O-3' ,'C-3','qa@test.example','completed', 80,'2026-10-10 12:00'),
  ('O-4' ,'C-4','d@x.com'        ,'completed', 90,'2026-09-30 23:30'),
  ('O-5' ,'C-5','e@x.com'        ,'completed', 70,'2026-10-12 08:00'),
  ('O-6' ,'C-6','E@x.com'        ,'completed', 55,'2026-10-12 08:30'),
  ('O-7' ,'C-7','g@x.com'        ,'completed', 40,'2026-09-20 15:00'),
  ('O-8' ,'C-8','h@x.com'        ,'completed',120,'2026-10-25 11:00'),
  ('O-9' ,'C-9','i@x.com'        ,'completed',150,'2026-10-26 16:00')""")

# ------------------------------------------------------------------ the two old numbers (for reconciliation)
con.execute("""CREATE VIEW old_marketing AS
    SELECT COUNT(DISTINCT customer_id) AS n FROM raw_orders
    WHERE order_ts >= DATE '2026-10-28' - INTERVAL 30 DAY""")
con.execute("""CREATE VIEW old_finance AS
    SELECT COUNT(DISTINCT lower(email)) AS n FROM raw_orders
    WHERE status = 'completed' AND email NOT LIKE '%@test.example'
      AND order_ts >= DATE_TRUNC('month', DATE '2026-10-28')""")

# ------------------------------------------------------------------ INTERMEDIATE LAYER: clean + rules, defined once
con.execute("""CREATE VIEW stg_orders AS             -- rename, normalise; no business rules
    SELECT order_id, customer_id, lower(email) AS email_normalized, status, amount, order_ts
    FROM raw_orders""")
con.execute("""CREATE VIEW int_valid_orders AS       -- the rules for a counted order
    SELECT * FROM stg_orders
    WHERE status = 'completed'                       -- rule 1: cancelled orders are not activity
      AND email_normalized NOT LIKE '%@test.example' -- rule 2: internal test accounts never count""")

# ------------------------------------------------------------------ SUMMARY LAYER: the one metric
con.execute("""CREATE VIEW active_customers_mtd AS   -- month to date, UTC, counted by customer_id
    SELECT DATE '2026-10-28' AS as_of_date,
           COUNT(DISTINCT customer_id) AS active_customers
    FROM int_valid_orders
    WHERE order_ts >= DATE_TRUNC('month', DATE '2026-10-28')
      AND order_ts <  DATE '2026-10-28' + INTERVAL 1 DAY""")

print("RESULT")
print("  old marketing:", con.execute("SELECT n FROM old_marketing").fetchone()[0])
print("  old finance  :", con.execute("SELECT n FROM old_finance").fetchone()[0])
print("  new metric   :", con.execute("SELECT active_customers FROM active_customers_mtd").fetchone()[0])

# ------------------------------------------------------------------ TESTS: each query returns the bad rows
CHECKS = [
    ("order_id is unique",            "uniqueness",   "error",
     "SELECT order_id FROM stg_orders GROUP BY 1 HAVING COUNT(*) > 1"),
    ("order_id is not null",          "completeness", "error",
     "SELECT * FROM stg_orders WHERE order_id IS NULL"),
    ("customer_id is not null",       "completeness", "error",
     "SELECT * FROM stg_orders WHERE customer_id IS NULL"),
    ("status is an accepted value",   "validity",     "error",
     "SELECT * FROM stg_orders WHERE status IS NULL OR status NOT IN ('completed','cancelled')"),
    ("one row per as_of_date",        "uniqueness",   "error",
     "SELECT as_of_date FROM active_customers_mtd GROUP BY 1 HAVING COUNT(*) > 1"),
    ("one email is one account",      "uniqueness",   "warn",
     """SELECT email_normalized, COUNT(DISTINCT customer_id) FROM stg_orders
        GROUP BY 1 HAVING COUNT(DISTINCT customer_id) > 1"""),
]
print("\nTESTS")
for name, dim, severity, sql in CHECKS:
    bad = con.execute(sql).fetchall()
    outcome = "PASS" if not bad else ("WARN" if severity == "warn" else "FAIL")
    print(f"  {outcome:5}{name:32}[{dim}]  {bad if bad else ''}")

# ------------------------------------------------------------------ MIGRATION: old names now point at the one definition
con.execute("""CREATE VIEW marketing_active_customers AS SELECT as_of_date, active_customers FROM active_customers_mtd""")
con.execute("""CREATE VIEW finance_active_customers   AS SELECT as_of_date, active_customers FROM active_customers_mtd""")
print("\nMIGRATION  old table names now read the single definition:")
print("  marketing_active_customers:", con.execute("SELECT active_customers FROM marketing_active_customers").fetchone()[0])
print("  finance_active_customers  :", con.execute("SELECT active_customers FROM finance_active_customers").fetchone()[0])
