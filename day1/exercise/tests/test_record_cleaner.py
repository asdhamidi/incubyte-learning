from re import match
from ..main import clean_record
import pytest

def test_clean_record_returns_empty_list_when_no_list_given():
    assert clean_record({}) == {}

def test_clean_record_raises_missing_id():
    with pytest.raises(ValueError):
            clean_record({"name": "Ada"})

def test_clean_record_raises_empty_id():
    with pytest.raises(ValueError):
        clean_record(record={"name": "Alice", "id": ""})

def test_clean_record_trims_whitespace_from_string_fields():
    record = {"id": " 42 ", "name": "  Ada  "}
    assert clean_record(record) == {"id": "42", "name": "Ada"}

@pytest.mark.parametrize("bad_date", ["22/10/2026", "2026-10-22"])
def test_clean_record_normalizes_date(bad_date):
    record = {"id": " 42 ", "name": "  Ada  ", "date": bad_date}
    assert clean_record(record) == {"id": "42", "name": "Ada", "date": "2026-10-22"}
