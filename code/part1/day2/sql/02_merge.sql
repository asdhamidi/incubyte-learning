MERGE INTO intermediate_orders AS t
USING (
    -- one row per business key: the latest version in the batch,
    -- with load_seq as the unique tie-breaker so the winner is always the same
    SELECT order_id, customer, amount, status, updated_at, is_deleted
    FROM raw_orders
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY order_id
        ORDER BY updated_at DESC, load_seq DESC
    ) = 1
) AS s
ON t.order_id = s.order_id
-- deletes first, since only the first clause that is true for a row runs
WHEN MATCHED AND s.is_deleted AND s.updated_at > t.updated_at THEN
    DELETE
-- the guard: late or already-applied records cannot overwrite newer data
WHEN MATCHED AND NOT s.is_deleted AND s.updated_at > t.updated_at THEN
    UPDATE SET customer = s.customer,
               amount = s.amount,
               status = s.status,
               updated_at = s.updated_at
-- a delete for an order we never loaded must not create it
WHEN NOT MATCHED AND NOT s.is_deleted THEN
    INSERT (order_id, customer, amount, status, updated_at)
    VALUES (s.order_id, s.customer, s.amount, s.status, s.updated_at);
