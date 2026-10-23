import duckdb
import pytest

import pipeline


@pytest.fixture
def con():
    connection = duckdb.connect()
    yield connection
    connection.close()


@pytest.fixture
def loaded(con):
    pipeline.setup(con)
    return con
