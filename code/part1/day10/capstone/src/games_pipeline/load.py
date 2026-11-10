"""Load a games file into raw_games and build staging.

DuckDB stands in for Snowflake here so the same steps run in tests and CI. In
Snowflake the raw load is a COPY INTO from the external stage (see sql/snowflake).
The staging SQL is shared by both engines.
"""

import csv
from pathlib import Path

from .contract import assert_contract

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"

# every column of the file, loaded as text
FILE_COLUMNS = [
    "id",
    "rated",
    "created_at",
    "last_move_at",
    "turns",
    "victory_status",
    "winner",
    "increment_code",
    "white_id",
    "white_rating",
    "black_id",
    "black_rating",
    "moves",
    "opening_eco",
    "opening_name",
    "opening_ply",
]


def _create_raw_table(con):
    columns = ", ".join(f"{name} VARCHAR" for name in FILE_COLUMNS)
    con.execute(
        f"CREATE TABLE IF NOT EXISTS raw_games ({columns}, "
        "source_file VARCHAR, source_line INTEGER, loaded_at TIMESTAMP)"
    )


def _read_rows(path):
    with Path(path).open(newline="") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader)
        for line_number, cells in enumerate(reader, start=2):
            if cells:
                row = dict(zip(header, cells))
                yield [row.get(c) for c in FILE_COLUMNS], line_number


def load_raw(con, path, loaded_at):
    """Land a file in raw_games as delivered. Loading the same file again replaces its rows.

    The contract is checked first, so a bad file loads nothing.
    """
    assert_contract(path)
    name = Path(path).name

    _create_raw_table(con)
    marks = ", ".join(["?"] * (len(FILE_COLUMNS) + 3))
    con.begin()
    try:
        con.execute("DELETE FROM raw_games WHERE source_file = ?", [name])
        con.executemany(
            f"INSERT INTO raw_games VALUES ({marks})",
            [[*cells, name, line, loaded_at] for cells, line in _read_rows(path)],
        )
        con.commit()
    except Exception:
        con.rollback()
        raise


def run_sql_file(con, name):
    con.execute((SQL_DIR / name).read_text())


def build_staging(con):
    run_sql_file(con, "stg_games.sql")


def build_summary(con):
    run_sql_file(con, "games_summary.sql")


def read_summary(con):
    """The summary as (band, games, higher_rated_won, win_rate_pct), in band order."""
    return con.execute(
        """
        SELECT gap_band, games, higher_rated_won, higher_rated_win_rate_pct
        FROM games_summary ORDER BY band_min_gap
        """
    ).fetchall()
