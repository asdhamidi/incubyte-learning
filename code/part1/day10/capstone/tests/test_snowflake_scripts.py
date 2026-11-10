from pathlib import Path

import pytest
from games_pipeline.checks import export_checks_sql
from games_pipeline.load import FILE_COLUMNS

SQL = Path(__file__).resolve().parent.parent / "sql"
SNOWFLAKE = SQL / "snowflake"

# These scripts run in Snowflake by hand, so CI cannot execute them. These tests keep them
# from drifting away from the code that CI does run.


def script(name):
    return (SNOWFLAKE / name).read_text()


def test_the_raw_table_has_every_file_column_and_the_lineage_columns():
    ddl = script("02_raw_table.sql")

    for column in [*FILE_COLUMNS, "source_file", "source_line", "loaded_at"]:
        assert column in ddl, f"{column} missing from the Snowflake raw table"


def test_the_load_matches_columns_by_name_not_by_position():
    load = script("03_load.sql")

    assert "MATCH_BY_COLUMN_NAME" in load
    assert "INCLUDE_METADATA" in load
    assert "$1" not in load, (
        "a positional load would break if the columns were reordered"
    )


def test_the_load_records_the_file_name_line_and_time():
    load = script("03_load.sql")

    for field in [
        "METADATA$FILENAME",
        "METADATA$FILE_ROW_NUMBER",
        "METADATA$START_SCAN_TIME",
    ]:
        assert field in load


def test_the_file_format_is_tab_separated_with_a_header_row():
    stage = script("01_stage_and_format.sql")

    assert "PARSE_HEADER = TRUE" in stage
    assert "FIELD_DELIMITER = '\\t'" in stage
    assert "EMPTY_FIELD_AS_NULL = FALSE" in stage  # raw keeps values as delivered


def test_the_snowflake_checks_are_the_same_queries_the_tests_run():
    assert script("04_checks.sql") == export_checks_sql()


@pytest.mark.parametrize("name", ["stg_games.sql", "games_summary.sql"])
def test_shared_sql_has_no_duckdb_only_syntax(name):
    sql = (SQL / name).read_text()

    for duckdb_only in ["read_csv", "epoch_ms", "EXCLUDE", "REPLACE (", "::"]:
        assert duckdb_only not in sql, (
            f"{name} uses {duckdb_only}, which Snowflake lacks"
        )
