"""Contract for the incoming games file.

Lists only the columns the pipeline reads. Extra columns and column order are
tolerated, a missing column or a value of the wrong shape is not. Checks shape,
not meaning: whether `winner` holds an accepted value is a data quality check.
"""

import csv
import logging
import math
from pathlib import Path

log = logging.getLogger(__name__)

# The Lichess download is a plain comma-separated file. Its formats are mixed: `rated` is
# True, False, TRUE or FALSE, and `created_at` is a whole number or scientific notation
# such as 1.50421E+12. Both are accepted, and raw keeps them exactly as delivered.
DELIMITER = ","

# column name -> what a value in that column has to look like
REQUIRED_COLUMNS = {
    "id": "text",
    "rated": "true_false",
    "created_at": "number",
    "white_rating": "integer",
    "black_rating": "integer",
    "winner": "any",
    "victory_status": "any",
}


class ContractViolation(Exception):
    """The file does not meet the contract. The message lists every problem."""


def read_rows(path):
    """Every row of the file as a list of cells, header first. Shared by the contract and the load."""
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f, delimiter=DELIMITER))


def _is_number(value):
    try:
        return math.isfinite(float(value))
    except ValueError:
        return False


def _check_value(column, kind, value):
    if kind == "text" and value == "":
        return f"{column} is empty"
    if kind == "true_false" and value.lower() not in ("true", "false", "TRUE", "FALSE"):
        return f"{column} {value!r} is not True or False"
    if kind == "integer":
        try:
            int(value)
        except ValueError:
            return f"{column} {value!r} is not an integer"
    if kind == "number" and not _is_number(value):
        return f"{column} {value!r} is not a number"
    return None


def validate_file(path):
    """Return every contract problem in the file. An empty list means it is valid."""
    rows = read_rows(path)

    if not rows:
        return ["file is empty"]

    header = rows[0]
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        # Row checks are meaningless without the columns, so report these alone.
        return [f"missing column '{c}'" for c in missing]

    problems = []
    for line_number, cells in enumerate(rows[1:], start=2):
        if not cells:
            continue
        if len(cells) != len(header):
            problems.append(
                f"line {line_number}: expected {len(header)} fields, found {len(cells)}"
            )
            continue
        row = dict(zip(header, cells))
        for column, kind in REQUIRED_COLUMNS.items():
            problem = _check_value(column, kind, row[column])
            if problem:
                problems.append(f"line {line_number}: {problem}")
    log.debug(
        "%s: %d data rows checked, %d problems",
        Path(path).name,
        len(rows) - 1,
        len(problems),
    )
    return problems


def assert_contract(path):
    """The runtime gate: raise before anything is loaded if the file breaks the contract."""
    problems = validate_file(path)
    if problems:
        log.error(
            "%s breaks the contract with %d problems", Path(path).name, len(problems)
        )
        raise ContractViolation(
            f"{Path(path).name} breaks the contract:\n- " + "\n- ".join(problems)
        )
