import duckdb


def pretty_print(heading, data):
    if heading:
        print("-" * 25 + heading + "-" * 25)

    print(data)

    if heading:
        print("-" * 75)


con = duckdb.connect("renewals.duckdb")

pretty_print("renewals", data=con.execute(query="SELECT * FROM renewals").df())
pretty_print(
    "renewals_by_outcome",
    data=con.execute(query="SELECT count(*), outcome FROM renewals group by 2").df(),
)
pretty_print(
    "renewals_by_renewal_date",
    data=con.execute(
        query="SELECT count(*), CAST(DATE_TRUNC('quarter', renewal_due_date) AS DATE) AS quarter_start FROM renewals group by 2"
    ).df(),
)
pretty_print(
    "renewals_by_status_renewal_date",
    data=con.execute(
        query="SELECT count(*), outcome, CAST(DATE_TRUNC('quarter', renewal_due_date) AS DATE) AS quarter_start FROM renewals group by 2,3"
    ).df(),
)
pretty_print(
    "subscriptions", data=con.execute(query="SELECT * FROM subscriptions").df()
)
pretty_print(
    "subs_by_plan",
    data=con.execute(query="SELECT count(*), plan FROM subscriptions group by 2").df(),
)
pretty_print(
    "subs_by_status",
    data=con.execute(
        query="SELECT count(*), status FROM subscriptions group by 2"
    ).df(),
)
pretty_print(
    "subs_by_status_and_date",
    data=con.execute(
        query="SELECT count(*), status, term_end_date FROM subscriptions group by 2, 3"
    ).df(),
)
pretty_print(
    "subs_renewal_join",
    data=con.execute(
        query="""SELECT
    CAST(DATE_TRUNC('quarter', r.renewal_due_date) AS DATE) AS quarter_start,
    s.plan,
    CASE
        WHEN r.outcome = 'renewed' THEN 'renewed'
        WHEN r.outcome = 'churned' THEN 'churned'
        WHEN DATEDIFF('day', r.renewal_due_date, a.as_of_date) > 30 THEN 'churned'
        ELSE 'open'
    END AS result
FROM renewals r
JOIN subscriptions s USING (subscription_id)
CROSS JOIN v_as_of a
WHERE s.plan <> 'trial'"""
    ).df(),
)

con.execute("CREATE OR REPLACE VIEW v_as_of AS SELECT DATE '2026-10-28' AS as_of_date;")
con.execute(
    query="""
    CREATE OR REPLACE VIEW v_renewal_rate_by_quarter AS
    WITH classified AS (
        SELECT
            CAST(DATE_TRUNC('quarter', r.renewal_due_date) AS DATE) AS quarter_start,
            s.plan,
            CASE
                WHEN r.outcome = 'renewed' THEN 'renewed'
                WHEN r.outcome = 'churned' THEN 'churned'
                WHEN DATEDIFF('day', r.renewal_due_date, a.as_of_date) > 30 THEN 'churned'
                ELSE 'open'
            END AS result
        FROM renewals r
        JOIN subscriptions s USING (subscription_id)
        CROSS JOIN v_as_of a
        WHERE s.plan <> 'trial'
    )
    SELECT
        quarter_start,
        COALESCE(plan, 'all')                                          AS plan,
        COUNT(*)                                                       AS due,
        SUM(CASE WHEN result = 'renewed' THEN 1 ELSE 0 END)            AS renewed,
        SUM(CASE WHEN result = 'churned' THEN 1 ELSE 0 END)            AS churned,
        SUM(CASE WHEN result = 'open'    THEN 1 ELSE 0 END)            AS open_renewals,
        ROUND(100.0 * SUM(CASE WHEN result = 'renewed' THEN 1 ELSE 0 END)
              / NULLIF(SUM(CASE WHEN result <> 'open' THEN 1 ELSE 0 END), 0), 1) AS renewal_rate_pct
    FROM classified
    GROUP BY GROUPING SETS ((quarter_start, plan), (quarter_start));
     """
)


pretty_print(
    "renewal_rate_by_quarter",
    data=con.execute(query="SELECT * FROM v_renewal_rate_by_quarter").df(),
)

pretty_print(
    "q3_enterprise_renewals",
    data=con.execute(
        query="""SELECT r.subscription_id, r.renewal_due_date, r.outcome
FROM renewals r JOIN subscriptions s USING (subscription_id)
WHERE s.plan = 'enterprise'
  AND r.renewal_due_date BETWEEN '2026-07-01' AND '2026-09-30'
ORDER BY r.renewal_due_date;"""
    ).df(),
)
