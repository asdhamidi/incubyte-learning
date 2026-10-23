-- Target table: what is already loaded.
CREATE OR REPLACE TABLE intermediate_orders (
    order_id   INTEGER,
    customer   VARCHAR,
    amount     INTEGER,
    status     VARCHAR,
    updated_at TIMESTAMP
);

INSERT INTO intermediate_orders VALUES
    (1, 'alice', 100, 'placed',  '2026-10-01 10:00'),
    (2, 'bob',   200, 'placed',  '2026-10-01 11:00'),
    (3, 'carol', 300, 'shipped', '2026-10-02 09:00'),
    (4, 'dave',  400, 'placed',  '2026-10-02 10:00');

-- Incremental batch: contains duplicates and a late record.
CREATE OR REPLACE TABLE raw_orders (
    order_id   INTEGER,
    customer   VARCHAR,
    amount     INTEGER,
    status     VARCHAR,
    updated_at TIMESTAMP
);

INSERT INTO raw_orders VALUES
    (2, 'bob',   200, 'shipped', '2026-10-03 09:00'),  -- real update to an existing order
    (2, 'bob',   200, 'placed',  '2026-10-02 08:00'),  -- duplicate key in batch, older version
    (3, 'carol', 300, 'placed',  '2026-10-01 08:00'),  -- late record: older than what the target holds
    (5, 'erin',  500, 'placed',  '2026-10-03 10:00'),  -- new order
    (5, 'erin',  550, 'placed',  '2026-10-03 12:00');  -- duplicate new key, latest should win
