MERGE INTO intermediate_orders AS t
USING (
    SELECT order_id, customer, amount, status, updated_at
    FROM raw_orders
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC) = 1
) AS s
ON t.order_id = s.order_id
WHEN MATCHED AND s.updated_at > t.updated_at THEN
    UPDATE SET customer = s.customer,
               amount = s.amount,
               status = s.status,
               updated_at = s.updated_at
WHEN NOT MATCHED THEN
    INSERT (order_id, customer, amount, status, updated_at)
    VALUES (s.order_id, s.customer, s.amount, s.status, s.updated_at);
