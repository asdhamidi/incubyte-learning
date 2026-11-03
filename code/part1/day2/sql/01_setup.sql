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
    (4, 'dave',  400, 'placed',  '2026-10-02 10:00'),
    (7, 'gina',  700, 'placed',  '2026-10-02 12:00');

-- Incremental batch: duplicates, late records, a tie on updated_at and delete flags.
-- load_seq is the order the rows arrived in, and breaks ties on updated_at.
CREATE OR REPLACE TABLE raw_orders (
    order_id   INTEGER,
    customer   VARCHAR,
    amount     INTEGER,
    status     VARCHAR,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN,
    load_seq   INTEGER
);

INSERT INTO raw_orders VALUES
    (2, 'bob',   200, 'shipped', '2026-10-03 09:00', false, 1),   -- real update to an existing order
    (2, 'bob',   200, 'placed',  '2026-10-02 08:00', false, 2),   -- duplicate key in batch, older version
    (3, 'carol', 300, 'placed',  '2026-10-01 08:00', false, 3),   -- late record: older than what the target holds
    (5, 'erin',  500, 'placed',  '2026-10-03 10:00', false, 4),   -- new order
    (5, 'erin',  550, 'placed',  '2026-10-03 12:00', false, 5),   -- duplicate new key, latest should win
    (8, 'hana',  800, 'placed',  '2026-10-03 13:00', false, 6),   -- tie on updated_at with the next row
    (8, 'hana',  810, 'placed',  '2026-10-03 13:00', false, 7),   -- same timestamp, higher load_seq should win
    (4, 'dave',  400, 'placed',  '2026-10-04 09:00', true,  8),   -- delete of an existing order
    (6, 'frank', 600, 'placed',  '2026-10-02 09:00', true,  9),   -- delete of an order that was never loaded
    (7, 'gina',  700, 'placed',  '2026-10-01 12:00', true,  10);  -- late delete: older than what the target holds
