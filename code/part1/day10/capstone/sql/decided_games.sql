-- The games that count for the upset views: the same rules as games_summary.
-- Rated, decisive (no draws), and with two different ratings, so one player is the favourite.
-- A view over stg_games, so it follows the last good staging. Runs on DuckDB and Snowflake.
CREATE OR REPLACE VIEW decided_games AS
SELECT
    opening_name,
    turns,
    victory_status,
    CASE
        WHEN winner = CASE WHEN white_rating > black_rating THEN 'black' ELSE 'white' END
        THEN 1 ELSE 0
    END AS lower_rated_won
FROM stg_games
WHERE rated
  AND winner IN ('white', 'black')
  AND white_rating <> black_rating;
