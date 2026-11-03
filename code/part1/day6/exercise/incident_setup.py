"""Day 6 exercise: builds incident.duckdb with raw -> staging -> intermediate -> summary."""

import duckdb

con = duckdb.connect("incident.duckdb")
con.execute("DROP VIEW IF EXISTS daily_revenue")
con.execute("DROP VIEW IF EXISTS int_valid_orders")
con.execute("DROP VIEW IF EXISTS stg_orders")
con.execute("DROP TABLE IF EXISTS raw_orders")

con.execute("""CREATE TABLE raw_orders (
    order_id VARCHAR, channel VARCHAR, status VARCHAR, amount DOUBLE,
    order_date DATE, loaded_at TIMESTAMP)""")

rows = []
for day, n, loaded in (
    ("2026-10-26", 200, "2026-10-27 01:00:00"),
    ("2026-10-27", 190, "2026-10-28 01:00:00"),
):
    for i in range(n):
        channel = "mobile" if i % 5 in (0, 1) else "web"
        status = "cancelled" if i % 10 == 9 else "completed"
        if day == "2026-10-27" and channel == "mobile" and status == "completed":
            status = "complete"
        rows.append((f"{day}-{i}", channel, status, 20 + (i * 7) % 80, day, loaded))
con.executemany("INSERT INTO raw_orders VALUES (?,?,?,?,?,?)", rows)

con.execute("""CREATE VIEW stg_orders AS
    SELECT order_id, channel, status, amount, order_date FROM raw_orders""")
con.execute("""CREATE VIEW int_valid_orders AS
    SELECT * FROM stg_orders WHERE status = 'completed'""")
con.execute("""CREATE VIEW daily_revenue AS
    SELECT order_date, COUNT(*) AS orders, SUM(amount) AS revenue
    FROM int_valid_orders GROUP BY order_date""")

print(
    "incident.duckdb created. Tables and views: raw_orders, stg_orders, int_valid_orders, daily_revenue"
)
print()
print("What the dashboard shows:")
for r in con.execute("SELECT * FROM daily_revenue ORDER BY order_date").fetchall():
    print("  ", r)
