import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import duckdb
import pipeline
import pytest


@pytest.fixture
def con():
    connection = duckdb.connect()
    yield connection
    connection.close()


@pytest.fixture
def loaded(con):
    pipeline.setup(con)
    return con
