import pipeline


def order_ids(con):
    rows = con.execute(
        "SELECT order_id FROM intermediate_orders ORDER BY order_id"
    ).fetchall()
    return [row[0] for row in rows]


def test_setup_creates_raw_and_intermediate_tables(con):
    pipeline.setup(con)

    tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    assert {"raw_orders", "intermediate_orders"} <= tables


def test_merge_changes_the_orders_in_the_intermediate_table(loaded):
    assert order_ids(loaded) == [1, 2, 3, 4, 7]

    pipeline.merge(loaded)

    assert order_ids(loaded) == [1, 2, 3, 5, 7, 8]


def test_snapshot_copies_the_intermediate_table(loaded):
    pipeline.merge(loaded)

    pipeline.snapshot(loaded)

    count = lambda table: loaded.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    assert count("intermediate_orders_after_run1") == count("intermediate_orders")


def test_idempotency_diff_returns_diff_counts_and_sums(loaded):
    pipeline.merge(loaded)
    pipeline.snapshot(loaded)
    pipeline.merge(loaded)

    diff_rows, rows_run1, rows_run2, sum_run1, sum_run2 = pipeline.idempotency_diff(
        loaded
    )

    assert (diff_rows, rows_run1, rows_run2) == (0, 6, 6)
    assert sum_run1 == sum_run2 == 2660


def test_idempotency_diff_reports_a_changed_row(loaded):
    pipeline.merge(loaded)
    pipeline.snapshot(loaded)
    loaded.execute("UPDATE intermediate_orders SET amount = 1 WHERE order_id = 2")

    diff_rows, *_ = pipeline.idempotency_diff(loaded)

    assert diff_rows == 2


def test_union_counts_returns_row_count_and_total_per_operator(loaded):
    assert pipeline.union_counts(loaded) == {"UNION ALL": (6, 470), "UNION": (3, 220)}
