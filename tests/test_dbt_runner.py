from pathlib import Path
from unittest.mock import Mock, patch

from pytest import MonkeyPatch

from scripts.run_dbt import main


def test_runner_requires_local_profile(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["parse"]) == 2


def test_runner_places_project_flags_after_command(
    monkeypatch: MonkeyPatch,
) -> None:
    completed = Mock(returncode=0)

    monkeypatch.setattr(Path, "exists", lambda self: True)

    with (
        patch("scripts.run_dbt.shutil.which", return_value="dbt"),
        patch(
            "scripts.run_dbt.load_env_file",
            return_value={"SNOWFLAKE_ACCOUNT": "example"},
        ),
        patch(
            "scripts.run_dbt.subprocess.run",
            return_value=completed,
        ) as run,
    ):
        assert main(["parse", "--no-partial-parse"]) == 0

    command = run.call_args.args[0]

    assert command == [
        "dbt",
        "parse",
        "--no-partial-parse",
        "--project-dir",
        "dbt",
        "--profiles-dir",
        "dbt",
    ]
