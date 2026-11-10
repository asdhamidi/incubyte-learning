-- The answer to the stakeholder question, by rating-gap band.
SELECT gap_band, games, higher_rated_won, higher_rated_win_rate_pct
FROM games_summary
ORDER BY band_min_gap;

-- Overall, from the counts. Never average the rates in the table above.
SELECT
    SUM(games)            AS games,
    SUM(higher_rated_won) AS higher_rated_won,
    ROUND(100.0 * SUM(higher_rated_won) / SUM(games), 1) AS higher_rated_win_rate_pct
FROM games_summary;
