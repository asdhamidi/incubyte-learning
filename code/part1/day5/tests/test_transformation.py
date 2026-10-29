import pytest
from ..main import flatten_json



def test_flatten_json_exists():
    test_json = {
        "name": "adam",
        "designation": "SC1",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
    }

    result_json = {
        "name": "adam",
        "designation": "SC1",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
    }

    assert flatten_json(test_json) == result_json

def test_flatten_json_empty_json():
    assert flatten_json({}) == {}


def test_flatten_json_nested_json():
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

def test_flatten_json_2nd_order_nested_json():
    nested_json = {
        "name": "adam",
        "work": {
            "company": "Incubyte",
            "engagement": {
                "client": "ABC",
                "role": "Data Craftsperson"
            }
        },
        "address": {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
    }

    flattened_json = {
        "name": "adam",
        "company": "Incubyte",
        "client": "ABC",
        "role": "Data Craftsperson",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
    }

    assert flatten_json(nested_json) == flattened_json
