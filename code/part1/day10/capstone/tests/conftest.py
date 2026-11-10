import sys
from datetime import datetime
from pathlib import Path

import duckdb
import pytest

CAPSTONE = Path(__file__).resolve().parent.parent

# Imports from src/ and paths to sample data must work from any working directory,
# because CI runs pytest from the repo root while pytest.ini lives in this folder.
sys.path.insert(0, str(CAPSTONE / "src"))


@pytest.fixture
def sample_path():
    return CAPSTONE / "sample_data" / "games_sample.tsv"


@pytest.fixture
def loaded_at():
    return datetime(2026, 11, 10, 9, 0, 0)


@pytest.fixture
def con():
    connection = duckdb.connect()
    yield connection
    connection.close()


@pytest.fixture
def raw_con(con, sample_path, loaded_at):
    """DuckDB with the sample file loaded into raw_games."""
    from games_pipeline.load import load_raw

    load_raw(con, sample_path, loaded_at)
    return con


@pytest.fixture
def staged_con(raw_con):
    """DuckDB with the sample file loaded and staged."""
    from games_pipeline.load import build_staging

    build_staging(raw_con)
    return raw_con
