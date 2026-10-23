# Part 1 · Day 2 — SQL Precision for Pipelines

**Date completed:** 2026-10-23 · **Time spent:** ~5.5 hours

## Success criteria
| Criterion (copied from the planner) | Done? | Evidence (link or section below) |
| ----------------------------------- | ----- | -------------------------------- |
| Set operators precisely - UNION removes duplicates and UNION ALL keeps every row and why that difference silently changes totals in a pipeline | Yes | [Set Operators - UNION vs UNION ALL](#set-operators)|
| Learn: MERGE for incremental loads - matching on a business key and handling inserts and updates and deletes in one statement | Yes | [MERGE for incremental loads](#merge-for-incremental-loads) |
| Study: idempotency - a load you can re-run without creating duplicates or losing rows | Yes | [Idempotency](#idempotency) |
| Learn: handling late-arriving records - data that lands two or three days after the event it describes | Yes | [Late-arriving records](#late-arriving-records) |
| Learn: window functions for deduplication and latest-record-per-key with ROW_NUMBER and QUALIFY | Yes | [ROW_NUMBER and QUALIFY for dedup](#row_number-and-qualify-for-dedup) |
| Practice: in DuckDB build a small orders table and an incremental batch with duplicates and late records then write the MERGE that loads it | Yes | [Code](../code/part1/day2/), [MERGE](../code/part1/day2/sql/02_merge.sql) |
| Exercise: run the same load twice and prove with a query that the result did not change | Yes | [Idempotency check](../code/part1/day2/sql/03_idempotency_check.sql) |
| Exercise: write one query with UNION and one with UNION ALL over the same inputs and explain the difference in row counts | Partly | [Queries](../code/part1/day2/sql/04_union_vs_union_all.sql)|
| Reflection: which of these would have caused a silent data error in a pipeline you have built | Pending | [Reflection](../code/part1/day2/reflection.md) |


## Key learnings
- Idempotency and how to design for that
- Set operators and common pitfalls
- Late arriving data and mechanisms to handle that
- Window function for deduplication
- Functional Programming in Data Engineering through the blog by Maxime Beauchemin
- Spinning up DuckDB and doing learning (and fun!) activity with it

## Exercises
The exercise was fun and a good learning moment. Always liked duckdb for providing the capability to do these quick things, while still packing power. I was a bit confused by the wording of "build a small orders table and an incremental batch with duplicates and late records then write the MERGE that loads it", hence I went with my interpretation, assuming the it was idempotency and merge that was to be practiced.
Practiced the UNION vs UNION ALL thing, as well, by replicating a very common example to showcase the silent killer of this.

## Reflection
Revisiting the core concepts of idempotency and handling late-arriving data was a refresher which helped clear some concepts. Set operations and merge was also a refresher.

Reading the blog on Functional Data Engineering was quite revelatory and re-introduced me to the approach of following functional principles in data engineering. I felt that the concepts were similar to SOLID principles and modular programming applied to the data engineering domain. I am a bit skeptic about some ideas, but overall I liked the perscpective presented in the blog. Plus, the author was the creator of Airflow, so instantly became a fan.

## AI use
I use Claude to learn the concepts by asking questions, clarifications, doubts, and examples.
I used Claude Code to plan for this exercise, generate the scaffolding and some boilerplate code. I made my updates and changes in the code, did some restructuring, and then got a final review with it.
I also used Claude to tidy up the notes.

## Open questions
I really liked the suggested blog. Any other blogs that you would suggest?

## Changes after review
NA

---
## Notes
### Set Operators
- `UNION ALL` stacks the result sets and keeps every row. 
- `UNION` stacks them, then removes duplicates, where a duplicate means all selected columns are equal, within a single input as well as across inputs.
- Columns are matched by **position**, not name. NULLs count as equal when deduplicating.
- `UNION` costs more (sort or hash), and it can silently drop real rows. Three separate $100 sales with no ID column collapse into one.
- `UNION ALL` can double-count if your sources overlap.
- Default to `UNION ALL` for disjoint sources. If dedup needed, can be done with `ROW_NUMBER()` on a business key. 
- Example:
```sql
SELECT store, sale_date, amount FROM web_sales
UNION ALL
SELECT store, sale_date, amount FROM app_sales;
-- 5 rows, SUM(amount) = 420

SELECT store, sale_date, amount FROM web_sales
UNION
SELECT store, sale_date, amount FROM app_sales;
-- 3 rows, SUM(amount) = 220
```
### MERGE for incremental loads
- `MERGE` matches source to target on a **business key**, then runs one action per row: update or delete when matched, insert when not matched. All of it runs atomically in one statement.
- Only the first `WHEN` clause that is true for a row runs, so order the specific conditions first.
- The source must have one row per key. Duplicates cause an error (Snowflake’s default) or, for unmatched keys, duplicate inserts. Dedup with `QUALIFY ROW_NUMBER() ... = 1`.
- Guard updates with `AND s.updated_at > t.updated_at` so stale or rerun data can’t overwrite newer data.
- NULL keys never match, so they get inserted again on every run.
- Snowflake has no `NOT MATCHED BY SOURCE`. Use delete flags in the source for deletes.
- **SCD2:** a matched row can only trigger one action. Changed rows are fed twice, once with the real key to expire the old row and once with a NULL key to force the insert of the new version. `IS DISTINCT FROM` is used for change detection. Alternatively, an expire step and an insert step are ran in one transaction, which is easier to read.
- Example:
```sql
MERGE INTO dim_customer AS t
USING (
  SELECT customer_id, name, email, updated_at, is_deleted
  FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id
                              ORDER BY updated_at DESC) AS rn
    FROM stg_customer_changes
  ) x
  WHERE rn = 1                                   -- one row per key
) AS s
ON t.customer_id = s.customer_id                 -- business key
WHEN MATCHED AND s.is_deleted THEN
  DELETE
WHEN MATCHED AND s.updated_at > t.updated_at THEN
  UPDATE SET name = s.name, email = s.email, updated_at = s.updated_at
WHEN NOT MATCHED AND NOT s.is_deleted THEN
  INSERT (customer_id, name, email, updated_at)
  VALUES (s.customer_id, s.name, s.email, s.updated_at);
```
### Idempotency
- A load is idempotent if rerunning it on the same input gives the same final state, with no duplicates and no lost rows. Retries, backfills and double deliveries make this essential.
- **Patterns:**
    - Guarded `MERGE`, for key-based updates.
    - Delete and insert a partition in **one transaction**, when a run owns a slice such as a day.
    - Build a new table and swap it in, for small tables.
    - Append with a `load_id`, then dedup, for raw or landing layers only.
- **Watermarks:** use `>=` plus an overlap window, since `>` misses ties and late data. The overlap is safe because the load is idempotent. Advance the watermark only **after** the commit.
- **Idempotency breakers:** `CURRENT_TIMESTAMP()` or random IDs in business columns, “today” instead of a run-date parameter, non-unique keys, and multi-step loads with no transaction.
#### Idempotency: design notes
**Principle:** at-least-once delivery + idempotent processing = effectively-once results. Design for the retry.
##### Three levels (fix all three)
- **Record:** the same record twice gives one row (key, guarded `MERGE`, dedup)
- **Batch:** re-running a slice gives the same result (partition replace, atomic commit)
- **Pipeline:** retries, overlaps and backfills stay consistent (run ledger, locking)
##### Layers
```
Landing (raw, append-only, load_id) → Staging (deduped) → Core (MERGE / partition replace) → Serving (rebuildable)
```
- Landing is immutable, so it's your replay source
- Each layer is a deterministic function of the one above
- Serving tables are disposable
##### Building blocks
- **Run identity:** a logical date or `run_id` passed as a parameter, never derived from "now"
- **Deterministic keys:** business key, or a hash with `COALESCE`
- **Atomic commit:** transaction, or build and swap
- **State moves last:** advance the watermark in the same transaction, or derive it from the target
- **Run ledger:** run_id, window, status, row counts, checksum. It's an optimization and audit trail, so the load must still be idempotent on its own
##### Pattern picker

| Situation                        | Pattern                                              |
| -------------------------------- | ---------------------------------------------------- |
| A run owns a slice (day, tenant) | Partition replace (delete + insert, one transaction) |
| Rows update over time by key     | Guarded `MERGE` on a deduped source                  |
| Small table or big logic change  | Build and swap                                       |
| Raw / landing layer              | Append with `load_id`                                |
| File ingestion                   | File ledger + key-level dedup                        |
| Streaming                        | Dedup on event ID with TTL + batch reconciliation    |
| External side effects            | Outbox + idempotency key                             |
### Late-arriving records
- **Problem:** `event_ts` (when it happened) and `ingested_at` (when you received it) can differ by days.
- **What breaks:** filtering incrementals on event date, loading only “today’s partition”, aggregates built once and never revisited, and stamping late rows with their arrival date.
- **Design:**
    1. **Keep three timestamps:** `event_ts` (reporting day), `ingested_at` (what to load), and `updated_at` (which version wins).
	2. **Load by arrival time into append-only raw:** late rows have old event dates and would be skipped otherwise, and raw lets you replay.
	3. **Upsert with a guarded `MERGE`:** a late, older version can’t overwrite a newer one because the source version decides the winner.
	4. **Rebuild only the touched event dates in one transaction:** this fixes the affected daily totals cheaply without leaving a day empty.
	5. **Re-read the last N days (N from your p99 lateness):** it catches what slipped through, and it’s safe because the merge is idempotent.
	6. **Set a policy for rows beyond the window (accept, quarantine, or drop) and count them:** very late rows will happen, so decide in advance.
- **Streaming equivalent:** watermark plus allowed lateness, a side output for very late rows, and periodic batch reconciliation.
- **Late dimensions:** insert a placeholder or “Unknown” member when a fact arrives before its dimension. Join SCD2 dimensions as of **event time**. Backdated dimension changes need validity windows split.
- **Silent failures:** a lookback shorter than real lateness, a rebuild with no transaction, and ordering by arrival instead of source version.

### ROW_NUMBER and QUALIFY for dedup

- **Pattern:**
```sql
  SELECT * FROM t
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY business_key
    ORDER BY updated_at DESC NULLS LAST, load_id DESC) = 1;
```

`PARTITION BY` is “the same record”, `ORDER BY` decides the winner, and `= 1` keeps one row per key.

- **Why `QUALIFY`:** window results don’t exist yet when `WHERE` runs. `QUALIFY` filters after them with no subquery. Where it isn’t supported (Postgres, SQL Server), wrap in a subquery and filter on `rn = 1`.
- **Two different jobs:**
    - Exact duplicates: partition by all columns, or use `DISTINCT`.
    - Latest version per entity: partition by the **key only**, order by the version descending.
- **`ROW_NUMBER` vs `RANK`:** `ROW_NUMBER` gives exactly one winner. `RANK` and `DENSE_RANK` keep ties, so `= 1` can return several rows.
- **Traps:**
    - No tie-breaker makes the winner arbitrary and the load non-idempotent. Always end with a unique column.
    - NULLs sort first under `DESC` in Snowflake, so use `NULLS LAST`.
    - Order by the source version, not by arrival time.
    - A NULL key puts all those rows into one partition, and only one survives.
    - Dedup drops rows silently, so log `rows_in`, `rows_out` and `rows_dropped`.
- **Also useful:** top N per group (`<= N`), duplicate audits (`QUALIFY COUNT(*) OVER (PARTITION BY key) > 1`), and first-per-key (`ASC`).

### Functional Data Engineering: one-liner notes
#### Big picture
- Apply functional programming ideas (purity, immutability) to ETL/batch pipelines for clarity.
- Core goal: reproducibility, achieved through immutable data plus versioned logic.
#### Pure tasks
- A task should be deterministic and idempotent. Rerunning it gives the same result.
- Rerunning overwrites prior output, so there is no double-counting.
- One task, one output.
- Isolate temp tables and intermediate state so task instances can run in parallel.
#### Immutable partitions
- Don't UPDATE/APPEND/DELETE rows; fully overwrite whole partitions. - DEBATABLE
- Without native partitions, use per-partition tables with a UNION ALL view, or DELETE then INSERT by partition key.
- TRUNCATE PARTITION is cheap; DELETE is expensive.
#### Persistent immutable staging
- Keep all raw source data forever, unchanged.
- This lets you rebuild the whole warehouse from scratch, so derived tables can have shorter retention.
#### Changing logic over time
- Retroactive change: recompute the dirty downstream partitions.
- Non-retroactive change: gate the new logic behind an effective date inside the task.
- Source control should describe how to build the warehouse for all time periods.
- Prefer dated parameter tables (e.g., tax rates) over hard-coded conditionals.
#### Dimensions
- Replace UPSERTs and SCDs with full dimension snapshots, one partition per ETL run.
- Duplication is fine: dimensions are small, and storage is cheap compared to engineering time.
- Type-2 SCD means surrogate keys, lookups and mutations, which are error-prone and hard to reproduce.
- Denormalize attributes-at-event-time into facts; join to historical snapshots only when needed.
- Nested types (e.g., a `state_history` map) track history without changing the grain.
#### Unit of work and lineage
- One task = one table, one task instance = one partition.
- Lineage becomes a graph of partitions and task instances, not rows.
#### Past dependencies
- Avoid partitions that depend on the previous partition of the same table.
- They create deep, serial DAGs that backfill slowly.
- Handle cumulative metrics in a separate, specialized model.
#### Late-arriving facts
- Separate event time from processing time, and partition on processing time.
- This gives a "time machine" (e.g., February sales as of March 1 vs. today).
- Cost: lost partition pruning on event-time queries.
