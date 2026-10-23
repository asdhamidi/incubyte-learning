# Reflection
In the context of this exercise, there are can be several silent data errors.
- If we do not properly guard the merge statement with a qualify statement, it will pick two records for the same business key, that can silently cause data errors and shift metrics. Further, without a temporal guard (s.updated_at > t.updated_at ), multiple records can be picked and cause problems.
- Without a stable business key and that guard, every rerun re-applies the batch and corrupts the table further. The merge in [02_merge.sql](./sql/02_merge.sql) takes care of these, hence does not face these issues.
- UNION vs UNION ALL - this can fail silently if the actual needed logic is not correctly reflected in the SQL with either of those clauses. If duplicates are actually not needed, then UNION, if they are needed, then UNION ALL.
