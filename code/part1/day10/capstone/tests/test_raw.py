from datetime import datetime

import pytest
from games_pipeline.contract import ContractViolation
from games_pipeline.load import load_raw


def count(con, sql):
    return con.execute(sql).fetchone()[0]


def broken_copy(sample_path, tmp_path, name="games.tsv"):
    bad = tmp_path / name
    bad.write_text(sample_path.read_text().replace("winner", "result"))
    return bad


def test_raw_keeps_every_row_of_the_file(raw_con):
    assert count(raw_con, "SELECT COUNT(*) FROM raw_games") == 40


def test_raw_keeps_the_duplicate_delivery(raw_con):
    rows, ids = raw_con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT id) FROM raw_games"
    ).fetchone()

    assert (rows, ids) == (40, 39)


def test_raw_columns_are_all_text(raw_con):
    types = raw_con.execute(
        """
        SELECT DISTINCT data_type FROM information_schema.columns
        WHERE table_name = 'raw_games'
          AND column_name NOT IN ('source_file', 'source_line', 'loaded_at')
        """
    ).fetchall()

    assert types == [("VARCHAR",)]


def test_raw_records_where_each_row_came_from(raw_con, loaded_at):
    files, first, last, lines, loaded = raw_con.execute(
        """
        SELECT COUNT(DISTINCT source_file), MIN(source_line), MAX(source_line),
               COUNT(DISTINCT source_line), MIN(loaded_at)
        FROM raw_games
        """
    ).fetchone()

    assert files == 1
    assert (first, last, lines) == (2, 41, 40)
    assert loaded == loaded_at


def test_loading_the_same_file_twice_does_not_duplicate_rows(raw_con, sample_path):
    load_raw(raw_con, sample_path, datetime(2026, 11, 11, 9, 0, 0))

    assert count(raw_con, "SELECT COUNT(*) FROM raw_games") == 40


def test_a_file_that_breaks_the_contract_loads_nothing(
    con, sample_path, tmp_path, loaded_at
):
    bad = broken_copy(sample_path, tmp_path)

    with pytest.raises(ContractViolation):
        load_raw(con, bad, loaded_at)

    tables = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = 'raw_games'"
    ).fetchall()
    assert tables == []


def test_a_failed_file_leaves_earlier_raw_rows_untouched(
    raw_con, sample_path, tmp_path
):
    bad = broken_copy(sample_path, tmp_path, name="other.tsv")

    with pytest.raises(ContractViolation):
        load_raw(raw_con, bad, datetime(2026, 11, 11, 9, 0, 0))

    assert count(raw_con, "SELECT COUNT(*) FROM raw_games") == 40
