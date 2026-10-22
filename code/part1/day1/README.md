# Day 1 Exercise: Record Cleaner

A small Python function, `clean_record`, built test-first.

## What it does

- Returns `{}` for an empty record
- Raises `ValueError` if `id` is missing or empty
- Trims whitespace from string values
- Normalises `date` (`YYYY-MM-DD` or `DD/MM/YYYY`) to ISO format

## Run the tests

```bash
uv run pytest
```

## Files

- `main.py`: the `clean_record` implementation
- `tests/test_record_cleaner.py`: tests
- `reflection.md`: my reflections on the exercise
