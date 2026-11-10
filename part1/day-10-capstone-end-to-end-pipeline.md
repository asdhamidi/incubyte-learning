# Part 1 · Day 10 — Capstone: An End-to-End Pipeline

**Date completed:** 2026-10-11 · **Time spent:** ~5 hours
## Success criteria
| Criterion (copied from the planner) | Done? | Evidence (link or section below) |
| ----------------------------------- | ----- | -------------------------------- |
| Builds an end-to-end pipeline from Blob Storage to Snowflake | Yes | [Architecture](#architecture), [Cloud run](#cloud-run), [runbook](../code/part1/day10/capstone/docs/runbook_cloud.md); the sample file was landed, loaded, checked and summarised in Snowflake |
| Tests the pipeline and runs tests in CI through a pull request | Yes | [How it was built](#how-it-was-built-test-first), [Tests and CI](#tests-and-ci), [pull request #4](https://github.com/asdhamidi/incubyte-learning/pull/4) merged with a green check, [screenshot](../assets/day10/pr_checks_green.png) |
| Adds a data quality check with a failure plan | Yes | [Data quality check](#data-quality-check-and-failure-plan), [failure plan](../code/part1/day10/capstone/docs/dq_failure_plan.md), [tests](../code/part1/day10/capstone/tests/test_dq.py) |
| Answers a stakeholder question with a clear metric definition | Partly | [The question and the metric](#the-question-and-the-metric), [metric definition](../code/part1/day10/capstone/docs/metric_definition.md); the answer needs the real file |
| Presents the work concisely | Pending | [Ten-minute walkthrough](#ten-minute-walkthrough) |
| Writes a comprehensive reflection | Pending | [Reflection on the two weeks](#reflection-on-the-two-weeks) |

## Key learnings
## Exercises
## Reflection
## AI use
- Built the capstone step by step with Claude Code, test-first: each step's tests were written and seen failing before the code existed.
- The cloud steps (the upload and the Snowflake load) were run by me in my own accounts.
## Open questions
## Changes after review

---
## Notes

### The question and the metric
**Do higher-rated players actually win more games, and how does that change as the rating gap grows?** It is the kind of question a ratings or matchmaking owner asks, and it needs a precise definition before any SQL.

The metric is `higher_rated_win_rate_by_gap_band`, the share of decided rated games won by the higher-rated player, split into four bands of rating gap (1-99, 100-199, 200-399, 400+). Full definition: [metric_definition.md](../code/part1/day10/capstone/docs/metric_definition.md).
- Rated games only. Draws are left out, and so are games where both ratings are equal. A game delivered twice counts once.
- The game count sits next to every rate, since small bands are noisy.
- The definition has a worked example of six rows checked by hand, and a test runs the same six rows through the whole pipeline and gets the same result.
- The sample file is synthetic, so its rates mean nothing. Only the real Lichess file can answer the question.

### Architecture
```text
Lichess games file (TSV)
   -> Azure Blob Storage          container `capstone`, folder `games/`
   -> Snowflake external stage    storage integration, COPY INTO
   -> RAW_GAMES                   the file as delivered, plus file name, line and load time
   -> STG_GAMES                   one row per game, typed
   -> GAMES_SUMMARY (view)        higher-rated win rate by rating-gap band
```

| Layer | Holds | Rules |
|---|---|---|
| Raw | The file as delivered, all text | No logic. Never edited |
| Staging | One row per game, with real types | Dedupe, casts and renames only |
| Summary | A view with one row per rating-gap band | The metric rules live here and only here |

- DuckDB stands in for Snowflake in tests and CI. The staging and summary SQL files are the same ones that run in Snowflake, and a test blocks DuckDB-only syntax in them. Only the load differs (`read_csv` in DuckDB, `COPY INTO` in Snowflake).
- The Snowflake load matches columns by the header names and not by position, so a reordered file can't load values into the wrong columns.
- Design notes: [design.md](../code/part1/day10/capstone/docs/design.md).

### How it was built, test-first
Each step started with tests that failed, then the code that made them pass, then a check that the tests catch a deliberate break.

| Step | What | Tests |
|---|---|---|
| Contract | Validator for the file: the columns and types the pipeline reads, and a gate that stops a bad file before anything loads | 14 |
| Raw and staging | Raw load that replaces a file's rows on reload, and staging that dedupes with a unique tie-breaker | 14 |
| Data tests | Six checks on staging (not null, unique, ratings positive, row counts match raw), each also run against a planted bad row to prove it can fail | 13 |
| Summary | The metric, with boundary tests on every band edge, and a cross-check against the metric worked out in plain Python | 22 |
| Data quality check | The `winner` check, and the pipeline that puts staging back to its last good version when it fails | 14 |
| Cloud steps | Upload that checks the contract first, and guards that keep the Snowflake scripts in line with the tested code | 14 |

- 92 tests in the capstone, and 154 across the repo in CI.
- Mutation checks, done by breaking the code on purpose: removing the dedupe failed 6 tests, including the draws in the metric failed 4, skipping the contract gate failed 2, and skipping the rollback of staging failed 2 tests. One test of mine was too weak at first, and a mutation check showed it.
- Two problems came up from CI and not from my own tests. The capstone's tests read their sample file relative to the working directory, which fails when CI runs from the repo root. And a module named `pipeline` clashed with Day 2's, so the capstone code moved into a `games_pipeline` package.

### Tests and CI
| Test | What it protects | When |
|---|---|---|
| Contract | The file still has the columns and types the pipeline reads | Before the load |
| Component | Each SQL step on small fixtures, including the worked example | Every push |
| Data | Not null, unique, positive ratings, row counts match raw | After staging |
| Data quality check | `winner` is one of white, black, draw | Every load |

- `python ci.py` runs four stages in order: no data files committed, format, lint, tests. GitHub Actions runs the same command on every push.
- Work went on the branch `capstone-pipeline` in six small commits, one per step, so each can be reverted on its own.
- I ran CI on a clean checkout of the branch before pushing, so nothing the branch needs is untracked or ignored.
- The branch went in as [pull request #4](https://github.com/asdhamidi/incubyte-learning/pull/4) with its six commits. The `CI / test` check passed on the branch and again on `main` after the merge.

![Pull request 4 merged, with its checks passed](../assets/day10/pr_checks_green.png)

*Pull request #4 with six commits, merged after the checks passed.*

### Data quality check and failure plan
The check is `winner_accepted_values`. In staging, `winner` must be `white`, `black` or `draw`, and never NULL. It matters because the summary only counts `white` and `black`, so a new spelling would drop games out of the metric without any error. This is the same silent failure as the `complete` status on Day 6. The check blocks the summary.

When it fails:
- **Contain:** `games_summary` is a view over staging, so staging is what gets protected. The pipeline puts `stg_games` back to its last good version and keeps the rejected build in `stg_games_rejected`, and raw keeps the new data.
- **Tell:** the pipeline owner straight away, and the stakeholder within the hour if the summary stays stale, in plain terms.
- **Investigate:** which values, which delivery, then the raw rows.
- **Fix and recover:** find out what the value means, correct or map it, reload (a reload replaces the file's rows), rerun.
- **Check it's fixed:** the check returns no rows and the counts reconcile.

Tests cover an unknown value, a different case, NULL, an empty string, the summary staying unchanged after a failure, staging being put back to its last good version, the rejected build being kept, and a rerun with a fixed file recovering. Full plan: [dq_failure_plan.md](../code/part1/day10/capstone/docs/dq_failure_plan.md).

![The winner check returning no rows in Snowflake](../assets/day10/checks_empty.png)

*The check run in Snowflake on the loaded data: no unexpected `winner` values.*

### Cloud run
Runbook: [runbook_cloud.md](../code/part1/day10/capstone/docs/runbook_cloud.md). The sample file was landed in Blob Storage, staged in Snowflake and loaded into `raw_games`, and the numbers matched the local run.

![The capstone container in Azure with games/games_sample.tsv](../assets/day10/storage_account_files.png)

*The file in Blob Storage, under `capstone/games/`.*

![LIST @capstone_stage showing the uploaded file](../assets/day10/snowflake_stage_list.png)

*The Snowflake stage can see the file.*

![COPY INTO result: 40 raw rows and 39 distinct games](../assets/day10/copy_into.png)

*The load: 40 raw rows and 39 distinct games, as expected (one game is delivered twice).*

![The summary in Snowflake for the sample file](../assets/day10/summary_sample.png)

*The summary for the sample file in Snowflake: 25 games in four bands (25.0, 50.0, 25.0 and 18.2), the same numbers as the local run.*

### The stakeholder answer
To be written from the real file. Run the pipeline on the real Lichess file in Snowflake (runbook steps 3 and 4), read `games_summary`, then write three sentences: the answer with the number and the comparison first, the evidence (the bands and the game counts), then the caveat (draws excluded, small bands, what the data can't say). Numbers from the sample file are not a finding and should not go here.

### Ten-minute walkthrough
| Time | What to show |
|---|---|
| 0:00 | The question and who is asking, and the metric definition in one slide |
| 1:30 | The architecture, one picture, and why DuckDB stands in for Snowflake in tests |
| 3:00 | The tests: run `python ci.py`, then break one thing and show CI go red, then green |
| 5:30 | The data quality check failing on a bad `winner`, what stops, and the failure plan |
| 7:00 | The answer to the stakeholder from the summary table, in three sentences |
| 9:00 | What I would do next, and one question for the pod |

### Open items
- Add a screenshot of the green `CI / test` check on pull request #4.
- Run the transform in Snowflake (runbook steps 4 and 5) and add the summary and the data quality failure screenshots.
- Change the Snowflake app's role on the storage account from Storage Blob Data Contributor to Reader, then retake the role assignment screenshot.
- Check that the real file went through: `SELECT source_file, COUNT(*) FROM raw_games GROUP BY 1;` should list it. The summary screenshot shows 25 games, which is the sample file, so the real file's result still needs capturing.
- Write the stakeholder answer from the real file's summary.

---
## Reflection on the two weeks
Looking back over the two weeks, the thing that changed most was how I start. Before, I started from the code. Now I start from the question and the definition, and I write the expected result by hand before I write any SQL. The metric framework from the analytics day and the test-first approach from the testing day ended up being the same habit: say exactly what the right answer is, then build until the pipeline agrees.

A lot of the early days were refreshers that I understood better by doing them again. Idempotency, late-arriving data and the traps in MERGE and set operators were familiar, but writing the tests for them showed me how easily a result can look right and be wrong. The AWS-to-Azure mapping carried over well: Glue and Step Functions became Data Factory, S3 became Blob Storage. The part that did not map one to one was IAM and the way Azure organises tenants, subscriptions and role assignments. That showed up again in this capstone when the Snowflake app needed its own role on a new storage account.

I had set up data quality checks before, but I had not tested them properly. Building them test-first, with a planted bad row for every check, and writing down what happens when one fails, made them much more trustworthy. The same goes for CI. I had used it before without setting it up myself, and having CI catch two problems that my own tests missed (a path that only worked from one folder, and a module name clash) was the best argument for it.

Where I still want to grow:
- Cloud permissions across the two clouds, especially IAM, which I still cannot translate in my head the way I can with storage and orchestration.
- Building and testing real models in dbt, which so far I know from notes and a project layout, not from a project of my own.
- Power BI measures. My first report counted cancelled orders because it used plain sums, and I would like to build the measures that carry the metric definition.
- Writing answers for stakeholders faster. The definition and the checks are slow the first time, and I want them to become a template I reuse.
