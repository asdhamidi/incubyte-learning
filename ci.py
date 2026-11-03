"""Cross-platform CI entry point (Windows, Mac, Linux). Run: python ci.py
Runs the same four checks as ci.sh, cheapest first."""

import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, check=False).returncode == 0


def fail(message):
    print(f"   FAILED: {message}")
    sys.exit(1)


print("1/4 no data or database files committed")
listing = subprocess.run(
    ["git", "ls-files"], check=False, capture_output=True, text=True
)
bad = [
    f for f in listing.stdout.splitlines() if re.search(r"\.(duckdb|db|parquet)$", f)
]
if bad:
    print("\n".join(bad))
    fail("data files must not be committed")

print("2/4 formatting")
if not run([sys.executable, "-m", "ruff", "format", "--check", ".", "-q"]):
    fail("run: python -m ruff format .")

print("3/4 lint")
if not run([sys.executable, "-m", "ruff", "check", ".", "-q"]):
    fail("run: python -m ruff check --fix .")

print("4/4 tests")
if not run([sys.executable, "-m", "pytest", "-q"]):
    fail("tests failed")

print("CI passed")
