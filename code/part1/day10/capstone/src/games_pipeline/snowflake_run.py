"""Run the pipeline in Snowflake with one command.

    python -m games_pipeline.snowflake_run --local-file path/to/games.csv --storage-account <account>

With --storage-account the command first checks the local file against the contract and
uploads it to Blob Storage (replacing a file of the same name), and points the Snowflake
stage at that folder. Without it, the file must already be in Blob Storage under the
existing stage's folder (see sql/snowflake/01), and the file's name is given as the first
argument. Either way the file format is created first. The command then loads it into raw, rebuilds staging, runs the data quality check, and then builds
the summary view. It follows the same rules as `run_pipeline`: a failed check puts staging
back to its last good version, keeps the rejected build, and exits with an error.

Sign-in settings come from environment variables, never from arguments or files.
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from .checks import DQ_CHECKS
from .contract import ContractViolation, assert_contract
from .land import land
from .load import SQL_DIR
from .log import configure_logging, step
from .pipeline import DataQualityFailure, describe_failure

log = logging.getLogger(__name__)

REQUIRED_SETTINGS = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
]
SAFE_FILE_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$")
STAGE_URL = re.compile(
    r"^azure://[a-z0-9]{3,24}\.blob\.core\.windows\.net/[a-z0-9][a-z0-9\-]{2,62}/[A-Za-z0-9_.\-]+/$"
)

# The same file format as sql/snowflake/01_stage_and_format.sql. Comma-separated with a
# header row, matched to table columns by name. Empty values stay empty text, because
# raw keeps the file as delivered.
FILE_FORMAT = """
    CREATE OR REPLACE FILE FORMAT capstone_csv
        TYPE = CSV
        FIELD_DELIMITER = ','
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        PARSE_HEADER = TRUE
        EMPTY_FIELD_AS_NULL = FALSE
        ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE"""


def stage_url_for(account, container, folder):
    return f"azure://{account}.blob.core.windows.net/{container}/{folder}/"


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
    # never log the password: only where and how we sign in
    log.info(
        "connecting to account %s as %s (role %s, warehouse %s, %s.%s, sign-in: %s)",
        settings["account"],
        settings["user"],
        settings["role"],
        settings["warehouse"],
        settings["database"],
        settings["schema"],
        settings["authenticator"],
    )
    if settings["authenticator"] == "externalbrowser":
        log.info("a browser window will open to sign in")
    with step(log, "sign in"):
        return connect(**settings)


def _script(*parts):
    return SQL_DIR.joinpath(*parts).read_text()


def _copy_statement(stage_file):
    return f"""
        COPY INTO raw_games
        FROM @capstone_stage
        FILE_FORMAT = (FORMAT_NAME = capstone_csv)
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        INCLUDE_METADATA = (
            source_file = METADATA$FILENAME,
            source_line = METADATA$FILE_ROW_NUMBER,
            loaded_at = METADATA$START_SCAN_TIME
        )
        FILES = ('{stage_file}')
        FORCE = TRUE
        ON_ERROR = ABORT_STATEMENT"""


def _count(cursor, table, where=""):
    cursor.execute(f"SELECT COUNT(*) FROM {table} {where}".strip())
    row = cursor.fetchone()
    return row[0] if row else 0


def _setup(cursor, stage_url):
    """The one-time Snowflake objects, created again on every run (safe to repeat).

    The storage integration is not touched here: it needs an account admin once and is
    shared (see docs/runbook_cloud.md, steps 0 and 2).
    """
    cursor.execute(FILE_FORMAT)
    log.info("file format capstone_csv ready")
    if stage_url:
        cursor.execute(
            f"CREATE OR REPLACE STAGE capstone_stage URL = '{stage_url}' "
            "STORAGE_INTEGRATION = azure_int"
        )
        log.info("stage capstone_stage points at %s", stage_url)


def _load_raw(cursor, stage_file, source_file):
    """Replace this file's raw rows with a fresh load, in one transaction."""
    cursor.execute(_script("snowflake", "02_raw_table.sql"))
    where = f"WHERE source_file = '{source_file}'"
    log.info("raw_games ready, %d rows from other loads", _count(cursor, "raw_games"))
    with step(log, f"load {source_file} into raw_games"):
        cursor.execute("BEGIN")
        try:
            cursor.execute(f"DELETE FROM raw_games {where}")
            log.info("removed the rows of an earlier load of this file (if any)")
            cursor.execute(_copy_statement(stage_file))
            loaded = _count(cursor, "raw_games", where)
        except Exception:
            log.error("load failed, rolling back so raw is as it was")
            cursor.execute("ROLLBACK")
            raise
        cursor.execute("COMMIT")
    log.info("raw_games now holds %d rows from %s", loaded, source_file)


def _staging_exists(cursor):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = CURRENT_SCHEMA() AND table_name = 'STG_GAMES'"
    )
    return cursor.fetchone()[0] > 0


