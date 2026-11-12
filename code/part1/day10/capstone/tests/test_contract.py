from pathlib import Path

import pytest
from games_pipeline.contract import ContractViolation, assert_contract, validate_file

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
SAMPLES = sorted(SAMPLE_DIR.glob("*.csv"))
SAMPLE = SAMPLE_DIR / "games_sample.csv"


def sample_lines():
    return SAMPLE.read_text().splitlines()


def write_csv(tmp_path, lines):
    path = tmp_path / "games.csv"
    path.write_text("\n".join(lines) + "\n")
    return path


def with_value(lines, line_number, column, value):
    """Copy of the sample lines with one cell changed. line_number is 1-based, header is 1."""
    header = lines[0].split(",")
    cells = lines[line_number - 1].split(",")
    cells[header.index(column)] = value
    changed = list(lines)
    changed[line_number - 1] = ",".join(cells)
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

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == ["missing column 'white_rating'"]


def test_every_missing_column_is_reported_at_once(tmp_path):
    lines = sample_lines()
    lines[0] = lines[0].replace("winner", "result").replace("rated", "is_rated")

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == ["missing column 'rated'", "missing column 'winner'"]


def test_extra_columns_are_tolerated(tmp_path):
    lines = [line + ",x" for line in sample_lines()]
    lines[0] = lines[0].rsplit(",", 1)[0] + ",new_field"

    assert validate_file(write_csv(tmp_path, lines)) == []


def test_column_order_does_not_matter(tmp_path):
    reversed_lines = [",".join(reversed(line.split(","))) for line in sample_lines()]

    assert validate_file(write_csv(tmp_path, reversed_lines)) == []


def test_empty_file_is_reported(tmp_path):
    path = tmp_path / "games.csv"
    path.write_text("")

    assert validate_file(path) == ["file is empty"]


# --- the rows ---------------------------------------------------------------


def test_non_integer_rating_is_reported_with_line_and_column(tmp_path):
    lines = with_value(sample_lines(), 3, "white_rating", "abc")

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == ["line 3: white_rating 'abc' is not an integer"]


def test_empty_id_is_reported(tmp_path):
    lines = with_value(sample_lines(), 2, "id", "")

    assert validate_file(write_csv(tmp_path, lines)) == ["line 2: id is empty"]


def test_rated_must_be_true_or_false(tmp_path):
    lines = with_value(sample_lines(), 4, "rated", "maybe")

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == ["line 4: rated 'maybe' is not True or False"]


def test_short_row_is_reported(tmp_path):
    lines = sample_lines()
    lines[4] = ",".join(lines[4].split(",")[:10])

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == ["line 5: expected 16 fields, found 10"]


def test_all_row_problems_are_reported_together(tmp_path):
    lines = with_value(sample_lines(), 3, "white_rating", "abc")
    lines = with_value(lines, 6, "created_at", "yesterday")

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == [
        "line 3: white_rating 'abc' is not an integer",
        "line 6: created_at 'yesterday' is not a number",
    ]


# --- the gate ---------------------------------------------------------------


def test_assert_contract_passes_for_a_valid_file():
    assert_contract(SAMPLE)


def test_assert_contract_raises_and_lists_every_problem(tmp_path):
    lines = sample_lines()
    lines[0] = lines[0].replace("winner", "result")
    lines = with_value(lines, 3, "white_rating", "abc")

    with pytest.raises(ContractViolation) as error:
        assert_contract(write_csv(tmp_path, lines))

    assert "missing column 'winner'" in str(error.value)


# --- the formats in the real Lichess download -------------------------------


@pytest.mark.parametrize("value", ["True", "False", "TRUE", "FALSE", "true", "false"])
def test_rated_accepts_any_case_of_true_and_false(tmp_path, value):
    lines = with_value(sample_lines(), 3, "rated", value)

    assert validate_file(write_csv(tmp_path, lines)) == []


@pytest.mark.parametrize("value", ["yes", "1", "T", ""])
def test_rated_still_rejects_anything_else(tmp_path, value):
    lines = with_value(sample_lines(), 3, "rated", value)

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == [f"line 3: rated {value!r} is not True or False"]


@pytest.mark.parametrize(
    "value", ["1504210000000", "1.50421E+12", "1.50421e+12", "1504210000000.0"]
)
def test_created_at_accepts_whole_numbers_and_scientific_notation(tmp_path, value):
    lines = with_value(sample_lines(), 3, "created_at", value)

    assert validate_file(write_csv(tmp_path, lines)) == []


@pytest.mark.parametrize("value", ["yesterday", "nan", "inf", ""])
def test_created_at_still_has_to_be_a_number(tmp_path, value):
    lines = with_value(sample_lines(), 3, "created_at", value)

    problems = validate_file(write_csv(tmp_path, lines))

    assert problems == [f"line 3: created_at {value!r} is not a number"]


def test_the_sample_file_mixes_the_formats_like_the_real_file():
    text = SAMPLE.read_text()

    assert "TRUE" in text and "True" in text
    assert "E+12" in text
