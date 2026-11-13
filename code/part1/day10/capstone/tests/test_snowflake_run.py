import subprocess

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
        if statement.startswith("SELECT COUNT(*) FROM"):
            return [(7,)]
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


# --- logging ----------------------------------------------------------------


def test_a_clean_run_logs_each_step_in_order(caplog):
    caplog.set_level("INFO")
    run_in_snowflake(FakeConnection(), "games.csv")
    text = "\n".join(record.getMessage() for record in caplog.records)
    steps = [
        "load games/games.csv into raw_games",
        "raw_games now holds 7 rows",
        "first run: no staging yet",
        "build stg_games done",
        "data quality check winner_accepted_values passed",
        "build games_summary done",
        "summary has 2 bands",
    ]
    positions = [text.index(s) for s in steps]
    assert positions == sorted(positions)


def test_a_failed_check_is_logged_as_an_error_with_the_restore(caplog):
    caplog.set_level("INFO")
    with pytest.raises(DataQualityFailure):
        run_in_snowflake(
            FakeConnection(staging_exists=True, offenders=[("whtie", 2)]), "games.csv"
        )
    errors = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    warnings = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert any("FAILED" in message for message in errors)
    assert any("last good version" in message for message in warnings)


def test_the_password_is_never_logged(caplog):
    caplog.set_level("DEBUG")
    env = {**ENV, "SNOWFLAKE_PASSWORD": "s3cret-value"}
    connect_from_env(env, connect=lambda **settings: FakeConnection())
    assert "s3cret-value" not in caplog.text
    assert "org-account" in caplog.text


# --- uploading to Blob Storage first ----------------------------------------


class FakeUpload:
    """Stands in for `land`: records what it was asked to upload."""

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, path, account, container, folder="games", overwrite=False):
        self.calls.append((str(path), account, container, folder, overwrite))
        if self.fail:
            raise subprocess.CalledProcessError(1, "az", stderr="the upload failed")
        return f"{folder}/{path.name if hasattr(path, 'name') else path}"


def test_the_command_uploads_the_local_file_before_it_connects(sample_path):
    order = []
    upload = FakeUpload()

    def tracked_upload(*args, **kwargs):
        order.append("upload")
        return upload(*args, **kwargs)

    def connect(**kwargs):
        order.append("connect")
        return FakeConnection()

    code = main(
        ["--local-file", str(sample_path), "--storage-account", "stacct"],
        env=ENV,
        connect=connect,
        upload=tracked_upload,
    )

    assert code == 0
    assert order == ["upload", "connect"]
    # the folder and container default to the ones the stage reads, and a re-run replaces the blob
    assert upload.calls == [(str(sample_path), "stacct", "capstone", "games", True)]


def test_the_file_name_in_the_stage_defaults_to_the_local_files_name(sample_path):
    connection = FakeConnection()

    main(
        ["--local-file", str(sample_path), "--storage-account", "stacct"],
        env=ENV,
        connect=lambda **kwargs: connection,
        upload=FakeUpload(),
    )

    copy = connection.statements[position(connection, "COPY INTO raw_games")]
    assert f"FILES = ('{sample_path.name}')" in copy


def test_a_bad_local_file_is_never_uploaded(sample_path, tmp_path, capsys):
    bad = tmp_path / "games.csv"
    bad.write_text(sample_path.read_text().replace("winner", "result"))
    upload = FakeUpload()

    code = main(
        ["--local-file", str(bad), "--storage-account", "stacct"],
        env=ENV,
        connect=lambda **kwargs: FakeConnection(),
        upload=upload,
    )

    assert code == 1
    assert upload.calls == []


def test_a_failed_upload_stops_the_run_before_connecting(sample_path, capsys):
    connected = []

    code = main(
        ["--local-file", str(sample_path), "--storage-account", "stacct"],
        env=ENV,
        connect=lambda **kwargs: connected.append(kwargs),
        upload=FakeUpload(fail=True),
    )

    assert code == 1
    assert connected == []
    assert "upload failed" in capsys.readouterr().err  # our own prefix


def test_without_a_storage_account_nothing_is_uploaded(sample_path):
    upload = FakeUpload()

    main(
        ["games.csv", "--local-file", str(sample_path)],
        env=ENV,
        connect=lambda **kwargs: FakeConnection(),
        upload=upload,
    )

    assert upload.calls == []


def test_the_storage_account_can_come_from_the_environment(sample_path):
    upload = FakeUpload()

    main(
        ["--local-file", str(sample_path)],
        env={**ENV, "AZURE_STORAGE_ACCOUNT": "fromenv"},
        connect=lambda **kwargs: FakeConnection(),
        upload=upload,
    )

    assert upload.calls[0][1] == "fromenv"


def test_the_command_needs_a_file_name_or_a_local_file(capsys):
    code = main([], env=ENV, connect=lambda **kwargs: FakeConnection())

    assert code == 1
    assert "stage_file or --local-file" in capsys.readouterr().err


# --- the one-time setup is part of the run ----------------------------------

STAGE_URL = "azure://stacct.blob.core.windows.net/capstone/games/"


def test_the_run_creates_the_file_format_before_loading():
    connection = FakeConnection()

    run_in_snowflake(connection, "games.csv")

    create = connection.statements[
        position(connection, "CREATE OR REPLACE FILE FORMAT")
    ]
    assert "capstone_csv" in create
    assert "FIELD_DELIMITER = ','" in create
    assert "PARSE_HEADER = TRUE" in create
    assert position(connection, "CREATE OR REPLACE FILE FORMAT") < position(
        connection, "COPY INTO"
    )


def test_the_run_creates_the_stage_when_it_knows_where_the_blob_is():
    connection = FakeConnection()

    run_in_snowflake(connection, "games.csv", stage_url=STAGE_URL)

    create = connection.statements[position(connection, "CREATE OR REPLACE STAGE")]
    assert f"URL = '{STAGE_URL}'" in create
    assert "STORAGE_INTEGRATION = azure_int" in create
    assert position(connection, "CREATE OR REPLACE STAGE") < position(
        connection, "COPY INTO"
    )


def test_without_a_blob_location_the_existing_stage_is_left_alone():
    connection = FakeConnection()

    run_in_snowflake(connection, "games.csv")

    assert not ran(connection, "CREATE OR REPLACE STAGE")


@pytest.mark.parametrize(
    "url",
    [
        "azure://bad account.blob.core.windows.net/capstone/games/",
        "https://stacct.blob.core.windows.net/capstone/games/",
        "azure://stacct.blob.core.windows.net/capstone/games/'; DROP TABLE x; --",
    ],
)
def test_an_unexpected_stage_url_is_refused_before_any_statement(url):
    connection = FakeConnection()

    with pytest.raises(ValueError):
        run_in_snowflake(connection, "games.csv", stage_url=url)

    assert connection.statements == []


def test_the_command_points_the_stage_at_the_uploaded_blob(sample_path):
    connection = FakeConnection()

    main(
        ["--local-file", str(sample_path), "--storage-account", "stacct"],
        env=ENV,
        connect=lambda **kwargs: connection,
        upload=FakeUpload(),
    )

    create = connection.statements[position(connection, "CREATE OR REPLACE STAGE")]
    assert f"URL = '{STAGE_URL}'" in create


def test_the_setup_is_logged(caplog):
    caplog.set_level("INFO")

    run_in_snowflake(FakeConnection(), "games.csv", stage_url=STAGE_URL)

    assert "file format capstone_csv ready" in caplog.text
    assert "stage capstone_stage points at" in caplog.text
