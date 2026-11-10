"""Contract for the incoming games file.

Lists only the columns the pipeline reads. Extra columns and column order are
tolerated, a missing column or a value of the wrong shape is not. Checks shape,
not meaning: whether `winner` holds an accepted value is a data quality check.
"""

import csv
from pathlib import Path

# column name -> what a value in that column has to look like
REQUIRED_COLUMNS = {
    "id": "text",
    "rated": "true_false",
    "created_at": "integer",
    "white_rating": "integer",
    "black_rating": "integer",
    "winner": "any",
    "victory_status": "any",
}


class ContractViolation(Exception):
    """The file does not meet the contract. The message lists every problem."""


def _check_value(column, kind, value):
    if kind == "text" and value == "":
        return f"{column} is empty"
    if kind == "true_false" and value not in ("True", "False"):
        return f"{column} {value!r} is not True or False"
    if kind == "integer":
        try:
            int(value)
        except ValueError:
            return f"{column} {value!r} is not an integer"
    return None


def validate_file(path):
    """Return every contract problem in the file. An empty list means it is valid."""
    with Path(path).open(newline="") as f:
        rows = list(csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE))

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
    return problems


def assert_contract(path):
    """The runtime gate: raise before anything is loaded if the file breaks the contract."""
    problems = validate_file(path)
    if problems:
        raise ContractViolation(
            f"{Path(path).name} breaks the contract:\n- " + "\n- ".join(problems)
        )
