# Day 2 Exercise: Incremental MERGE in DuckDB

`raw_orders` (an incremental batch with duplicate and late-arriving records) is merged into `intermediate_orders`. Built test-first.

## Run

```bash
uv run pytest
uv run python merge_and_idempotency.py
uv run python union.py
```

## Files

- `sql/`: setup, the `MERGE`, the idempotency check, and the `UNION` / `UNION ALL` queries
- `pipeline.py`: small functions that run those SQL files
- `merge_and_idempotency.py`: runs the merge twice and prints the tables and the idempotency check
- `union.py`: prints the `UNION ALL` vs `UNION` row counts
- `tests/test_pipeline.py`: tests for the functions
- `tests/test_orders_data.py`: tests for the input data and the merged result