def _quarantine(cursor, had_staging):
    cursor.execute("CREATE OR REPLACE TABLE stg_games_rejected CLONE stg_games")
    log.warning("rejected build kept in stg_games_rejected")
    if had_staging:
        cursor.execute("CREATE OR REPLACE TABLE stg_games CLONE stg_games_last_good")
        cursor.execute("DROP TABLE stg_games_last_good")
        log.warning("stg_games put back to its last good version")
    else:
        cursor.execute("DROP TABLE stg_games")
        log.warning("no earlier good version, stg_games removed")


def run_in_snowflake(connection, stage_file, folder="games", stage_url=None):
    """Load a staged file, rebuild staging, check it and build the summary.

    With a stage_url the stage is created pointing at the Blob folder, otherwise the
    existing stage is used. Returns the summary rows. Raises DataQualityFailure if a
    check fails.
    """
    if not SAFE_FILE_NAME.match(stage_file) or not SAFE_FILE_NAME.match(folder):
        raise ValueError(f"unsafe file or folder name: {stage_file!r}, {folder!r}")
    if stage_url is not None and not STAGE_URL.match(stage_url):
        raise ValueError(f"unexpected stage location: {stage_url!r}")

    cursor = connection.cursor()
    try:
        _setup(cursor, stage_url)
        _load_raw(cursor, stage_file, f"{folder}/{stage_file}")

        had_staging = _staging_exists(cursor)
        if had_staging:
            cursor.execute(
                "CREATE OR REPLACE TABLE stg_games_last_good CLONE stg_games"
            )
            log.info("snapshot of the current staging kept as stg_games_last_good")
        else:
            log.info("first run: no staging yet, so no snapshot")
        with step(log, "build stg_games"):
            cursor.execute(_script("stg_games.sql"))
        log.info("stg_games holds %d games after dedupe", _count(cursor, "stg_games"))

        for name, query in DQ_CHECKS.items():
            offenders = cursor.execute(query).fetchall()
            if offenders:
                log.error("data quality check %s FAILED", name)
                _quarantine(cursor, had_staging)
                raise DataQualityFailure(describe_failure(name, offenders))
            log.info("data quality check %s passed", name)

        with step(log, "build games_summary"):
            cursor.execute(_script("games_summary.sql"))
            cursor.execute("DROP TABLE IF EXISTS stg_games_rejected")
            cursor.execute("DROP TABLE IF EXISTS stg_games_last_good")
        cursor.execute(
            "SELECT gap_band, games, higher_rated_won, higher_rated_win_rate_pct "
            "FROM games_summary ORDER BY band_min_gap"
        )
        rows = cursor.fetchall()
        log.info("summary has %d bands", len(rows))
        return rows
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


def main(argv=None, env=None, connect=None, upload=land):
    parser = argparse.ArgumentParser(
        description="Load a staged games file in Snowflake, check it and build the summary."
    )
    parser.add_argument(
        "stage_file",
        nargs="?",
        help="the file's name in the stage, e.g. games.csv (default: the local file's name)",
    )
    parser.add_argument(
        "--folder", default="games", help="the stage's folder in the container"
    )
    parser.add_argument(
        "--local-file", help="a local copy, checked against the contract first"
    )
    parser.add_argument(
        "--storage-account",
        help="upload the local file to this storage account first "
        "(default: AZURE_STORAGE_ACCOUNT, if set)",
    )
    parser.add_argument(
        "--container", default="capstone", help="the Blob container to upload to"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="also show debug logs"
    )
    args = parser.parse_args(argv)
    env = os.environ if env is None else env
    configure_logging(args.verbose)

    stage_file = args.stage_file or (args.local_file and Path(args.local_file).name)
    if not stage_file:
        print("give the stage_file or --local-file", file=sys.stderr)
        return 1
    account = args.storage_account or env.get("AZURE_STORAGE_ACCOUNT")

    try:
        if args.local_file:
            with step(log, f"check {args.local_file} against the contract"):
                assert_contract(args.local_file)
    except ContractViolation as error:
        print(error, file=sys.stderr)
        return 1

    if account and not re.fullmatch(r"[a-z0-9]{3,24}", account):
        print(f"not a storage account name: {account!r}", file=sys.stderr)
        return 1

    if args.local_file and account:
        try:
            blob = upload(
                args.local_file, account, args.container, args.folder, overwrite=True
            )
        except (subprocess.CalledProcessError, OSError) as error:
            log.error("the upload to Blob Storage failed")
            print(f"upload failed: {error}", file=sys.stderr)
            return 1
        log.info("%s is in Blob Storage", blob)

    try:
        connection = connect_from_env(env, connect)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    try:
        stage_url = (
            stage_url_for(account, args.container, args.folder) if account else None
        )
        rows = run_in_snowflake(connection, stage_file, args.folder, stage_url)
    except (DataQualityFailure, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    except Exception:
        log.exception("the run stopped on an unexpected error")
        return 1
    finally:
        connection.close()
        log.info("connection closed")

    log.info("run finished")
    _print_summary(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
