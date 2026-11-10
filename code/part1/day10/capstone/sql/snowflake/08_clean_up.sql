-- Run after a load where every check returned no rows and games_summary is in place.
-- Removes the snapshot and any earlier rejected build.
DROP TABLE IF EXISTS stg_games_last_good;
DROP TABLE IF EXISTS stg_games_rejected;
