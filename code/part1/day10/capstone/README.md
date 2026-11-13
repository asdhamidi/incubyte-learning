# End-to-end pipeline capstone

Local file -> Azure Blob Storage -> Snowflake (raw, staging, summary) with tests and CI. Question answered: do higher-rated players win more, and how does that change as the rating gap grows? A follow-up answers when the lower-rated player wins.

Data: the Kaggle "Chess Game Dataset (Lichess)" (`games.csv`, 20,058 games). The file is never committed.

## Run the checks
    pip install -r requirements.txt
    python ci.py

## Run the pipeline
One command takes the local file all the way to the summary:

    pip install -r requirements-snowflake.txt
    az login
    python -m games_pipeline.snowflake_run --local-file path/to/games.csv --storage-account <storage-account>

Run it from `src/`. The Snowflake sign-in settings (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_ROLE`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`, and `SNOWFLAKE_PASSWORD` with `SNOWFLAKE_AUTHENTICATOR=snowflake` if the account has no browser sign-in) are set in your own shell, never in the repo. The full steps are in `docs/runbook_cloud.md`.

In order, it:
1. checks the file against the contract, so a bad file never leaves your machine
2. uploads it to Blob Storage, replacing a file of the same name
3. creates the Snowflake file format and the stage that points at the Blob folder
4. loads it into `raw_games` with `COPY INTO`, in one transaction that rolls back on an error
5. keeps the last good staging, then rebuilds `stg_games`
6. runs the data quality check. On a failure, staging goes back to the last good version, the rejected build is kept in `stg_games_rejected`, and the command exits with an error
7. builds `games_summary` and the three upset views, and prints them

The storage integration is set up once by an account admin (runbook step 0) and is not part of the command. Without `--storage-account` nothing is uploaded, and the file must already be in Blob Storage.

### What you see
Progress goes to the terminal as short lines: a time, a mark and the message. `>` is a step starting, `+` is a step done with its time, `!` is a warning and `x` is an error. `-v` adds debug detail. The password is never logged. The result tables print last, with the counts next to each rate and a bar.

## What it answers
`games_summary` is the higher-rated win rate by rating-gap band (1-99, 100-199, 200-399, 400+). Three more views show how often the lower-rated player wins, over the same games:

| View | By |
|---|---|
| `upset_by_opening` | Opening family (the name before the first colon) |
| `upset_by_ending` | How the game ended: mate, resign or out of time |
| `upset_by_length` | Game length in moves: 1-30, 31-60, 61-90, 91+ |

The rules are in `docs/metric_definition.md`. Every view counts the same games as the summary: rated, decisive, with two different ratings.

## Layout
| Path | Holds |
|---|---|
| `src/games_pipeline/` | `contract.py` (file contract and gate), `load.py` (raw load and the SQL runners), `checks.py` (data tests and the data quality check), `pipeline.py` (the run in order, on DuckDB), `land.py` (check, then upload to Blob Storage), `snowflake_run.py` (the one command above), `report.py` (the printed tables), `log.py` (the progress log) |
| `sql/` | `stg_games.sql`, `games_summary.sql` and the upset views (`decided_games`, `upset_by_opening`, `upset_by_ending`, `upset_by_length`), shared by DuckDB and Snowflake |
| `sql/snowflake/` | The same steps as separate worksheet scripts, for running by hand: stage and file format, raw table, load, checks, read the summary |
| `tests/` | pytest tests: contract, raw, staging, data tests, summary, upset views, data quality check, upload, runner, report, log, Snowflake script guards |
| `sample_data/` | Small fixture files only, never real data |
| `docs/` | Design, metric definition, data quality failure plan, cloud runbook |
| `ci.py` | The single entry point that runs the checks |

The sample file is comma-separated, like the Lichess download, and mixes its value formats (`True` and `TRUE`, whole-number and scientific-notation timestamps). It contains one duplicated game id.

## How it fits together
DuckDB stands in for Snowflake in tests and CI, so the transformation SQL is tested on every push. The runner is tested against a fake Snowflake connection that records the SQL it is given, so no account is needed. What the SQL does in Snowflake is checked by running it there (`docs/runbook_cloud.md`). `sql/snowflake/04_checks.sql` is generated from `checks.py` (`python -m games_pipeline.checks`), and a test fails if they drift apart.
