# End-to-end pipeline capstone

Blob Storage -> Snowflake (raw, staging, summary) with tests and CI. Question answered: do higher-rated players win more, and how does that change as the rating gap grows?

## Run the checks
    pip install -r requirements.txt
    python ci.py

## Layout
| Path | Holds |
|---|---|
| `src/games_pipeline/` | `contract.py` (file contract and gate), `load.py` (raw load and the SQL runners), `checks.py` (data tests and the data quality check), `pipeline.py` (the run in order), `land.py` (check, then upload to Blob Storage), `snowflake_run.py` (one command for the Snowflake steps) |
| `sql/` | `stg_games.sql` and `games_summary.sql`, shared by DuckDB and Snowflake |
| `sql/snowflake/` | The scripts that only run in Snowflake: stage and file format, raw table, load, checks, read the summary |
| `tests/` | pytest tests: contract, raw, staging, data tests, summary, data quality check, upload, Snowflake script guards |
| `sample_data/` | Small fixture files only, never real data |
| `docs/` | Design, metric definition, data quality failure plan, cloud runbook |
| `ci.py` | The single entry point that runs the checks |

The sample file is tab-separated, like the Lichess file, and contains one duplicated game id.

## How it fits together
DuckDB stands in for Snowflake in tests and CI, so the transformation SQL is tested on every push. The two cloud steps, the upload and the Snowflake load, run by hand: see `docs/runbook_cloud.md`. `sql/snowflake/04_checks.sql` is generated from `checks.py` (`python -m games_pipeline.checks`), and a test fails if they drift apart.
