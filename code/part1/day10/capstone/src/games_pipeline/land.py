"""Land a games file in Azure Blob Storage.

The file is checked against the contract first, so a file that breaks it never
reaches Blob Storage. The upload itself is the Azure CLI (`az storage blob upload`),
signed in with `az login`.

    python -m games_pipeline.land sample_data/games_sample.csv --account <storage-account> --container capstone
"""

import argparse
import logging
import shutil
import subprocess
from pathlib import Path

from .contract import assert_contract
from .log import configure_logging, step

log = logging.getLogger(__name__)


def blob_name(path, folder="games"):
    return f"{folder.strip('/')}/{Path(path).name}"


def build_upload_command(path, account, container, folder="games", overwrite=False):
    command = [
        "az",
        "storage",
        "blob",
        "upload",
        "--account-name",
        account,
        "--container-name",
        container,
        "--name",
        blob_name(path, folder),
        "--file",
        str(path),
        "--auth-mode",
        "login",
    ]
    if overwrite:
        command.append("--overwrite")
    return command


def land(path, account, container, folder="games", overwrite=False, run=subprocess.run):
    """Check the contract, then upload. Returns the blob name."""
    with step(log, f"check {path} against the contract"):
        assert_contract(path)
    command = build_upload_command(path, account, container, folder, overwrite)
    command[0] = shutil.which("az") or "az"
    with step(log, f"upload to {account}/{container}/{blob_name(path, folder)}"):
        run(command, check=True)
    return blob_name(path, folder)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a games file and upload it.")
    parser.add_argument("file")
    parser.add_argument("--account", required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--folder", default="games")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    blob = land(args.file, args.account, args.container, args.folder, args.overwrite)
    print(f"uploaded {blob}")


if __name__ == "__main__":
    main()
