# Data quality check: winner_accepted_values

| Field | Value |
|---|---|
| What it checks | `winner` in `stg_games` is `white`, `black` or `draw`, and never NULL |
| Dimension | Validity |
| Where it runs and when | After staging and before the summary is built, on every load. Code: `DQ_CHECKS` in `src/checks.py`, run by `run_pipeline` in `src/pipeline.py` |
| Threshold | Zero rows. Any other value fails the check |
| Severity | Blocks the load of the summary |

## Why this check
The summary only counts games where `winner` is `white` or `black`. If the source starts sending another spelling (`White`, `whtie`, an empty value), those games drop out of the metric without any error and every rate shifts. This is the same silent failure as the `complete` vs `completed` status in Day 6. A contract test cannot catch it, because the column is still there and still text.

## When it fails
1. **Contain:** the pipeline stops before the summary step. `games_summary` is not rebuilt, so it keeps its last good version and readers see older but correct numbers. Raw and staging keep the new data so it can be investigated. The failure message names the check, the unexpected values and how many rows have each, for example `winner_accepted_values failed: unexpected values 'whtie' (2 rows)`.
2. **Who is told, and how fast:** the pipeline owner, straight away, through the failed run (a red CI run or a failed task). If the summary is going to stay stale past its normal refresh, the stakeholder is told within the hour, in plain terms: what happened, which numbers are stale since when, what is being done, and when the next update comes.
3. **How to investigate:** the first three queries.
   ```sql
   -- 1. Which values, and how many rows each
   SELECT winner, COUNT(*) FROM stg_games
   WHERE winner IS NULL OR winner NOT IN ('white', 'black', 'draw')
   GROUP BY winner;

   -- 2. Which delivery they came from
   SELECT source_file, loaded_at, COUNT(*) FROM stg_games
   WHERE winner IS NULL OR winner NOT IN ('white', 'black', 'draw')
   GROUP BY source_file, loaded_at;

   -- 3. The raw rows, to compare with the file (source_line is the line in the file)
   SELECT id, winner, victory_status, source_file, source_line FROM raw_games
   WHERE winner IS NULL OR winner NOT IN ('white', 'black', 'draw')
   LIMIT 20;
   ```
4. **How to fix and recover:** find out what the value means. If the source made a mistake, ask for a corrected file and load it. Loading a file again replaces that file's raw rows, so a rerun is safe. If it is a real new outcome, decide with the metric owner how it counts, then either map it in staging or add it to the accepted list, and update `metric_definition.md` and its change log. Rerun the pipeline.
5. **How we know it's fixed:** the check returns no rows, the summary is rebuilt, the `rows_match_raw` data test still passes, and the games counted in the summary equal the count from a direct query on staging. The stakeholder is told the numbers are current.

## What the tests prove
`tests/test_dq.py` covers a clean run, an unknown value with its count, a different case, a NULL winner, an empty winner, the summary staying unchanged after a failure, the new data being kept in raw and staging, the failure message naming the value, and a rerun with a fixed file recovering.
