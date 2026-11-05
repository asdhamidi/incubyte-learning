"""Prints a profile of tables in a DuckDB file, ready to paste into an assistant prompt.
Usage:  python profile.py practice.duckdb customers orders
Check the output for personal data before you paste it anywhere."""

import sys

import duckdb


def profile(con, table, max_values=8, sample=5):
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    lines = [f"TABLE {table}: {n} rows", "COLUMNS (name, type, nulls, distinct):"]
    for name, typ, *_ in con.execute(f"DESCRIBE {table}").fetchall():
        nulls, distinct = con.execute(
            f'SELECT COUNT(*) - COUNT("{name}"), COUNT(DISTINCT "{name}") FROM {table}'
        ).fetchone()
        lines.append(f"  {name} {typ} nulls={nulls} distinct={distinct}")
        if distinct <= max_values and typ == "VARCHAR":
            vals = con.execute(
                f'SELECT "{name}", COUNT(*) FROM {table} GROUP BY 1 ORDER BY 2 DESC, 1'
            ).fetchall()
            lines.append("     values: " + ", ".join(f"{v!r}:{c}" for v, c in vals))
        elif typ in ("TIMESTAMP", "DATE", "DOUBLE", "INTEGER", "BIGINT"):
            lo, hi = con.execute(
                f'SELECT MIN("{name}"), MAX("{name}") FROM {table}'
            ).fetchone()
            lines.append(f"     range: {lo} to {hi}")
    lines.append(f"SAMPLE ({sample} rows):")
    for r in con.execute(f"SELECT * FROM {table} LIMIT {sample}").fetchall():
        lines.append("  " + str(r))
    return "\n".join(lines)


if __name__ == "__main__":
    path, tables = sys.argv[1], sys.argv[2:]
    con = duckdb.connect(path, read_only=True)
    print("\n\n".join(profile(con, t) for t in tables))
