-- Load the staged file into raw_games.
-- Columns are matched by the header names, not by position, and the file name, line number
-- and scan time are recorded for every row (the same lineage columns the DuckDB loader fills).
COPY INTO raw_games
FROM @capstone_stage
FILE_FORMAT = (FORMAT_NAME = capstone_tsv)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
INCLUDE_METADATA = (
    source_file = METADATA$FILENAME,
    source_line = METADATA$FILE_ROW_NUMBER,
    loaded_at   = METADATA$START_SCAN_TIME
)
ON_ERROR = ABORT_STATEMENT;

-- Snowflake remembers which files it has loaded and skips them, so running this again
-- loads zero rows. To reload a corrected file that has the same name, remove its rows
-- first and force the load:
--
--   DELETE FROM raw_games WHERE source_file = 'games_sample.tsv';
--   COPY INTO raw_games ... FORCE = TRUE;   -- same statement as above, plus FORCE = TRUE

SELECT COUNT(*) AS raw_rows, COUNT(DISTINCT id) AS distinct_games FROM raw_games;
