# Capstone design

## Question
**Do higher-rated players actually win more games, and how does that change as the rating gap grows?**

Asked by a ratings or matchmaking owner, who wants to know whether ratings predict results well enough to build matches on. The answer comes from one summary table, `games_summary`, defined in `metric_definition.md`.

## Architecture
```text
Lichess games file (TSV)
   -> Azure Blob Storage          container `capstone`, folder `games/`
   -> Snowflake external stage    storage integration, COPY INTO
   -> RAW_GAMES                   exact copy of the file plus file name and load time
   -> STG_GAMES                   one row per game, typed and cleaned
   -> GAMES_SUMMARY (view)        higher-rated win rate by rating-gap band
```

Tests and CI run the same transformation SQL on DuckDB, which stands in for Snowflake. Only the load step differs (`COPY INTO` in Snowflake, `read_csv` in DuckDB). The upload to Blob Storage and the Snowflake load are run by hand against the real accounts.

## Layers
| Layer | Holds | Rules |
|---|---|---|
| Raw | The file as delivered, all text, plus `source_file` and `loaded_at` | No logic. Never edited |
| Staging | One row per `id`, with real types (ratings as integers, `rated` as a boolean, `created_at` kept as epoch milliseconds in `created_at_ms`) | Dedupe, casts and renames only. No business rules |
| Summary | A view with one row per rating-gap band | The metric rules live here and only here |

## Test strategy
| Test | What it protects | Where |
|---|---|---|
| Contract | The file still has the columns and types the pipeline reads. Fails fast if a column disappears | Before the load |
| Component | Each SQL step on small fixtures, including the worked example from the metric definition | Every push |
| Data | Not null and unique on `id`, accepted values on `winner` and `rated` | After staging |
| Data quality check | One check with a failure plan, see `dq_failure_plan.md` | Every load |

Built test-first: each step starts with a failing test. CI runs `python ci.py` on every push, and a pull request is the gate.

## Decisions and open questions
- **The summary is a view over staging**, so it never needs rebuilding. The cost is that a view follows staging immediately, so staging is what a failed data quality check has to protect: the pipeline puts staging back to its last good version and keeps the rejected build in `stg_games_rejected`.
- **Same SQL on both engines.** CTEs and standard functions only, so one file runs on DuckDB and Snowflake.
- **Duplicates are removed in staging**, by `id`. The sample file has one game delivered twice.
- **Draws and unrated games are excluded from the metric**, and draws are reported as a caveat.
- **Sample numbers are not an answer.** The sample file is synthetic, so its rates mean nothing. The answer comes from the real file run through the same pipeline.
- Open: the real Blob container, Snowflake database and schema names, and which Lichess file (full or a slice) to load.
