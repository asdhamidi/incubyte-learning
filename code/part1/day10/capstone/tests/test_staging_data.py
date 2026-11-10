import pytest
from games_pipeline.checks import STAGING_CHECKS, run_check

# Each check is a query that returns the offending rows.
# For every check, a bad row is planted to prove the check can fail.

PLANTED_BAD_ROW = {
    "id_not_null": "INSERT INTO stg_games SELECT * REPLACE (NULL AS id) FROM stg_games LIMIT 1",
    "id_unique": "INSERT INTO stg_games SELECT * FROM stg_games LIMIT 1",
    "rated_not_null": "INSERT INTO stg_games SELECT * REPLACE (NULL AS rated) FROM stg_games LIMIT 1",
    "ratings_not_null": "INSERT INTO stg_games SELECT * REPLACE (NULL AS white_rating) FROM stg_games LIMIT 1",
    "ratings_positive": "INSERT INTO stg_games SELECT * REPLACE (-5 AS black_rating) FROM stg_games LIMIT 1",
    "rows_match_raw": "DELETE FROM stg_games WHERE id = 'g1000x'",
}


def test_every_check_has_a_planted_bad_row_test():
    assert set(STAGING_CHECKS) == set(PLANTED_BAD_ROW)


@pytest.mark.parametrize("name", sorted(STAGING_CHECKS))
def test_staged_sample_passes_the_check(staged_con, name):
    assert run_check(staged_con, name) == []


@pytest.mark.parametrize("name", sorted(PLANTED_BAD_ROW))
def test_check_fails_on_a_planted_bad_row(staged_con, name):
    staged_con.execute(PLANTED_BAD_ROW[name])

    assert len(run_check(staged_con, name)) == 1
