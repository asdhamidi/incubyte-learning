from pathlib import Path

from duckdb import DuckDBPyConnection

SQL_DIR = Path(__file__).resolve().parents[0] / "sql"


def _run(con: DuckDBPyConnection, script: str):
    return con.execute((SQL_DIR / script).read_text())


def setup(con: DuckDBPyConnection) -> None:
    """Create intermediate_orders (seeded) and raw_orders (the incremental batch)."""
    _run(con, "01_setup.sql")


def merge(con: DuckDBPyConnection) -> None:
    """Load raw_orders into intermediate_orders."""
    _run(con, "02_merge.sql")


def snapshot(con: DuckDBPyConnection) -> None:
    con.execute(
        "CREATE OR REPLACE TABLE intermediate_orders_after_run1 AS SELECT * FROM intermediate_orders"
    )


def idempotency_diff(con: DuckDBPyConnection) -> tuple:
    """(diff_rows, rows_run1, rows_run2, sum_run1, sum_run2) against the snapshot."""
    return _run(con, "03_idempotency_check.sql").fetchone()


def union_counts(con: DuckDBPyConnection) -> dict[str, tuple[int, int]]:
    """{operator: (row_count, total_amount)} for UNION ALL and UNION over the same inputs."""
    rows = _run(con, "04_union_vs_union_all.sql").fetchall()
    return {operator: (row_count, total) for operator, row_count, total in rows}
