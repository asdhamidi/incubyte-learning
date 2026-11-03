import pytest

from ..main import clean_record


def test_clean_record_raises_missing_id_for_empty_record():
    with pytest.raises(ValueError):
        clean_record({})


def test_clean_record_raises_missing_id():
    with pytest.raises(ValueError):
        clean_record({"name": "Ada"})


def test_clean_record_raises_empty_id():
    with pytest.raises(ValueError):
        clean_record(record={"name": "Alice", "id": ""})


@pytest.mark.parametrize("blank_id", ["   ", "\t", " \n "])
def test_clean_record_raises_whitespace_only_id(blank_id):
    with pytest.raises(ValueError):
        clean_record({"id": blank_id, "name": "Alice"})


def test_clean_record_raises_none_id():
    with pytest.raises(ValueError):
        clean_record({"id": None, "name": "Alice"})


def test_clean_record_trims_whitespace_from_string_fields():
    record = {"id": " 42 ", "name": "  Ada  "}
    assert clean_record(record) == {"id": "42", "name": "Ada"}


@pytest.mark.parametrize("valid_date", ["22/10/2026", "2026-10-22"])
def test_clean_record_normalizes_date(valid_date):
    record = {"id": " 42 ", "name": "  Ada  ", "date": valid_date}
    assert clean_record(record) == {"id": "42", "name": "Ada", "date": "2026-10-22"}


@pytest.mark.parametrize(
    "unrecognised_date", ["not-a-date", "2026/10/22", "22-10-2026", "32/13/2026", ""]
)
def test_clean_record_raises_unrecognised_date(unrecognised_date):
    with pytest.raises(ValueError):
        clean_record({"id": "42", "date": unrecognised_date})


@pytest.mark.parametrize("not_text", [None, 20261022])
def test_clean_record_raises_date_that_is_not_text(not_text):
    with pytest.raises(ValueError):
        clean_record({"id": "42", "date": not_text})
