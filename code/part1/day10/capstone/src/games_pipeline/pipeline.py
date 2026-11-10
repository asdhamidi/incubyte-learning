"""The pipeline in order: contract gate, raw, staging, data quality check, summary.

A failed data quality check stops the run before the summary is rebuilt, so the
summary keeps its last good version. Raw and staging keep the new data so the
cause can be investigated.
"""

from .checks import DQ_CHECKS, run_dq_check
from .load import build_staging, build_summary, load_raw, read_summary


class DataQualityFailure(Exception):
    """A data quality check found bad rows. The message names the check and the values."""


def _describe(name, offenders):
    values = ", ".join(f"{value!r} ({n} rows)" for value, n in offenders)
    return f"{name} failed: unexpected values {values}"


def run_pipeline(con, path, loaded_at):
    load_raw(con, path, loaded_at)  # raises ContractViolation before anything loads
    build_staging(con)

    for name in DQ_CHECKS:
        offenders = run_dq_check(con, name)
        if offenders:
            raise DataQualityFailure(_describe(name, offenders))

    build_summary(con)
    return read_summary(con)
