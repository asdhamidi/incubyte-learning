-- Upset rate by how the game ended (mate, resign, out of time): how often the lower-rated
-- player wins, for each way a game can end. Counts sit next to the rate.
CREATE OR REPLACE VIEW upset_by_ending AS
SELECT
    COALESCE(victory_status, 'unknown') AS victory_status,
    COUNT(*) AS games,
    SUM(lower_rated_won) AS lower_rated_won,
    ROUND(100.0 * SUM(lower_rated_won) / COUNT(*), 1) AS upset_rate_pct
FROM decided_games
GROUP BY 1;
