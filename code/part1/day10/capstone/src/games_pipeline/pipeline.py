"""The pipeline in order: contract gate, raw, staging, data quality check, summary.

The summary is a view over staging, so staging is what has to be protected. A failed
data quality check puts staging back to its last good version and keeps the rejected
build in `stg_games_rejected`, so the summary keeps showing the last good numbers and
the cause can be investigated. Raw keeps the new data too.
"""

import logging

from .checks import DQ_CHECKS, run_dq_check
from .load import build_staging, build_summary, load_raw, read_summary
from .log import step

log = logging.getLogger(__name__)


class DataQualityFailure(Exception):
    """A data quality check found bad rows. The message names the check and the values."""


def describe_failure(name, offenders):
    values = ", ".join(f"{value!r} ({n} rows)" for value, n in offenders)
    return f"{name} failed: unexpected values {values}"


def _table_exists(con, name):
    count = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [name]
    ).fetchone()[0]
    return count > 0


def _count(con, table):
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _quarantine(con, had_staging):
    """Keep the rejected build, and put staging back to the last good one if there is one."""
    con.execute("CREATE OR REPLACE TABLE stg_games_rejected AS SELECT * FROM stg_games")
    log.warning("rejected build kept in stg_games_rejected")
    if had_staging:
        con.execute(
            "CREATE OR REPLACE TABLE stg_games AS SELECT * FROM stg_games_last_good"
        )
        con.execute("DROP TABLE stg_games_last_good")
        log.warning("stg_games put back to its last good version")
    else:
        con.execute("DROP TABLE stg_games")
        log.warning("no earlier good version, stg_games removed")


def run_pipeline(con, path, loaded_at):
    with step(log, f"load {path} into raw_games"):
        load_raw(con, path, loaded_at)  # raises ContractViolation before anything loads

    had_staging = _table_exists(con, "stg_games")
    if had_staging:
        con.execute(
            "CREATE OR REPLACE TABLE stg_games_last_good AS SELECT * FROM stg_games"
        )
        log.info("snapshot of the current staging kept as stg_games_last_good")
    else:
        log.info("first run: no staging yet, so no snapshot")
    with step(log, "build stg_games"):
        build_staging(con)
    log.info("stg_games holds %d games after dedupe", _count(con, "stg_games"))

    for name in DQ_CHECKS:
        offenders = run_dq_check(con, name)
        if offenders:
            log.error("data quality check %s FAILED", name)
            _quarantine(con, had_staging)
            raise DataQualityFailure(describe_failure(name, offenders))
        log.info("data quality check %s passed", name)

    with step(log, "build games_summary"):
        build_summary(con)  # a view, so it follows the staging that just passed
    con.execute("DROP TABLE IF EXISTS stg_games_rejected")
    con.execute("DROP TABLE IF EXISTS stg_games_last_good")
    return read_summary(con)
