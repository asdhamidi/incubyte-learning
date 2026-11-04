"""Day 8 exercise data: builds renewals.duckdb with `subscriptions` and `renewals`.
Treat the generation code as a black box and work from the tables."""

from datetime import date, timedelta

import duckdb

con = duckdb.connect("renewals.duckdb")
con.execute("DROP TABLE IF EXISTS renewals")
con.execute("DROP TABLE IF EXISTS subscriptions")
con.execute("""CREATE TABLE subscriptions (
    subscription_id VARCHAR, customer_id VARCHAR, plan VARCHAR, region VARCHAR,
    start_date DATE, term_end_date DATE, status VARCHAR, mrr DOUBLE)""")
con.execute("""CREATE TABLE renewals (
    subscription_id VARCHAR, renewal_due_date DATE, outcome VARCHAR,
    outcome_date DATE, renewed_mrr DOUBLE)""")

subs, rens = [], []
n = 0
regions = ["North", "South", "East", "West"]


def spread(start, count, i):
    """Spread due dates evenly across a quarter starting at `start` (91 days)."""
    return start + timedelta(days=(i * 7) % 90)


def add(plan, due, outcome, mrr, early_cancel=False):
    global n
    n += 1
    sid, cid = f"S-{n:04d}", f"C-{(n + 3) // 2:04d}" if n % 11 == 0 else f"C-{n:04d}"
    start = due - timedelta(days=365)
    status = "cancelled" if (early_cancel or outcome == "churned") else "active"
    subs.append((sid, cid, plan, regions[n % 4], start, due, status, mrr))
    if outcome == "renewed":
        new_mrr = mrr * 0.8 if (plan == "enterprise" and n % 9 == 0) else mrr
        rens.append((sid, due, "renewed", due + timedelta(days=(n % 5)), new_mrr))
    elif outcome == "churned":
        rens.append((sid, due, "churned", due, None))
    else:
        rens.append((sid, due, "pending", None, None))


Q2, Q3 = date(2026, 4, 1), date(2026, 7, 1)


def batch(plan, qstart, renewed, churned, mrr, pending_overdue=0, pending_open=0):
    i = 0
    for _ in range(renewed):
        add(plan, spread(qstart, 0, i), "renewed", mrr)
        i += 1
    for k in range(churned):
        add(plan, spread(qstart, 0, i), "churned", mrr, early_cancel=(k == 0))
        i += 1
    for _ in range(pending_overdue):  # due long ago, still pending
        add(
            plan,
            date(qstart.year, qstart.month, 10) + timedelta(days=i % 40),
            "pending",
            mrr,
        )
        i += 1
    for k in range(pending_open):  # due in the last two days of the quarter
        add(plan, date(2026, 9, 29 + (k % 2)), "pending", mrr)
        i += 1


batch("enterprise", Q2, renewed=76, churned=4, mrr=1000)
batch("smb", Q2, renewed=12, churned=8, mrr=100)
batch("enterprise", Q3, renewed=24, churned=1, mrr=1000, pending_open=1)
batch("smb", Q3, renewed=48, churned=24, mrr=100, pending_overdue=3, pending_open=3)
for q in (Q2, Q3):  # trials: never part of the metric
    for k in range(3):
        add("trial", spread(q, 0, k * 5), "renewed", 0.0)
        add("trial", spread(q, 0, k * 5 + 2), "churned", 0.0)

con.executemany("INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?,?)", subs)
con.executemany("INSERT INTO renewals VALUES (?,?,?,?,?)", rens)
print("renewals.duckdb created")
print(
    "  subscriptions:", con.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
)
print("  renewals     :", con.execute("SELECT COUNT(*) FROM renewals").fetchone()[0])
print("  as-of date for this exercise: 2026-10-28")
