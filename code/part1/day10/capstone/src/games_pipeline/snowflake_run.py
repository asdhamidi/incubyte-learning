"""Run the pipeline in Snowflake with one command.

    python -m games_pipeline.snowflake_run games.csv --local-file path/to/games.csv

The file is already in Blob Storage under the stage's folder (see sql/snowflake/01). The
command loads it into raw, rebuilds staging, runs the data quality check, and then builds
the summary view. It follows the same rules as `run_pipeline`: a failed check puts staging
back to its last good version, keeps the rejected build, and exits with an error.

Sign-in settings come from environment variables, never from arguments or files.
"""

import argparse
import os
import re
import sys

from .checks import DQ_CHECKS
from .contract import ContractViolation, assert_contract
from .load import SQL_DIR
from .pipeline import DataQualityFailure, describe_failure

REQUIRED_SETTINGS = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
]
SAFE_FILE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$")


def connect_from_env(env, connect=None):
    """Open a Snowflake connection from SNOWFLAKE_* settings. Browser sign-in by default."""
    missing = [name for name in REQUIRED_SETTINGS if not env.get(name)]
    if missing:
        raise ValueError("missing settings: " + ", ".join(missing))

    settings = {
        "account": env["SNOWFLAKE_ACCOUNT"],
        "user": env["SNOWFLAKE_USER"],
        "role": env["SNOWFLAKE_ROLE"],
        "warehouse": env["SNOWFLAKE_WAREHOUSE"],
        "database": env["SNOWFLAKE_DATABASE"],
        "schema": env["SNOWFLAKE_SCHEMA"],
        "authenticator": env.get("SNOWFLAKE_AUTHENTICATOR", "externalbrowser"),
    }
    if env.get("SNOWFLAKE_PASSWORD"):
        settings["password"] = env["SNOWFLAKE_PASSWORD"]

    if connect is None:
        try:
            import snowflake.connector
        except ModuleNotFoundError as error:
            raise ValueError(
                "the Snowflake connector is not installed: "
                "pip install -r requirements-snowflake.txt"
            ) from error
        connect = snowflake.connector.connect
    return connect(**settings)


def _script(*parts):
    return SQL_DIR.joinpath(*parts).read_text()


def _copy_statement(stage_file):
    return f"""
        COPY INTO raw_games
        FROM @capstone_stage
        FILE_FORMAT = (FORMAT_NAME = capstone_tsv)
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        INCLUDE_METADATA = (
            source_file = METADATA$FILENAME,
            source_line = METADATA$FILE_ROW_NUMBER,
            loaded_at = METADATA$START_SCAN_TIME
        )
        FILES = ('{stage_file}')
        FORCE = TRUE
        ON_ERROR = ABORT_STATEMENT"""


def _load_raw(cursor, stage_file, source_file):
    """Replace this file's raw rows with a fresh load, in one transaction."""
    cursor.execute(_script("snowflake", "02_raw_table.sql"))
    cursor.execute("BEGIN")
    try:
        cursor.execute(f"DELETE FROM raw_games WHERE source_file = '{source_file}'")
        cursor.execute(_copy_statement(stage_file))
    except Exception:
        cursor.execute("ROLLBACK")
        raise
    cursor.execute("COMMIT")


def _staging_exists(cursor):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = CURRENT_SCHEMA() AND table_name = 'STG_GAMES'"
    )
    return cursor.fetchone()[0] > 0


def _quarantine(cursor, had_staging):
    cursor.execute("CREATE OR REPLACE TABLE stg_games_rejected CLONE stg_games")
    if had_staging:
        cursor.execute("CREATE OR REPLACE TABLE stg_games CLONE stg_games_last_good")
        cursor.execute("DROP TABLE stg_games_last_good")
    else:
        cursor.execute("DROP TABLE stg_games")


def run_in_snowflake(connection, stage_file, folder="games"):
    """Load a staged file, rebuild staging, check it and build the summary.

    Returns the summary rows. Raises DataQualityFailure if a check fails.
    """
    if not SAFE_FILE_NAME.match(stage_file) or not SAFE_FILE_NAME.match(folder):
        raise ValueError(f"unsafe file or folder name: {stage_file!r}, {folder!r}")

    cursor = connection.cursor()
    try:
        _load_raw(cursor, stage_file, f"{folder}/{stage_file}")

        had_staging = _staging_exists(cursor)
        if had_staging:
            cursor.execute(
                "CREATE OR REPLACE TABLE stg_games_last_good CLONE stg_games"
            )
        cursor.execute(_script("stg_games.sql"))

        for name, query in DQ_CHECKS.items():
            offenders = cursor.execute(query).fetchall()
            if offenders:
                _quarantine(cursor, had_staging)
                raise DataQualityFailure(describe_failure(name, offenders))

        cursor.execute(_script("games_summary.sql"))
        cursor.execute("DROP TABLE IF EXISTS stg_games_rejected")
        cursor.execute("DROP TABLE IF EXISTS stg_games_last_good")
        cursor.execute(
            "SELECT gap_band, games, higher_rated_won, higher_rated_win_rate_pct "
            "FROM games_summary ORDER BY band_min_gap"
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def _print_summary(rows):
    print("gap band    games  higher won    rate")
    for band, games, won, rate in rows:
        print(f"{band:<9} {games:>7} {won:>11} {rate:>7}%")
    games = sum(row[1] for row in rows)
    won = sum(row[2] for row in rows)
    rate = 100.0 * won / games if games else 0.0
    print(f"overall: {games} games, {won} won by the higher-rated player ({rate:.1f}%)")


def main(argv=None, env=None, connect=None):
    parser = argparse.ArgumentParser(
        description="Load a staged games file in Snowflake, check it and build the summary."
    )
    parser.add_argument(
        "stage_file", help="the file's name in the stage, e.g. games.csv"
    )
    parser.add_argument(
        "--folder", default="games", help="the stage's folder in the container"
    )
    parser.add_argument(
        "--local-file", help="a local copy, checked against the contract first"
    )
    args = parser.parse_args(argv)
    env = os.environ if env is None else env

    try:
        if args.local_file:
            assert_contract(args.local_file)
        connection = connect_from_env(env, connect)
    except (ContractViolation, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    try:
        rows = run_in_snowflake(connection, args.stage_file, args.folder)
    except (DataQualityFailure, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    finally:
        connection.close()

    _print_summary(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
