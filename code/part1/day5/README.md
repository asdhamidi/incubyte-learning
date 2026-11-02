# Day 5 Exercise: Testing a Data Pipeline

An order JSON is flattened into rows, checked against a contract at the boundary, and the loaded table is checked with data tests. Built test-first.

## Run

From this folder (the tests read `sample_orders/` relative to it):

```bash
uv run python -m pytest
uv run python demonstration.py
```

## Files

- `flatten_orders.py`: the contract (expected fields and types) and `validate_order`, which returns a list of problems,
- `data_checks.py`: `flatten_order`, one row per item with `line_total`, and a `ValueError` when `items` is missing,
- `exercise1.py`: `flatten_json`, flattens nested dicts,
- `demonstration.py`: runnable demos of test-first, breaking upstream changes, fail fast vs fail late, data tests and managed ingestion traps,
- `sample_orders/`: 10 sample order JSON files standing in for upstream payloads,
- `tests/test_validator.py`: contract tests, including every sample file,
- `tests/test_data.py`: three data tests on the loaded `order_lines` table (not null, unique, accepted values),
- `tests/test_exercise1.py`: tests for `flatten_json`.
