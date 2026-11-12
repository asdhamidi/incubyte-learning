from datetime import datetime

from games_pipeline.load import build_staging

COLUMNS = (
    "id, rated, created_at, last_move_at, turns, victory_status, winner, "
    "increment_code, white_id, white_rating, black_id, black_rating, moves, "
    "opening_eco, opening_name, opening_ply"
)


def count(con, sql):
    return con.execute(sql).fetchone()[0]


def insert_raw(con, game_id, loaded_at, source_line=2, **overrides):
    """Add one raw row, copied from the first sample row with some columns changed."""
    values = con.execute(
        f"SELECT {COLUMNS} FROM raw_games ORDER BY source_line LIMIT 1"
    )
    row = dict(zip(COLUMNS.split(", "), values.fetchone()))
    row.update(overrides, id=game_id)
    names = ", ".join([*row, "source_file", "source_line", "loaded_at"])
    marks = ", ".join(["?"] * (len(row) + 3))
    con.execute(
        f"INSERT INTO raw_games ({names}) VALUES ({marks})",
        [*row.values(), "extra.csv", source_line, loaded_at],
    )


def test_staging_has_one_row_per_game(staged_con):
    rows, ids = staged_con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT id) FROM stg_games"
    ).fetchone()

    assert (rows, ids) == (39, 39)


def test_staging_keeps_the_duplicated_game_once(staged_con):
    assert count(staged_con, "SELECT COUNT(*) FROM stg_games WHERE id = 'g1003x'") == 1


def test_staging_casts_columns_to_real_types(staged_con):
    types = dict(
        staged_con.execute(
            """
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name = 'stg_games'
            """
        ).fetchall()
    )

    assert types["rated"] == "BOOLEAN"
    assert types["created_at_ms"] == "BIGINT"
    assert types["white_rating"] == "INTEGER"
    assert types["black_rating"] == "INTEGER"


def test_staging_keeps_where_each_game_came_from(staged_con):
    columns = {
        row[0]
        for row in staged_con.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'stg_games'"
        ).fetchall()
    }

    assert {"source_file", "loaded_at"} <= columns


def test_staging_applies_no_business_rules(staged_con):
    unrated = count(staged_con, "SELECT COUNT(*) FROM stg_games WHERE NOT rated")
    draws = count(staged_con, "SELECT COUNT(*) FROM stg_games WHERE winner = 'draw'")

    assert (unrated, draws) == (12, 5)


def test_the_earliest_delivery_wins_when_an_id_repeats(raw_con):
    insert_raw(
        raw_con, "late1", datetime(2026, 11, 12), white_rating="1500", winner="white"
    )
    insert_raw(
        raw_con, "late1", datetime(2026, 11, 11), white_rating="1600", winner="black"
    )

    build_staging(raw_con)

    row = raw_con.execute(
        "SELECT white_rating, winner FROM stg_games WHERE id = 'late1'"
    ).fetchone()
    assert row == (1600, "black")


def test_a_tie_in_delivery_time_is_broken_by_file_line(raw_con):
    same_time = datetime(2026, 11, 11)
    insert_raw(raw_con, "tie1", same_time, source_line=50, white_rating="1700")
    insert_raw(raw_con, "tie1", same_time, source_line=49, white_rating="1800")

    build_staging(raw_con)

    rating = raw_con.execute(
        "SELECT white_rating FROM stg_games WHERE id = 'tie1'"
    ).fetchone()[0]
    assert rating == 1800


def test_staging_reads_the_formats_in_the_real_file(raw_con):
    insert_raw(
        raw_con, "fmt1", datetime(2026, 11, 11), rated="TRUE", created_at="1.50421E+12"
    )
    insert_raw(
        raw_con,
        "fmt2",
        datetime(2026, 11, 11),
        rated="False",
        created_at="1504210000000",
    )

    build_staging(raw_con)

    rows = {
        row[0]: row[1:]
        for row in raw_con.execute(
            "SELECT id, rated, created_at_ms FROM stg_games WHERE id IN ('fmt1', 'fmt2')"
        ).fetchall()
    }
    assert rows["fmt1"] == (True, 1504210000000)
    assert rows["fmt2"] == (False, 1504210000000)
