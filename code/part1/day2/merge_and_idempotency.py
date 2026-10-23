import duckdb

import pipeline

LINE_DIVIDER = "-" * 25


def show_records(con, table_name, column_names, order_by):
    columns = ", ".join(column_names)
    table_name = table_name.strip()
    sql = f"SELECT {columns} FROM {table_name}"
    if order_by:
        sql += f" ORDER BY {order_by}"

    for row in con.execute(sql).fetchall():
        print(" ", row)


def main():
    con = duckdb.connect()

    # Setting up tables and making initial inserts
    pipeline.setup(con)

    print(f"{LINE_DIVIDER}raw_orders{LINE_DIVIDER}")
    show_records(con, "raw_orders", "*", "order_id")

    print(f"{LINE_DIVIDER}intermediate_orders before run 1{LINE_DIVIDER}")
    show_records(con, "intermediate_orders", "*", "order_id")

    # Running the merge statements
    pipeline.merge(con)

    print(f"{LINE_DIVIDER}intermediate_orders after run 1{LINE_DIVIDER}")
    show_records(con, "intermediate_orders", "*", "order_id")

    # Savings a pre-merge copy of the intermediate table
    pipeline.snapshot(con)
    print(
        f"{LINE_DIVIDER}pre-second merge copy of intermediate_orders [intermediate_orders_after_run1] after run 1{LINE_DIVIDER}"
    )
    show_records(con, "intermediate_orders_after_run1", "*", "order_id")

    print(f"{LINE_DIVIDER}merge runs again{LINE_DIVIDER}")
    pipeline.merge(con)

    print(
        "idempotency (diff_rows, rows_run1, rows_run2, sum_run1, sum_run2):",
        pipeline.idempotency_diff(con),
    )


if __name__ == "__main__":
    main()
