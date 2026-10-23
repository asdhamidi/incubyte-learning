-- Compares intermediate_orders (after the 2nd run) with intermediate_orders_after_run1 (snapshot taken after the 1st run).
-- diff_rows must be 0 and the counts / sums must match.
SELECT
    (SELECT COUNT(*) FROM (
        (SELECT * FROM intermediate_orders EXCEPT SELECT * FROM intermediate_orders_after_run1)
        UNION ALL
        (SELECT * FROM intermediate_orders_after_run1 EXCEPT SELECT * FROM intermediate_orders)
    )) AS diff_rows,
    (SELECT COUNT(*) FROM intermediate_orders_after_run1) AS rows_run1,
    (SELECT COUNT(*) FROM intermediate_orders)            AS rows_run2,
    (SELECT SUM(amount) FROM intermediate_orders_after_run1) AS sum_run1,
    (SELECT SUM(amount) FROM intermediate_orders)            AS sum_run2;
