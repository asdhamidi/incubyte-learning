# Part 1 · Day 9 — AI in Data Work

**Date completed:** 2026-11-05 · **Time spent:** ~2.5 hours
## Success criteria
| Criterion (copied from the planner)                      | Done? | Evidence (link or section below)                                                                                                                                                              |
| -------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Understands Cortex Code and where it fits                | Yes   | [Cortex Code, and Claude Code with BEE](#cortex-code-and-claude-code-with-bee)                                                                                                                |
| Uses Claude Code and BEE for data work                   | Yes   | [Cortex Code, and Claude Code with BEE](#cortex-code-and-claude-code-with-bee), [practice code](../code/part1/day9/practice/setup.py), [exercise code](../code/part1/day9/exercise/report.py) |
| Reviews AI-generated SQL against an expected result      | Yes   | [Reviewing AI-generated SQL](#reviewing-ai-generated-sql), [Practice](#practice-ai-written-query-against-a-hand-checked-result), [query](../code/part1/day9/checker.py)                       |
| Grounds AI output in real data                           | Yes   | [Why AI output sounds right and is still wrong](#why-ai-output-sounds-right-and-is-still-wrong), [profile pack](../code/part1/day9/practice/profile.py)                                       |
| Keeps comments in line with the code                     | Yes   | [Keeping comments and documentation honest](#keeping-comments-and-documentation-honest), [Exercise](#exercise-fix-every-stale-comment), [report.py](../code/part1/day9/exercise/report.py)    |
| Writes a personal checklist for accepting AI-written SQL | Yes   | [Reflection On AI Personal Checklist](#reflection-on-ai-personal-checklist)                                                                                                                   |

## Key learnings
- Using BEE
- Reinforced good habits and practices while working with AI-assisted tools
- Learnt about code as a documentation and how that is even more useful in AI-assisted coding world.
## Exercises
- Fixed a Claude generated code to align comments with the logic in the script.
## Reflection
- I learnt the importance of having proper documentation in the code because after the first iteration in code generation, it is useful for both humans and AI.
## AI use
- Used Claude to format these notes.
- Used Claude to generate a mock-script to fix the comments.
## Open questions
NA
## Changes after review
NA

---
## Notes

### Cortex Code, and Claude Code with BEE
Cortex Code is Snowflake's agent for SQL and pipeline work. It comes in three forms - Snowsight, a standalone desktop IDE, and a CLI that runs in a local shell.

Claude Code is an agentic coding tool that reads a codebase, edits files, runs commands and works with development tools, in the terminal, an IDE, the desktop app or the browser. 

BEE adds structure on top. `/bee:start` triages the work:

| Tier      | When                           | What runs                                                    |
| --------- | ------------------------------ | ------------------------------------------------------------ |
| quick-fix | Small, well understood         | Direct change. A bug gets a failing test first, then the fix |
| standard  | Well understood but multi-step | A plan, then implementation                                  |
| full      | Large or high-risk             | A spec, then a plan, then implementation                     |

- Commands include `/bee:discover`, `/bee:brainstorm`, `/bee:spec-writer`, `/bee:planner`, `/bee:plan-implementer`, `/bee:review` and `/bee:qc`.

|          | Cortex Code                                                 | Claude Code with BEE                                                                      |
| -------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Lives    | In Snowflake                                                | In the repo and terminal                                                                  |
| Knows    | Account objects, roles, schemas                             | Files, tests, git history                                                                 |
| Best for | Exploring data, writing and fixing SQL against real objects | Changes that go through a branch, tests, CI and review, and larger changes needing a plan |
### Reviewing AI generated SQL
Treat it like a review request from a confident newcomer - it reads well, it runs, and some bugs still return plausible numbers. Verify the meaning, not the syntax. 

In the example, the AI was given a database profile of a DuckDB database for two tables and a requirement. The requirement was revenue by segment for completed, non-refunded October orders, excluding internal customers, with no-segment customers as `unknown`. The expected result was enterprise 150, smb 80, unknown 70, total 300. 

| Variant                                      | Result           | Bug                                    |
| -------------------------------------------- | ---------------- | -------------------------------------- |
| Correct                                      | 150 / 80 / 70    |                                        |
| A. Joined `order_items`, summed order amount | enterprise 250   | Fan-out                                |
| B. `BETWEEN '2026-10-01' AND '2026-10-31'`   | enterprise 100   | Boundary (stops at midnight of 31 Oct) |
| C. `segment <> 'internal'`                   | no `unknown` row | NULL drops the row                     |
| D. `NOT IN (SELECT order_id FROM refunds)`   | no rows          | A NULL in the subquery                 |

#### Checking an AI-generated SQL area by area

| Area          | Check                                                                                                                                                 |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Requirement   | Expected result by hand first, on a small fixture                                                                                                     |
| Grain         | What is one row after each join? Do the counts match?                                                                                                 |
| Joins         | Is every table needed? Inner or left? Complete key? Is the "one" side unique? A `LEFT JOIN` plus a `WHERE` on the right table acts like an inner join |
| Filters       | Boundaries, NULL behaviour, status values and case, time zones, hard-coded constants                                                                  |
| Aggregation   | `SUM` at the right grain, `COUNT(*)` vs `COUNT(DISTINCT)`, `AVG` of rates, `DISTINCT` hiding duplicates                                               |
| Set operators | `UNION` vs `UNION ALL`, column order and types                                                                                                        |
| Reconcile     | An independent total, and segments that add up to the whole                                                                                           |
### Why AI output sounds right and is still wrong
AI can fail across an array of areas:

| Failure                      | Example                                              | Catch with                      |
| ---------------------------- | ---------------------------------------------------- | ------------------------------- |
| Invented objects             | A column that doesn't exist                          | The schema I provided           |
| Wrong guess about values     | `'complete'` for `'completed'`, `'USD'` for `'usd'`  | A profile of real values        |
| Dialect confusion            | Function or argument order differing between engines | Running it on the target engine |
| Plausible wrong semantics    | Fan-out, boundaries, NULLs                           | A hand-checked expected result  |
| False explanation            | A comment says "excludes refunds" but doesn't        | Tests                           |
| Stale knowledge              | Changed syntax                                       | Current docs                    |
| Overconfidence about my data | "One row per order"                                  | A uniqueness query              |
### Keeping comments and documentation honest
A comment is a claim, and nothing fails when it's false. Comments should explain the reasoning behind the code, not just what it does.

| Comment says                | Code does                   | Effect                           |
| --------------------------- | --------------------------- | -------------------------------- |
| "last 30 days"              | `INTERVAL 90 DAY`           | A September order (300) included |
| "excluding refunded orders" | Excludes only `'cancelled'` | Refunded order (200) counted     |
| "latest event per order"    | `ORDER BY event_ts ASC`     | Keeps the earliest event         |
| "amounts in USD"            | No filter or conversion     | A EUR order (80) added           |
The method is to pull out each comment's claims, verify each with a probe or test, and then decide which side is wrong. 

|Type of comment|Action|
|---|---|
|Restates the code|Delete|
|Explains why|Keep, and verify|
|Header with purpose and definition|Keep, and check against the metric definition|
|TODO or open question|Keep, with an owner or ticket and a date|
|A number or value in prose|Replace with a named constant|
|Commented-out code|Delete (Git remembers)|

Good habits when working with AI:
- Change code and its comments in the same commit.
- Review comments in PRs.
- Turn important claims into tests.
- Document where people look
- Be sceptical of AI-written comments, since they describe intent.
- Put a number in one named place (`window_days`), not in prose.

---
## Hands-on: practice and exercises
- **Practice:** an AI-written query checked against a hand-checked result, see [Practice: AI-written query against a hand-checked result](#practice-ai-written-query-against-a-hand-checked-result)
- **Exercise:** fix every stale comment in a script, see [Exercise: fix every stale comment](#exercise-fix-every-stale-comment)
### Practice: AI-written query against a hand-checked result
Code: [`practice/setup.py`](../code/part1/day9/practice/setup.py) builds the data, [`practice/profile.py`](../code/part1/day9/practice/profile.py) prints the profile pack for the prompt, and [`checker.py`](../code/part1/day9/checker.py) is the assistant's query.

The requirement was new-customer AOV for Q3 2026, by segment. A new customer is one whose first-ever completed order falls in Q3, and the value is that first order (amount minus discount, with a NULL discount as 0). Cancelled orders and test accounts (`@test.example`) are excluded, each `order_id` counts once, status is case-insensitive, and a customer with no segment is `unknown`.

The assistant's query handled most of the traps (the duplicate order, status case, a cancelled first order, first order over all history, the Q3 boundaries, the test account and the NULL segment) and missed two:
- It averaged all Q3 orders of a new customer instead of just the first order. The `orders` column was larger than `new_customers`, which showed it.
- It ignored the `discount` column. The profile showed `discount` with NULLs that the query never used.
- Smaller things - the label `unassigned` instead of `unknown`, and a comment with hard-coded row counts that will go stale.

|Segment|Assistant's first query|Hand-checked key|
|---|---|---|
|enterprise|107.5|103.33|
|smb|60.0|80.0|
|unknown (shown as `unassigned`)|60.0|60.0|

When the query and a hand calculation disagree, either can be wrong, so resolve it row by row. The fix is to carry `discount` through the CTEs, pick each customer's first completed order with `ROW_NUMBER` (tie-break on `order_id`) and label the segment `unknown`. That gives 103.33, 80.0 and 60.0 across 5 customers, which matches the key.

### Exercise: fix every stale comment
Code: [`exercise/report.py`](../code/part1/day9/exercise/report.py) with its input [`sales_raw.csv`](../code/part1/day9/exercise/sales_raw.csv) and output [`top_products.csv`](../code/part1/day9/exercise/top_products.csv)

I didn't have a suitable script of my own to hand, so I practised on a stand-in nightly sales report. About eleven of its comments contradicted the code. These were the main ones:

|Comment said|Code did|Which side|
|---|---|---|
|"top 5 products by revenue" (header, `TOP_N`, "biggest revenue first")|`LIMIT 10`, `ORDER BY units`|Code probably wrong (four places agreed)|
|"always yesterday, computed at runtime"|A fixed date|Code wrong|
|"convert to EUR"|Rates with USD = 1.00, so USD|Ask finance|
|"ignore orders under 10"|`5.0`|Ask the owner|
|"comma-separated"|`delimiter=";"`|Ask the file's readers|
|"retry up to 3 times"|`range(2)`, with no pause|Ask|
|"load exactly as is, no cleaning"|`SELECT DISTINCT`|Comment wrong|
|"exit with code 1 if nothing to report"|`sys.exit(0)`|Ask|
|`# increment counter`|`n += 1`|Delete|

## Reflection On AI Personal Checklist

My personal method involves these steps: 1. Objects mentioned are right, 2. Syntax matches the engine I am working with, 3. The logic follows - overall and step-by-step, 4. Check if any hardcoded values are actually dynamic as in it should be brought from a YAML, JSON, or a variable table so update can be made in one places, and 5. Lastly check the data against my own SQL query for each part so that each logical piece reflects what I want.
