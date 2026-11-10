-- Staging: one row per game, with real types. No business rules here.
-- Runs unchanged on DuckDB (tests, CI) and Snowflake.
-- created_at stays as epoch milliseconds: turning it into a timestamp is engine-specific
-- and the metric does not need it yet.
CREATE OR REPLACE TABLE stg_games AS
SELECT
    id,
    CAST(rated AS BOOLEAN)        AS rated,
    CAST(created_at AS BIGINT)    AS created_at_ms,
    CAST(white_rating AS INTEGER) AS white_rating,
    CAST(black_rating AS INTEGER) AS black_rating,
    winner,
    victory_status,
    source_file,
    loaded_at
FROM raw_games
-- a game can be delivered twice: keep the earliest delivery,
-- with the file line as the unique tie-breaker so the winner is always the same
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY id
    ORDER BY loaded_at, source_file, source_line
) = 1;
