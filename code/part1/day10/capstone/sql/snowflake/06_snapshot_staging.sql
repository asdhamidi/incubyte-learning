-- Run before rebuilding staging (before sql/stg_games.sql), except on the very first run
-- when stg_games does not exist yet.
-- games_summary is a view over stg_games, so staging is what has to be protected. This keeps
-- the last good staging, so it can be put back if a data quality check fails.
CREATE OR REPLACE TABLE stg_games_last_good CLONE stg_games;
