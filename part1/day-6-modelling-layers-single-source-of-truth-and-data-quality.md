# Part 1 · Day 6 — Modelling Layers Single Source of Truth & Data Quality

**Date completed:** 2026-11-01 · **Time spent:** ~3 hours
## Success criteria
| Criterion (copied from the planner)                                   | Done? | Evidence (link or section below)                                                                                                                                        |
| --------------------------------------------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Explains raw and intermediate and summary layers                      | Yes   | [Layering a warehouse](#layering-a-warehouse)                                                                                                                           |
| Consolidates duplicated models into one source of truth               | Yes   | [Single source of truth](#single-source-of-truth), [Consolidating duplicated models](#consolidating-duplicated-models), [code](../code/part1/day6/practice/practice.py) |
| Names the core data quality dimensions                                | Yes   | [Data quality dimensions](#data-quality-dimensions)                                                                                                                     |
| Traces an issue across summary and intermediate and raw tables        | Yes   | [Tracing an issue backwards](#tracing-an-issue-backwards), [Incident exercise](#incident-exercise), [queries](../code/part1/day6/exercise/explore.py)                   |
| Contains and communicates an urgent issue early                       | Yes   | [Handling an urgent data quality issue](#handling-an-urgent-data-quality-issue), [message to the client](../code/part1/day6/exercise/message_to_client.md)              |
| Writes a blameless postmortem with a preventive check                 | Yes   | [Postmortem](../code/part1/day6/exercise/postmortem.md)                                                                                                                 |
| Reflection: what is the first query you run when a number looks wrong | Yes   | [Reflection](#reflection-debugging)                                                                                                                                     |

## Key learnings
- Learnt about data quality dimensions, how to handle failures, and communicate the problems effectively and structurally.
## Exercises
- Practiced on aligning cases where two different definitions causing data inconsistency between them can be aligned
- Main exercise was about doing analysis, exploration, and RCA. Writing up communication to the client and also the postmortem.
## Reflection
- This module was a good learning exercise about data quality dimensions and blameless postmortem.
- It was also a good exercise in communication to the client which should be succinct, clear, and to the point.
- I learnt not to use overly technical jargon to the client, who should be given information more along the line of impact and resolution rather than finer technical details.
## AI use
- I used AI to tidy up the notes.
- I used AI for the exercise to create an incident on which I can do RCA.
- I also got my message to client and postmortem reviewed and formatted once done.
## Open questions
Any more resources on the client communication part?
## Changes after review
NA

---
## Notes

### Layering a warehouse
Three layers, and the data only moves one way - raw, then intermediate, then summary.

|Layer|Holds|Logic allowed|Read by|
|---|---|---|---|
|**Raw**|Exact copy of the source plus a load timestamp. Append-only.|None|Only the layer above|
|**Intermediate**|Cleaned data: types, names, dedupe, business rules|Yes, the only place|Engineers, not end users|
|**Summary**|Aggregated, business-facing tables and metrics|Joins and aggregation|Dashboards, clients|

- The summary layer never reads raw directly, otherwise it skips the rules in the intermediate layer.
- Every cleaning or business rule should sit in one place only.
- Raw is never edited. It is what the source actually sent, so I can always replay from it.
- dbt calls these layers staging, intermediate and marts. So the intermediate layer here is staging plus intermediate in dbt, and the summary layer is marts.

### Single source of truth
Example: five raw orders, with one duplicate delivery, one cancelled order and one internal test order. The correct revenue for the day is 350.

|Setup|Report A|Report B|
|---|---|---|
|Each report cleans raw itself (A forgot duplicates and tests, B forgot cancelled and tests)|1100|930|
|Team A fixes only its own report (test orders)|600|930|
|Both read one layered metric|350|350|
|New rule added once in the intermediate layer (ignore orders under 150)|250|250|
- Duplicated models drift apart when a query is copied and then edited separately, when a fix reaches only one of the copies, or when the definition only lives in people's heads.
- If two reports give two answers, most likely the same definition exists twice.
- Stacking the transformations in layers means each one is applied in only one place.
- A metric should have one owner and one definition, and every report reads from it.
### dbt as one way to structure the layers
dbt is one way to build these layers as a project of SQL files, and its suggested structure lines up with the three layers.
- Raw is the source tables, loaded outside dbt and declared in a sources yaml file.
- Staging has one model per source table with only renaming, casting and basic cleaning. No joins or aggregation here, and it is the only place that reads the raw tables.
- Intermediate is where the business rules and joins get stacked into reusable steps. End users don't read from it.
- Marts are the business-facing tables, by entity or metric, and these are the summary layer.

```text
models/
├── staging/
│   └── shop/
│       ├── _shop__sources.yml        # declares the raw tables
│       ├── _shop__models.yml         # tests and docs for this folder
│       └── stg_shop__orders.sql
├── intermediate/
│   └── orders/
│       └── int_orders_validated.sql  # the rules for a counted order, defined once
└── marts/
    └── marketing/
        ├── _marketing__models.yml
        └── active_customers_mtd.sql
```

### Data quality dimensions
Dimensions are the ways of checking if data is fit for use. If I can put a problem under a dimension, it is easier to work out where it comes from.

| Dimension        | Question                      |
| ---------------- | ----------------------------- |
| **Completeness** | Is the expected data there?   |
| **Validity**     | Do values follow the rules?   |
| **Uniqueness**   | One row per real-world thing? |
| **Consistency**  | Do places agree?              |
| **Timeliness**   | Fresh enough for its use?     |
| **Accuracy**     | Does it match reality?        |
#### Symptom vs Likely Dimension

|Symptom|Likely dimension|
|---|---|
|Revenue doubled|Uniqueness|
|Revenue dropped overnight|Completeness or timeliness|
|Two reports differ|Consistency|
|Impossible values|Validity|
|Doesn't match finance|Accuracy|
### Tracing an issue backwards
Start from the symptom and walk back through the layers until I find the step where the number changes.
1. Confirm the symptom first - which metric, which days and segment, and by how much.
2. Count the same thing at every layer. The first layer where the count changes is where to look.
3. Compare the layers on either side of that step - the rows that went in but did not come out - and group them by each column to see what they have in common.
4. Look at the input of that step (a join, a lookup table, a filter value).
5. Confirm by fixing it in a copy and checking that the number comes back.

|Layer where the number changes|Common causes|
|---|---|
|Raw differs from source|Failed or late load, source change, duplicate delivery|
|Raw to staging|Type casts, dedupe rule, a status or date filter|
|Staging to intermediate|Joins, business rules, lookup tables|
|Intermediate to summary|Aggregation, grouping, date or time zone handling|
### Handling an urgent data quality issue
Order is contain, communicate, then fix the root cause.

| Step               | Purpose                                | Time scale      |
| ------------------ | -------------------------------------- | --------------- |
| Contain            | Stop the spread of bad data            | Minutes         |
| Communicate        | Let people avoid acting on bad numbers | Within the hour |
| Fix the root cause | Make sure it doesn't recur             | Hours to days   |
- Containing means pausing the downstream refresh, holding the last good version, putting a notice on the report and setting the bad rows aside. It is quick and can be undone, but it is not the fix.
- The first message to the client needs four things - what happened, the impact, what I am doing now (containment included), and when they will hear next, as a clock time. Five sentences or fewer.
    - Only say what is confirmed, and say what is not known yet.
    - Give the effect in business terms with numbers, not column names.
    - No blame, and no fix time I can't back up. The update time is the one to keep.
- Fixing means repairing the cause, rebuilding, checking against the layer counts, confirming the corrected figures with the client, and then writing the postmortem.

---
## Hands-on: practice and exercises
- **Practice:** [Consolidating duplicated models](#consolidating-duplicated-models)
- **Exercise 1:** trace a dropped metric across the layers, see [Incident exercise](#incident-exercise)
- **Exercise 2:** first client message and blameless postmortem, see [Incident exercise](#incident-exercise)
### Consolidating duplicated models
**Code**: [`practice/practice.py`](../code/part1/day6/practice/practice.py)
**Scenario**: two teams computed "active customers" differently, giving 8 and 4.

|Difference|Marketing|Finance|Customers affected|
|---|---|---|---|
|Order status|Any status|Completed only|C-2|
|Test accounts|Counted|Excluded|C-3|
|Window|Last 30 days|Calendar month|C-4|
|Identity|`customer_id`|`lower(email)`|C-5 and C-6|

Decisions: count by `customer_id`, calendar month (up to and including the as-of date), exclude test accounts, completed orders only, UTC month boundaries.
- Design is `stg_orders` (rename and normalise), `int_valid_orders` (completed only, no test accounts, defined once) and `active_customers_mtd` (distinct `customer_id`, month to date). I put "mtd" in the name so nobody mixes it up with a 30-day metric. A 30-day version would be a separate metric on the same intermediate model.
- One view with two CTEs and a `department` column is not a single source of truth. The two definitions are still there and the rules still exist twice. It is also a trap, since summing the rows without filtering on `department` gives 12 and counts the same customers twice. It is only useful as a side by side view during migration.
- `customer_id` counts accounts, not people. C-5 (`e@x.com`) and C-6 (`E@x.com`) look like one person. I defined the metric as active accounts and added a warning test that flags emails shared by several `customer_id`s.
- Time zone matters. The 30 Sept 23:30 UTC order falls on 1 Oct in IST, and with IST month boundaries the result would be 6.
- The status decision moves the number the most (5 with completed only, 6 with any status), so the metric owner should decide it.

**Reconciliation**: marketing 8, minus C-2 (cancelled only), minus C-3 (test), minus C-4 (outside the month), gives 5. Finance 4 becomes 5 because C-5 and C-6 count separately.
**Migration**: confirm the open decisions, run old and new in parallel, announce the change (8 and 4 become 5) with the reasons, repoint the old table names as views over the new metric, move reports to the metric directly, retire the old names on an announced date, and keep the tests running with a named owner.
### Incident exercise
**Code**: [`exercise/incident_setup.py`](../code/part1/day6/exercise/incident_setup.py) (builds the layered tables), [`exercise/explore.py`](../code/part1/day6/exercise/explore.py) (tracing queries)
**Write-ups**: [message to the client](../code/part1/day6/exercise/message_to_client.md), [postmortem](../code/part1/day6/exercise/postmortem.md)

Revenue for 27 Oct fell 47% (10,580 to 5,582) while raw rows fell only 5% (200 to 190).
- Counts by layer by day showed the drop at the intermediate layer. The status counts by day then showed 76 orders with `complete` instead of `completed` on 27 Oct, and grouping by channel showed all 76 are mobile.
- Impact is 76 orders and 4,436 in revenue left out (44% of the corrected 10,018). If the 76 are confirmed as completed, corrected revenue is down 5% on the previous day, which fits with the raw rows.
- For the client message I kept to a few things: put a number on the impact, no column names or "incorrect values", say what I have contained, give a clock time for the next update, and don't promise a fix before the source confirms what `complete` means.
- The postmortem has a summary, impact, timeline (detection, containment, message, cause, fix), one root cause, what went well and where we were lucky, and one preventive check.
- Blameless means looking at the contributing causes and not blaming a person or team. I describe the missing safeguard, not who missed it, and action items get one owner and a due date.
- The root cause is that the pipeline matched status to one exact value and nothing checked the incoming status values, so a new spelling was silently left out.
- The preventive check is an accepted-values test on `stg_orders.status` (`completed`, `cancelled`), run at staging before the intermediate and summary tables are built. If it fails it blocks the build, so the dashboard keeps its last good figures. The dimension is validity.

---
## Reflection Debugging
The first query that I write when a number looks wrong is on the direct source of that number to see data as it is in the source, then I look at the definition of the object and pan into the dimension which is directly affecting the problem - count logic and order number. 

If the root cause is not directly revealed at that point, I start drilling down to the underlying sources, the logic that lies on top of it, and any logic between the sources.
