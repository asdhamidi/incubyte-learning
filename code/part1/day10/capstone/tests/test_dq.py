import pytest
from games_pipeline.checks import run_dq_check
from games_pipeline.contract import ContractViolation
from games_pipeline.load import read_summary
from games_pipeline.pipeline import DataQualityFailure, run_pipeline

# The data quality check: `winner` in staging must be white, black or draw.
# The summary only counts 'white' and 'black', so an unrecognised value would be
# left out of the metric without any error. This check turns that into a failure.


def file_with(sample_path, tmp_path, name, edits):
    """A copy of the sample where edits maps (line, column) to a new value."""
    lines = sample_path.read_text().splitlines()
    header = lines[0].split("\t")
    for (line, column), value in edits.items():
        cells = lines[line - 1].split("\t")
        cells[header.index(column)] = value
        lines[line - 1] = "\t".join(cells)
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n")
    return path


# --- the check --------------------------------------------------------------


def test_the_sample_passes_the_winner_check(staged_con):
    assert run_dq_check(staged_con, "winner_accepted_values") == []


def test_an_unknown_winner_is_reported_with_its_count(staged_con):
    staged_con.execute(
        "UPDATE stg_games SET winner = 'whtie' WHERE id IN ('g1000x', 'g1001x')"
    )

    assert run_dq_check(staged_con, "winner_accepted_values") == [("whtie", 2)]


def test_a_different_case_is_reported(staged_con):
    staged_con.execute("UPDATE stg_games SET winner = 'White' WHERE id = 'g1000x'")

    assert run_dq_check(staged_con, "winner_accepted_values") == [("White", 1)]


def test_a_missing_winner_is_reported(staged_con):
    # NULL NOT IN (...) is never true, so the check has to ask for NULL on its own
    staged_con.execute("UPDATE stg_games SET winner = NULL WHERE id = 'g1000x'")

    assert run_dq_check(staged_con, "winner_accepted_values") == [(None, 1)]


def test_an_empty_winner_is_reported(staged_con):
    staged_con.execute("UPDATE stg_games SET winner = '' WHERE id = 'g1000x'")

    assert run_dq_check(staged_con, "winner_accepted_values") == [("", 1)]


# --- what happens when it fails ---------------------------------------------


def test_a_clean_run_builds_the_summary(con, sample_path, loaded_at):
    summary = run_pipeline(con, sample_path, loaded_at)

    assert [row[0] for row in summary] == ["1-99", "100-199", "200-399", "400+"]


def test_a_failed_check_keeps_the_last_good_summary(
    con, sample_path, tmp_path, loaded_at
):
    good = run_pipeline(con, sample_path, loaded_at)
    bad = file_with(
        sample_path,
        tmp_path,
        "bad.tsv",
        {
            (2, "id"): "bad1",
            (2, "winner"): "whtie",
            # a valid game in the same file: if the summary were rebuilt it would change
            (3, "id"): "new1",
        },
    )

    with pytest.raises(DataQualityFailure):
        run_pipeline(con, bad, loaded_at)

    assert read_summary(con) == good


def test_a_failed_check_keeps_the_new_data_for_investigation(
    con, sample_path, tmp_path, loaded_at
):
    run_pipeline(con, sample_path, loaded_at)
    bad = file_with(
        sample_path,
        tmp_path,
        "bad.tsv",
        {(2, "id"): "bad1", (2, "winner"): "whtie"},
    )

    with pytest.raises(DataQualityFailure):
        run_pipeline(con, bad, loaded_at)

    in_raw = con.execute("SELECT COUNT(*) FROM raw_games WHERE id = 'bad1'").fetchone()
    in_rejected = con.execute(
        "SELECT COUNT(*) FROM stg_games_rejected WHERE id = 'bad1'"
    ).fetchone()
    assert (in_raw[0], in_rejected[0]) == (1, 1)


def test_a_failed_check_puts_staging_back_to_its_last_good_version(
    con, sample_path, tmp_path, loaded_at
):
    run_pipeline(con, sample_path, loaded_at)
    good_ids = con.execute("SELECT id FROM stg_games ORDER BY id").fetchall()
    bad = file_with(
        sample_path,
        tmp_path,
        "bad.tsv",
        {(2, "id"): "bad1", (2, "winner"): "whtie", (3, "id"): "new1"},
    )

    with pytest.raises(DataQualityFailure):
        run_pipeline(con, bad, loaded_at)

    assert con.execute("SELECT id FROM stg_games ORDER BY id").fetchall() == good_ids


def test_a_failed_first_run_leaves_no_staging_and_no_summary(
    con, sample_path, tmp_path, loaded_at
):
    bad = file_with(sample_path, tmp_path, "bad.tsv", {(2, "winner"): "whtie"})

    with pytest.raises(DataQualityFailure):
        run_pipeline(con, bad, loaded_at)

    tables = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
    }
    assert "stg_games_rejected" in tables
    assert "stg_games" not in tables
    assert "games_summary" not in tables


def test_a_clean_run_clears_the_rejected_build(con, sample_path, tmp_path, loaded_at):
    run_pipeline(con, sample_path, loaded_at)
    bad = file_with(sample_path, tmp_path, "bad.tsv", {(2, "winner"): "whtie"})
    with pytest.raises(DataQualityFailure):
        run_pipeline(con, bad, loaded_at)

    fixed = file_with(sample_path, tmp_path, "bad.tsv", {(2, "winner"): "white"})
    run_pipeline(con, fixed, loaded_at)

    tables = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables"
        ).fetchall()
    }
    assert "stg_games_rejected" not in tables


def test_the_failure_names_the_value_and_how_many_rows(
    con, sample_path, tmp_path, loaded_at
):
    bad = file_with(
        sample_path,
        tmp_path,
        "bad.tsv",
        {(2, "winner"): "whtie", (3, "winner"): "whtie"},
    )

    with pytest.raises(DataQualityFailure) as error:
        run_pipeline(con, bad, loaded_at)

    assert "winner_accepted_values" in str(error.value)
    assert "'whtie'" in str(error.value)
    assert "2" in str(error.value)


def test_a_rerun_after_the_fix_recovers(con, sample_path, tmp_path, loaded_at):
    run_pipeline(con, sample_path, loaded_at)
    bad = file_with(
        sample_path, tmp_path, "bad.tsv", {(2, "id"): "bad1", (2, "winner"): "whtie"}
    )
    with pytest.raises(DataQualityFailure):
        run_pipeline(con, bad, loaded_at)

    fixed = file_with(
        sample_path, tmp_path, "bad.tsv", {(2, "id"): "bad1", (2, "winner"): "white"}
    )
    summary = run_pipeline(con, fixed, loaded_at)

    # the sample's summary plus one more game (bad1, a 639-point gap the higher-rated lost)
    assert summary == [
        ("1-99", 4, 1, 25.0),
        ("100-199", 2, 1, 50.0),
        ("200-399", 8, 2, 25.0),
        ("400+", 12, 2, 16.7),
    ]
    assert run_dq_check(con, "winner_accepted_values") == []


def test_a_contract_violation_stops_everything(con, sample_path, tmp_path, loaded_at):
    broken = tmp_path / "games.tsv"
    broken.write_text(sample_path.read_text().replace("winner", "result"))

    with pytest.raises(ContractViolation):
        run_pipeline(con, broken, loaded_at)

    tables = con.execute("SELECT table_name FROM information_schema.tables").fetchall()
    assert tables == []
