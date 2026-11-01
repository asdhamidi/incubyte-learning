# Postmortem: 27 October revenue understated
**Status:** cause found, correction pending confirmation from the source team. Times in the timeline are fictional.
## Summary
The 27 Oct revenue and order figures were understated because 76 mobile orders arrived with a status value the pipeline did not recognise, and were silently excluded. The client noticed first, the day after the data loaded.
## Impact


| Dimension       | Reported | If the 76 orders are confirmed as completed |
| --------------- | -------- | ------------------------------------------- |
| Orders, 27 Oct  | 95       | 171                                         |
| Revenue, 27 Oct | 5,582    | 10,018                                      |
- Revenue was understated by 4,436, which is 44% of the corrected figure. It showed a 47% drop against 26 Oct, when the corrected change is -5%, in line with the 5% fall in raw rows.
- Only mobile orders were affected. 26 Oct is unaffected.
- Every dashboard reading `daily_revenue` showed the understated figure.
- No data was lost. The raw table holds the original values.

## Timeline

|Time (28 Oct)|Event|
|---|---|
|01:00|27 Oct data loaded and the summary rebuilt, with 76 orders excluded|
|09:00|Client reports that 27 Oct revenue looks low|
|09:10|Dashboard refresh paused and 27 Oct marked as under review|
|09:30|Drop confirmed. Rows lost at the intermediate layer, all mobile, all with status `complete`|
|09:35|First message sent to the client, with the next update promised in two hours|
|Pending|Source team confirms the meaning of `complete`, then the figures are recalculated and checked against the layer counts|
## Root cause

The pipeline decided which orders count by matching the status to one exact value (`completed`), and nothing checked the status values arriving from the source. When mobile orders arrived on 27 Oct with `complete`, they were treated as not completed, with no error.
## Contributing factors
- Excluded rows had no visible trace. The filter dropped them without any count or alert.
- No volume or revenue check on the summary. A 47% drop against a 5% change in raw rows was not flagged, so the client found it first.
- Why the source started sending `complete` is not yet known.
## What went well, and where we got lucky
- The raw layer was untouched, so nothing was lost and the cause could be read directly from it.
- Counting at each layer found the failing step quickly, and containment came before the root cause.
- We were lucky on size: mobile is about 40% of orders, so the drop was hard to miss. A smaller segment could have gone unnoticed for much longer.

## The one check that would have caught it

| **Check**              | An accepted-values test on `stg_orders.status`, allowing only `completed` and `cancelled`                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Layer**              | Staging, run on every load before the intermediate and summary tables are built                                                                                   |
| **Dimension**          | Validity                                                                                                                                                          |
| **If it fails**        | Block the build: downstream tables are not rebuilt, the dashboard keeps the last good figures, and the alert names the unexpected value and how many rows have it |
| **Owner and due date** | Data engineering lead, 4 Nov 2026                                                                                                                                 |

```sql
SELECT status, COUNT(*)
FROM stg_orders
WHERE status IS NULL OR status NOT IN ('completed', 'cancelled')
GROUP BY status
```
On the 28 Oct 01:00 load, this returns `('complete', 76)`, so the check would have stopped the build before the summary table changed.
## Recovery steps (not the preventive check)
1. Confirm with the source team that `complete` means `completed`.
2. If confirmed, map it to `completed` in staging, so the rule is applied once.
3. Rebuild 27 Oct and reconcile the layer counts and the revenue figure.
4. Tell the client the corrected figures and the period affected.