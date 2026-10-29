import pytest
from transform import flatten_json


def test_one_row_per_item():
    nested_json = {
        "name": "adam",
        "designation": "SC1",
        "address": {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
    }

    flattened_json = {
        "name": "adam",
        "designation": "SC1",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
    }

    assert flatten_json(nested_json) == flattened_json
