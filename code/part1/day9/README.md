# Day 9 Exercise: Checking AI-Written SQL and Keeping Comments Honest

Two parts: an AI-written query checked against a hand-checked result, and a script whose comments were rewritten to match what the code does.

## Run

Run each script from its own folder (the database file is created in `practice/` and is not committed):

```bash
cd practice
uv run python setup.py                                          # builds practice.duckdb
uv run python profile.py practice.duckdb customers orders       # profile pack to paste into a prompt
uv run python ../checker.py                                     # the assistant's query

cd ../exercise
uv run python report.py                                         # writes top_products.csv
```

## Files

- `practice/setup.py`: builds `practice.duckdb` with `customers` and `orders` (one order is delivered twice)
- `practice/profile.py`: prints row counts, column types, nulls, distinct values, ranges and sample rows for a table
- `checker.py`: the assistant's first query for new-customer AOV by segment in Q3 2026. It must be run from `practice/`, where the database is
- `exercise/report.py`: a nightly sales report whose comments now describe the code, with `FIXME` where the behaviour needs an owner's decision
- `exercise/sales_raw.csv`, `exercise/top_products.csv`: the report's input and output
