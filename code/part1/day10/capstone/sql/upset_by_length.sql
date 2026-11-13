-- Upset rate by game length: how often the lower-rated player wins in short and long games.
-- `turns` counts moves by both players. A game with no usable turns count is 'unknown'.
CREATE OR REPLACE VIEW upset_by_length AS
WITH bucketed AS (
    SELECT
        lower_rated_won,
        CASE
            WHEN turns IS NULL THEN 'unknown'
            WHEN turns <= 30 THEN '1-30'
            WHEN turns <= 60 THEN '31-60'
            WHEN turns <= 90 THEN '61-90'
            ELSE '91+'
        END AS game_length,
        CASE
            WHEN turns IS NULL THEN 5
            WHEN turns <= 30 THEN 1
            WHEN turns <= 60 THEN 2
            WHEN turns <= 90 THEN 3
            ELSE 4
        END AS length_order
    FROM decided_games
)
SELECT
    game_length,
    length_order,
    COUNT(*) AS games,
    SUM(lower_rated_won) AS lower_rated_won,
    ROUND(100.0 * SUM(lower_rated_won) / COUNT(*), 1) AS upset_rate_pct
FROM bucketed
GROUP BY game_length, length_order;
