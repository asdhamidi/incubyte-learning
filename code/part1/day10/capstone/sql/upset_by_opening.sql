-- Upset rate by opening: how often the lower-rated player wins, for each opening family.
-- The family is the opening's name before the first colon, so every variation of the
-- Sicilian Defense counts as the Sicilian Defense. Counts sit next to the rate.
CREATE OR REPLACE VIEW upset_by_opening AS
SELECT
    COALESCE(NULLIF(TRIM(SPLIT_PART(opening_name, ':', 1)), ''), 'unknown') AS opening_family,
    COUNT(*) AS games,
    SUM(lower_rated_won) AS lower_rated_won,
    ROUND(100.0 * SUM(lower_rated_won) / COUNT(*), 1) AS upset_rate_pct
FROM decided_games
GROUP BY 1;
