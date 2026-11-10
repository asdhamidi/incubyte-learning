-- Run only if a query in 04_checks.sql returned rows.
-- Keeps the rejected build for investigation and puts the last good staging back, so
-- games_summary keeps showing the last good numbers.
CREATE OR REPLACE TABLE stg_games_rejected CLONE stg_games;
CREATE OR REPLACE TABLE stg_games CLONE stg_games_last_good;
DROP TABLE stg_games_last_good;

-- First run, with no last good staging: there is nothing to put back, so drop staging instead.
--   DROP TABLE stg_games;
