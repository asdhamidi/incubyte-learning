from datetime import datetime

import pipeline


def orders(con):
    rows = con.execute(
        "SELECT order_id, customer, amount, status, updated_at FROM intermediate_orders ORDER BY order_id"
    ).fetchall()
    return {row[0]: row[1:] for row in rows}


# --- the input data ---------------------------------------------------------

def test_raw_orders_contains_duplicate_keys(loaded):
    duplicated = loaded.execute(
        "SELECT order_id FROM raw_orders GROUP BY order_id HAVING COUNT(*) > 1 ORDER BY order_id"
    ).fetchall()

    assert duplicated == [(2,), (5,)]


def test_raw_orders_contains_a_late_record(loaded):
    late = loaded.execute(
        """
        SELECT r.order_id FROM raw_orders r
        JOIN intermediate_orders t USING (order_id)
        WHERE r.updated_at < t.updated_at
        """
    ).fetchall()

    assert late == [(3,)]


def test_intermediate_orders_starts_with_unique_keys(loaded):
    total, distinct = loaded.execute(
        "SELECT COUNT(*), COUNT(DISTINCT order_id) FROM intermediate_orders"
    ).fetchone()

    assert total == distinct == 4


# --- the data after the merge -----------------------------------------------

def test_new_order_is_inserted(loaded):
    pipeline.merge(loaded)

    assert 5 in orders(loaded)


def test_newer_record_updates_the_existing_order(loaded):
    pipeline.merge(loaded)

    assert orders(loaded)[2] == ("bob", 200, "shipped", datetime(2026, 10, 3, 9, 0))


def test_late_record_does_not_overwrite_newer_data(loaded):
    pipeline.merge(loaded)

    assert orders(loaded)[3] == ("carol", 300, "shipped", datetime(2026, 10, 2, 9, 0))


def test_duplicate_keys_in_the_batch_collapse_to_the_latest_record(loaded):
    pipeline.merge(loaded)

    assert orders(loaded)[5] == ("erin", 550, "placed", datetime(2026, 10, 3, 12, 0))


def test_orders_missing_from_the_batch_are_untouched(loaded):
    pipeline.merge(loaded)

    assert orders(loaded)[1] == ("alice", 100, "placed", datetime(2026, 10, 1, 10, 0))
    assert orders(loaded)[4] == ("dave", 400, "placed", datetime(2026, 10, 2, 10, 0))


def test_no_duplicate_keys_after_the_merge(loaded):
    pipeline.merge(loaded)

    total, distinct = loaded.execute(
        "SELECT COUNT(*), COUNT(DISTINCT order_id) FROM intermediate_orders"
    ).fetchone()
    assert total == distinct == 5


def test_running_the_same_load_twice_does_not_change_the_result(loaded):
    pipeline.merge(loaded)
    after_first_run = orders(loaded)

    pipeline.merge(loaded)

    assert orders(loaded) == after_first_run
