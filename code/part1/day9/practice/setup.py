"""Day 9 practice data: creates practice.duckdb with `customers` and `orders`."""

import duckdb

con = duckdb.connect("practice.duckdb")
con.execute("DROP TABLE IF EXISTS orders")
con.execute("DROP TABLE IF EXISTS customers")
con.execute(
    "CREATE TABLE customers (customer_id VARCHAR, email VARCHAR, segment VARCHAR)"
)
con.execute("""INSERT INTO customers VALUES
  ('C1','a@x.com','enterprise'),
  ('C2','b@x.com','smb'),
  ('C3','c@x.com', NULL),
  ('C4','qa@test.example','smb'),
  ('C5','e@x.com','enterprise'),
  ('C6','f@x.com','smb'),
  ('C7','g@x.com','smb'),
  ('C8','h@x.com','enterprise')""")
con.execute("""CREATE TABLE orders (order_id VARCHAR, customer_id VARCHAR, status VARCHAR,
                                    order_ts TIMESTAMP, amount DOUBLE, discount DOUBLE)""")
con.execute("""INSERT INTO orders VALUES
  ('O1' ,'C1','completed','2026-07-05 10:00', 120, 10),
  ('O2' ,'C2','completed','2026-08-10 12:00',  80, NULL),
  ('O2' ,'C2','completed','2026-08-10 12:00',  80, NULL),
  ('O3' ,'C3','completed','2026-09-30 23:59',  60, 0),
  ('O4' ,'C4','completed','2026-07-20 09:00', 500, 0),
  ('O5' ,'C5','cancelled','2026-07-02 08:00',  90, 0),
  ('O6' ,'C5','completed','2026-08-15 14:00', 100, 20),
  ('O7' ,'C6','completed','2026-06-30 23:30',  70, 0),
  ('O8' ,'C6','completed','2026-08-01 11:00',  90, 0),
  ('O9' ,'C7','completed','2026-10-01 00:00',  50, 0),
  ('O10','C8','COMPLETED','2026-09-15 16:00', 150, 30),
  ('O11','C2','completed','2026-09-05 10:00',  40, 0),
  ('O12','C1','completed','2026-08-20 13:00',  60, 0)""")
print(
    "practice.duckdb created: customers (8 rows), orders (13 rows, one of them delivered twice)"
)
