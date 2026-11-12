import pytest
from games_pipeline.pipeline import DataQualityFailure
from games_pipeline.snowflake_run import connect_from_env, main, run_in_snowflake

# The runner is tested against a fake connection that records the SQL it is given, so no
# Snowflake account is needed. What the SQL does in Snowflake is checked by running it
# there (docs/runbook_cloud.md).

ENV = {
    "SNOWFLAKE_ACCOUNT": "org-account",
    "SNOWFLAKE_USER": "someone",
    "SNOWFLAKE_ROLE": "ACCOUNTADMIN",
    "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
    "SNOWFLAKE_DATABASE": "INCUBYTE_LEARNING",
    "SNOWFLAKE_SCHEMA": "AZURE_LEARNING",
}
SUMMARY = [("1-99", 4, 1, 25.0), ("100-199", 2, 1, 50.0)]


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []

    def execute(self, sql):
        statement = " ".join(sql.split())
        self.connection.statements.append(statement)
        if self.connection.fail_on and self.connection.fail_on in statement:
            raise RuntimeError("the statement failed")
        self.rows = self.connection.answer(statement)
        return self

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class FakeConnection:
    def __init__(self, staging_exists=False, offenders=None, fail_on=None):
        self.statements = []
        self.staging_exists = staging_exists
        self.offenders = offenders or []
        self.fail_on = fail_on
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True

    def answer(self, statement):
        if "information_schema.tables" in statement:
            return [(1 if self.staging_exists else 0,)]
        if "winner IS NULL OR winner NOT IN" in statement:
            return self.offenders
        if "FROM games_summary ORDER BY" in statement:
            return SUMMARY
        return []


def position(connection, fragment):
    for index, statement in enumerate(connection.statements):
        if fragment in statement:
            return index
    raise AssertionError(f"no statement contains {fragment!r}")


def ran(connection, fragment):
    return any(fragment in statement for statement in connection.statements)


# --- connecting -------------------------------------------------------------


def test_the_connection_uses_the_settings_and_browser_sign_in_by_default():
    seen = {}

    connect_from_env(ENV, connect=lambda **kwargs: seen.update(kwargs))

    assert seen == {
        "account": "org-account",
        "user": "someone",
        "role": "ACCOUNTADMIN",
        "warehouse": "COMPUTE_WH",
        "database": "INCUBYTE_LEARNING",
        "schema": "AZURE_LEARNING",
        "authenticator": "externalbrowser",
    }


def test_the_sign_in_method_can_be_changed():
    seen = {}

    connect_from_env(
        {**ENV, "SNOWFLAKE_AUTHENTICATOR": "snowflake", "SNOWFLAKE_PASSWORD": "secret"},
        connect=lambda **kwargs: seen.update(kwargs),
    )

    assert seen["authenticator"] == "snowflake"
    assert seen["password"] == "secret"


def test_missing_settings_are_named_and_values_are_never_shown():
    env = {"SNOWFLAKE_ACCOUNT": "org-account", "SNOWFLAKE_USER": "someone"}

    with pytest.raises(ValueError) as error:
        connect_from_env(env, connect=lambda **kwargs: None)

    message = str(error.value)
    assert "SNOWFLAKE_ROLE" in message
    assert "SNOWFLAKE_SCHEMA" in message
    assert "org-account" not in message


# --- a clean run ------------------------------------------------------------


def test_a_clean_run_goes_through_the_steps_in_order():
    connection = FakeConnection()

    run_in_snowflake(connection, "games.csv")

    order = [
        "CREATE TABLE IF NOT EXISTS raw_games",
        "BEGIN",
        "DELETE FROM raw_games",
        "COPY INTO raw_games",
        "COMMIT",
        "CREATE OR REPLACE TABLE stg_games AS",
        "winner IS NULL OR winner NOT IN",
        "CREATE OR REPLACE VIEW games_summary",
        "DROP TABLE IF EXISTS stg_games_rejected",
        "FROM games_summary ORDER BY",
    ]
    positions = [position(connection, fragment) for fragment in order]
    assert positions == sorted(positions)


def test_a_clean_run_returns_the_summary():
    assert run_in_snowflake(FakeConnection(), "games.csv") == SUMMARY


def test_the_load_names_the_file_and_matches_columns_by_name():
    connection = FakeConnection()

    run_in_snowflake(connection, "games.csv")

    copy = connection.statements[position(connection, "COPY INTO raw_games")]
    assert "FROM @capstone_stage" in copy
    assert "FILES = ('games.csv')" in copy
    assert "FORCE = TRUE" in copy
    assert "MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE" in copy
    assert "INCLUDE_METADATA" in copy


def test_loading_a_file_again_replaces_its_rows():
    connection = FakeConnection()

    run_in_snowflake(connection, "games.csv")

    delete = connection.statements[position(connection, "DELETE FROM raw_games")]
    assert delete == "DELETE FROM raw_games WHERE source_file = 'games/games.csv'"
    assert position(connection, "DELETE FROM raw_games") < position(
        connection, "COPY INTO raw_games"
    )


