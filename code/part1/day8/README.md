# Day 8 Exercise: Renewal Rate for a Stakeholder

A vague request ("how are renewals doing?") turned into a defined metric, a view on top of it in DuckDB, one number checked by hand, and a three-sentence answer.

## Run

From this folder (the database file is created here and is not committed):

```bash
uv run python setup.py     # builds renewals.duckdb
uv run python explore.py   # the view, the checks and the answer
```

## Files

- `setup.py`: builds `renewals.duckdb` with the `subscriptions` and `renewals` tables (as-of date for the exercise is 2026-10-28)
- `explore.py`: `v_as_of`, the `v_renewal_rate_by_quarter` view, the quarter and plan results, the Q3 enterprise rows used for the hand check, and the three-sentence answer
