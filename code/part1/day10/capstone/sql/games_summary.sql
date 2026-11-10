-- Summary: higher-rated win rate by rating-gap band. See docs/metric_definition.md.
-- This is the only place the metric rules live. Runs unchanged on DuckDB and Snowflake.
-- A view over stg_games, so it always follows the last good staging (see pipeline.py).
-- Counts sit next to the rate, so a total is SUM(games), never an average of rates.
CREATE OR REPLACE VIEW games_summary AS
WITH decided AS (
    -- rated, decisive games where one player is rated higher
    SELECT
        winner,
        ABS(white_rating - black_rating) AS gap,
        CASE WHEN white_rating > black_rating THEN 'white' ELSE 'black' END AS higher_rated
    FROM stg_games
    WHERE rated
      AND winner IN ('white', 'black')
      AND white_rating <> black_rating
),
banded AS (
    SELECT
        winner,
        higher_rated,
        CASE
            WHEN gap < 100 THEN '1-99'
            WHEN gap < 200 THEN '100-199'
            WHEN gap < 400 THEN '200-399'
            ELSE '400+'
        END AS gap_band,
        CASE
            WHEN gap < 100 THEN 1
            WHEN gap < 200 THEN 100
            WHEN gap < 400 THEN 200
            ELSE 400
        END AS band_min_gap
    FROM decided
)
SELECT
    gap_band,
    band_min_gap,
    COUNT(*) AS games,
    SUM(CASE WHEN winner = higher_rated THEN 1 ELSE 0 END) AS higher_rated_won,
    ROUND(100.0 * SUM(CASE WHEN winner = higher_rated THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS higher_rated_win_rate_pct
FROM banded
GROUP BY gap_band, band_min_gap;
