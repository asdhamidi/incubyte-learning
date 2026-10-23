CREATE OR REPLACE TABLE web_sales (store VARCHAR, sale_date DATE, amount INTEGER);
CREATE OR REPLACE TABLE app_sales (store VARCHAR, sale_date DATE, amount INTEGER);

INSERT INTO web_sales VALUES
    ('A', '2026-10-01', 100),
    ('A', '2026-10-01', 100),  -- a real, separate sale that looks identical
    ('B', '2026-10-01', 50);
INSERT INTO app_sales VALUES
    ('A', '2026-10-01', 100),
    ('B', '2026-10-01', 50),
    ('C', '2026-10-01', 70);

-- `UNION ALL` keeps all 6 input rows (total 470),
-- while `UNION` removes fully identical rows within and across the inputs, leaving 3 (total 220).
-- It dropped the repeated `('A', 100)` sale and the `('B', 50)` row that appears in both tables, so totals shrink without any error.

SELECT 'UNION ALL' AS operator, COUNT(*) AS row_count, SUM(amount) AS total FROM (
    SELECT * FROM web_sales
    UNION ALL
    SELECT * FROM app_sales
)
UNION ALL
SELECT 'UNION', COUNT(*), SUM(amount) FROM (
    SELECT * FROM web_sales
    UNION
    SELECT * FROM app_sales
);
