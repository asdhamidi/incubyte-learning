from pathlib import Path

import pytest
from games_pipeline.contract import ContractViolation, assert_contract, validate_file

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SAMPLES = sorted(SAMPLE_DIR.glob("*.tsv"))
SAMPLE = SAMPLE_DIR / "games_sample.tsv"


def sample_lines():
    return SAMPLE.read_text().splitlines()


def write_tsv(tmp_path, lines):
    path = tmp_path / "games.tsv"
    path.write_text("\n".join(lines) + "\n")
    return path


def with_value(lines, line_number, column, value):
    """Copy of the sample lines with one cell changed. line_number is 1-based, header is 1."""
    header = lines[0].split("\t")
    cells = lines[line_number - 1].split("\t")
    cells[header.index(column)] = value
    changed = list(lines)
    changed[line_number - 1] = "\t".join(cells)
    return changed


# --- the sample files -------------------------------------------------------


def test_there_are_sample_files():
    assert SAMPLES, f"no sample files found in {SAMPLE_DIR}"


@pytest.mark.parametrize("path", SAMPLES, ids=lambda p: p.name)
def test_sample_files_meet_the_contract(path):
    assert validate_file(path) == []


# --- the header -------------------------------------------------------------


def test_renamed_column_is_reported_by_name_and_nothing_else(tmp_path):
    lines = sample_lines()
    lines[0] = lines[0].replace("white_rating", "white_elo")

    problems = validate_file(write_tsv(tmp_path, lines))

    assert problems == ["missing column 'white_rating'"]


def test_every_missing_column_is_reported_at_once(tmp_path):
    lines = sample_lines()
    lines[0] = lines[0].replace("winner", "result").replace("rated", "is_rated")

    problems = validate_file(write_tsv(tmp_path, lines))

    assert problems == ["missing column 'rated'", "missing column 'winner'"]


def test_extra_columns_are_tolerated(tmp_path):
    lines = [line + "\tx" for line in sample_lines()]
    lines[0] = lines[0].rsplit("\t", 1)[0] + "\tnew_field"

    assert validate_file(write_tsv(tmp_path, lines)) == []


def test_column_order_does_not_matter(tmp_path):
    reversed_lines = ["\t".join(reversed(line.split("\t"))) for line in sample_lines()]

    assert validate_file(write_tsv(tmp_path, reversed_lines)) == []


def test_empty_file_is_reported(tmp_path):
    path = tmp_path / "games.tsv"
    path.write_text("")

    assert validate_file(path) == ["file is empty"]


# --- the rows ---------------------------------------------------------------


def test_non_integer_rating_is_reported_with_line_and_column(tmp_path):
    lines = with_value(sample_lines(), 3, "white_rating", "abc")

    problems = validate_file(write_tsv(tmp_path, lines))

    assert problems == ["line 3: white_rating 'abc' is not an integer"]


def test_empty_id_is_reported(tmp_path):
    lines = with_value(sample_lines(), 2, "id", "")

    assert validate_file(write_tsv(tmp_path, lines)) == ["line 2: id is empty"]


def test_rated_must_be_true_or_false(tmp_path):
    lines = with_value(sample_lines(), 4, "rated", "maybe")

    problems = validate_file(write_tsv(tmp_path, lines))

    assert problems == ["line 4: rated 'maybe' is not True or False"]


def test_short_row_is_reported(tmp_path):
    lines = sample_lines()
    lines[4] = "\t".join(lines[4].split("\t")[:10])

    problems = validate_file(write_tsv(tmp_path, lines))

    assert problems == ["line 5: expected 16 fields, found 10"]


def test_all_row_problems_are_reported_together(tmp_path):
    lines = with_value(sample_lines(), 3, "white_rating", "abc")
    lines = with_value(lines, 6, "created_at", "yesterday")

    problems = validate_file(write_tsv(tmp_path, lines))

    assert problems == [
        "line 3: white_rating 'abc' is not an integer",
        "line 6: created_at 'yesterday' is not an integer",
    ]


# --- the gate ---------------------------------------------------------------


def test_assert_contract_passes_for_a_valid_file():
    assert_contract(SAMPLE)


def test_assert_contract_raises_and_lists_every_problem(tmp_path):
    lines = sample_lines()
    lines[0] = lines[0].replace("winner", "result")
    lines = with_value(lines, 3, "white_rating", "abc")

    with pytest.raises(ContractViolation) as error:
        assert_contract(write_tsv(tmp_path, lines))

    assert "missing column 'winner'" in str(error.value)
