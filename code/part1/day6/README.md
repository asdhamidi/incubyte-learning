# Day 6 Exercise: One Source of Truth and an Incident Trace

Two parts: consolidating two overlapping "active customers" definitions into one layered model, and tracing a revenue drop back through raw, staging, intermediate and summary tables.
## Run
Run each script from its own folder:
```bash
cd practice
uv run python practice.py

cd ../exercise
uv run python incident_setup.py   # rebuilds incident.duckdb
uv run python explore.py
```
## Files
- `practice/practice.py`: raw orders, the two old numbers (8 and 4), the single layered definition (`stg_orders`, `int_valid_orders`, `active_customers_mtd` = 5), data quality checks and the old table names repointed to the new metric
- `exercise/incident_setup.py`: builds `incident.duckdb` with raw, staging, intermediate and summary layers (`daily_revenue`)
- `exercise/explore.py`: the queries used to trace the 27 October drop to 76 orders with status `complete`
- `exercise/message_to_client.md`: first message to the client
- `exercise/postmortem.md`: blameless postmortem with the root cause and one preventive check