def test_the_first_run_takes_no_snapshot():
    connection = FakeConnection(staging_exists=False)

    run_in_snowflake(connection, "games.csv")

    assert not ran(connection, "stg_games_last_good CLONE")


def test_an_existing_staging_table_is_snapshotted_before_it_is_rebuilt():
    connection = FakeConnection(staging_exists=True)

    run_in_snowflake(connection, "games.csv")

    assert position(
        connection, "CREATE OR REPLACE TABLE stg_games_last_good CLONE stg_games"
    ) < position(connection, "CREATE OR REPLACE TABLE stg_games AS")
    assert ran(connection, "DROP TABLE IF EXISTS stg_games_last_good")


# --- when the data quality check fails --------------------------------------


def test_a_failed_check_puts_staging_back_and_keeps_the_rejected_build():
    connection = FakeConnection(staging_exists=True, offenders=[("whtie", 2)])

    with pytest.raises(DataQualityFailure) as error:
        run_in_snowflake(connection, "games.csv")

    assert "'whtie'" in str(error.value)
    assert ran(connection, "CREATE OR REPLACE TABLE stg_games_rejected CLONE stg_games")
    assert ran(
        connection, "CREATE OR REPLACE TABLE stg_games CLONE stg_games_last_good"
    )
    assert ran(connection, "DROP TABLE stg_games_last_good")


def test_a_failed_check_does_not_build_the_summary_or_clean_up():
    connection = FakeConnection(staging_exists=True, offenders=[("whtie", 2)])

    with pytest.raises(DataQualityFailure):
        run_in_snowflake(connection, "games.csv")

    assert not ran(connection, "CREATE OR REPLACE VIEW games_summary")
    assert not ran(connection, "DROP TABLE IF EXISTS stg_games_rejected")


def test_a_failed_check_on_the_first_run_leaves_no_staging():
    connection = FakeConnection(staging_exists=False, offenders=[("whtie", 2)])

    with pytest.raises(DataQualityFailure):
        run_in_snowflake(connection, "games.csv")

    assert ran(connection, "CREATE OR REPLACE TABLE stg_games_rejected CLONE stg_games")
    assert ran(connection, "DROP TABLE stg_games")
    assert not ran(connection, "stg_games CLONE stg_games_last_good")


# --- when the load fails ----------------------------------------------------


def test_a_failed_load_is_rolled_back_and_staging_is_untouched():
    connection = FakeConnection(fail_on="COPY INTO raw_games")

    with pytest.raises(RuntimeError):
        run_in_snowflake(connection, "games.csv")

    assert ran(connection, "ROLLBACK")
    assert not ran(connection, "COMMIT")
    assert not ran(connection, "CREATE OR REPLACE TABLE stg_games AS")


@pytest.mark.parametrize(
    "name", ["games'.csv", "games.csv; DROP TABLE raw_games", "", "a b.csv"]
)
def test_an_unsafe_file_name_is_refused_before_any_statement(name):
    connection = FakeConnection()

    with pytest.raises(ValueError):
        run_in_snowflake(connection, name)

    assert connection.statements == []


# --- the command ------------------------------------------------------------


def test_the_command_prints_the_summary_and_the_overall_rate(capsys):
    connection = FakeConnection()

    code = main(["games.csv"], env=ENV, connect=lambda **kwargs: connection)

    output = capsys.readouterr().out
    assert code == 0
    assert "1-99" in output
    assert "6 games" in output
    assert "33.3%" in output  # 2 of 6, from the counts
    assert connection.closed


def test_the_command_stops_on_a_bad_local_file_before_connecting(
    sample_path, tmp_path, capsys
):
    bad = tmp_path / "games.csv"
    bad.write_text(sample_path.read_text().replace("winner", "result"))
    connected = []

    code = main(
        ["games.csv", "--local-file", str(bad)],
        env=ENV,
        connect=lambda **kwargs: connected.append(kwargs),
    )

    assert code == 1
    assert connected == []
    assert "missing column 'winner'" in capsys.readouterr().err


def test_the_command_accepts_a_good_local_file(sample_path):
    connection = FakeConnection()

    code = main(
        ["games.csv", "--local-file", str(sample_path)],
        env=ENV,
        connect=lambda **kwargs: connection,
    )

    assert code == 0


def test_the_command_reports_a_failed_check_and_exits_non_zero(capsys):
    connection = FakeConnection(offenders=[("whtie", 2)])

    code = main(["games.csv"], env=ENV, connect=lambda **kwargs: connection)

    assert code == 1
    assert "whtie" in capsys.readouterr().err
    assert connection.closed


def test_the_command_names_missing_settings_and_does_not_connect(capsys):
    connected = []

    code = main(
        ["games.csv"],
        env={"SNOWFLAKE_ACCOUNT": "org-account"},
        connect=lambda **kwargs: connected.append(kwargs),
    )

    assert code == 1
    assert connected == []
    assert "SNOWFLAKE_USER" in capsys.readouterr().err


def test_the_load_uses_the_csv_file_format():
    connection = FakeConnection()

    run_in_snowflake(connection, "games.csv")

    copy = connection.statements[position(connection, "COPY INTO raw_games")]
    assert "FORMAT_NAME = capstone_csv" in copy
