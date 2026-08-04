"""Run dbt with the repository project, local profile, and ignored .env settings."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from industrial_service_platform.ingestion.config import load_env_file

PROJECT_DIR = Path("dbt")
PROFILE_PATH = PROJECT_DIR / "profiles.yml"
PROFILE_EXAMPLE_PATH = PROJECT_DIR / "profiles.example.yml"


def main(arguments: list[str] | None = None) -> int:
    """Load local settings and forward arguments to the dbt executable."""
    command_arguments = sys.argv[1:] if arguments is None else arguments

    if not command_arguments:
        print(
            "Usage: python scripts/run_dbt.py <dbt command> [options]",
            file=sys.stderr,
        )
        return 2

    if not PROFILE_PATH.exists():
        print(
            "dbt/profiles.yml is missing. Copy dbt/profiles.example.yml first.",
            file=sys.stderr,
        )
        return 2

    dbt_executable = shutil.which("dbt")
    if dbt_executable is None:
        print(
            'dbt is not installed. Run: python -m pip install -e ".[dev]"',
            file=sys.stderr,
        )
        return 2

    environment = os.environ.copy()

    for key, value in load_env_file(Path(".env")).items():
        environment.setdefault(key, value)

    command = [
        dbt_executable,
        *command_arguments,
        "--project-dir",
        str(PROJECT_DIR),
        "--profiles-dir",
        str(PROJECT_DIR),
    ]

    completed = subprocess.run(
        command,
        env=environment,
        check=False,
    )

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
