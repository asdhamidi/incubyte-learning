import duckdb

con = duckdb.connect("practice.duckdb")
result = con.execute("""WITH dedup_orders AS (
    -- order_id repeats (13 rows, 12 distinct ids), so keep one row per order
    SELECT order_id, customer_id, status, order_ts, amount
    FROM (
        SELECT order_id, customer_id, status, order_ts, amount,
               ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_ts) AS rn
        FROM orders
    ) t
    WHERE rn = 1
),
completed AS (
    -- status casing is inconsistent ('completed' vs 'COMPLETED')
    SELECT order_id, customer_id, order_ts, amount
    FROM dedup_orders
    WHERE LOWER(status) = 'completed'
),
first_order AS (
    -- computed over all history in the table, not just Q3, so returning customers aren't counted as new
    SELECT customer_id, MIN(order_ts) AS first_order_ts
    FROM completed
    GROUP BY customer_id
),
new_customers AS (
    -- customers has no signup date, so "new" is inferred from first completed order
    SELECT customer_id
    FROM first_order
    WHERE first_order_ts >= TIMESTAMP '2026-07-01 00:00:00'
      -- half-open bound: an order at exactly 2026-10-01 00:00:00 exists and belongs to Q4
      AND first_order_ts <  TIMESTAMP '2026-10-01 00:00:00'
)
SELECT
    COALESCE(c.segment, 'unassigned') AS segment,  -- segment has a NULL; keep it visible rather than dropping it
    COUNT(DISTINCT o.customer_id)     AS new_customers,
    COUNT(*)                          AS orders,
    AVG(o.amount)                     AS aov
FROM completed o
JOIN new_customers n ON n.customer_id = o.customer_id
JOIN customers c     ON c.customer_id = o.customer_id
WHERE o.order_ts >= TIMESTAMP '2026-07-01 00:00:00'
  AND o.order_ts <  TIMESTAMP '2026-10-01 00:00:00'
  -- exclude QA/test accounts from real-customer metrics
  AND c.email NOT LIKE '%@test.example'
GROUP BY COALESCE(c.segment, 'unassigned')
ORDER BY segment""").df()

print(result)
