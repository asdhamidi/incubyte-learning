# Part 1 · Day 5 — Testing Data Pipelines

**Date completed:** 2026-10-29 · **Time spent:** ~3 hours

## Success criteria
| Criterion (copied from the planner)                                                                     | Done? | Evidence (link or section below)                                                                                                                          |
| ------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Study: a layered testing strategy for data - unit and component and contract and flow tests             | Yes   | [Layered testing strategy](#layered-testing-strategy)                                                                                                     |
| Learn: test-first transformations - write the failing test for a transformation before the code         | Yes   | [Test-first transformations](#test-first-transformations)                                                                                                 |
| Learn: contract tests at the boundary so an upstream schema change fails fast                           | Yes   | [Contract tests](#contract-tests)                                                                                                                         |
| Learn: data tests on tables such as not null and unique and accepted values and relationships           | Yes   | [Data tests](#data-tests)                                                                                                                                 |
| Study: where managed ingestion tools such as Fivetran fit and what still needs testing when you use one | Yes   | [Managed ingestion tools (Fivetran)](#managed-ingestion-tools-fivetran)                                                                                   |
| Practice: test-first build a transformation that parses a JSON order into flat rows using pytest        | Yes   | [`flatten_order`](../code/part1/day5/data_checks.py)                                                                                                      |
| Exercise: add a contract test that fails when an expected field disappears from the input               | Yes   | [Contract test exercise](#contract-test-exercise), [validator](../code/part1/day5/flatten_orders.py), [tests](../code/part1/day5/tests/test_validator.py) |
| Exercise: add three data tests to the output table                                                      | Yes   | [Data test exercise](#data-test-exercise), [tests](../code/part1/day5/tests/test_data.py)                                                                 |
| Reflection: which bug from your past work would these tests have caught                                 | Yes   | [Reflection](#reflection-on-pipeline-testing)                                                                                                             |

## Key learnings
- I had been implementing things like contract checks, component, and unit tests previously as well, but I explored them more thoroughly here. 
- Doing more TDD was insightful as I understand how writing tests not only develops the function concurrently, but also develops a spec sheet indirectly.
## Exercises
- A contract test exercise to actually test a validator of a pipeline independently.
- Data tests to test the data itself.
## Reflection
- This was relatively lighter work than before but a good exploration into testing of the data world. I would continue to learn more on this as I go along as I feel this is a very foundational part of it.
## AI use
- I used Claude to discuss ideas, clarifications, and to tidy up my notes into a more proper form.
## Open questions
NA
## Changes after review
NA

---
## Notes

### Layered testing strategy
Each layer catches a different kind of bug, and no single layer catches everything. Lower layers are faster and point to the exact function at fault.

| Layer         | Tests                         | Input                         | Speed              | Runs                             |
| ------------- | ----------------------------- | ----------------------------- | ------------------ | -------------------------------- |
| **Unit**      | One function                  | Hand-written dicts            | Milliseconds       | Every change                     |
| **Component** | One SQL model or job          | Small fixture tables (DuckDB) | Seconds            | Every change                     |
| **Contract**  | The boundary with upstream    | Real or sampled upstream data | Seconds            | Every change and every new batch |
| **Flow**      | The whole pipeline end to end | Small known dataset           | Seconds to minutes | Before release                   |
| **Data**      | The real output tables        | Production data               | Varies             | After every load                 |
### Test-first transformations
Test-first means writing the test for a behaviour before the code that provides it. The cycle is red (write one failing test), green (least code to pass), refactor (tidy while the tests stay green).
- **Expected values come from the requirement, not the code.** A test written after the code tends to copy the implementation, so it repeats the bug instead of catching it.
- **Each test forces a decision.** Questions like "what happens on empty input?" get answered deliberately, before the code exists.
- **See it fail for the right reason.** A minimal stub makes the test fail on the actual comparison, not on a missing module.
- **A test that passes on its first run needs a sabotage check.** Break the code on purpose and confirm the test fails. If it still passes, it protects nothing.
- **Refactoring is safe.** An accidental `*` to `+` is caught immediately by the test that names the broken behaviour.
### Contract tests
A contract lists what the pipeline needs from an upstream source. A contract test checks incoming data against it at the boundary, before anything is loaded.

| Upstream change | Result |
| --- | --- |
| New field added | passes |
| New enum value (`'LOST'`) | passes (data test territory) |
| Field removed, renamed, or nested rename | fails |
| Type changed (`"12.5"` instead of `12.5`) | fails |
| Null in a required field | fails |
| Unit changed silently (kg to lb) | passes (missed) |
- Be strict about the fields the code depends on and tolerant about the rest. Failing on added fields creates noise.
- Contracts check shape, not meaning.
- **Fail fast vs fail late:** in a batch of four orders where order 3 has a renamed field, a pipeline without a check loaded orders 1 and 2 and crashed with `KeyError: 'id'`, leaving a half-loaded table. With the batch validated first, nothing was loaded and the bad order was named.
- List only the fields the code uses, and report all violations at once.
### Data tests
Data tests run on tables after a load and find problems no code test predicted.

| Test | Question | Query idea |
| --- | --- | --- |
| **Not null** | Is a required column ever empty? | `WHERE col IS NULL` |
| **Unique** | Does a key appear more than once? | `GROUP BY key HAVING COUNT(*) > 1` |
| **Accepted values** | Is a column limited to a known list? | `WHERE col IS NULL OR col NOT IN (...)` |
| **Relationships** | Does every child row have a parent? | `LEFT JOIN parent ... WHERE parent.key IS NULL` |

- **NULL gotcha:** `NULL NOT IN (...)` is never true in SQL, so a naive accepted-values query misses NULL rows. Add `IS NULL OR`, or pair it with a not-null test.
- Return the offending rows, not only a count, so the starting point is visible.
- Prove each check can fail by planting one bad row and asserting the count is exactly 1. A check that always returns 0 gives false comfort.
- Run them before consumers see the data (stage, test, then publish). Afterwards they are only an alarm.
- Decide what failure means: error (block) for business-critical keys, warning otherwise.
- Keep the tests few and meaningful, since every test is something to maintain.
- There can be a variety of other data tests - acceptable values, recon check, range check, type check, etc.
### Managed ingestion tools (Fivetran)
A managed ingestion tool sits at the start of the pipeline: it connects to sources, copies data into the warehouse, keeps it in sync and handles retries and scheduling.

Behaviours that affect testing:
- **Schema change handling** has three settings: Allow all (new schemas, tables and columns sync), Allow columns (only new columns for existing tables sync), and Block all (none of the new ones sync). The shape of the landing tables can change without any code change.
- **Soft delete** is the default sync mode, so rows deleted in the source are marked as deleted in the destination. The mark is a `_fivetran_deleted` column set to TRUE, and the row is still in the table.
- Connectors without the Captures Deletes feature stay in soft delete mode but do not flag deleted rows, so check whether the connector supports it.
- For tables without a primary key, a change inserts the new version of the row and marks the old version as deleted. Both versions exist in the table.
The tool guarantees movement, not meaning. Landing tables should be treated like an upstream API: contract and data tests at that boundary, then tests on the team's own transformations.

---
## Hands-on: exercises

### Setup
- `pytest` and `duckdb` in a virtual environment, Python 3.9 or newer.
- `flatten_order` (in `data_checks.py`) returns one row per item and raises a clear `ValueError` when `items` is missing.
- `sample_orders/` holds 10 JSON files shaped like the test `ORDER` (`O-1001` to `O-1010`), with different order IDs, customers, timestamps, items and eight currencies (USD, EUR, GBP, INR, JPY, CAD, AUD, SGD). They stand in for upstream payloads.

### Contract test exercise
- The contract (in `flatten_orders.py`) lists every field `flatten_order` reads with its expected type: order-level fields, `customer.id` and the item fields.
- A validator takes one order and returns a list of problems. It checks the `customer` fields only if `customer` exists, checks every item and names which one is wrong, and reports all problems at once.
- Unit tests for the validator use an order defined inside the test file, deep-copied before one thing is broken. Cases: missing top-level field, missing nested field, wrong type.
- A boundary test, parametrized per file, asserts the validator returns no problems for each file in `sample_orders`.
- **Proof it works:** rename `customer.id` to `customer.customer_id` in one sample file. Exactly one test (the boundary test for that file) should fail, naming the missing field. Then undo the edit.

### Data test exercise
- A pytest fixture builds an in-memory DuckDB table `order_lines` by running `flatten_order` over every sample file, so each test gets a fresh table.
- Three tests, each one SQL query that counts bad rows and asserts 0:
    - **Not null** on `order_id`.
    - **Unique** on `order_id` + `line_no`.
    - **Accepted values** on `currency`, with NULL counted as bad. The accepted list has to cover all eight currencies in the sample files.
- **Proof each can fail:** add one bad row in the fixture (NULL `order_id`, a copied line, currency `XXX`), confirm the matching test fails with `assert 1 == 0`, then remove it.

## Reflection On Pipeline Testing
I have created and maintained several data quality frameworks, but like most software development, the focus on individual functional blocks of the pipeline to be tested and refined was not something that was of critical importance. Particularly, doing it with a TDD approach led it to become more robust. 

I understood a lot about than just data tests, and I will be implementing this more thoroughly from now on, as well.

Regarding, the specific bug this would have caught are the outlier bug that I fail to think of because I would have focused on the core functionality rather than any gotchas or edge cases. TDD makes me focus on them first and develop any functionality incrementally. An example would be when I developed a Salesforce pipeline, I did not account in the "complicated" salesforce fields which couldn't be ingested, and let to pipeline failing.