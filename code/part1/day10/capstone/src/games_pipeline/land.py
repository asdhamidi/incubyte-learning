"""Land a games file in Azure Blob Storage.

The file is checked against the contract first, so a file that breaks it never
reaches Blob Storage. The upload itself is the Azure CLI (`az storage blob upload`),
signed in with `az login`.

    python -m games_pipeline.land sample_data/games_sample.tsv --account <storage-account> --container capstone
"""

import argparse
import shutil
import subprocess
from pathlib import Path

from .contract import assert_contract


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
    assert_contract(path)
    command = build_upload_command(path, account, container, folder, overwrite)
    command[0] = shutil.which("az") or "az"
    run(command, check=True)
    return blob_name(path, folder)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a games file and upload it.")
    parser.add_argument("file")
    parser.add_argument("--account", required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--folder", default="games")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    blob = land(args.file, args.account, args.container, args.folder, args.overwrite)
    print(f"uploaded {blob}")


if __name__ == "__main__":
    main()
