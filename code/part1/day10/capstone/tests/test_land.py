import pytest
from games_pipeline.contract import ContractViolation
from games_pipeline.land import build_upload_command, land


class FakeRunner:
    """Stands in for subprocess.run so no cloud call is made."""

    def __init__(self):
        self.calls = []

    def __call__(self, command, check):
        self.calls.append((command, check))


def test_the_upload_command_targets_the_account_container_and_blob(sample_path):
    command = build_upload_command(sample_path, "stlearn", "capstone", "games")

    assert command == [
        "az",
        "storage",
        "blob",
        "upload",
        "--account-name",
        "stlearn",
        "--container-name",
        "capstone",
        "--name",
        "games/games_sample.tsv",
        "--file",
        str(sample_path),
        "--auth-mode",
        "login",
    ]


def test_overwrite_is_only_added_when_asked_for(sample_path):
    plain = build_upload_command(sample_path, "stlearn", "capstone", "games")
    overwrite = build_upload_command(
        sample_path, "stlearn", "capstone", "games", overwrite=True
    )

    assert "--overwrite" not in plain
    assert overwrite[-1] == "--overwrite"


def test_a_trailing_slash_on_the_folder_is_ignored(sample_path):
    command = build_upload_command(sample_path, "stlearn", "capstone", "games/")

    assert "games/games_sample.tsv" in command


def test_a_valid_file_is_uploaded_once_and_the_blob_name_returned(sample_path):
    runner = FakeRunner()

    blob = land(sample_path, "stlearn", "capstone", run=runner)

    assert blob == "games/games_sample.tsv"
    assert len(runner.calls) == 1
    command, check = runner.calls[0]
    assert command[1:4] == ["storage", "blob", "upload"]
    assert check is True


def test_a_file_that_breaks_the_contract_is_never_uploaded(sample_path, tmp_path):
    bad = tmp_path / "games.tsv"
    bad.write_text(sample_path.read_text().replace("winner", "result"))
    runner = FakeRunner()

    with pytest.raises(ContractViolation):
        land(bad, "stlearn", "capstone", run=runner)

    assert runner.calls == []
