# Runbook: Blob Storage to Snowflake

The steps CI cannot run: they need your Azure and Snowflake accounts. Everything else (contract, staging, summary, data quality check) is tested locally and in CI on DuckDB. Run these once with the sample file to prove the cloud pipeline gives the same numbers, then again with the real Lichess file.

Replace `<storage-account>`, `<database>` and `<schema>` with your own names. Snowflake steps run as `ACCOUNTADMIN` (or a role with the same rights) in a worksheet.

## Expected results for the sample file
Compare each step with these, which come from the local run.

| Step | Expected |
|---|---|
| `raw_games` | 40 rows, 39 distinct ids |
| `stg_games` | 39 rows |
| Staging data tests | every query returns no rows |
| `winner_accepted_values` | no rows |
| `games_summary` | 1-99: 4 games, 1 won, 25.0 / 100-199: 2, 1, 50.0 / 200-399: 8, 2, 25.0 / 400+: 11, 2, 18.2 |
| Overall | 25 games, 6 won, 24.0% |

The sample file is synthetic, so these rates are not a finding. They are only there to prove the pipeline.

## 0. Set up Azure again
For when the subscription and its resources have been deleted but the Microsoft account and the Snowflake account still exist. Only a storage account is needed. The Data Factory and Azure SQL from Days 3 and 4 are not part of this pipeline.

1. **Subscription.** Portal, Subscriptions, + Add. The free account offer may not be available a second time, in which case use Pay-As-You-Go. This capstone stores a few kilobytes, so the cost is close to zero.
2. **Budget.** Cost Management, Budgets, + Add: a small monthly amount (for example $5) with an alert at 80% to your email, as on Day 3.
3. **Resource group.** Resource groups, + Create: `rg-capstone`, in a region near you.
4. **Storage account.** Storage accounts, + Create: in `rg-capstone`, a globally unique name (3 to 24 lowercase letters and numbers, for example `stcapstone` plus some digits), the same region, Standard, LRS. Leave public blob access off.
5. **Your own access.** Owner on the subscription does not let you read or write blob data. On the storage account, Access Control (IAM), + Add, Add role assignment, role **Storage Blob Data Contributor**, member: your user. Wait a minute or two. Without it, `az ... --auth-mode login` fails with a permissions error.
6. **Container.** On the storage account, Containers, + Container: `capstone`.
7. **Snowflake's access.** The Snowflake app from Day 3 still exists, because it lives in the tenant and not in the subscription. Run `DESC STORAGE INTEGRATION azure_int;` and copy `AZURE_MULTI_TENANT_APP_NAME`. On the new storage account, Access Control (IAM), + Add role assignment, role **Storage Blob Data Reader**, member: that app (search by the name, or by the part before the underscore).
   - If the app is not found in the members search, open `AZURE_CONSENT_URL` from the same `DESC` output, accept, and look again under Entra ID, Enterprise applications (Day 3, steps 4 and 5).
   - If you are in a different tenant than before, compare the Tenant ID (Entra ID, Overview) with `AZURE_TENANT_ID` in the `DESC` output. If they differ, recreate the integration with `CREATE OR REPLACE STORAGE INTEGRATION` using the new tenant ID, then redo the consent and the role assignment.

**Screenshot:** the storage account's role assignments showing your user and the Snowflake app.

When everything is finished, delete `rg-capstone` to stop any charges. Take the screenshots first.

## 1. Land the file in Blob Storage
Create a container named `capstone` in the storage account (portal, Containers, + Container). Sign in and upload. The script checks the contract first, so a bad file never leaves your machine.

```bash
az login
python -m games_pipeline.land sample_data/games_sample.tsv --account <storage-account> --container capstone
```

Run it from `code/part1/day10/capstone/src` (or with `src` on `PYTHONPATH`). It needs the Azure CLI and a data role on the storage account, such as Storage Blob Data Contributor. To replace a file that is already there, add `--overwrite` (check `az storage blob upload --help` for your CLI version).

**Screenshot:** the `capstone` container showing `games/games_sample.tsv`.

## 2. Stage, format and raw table
Run, in order:
1. `sql/snowflake/01_stage_and_format.sql` (finishes with `LIST @capstone_stage`)
2. `sql/snowflake/02_raw_table.sql`

**Screenshot:** the `LIST @capstone_stage` result.

## 3. Load
Run `sql/snowflake/03_load.sql`. It matches columns by the header names and records the file name, line and scan time. It ends with a row count: expect 40 rows and 39 distinct ids.

**Screenshot:** the `COPY INTO` result and the row count.

## 4. Transform
`games_summary` is a view over `stg_games`, so staging is what the data quality check protects. Run, in order:
1. `sql/snowflake/06_snapshot_staging.sql` keeps the last good staging (skip it on the very first run, when `stg_games` does not exist yet).
2. `sql/stg_games.sql` (the same file the tests run on DuckDB).
3. `sql/snowflake/04_checks.sql`: every query should return no rows. The last one is the data quality check.
4. If every query returned no rows: `sql/games_summary.sql` (creates the view, only needed once), then `sql/snowflake/08_clean_up.sql`.
5. If a query returned rows: `sql/snowflake/07_quarantine_staging.sql` instead, then follow `dq_failure_plan.md`.
6. `sql/snowflake/05_read_summary.sql`: the answer, by band and overall.

This is the same rule `run_pipeline` follows locally.

**Screenshot:** the summary result, with the checks all empty.

## 5. Show the data quality check failing
This is for the presentation. After step 4, plant a bad value and run the check.

```sql
UPDATE stg_games SET winner = 'whtie' WHERE id = 'g1000x';

SELECT winner, COUNT(*) AS n FROM stg_games
WHERE winner IS NULL OR winner NOT IN ('white', 'black', 'draw')
GROUP BY winner;   -- returns ('whtie', 1)
```

The summary is a view over staging, so it would now count the bad row's game out of the metric. Contain it by running `sql/snowflake/07_quarantine_staging.sql` (it needs the snapshot from `06_snapshot_staging.sql`, taken before the plant). Staging goes back to the last good version, the bad build stays in `stg_games_rejected`, and `05_read_summary.sql` shows the same numbers as before.

**Screenshots:** the check returning the bad row, and the summary unchanged after the quarantine.

## Loading the real file
Upload the real Lichess file the same way (`--container capstone`, a different file name), then repeat steps 3 to 4. Snowflake skips files it has already loaded. If you must reload a corrected file with the same name, see the note in `03_load.sql`.

`raw_games` keeps every file that was loaded, and staging reads all of it. The synthetic sample file would therefore be counted next to the real games. Before building staging for the real answer, check which files are in raw and remove the sample's rows:

```sql
SELECT source_file, COUNT(*) FROM raw_games GROUP BY 1;
DELETE FROM raw_games WHERE source_file = 'games/games_sample.tsv';   -- the name shown in the first query
```

Then run `06_snapshot_staging.sql`, `sql/stg_games.sql`, `04_checks.sql` and `05_read_summary.sql` as in step 4. Check the counts line up: the raw rows, the distinct ids in raw, the rows in `stg_games` (one per distinct id), and the games counted in the summary (fewer than staging, since unrated games, draws and equal ratings are left out).

## Names to settle
- The container and folder (`capstone/games/` here), the database and schema, and which Lichess file to load.
