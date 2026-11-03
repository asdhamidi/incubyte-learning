# Review: PR #7, Add revenue summary

## Summary

Thanks for picking this up, Sam. The need is clear (revenue by currency for finance), and the change sits mostly in a new file, which keeps it easy to read.

I ran `f2` on the sample orders and it returns:

```text
[('USD', 44), ('ALL', 44)]
```

The correct figures are USD 44.48 and EUR 15.00. The EUR row is missing, the USD figure has lost its cents, and the total isn't a meaningful number. The tests pass because they don't check any values. I'd like to fix the three blocking issues below before merging.

**Verdict: Request changes.**

## Blocking

**1. `reports.py`, `WHERE order_id <> 'O-1002'` · Logic**
This removes the only EUR order, so EUR disappears from the output and finance won't see it. What was wrong with O-1002? If the data is bad, it should be fixed or flagged where the data is cleaned, not hidden in a report, because the numbers would then differ from every other report. If the order is valid, the filter should go.

**2. `reports.py`, `rows.append(("ALL", total))` · Logic**
This adds amounts in different currencies, so the total isn't a real amount in any currency. Once the filter in point 1 is removed, it would show 59, which is 44 plus 15 across USD and EUR. Could we show a total per currency only? If finance needs one grand total, it needs an agreed conversion rate. Could you check with them which they want?

**3. `reports.py`, `CAST(... AS INTEGER)` · Logic**
This drops the cents, so 44.48 becomes 44, and every figure is off by up to a unit. Could we keep the decimals, for example `ROUND(SUM(...), 2)`?

**4. `dev.duckdb` · Hygiene**
This is a 536 KB binary database that was force-added past `.gitignore`. Database files can contain data, bloat the repository, and can't be reviewed or merged. Could you remove it from the commit (`git rm --cached dev.duckdb`, then amend or rebase so it isn't in the history) and keep it ignored?

**5. `test_data.py`, `test_f2` · Tests**
The test only checks `len(rows) > 0`, so it would pass with wrong numbers, missing currencies or an empty total. It passed on the output above, which is missing EUR and has the wrong USD value. Could it assert the expected values on the sample data (USD 44.48 and EUR 15.00)? Please also add a case where an excluded or missing currency would make it fail.

## Suggestions

**6. `reports.py`, `unit_price * qty` · Logic**
`order_lines` already has `line_total`. Recomputing it here means the rule exists in two places and can drift apart. Could we sum `line_total` instead?

**7. `reports.py`, return value · Design**
The total row sits in the same list as the currency rows, so anyone summing the output counts the total twice. If a grand total stays, could it be returned separately?

**8. `reports.py`, naming**
`f2` doesn't say what the function does. `revenue_by_currency` would. `cur` and `amt` could be `currency` and `revenue`, and the `'ALL'` marker in the currency column is easy to mistake for a real currency. The variable `total` is also ambiguous.

**9. `contract.py` · Scope**
The rename from `problems` to `issues` is unrelated to this change, and it makes the diff harder to read. Could it go in its own PR, or be dropped? The new `issues=[]` also loses the spacing style used in the rest of the file.

**10. Commit message and description**
`stuff` and "pls review" don't tell a reviewer what changed, why, how it was tested, or which dashboards read it. Could you add those, and name the specific ticket from finance?

## Nits

**11. `test_data.py`**
`test_f2` doesn't describe what it tests, it sits in the data-test file although it tests a report function, and it imports inside the function. A separate `test_reports.py` with a name like `test_revenue_by_currency_*` would read better.
