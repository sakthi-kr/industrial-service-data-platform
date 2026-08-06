"""Prepare versioned public files for the first complete release."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("config/release.json")
PYPROJECT_PATH = Path("pyproject.toml")
CITATION_PATH = Path("CITATION.cff")


def load_release_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load release metadata."""
    return json.loads(path.read_text(encoding="utf-8"))


def update_project_version(path: Path, version: str) -> None:
    """Update only the version field inside the TOML project table."""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_project = False
    replacements = 0
    updated: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped == "[project]":
            in_project = True
            updated.append(line)
            continue

        if in_project and stripped.startswith("[") and stripped != "[project]":
            in_project = False

        if in_project and re.fullmatch(r'version\s*=\s*"[^"]+"', stripped):
            indent = line[: len(line) - len(line.lstrip())]
            updated.append(f'{indent}version = "{version}"')
            replacements += 1
            continue

        updated.append(line)

    if replacements != 1:
        raise RuntimeError(
            "Expected exactly one project version field, "
            f"found {replacements}. No changes were written."
        )

    path.write_text("\n".join(updated) + "\n", encoding="utf-8", newline="\n")


def validate_citation(path: Path, version: str, release_date: str) -> None:
    """Confirm the tracked citation metadata matches the release config."""
    text = path.read_text(encoding="utf-8")
    required = (
        f"version: {version}",
        f"date-released: {release_date}",
    )
    missing = [value for value in required if value not in text]
    if missing:
        raise RuntimeError(f"Citation metadata is incomplete: {missing}")


def main() -> int:
    """Prepare and validate version metadata."""
    config = load_release_config()
    version = str(config["version"])
    release_date = str(config["release_date"])

    update_project_version(PYPROJECT_PATH, version)
    validate_citation(CITATION_PATH, version, release_date)

    print(f"Release metadata prepared: version={version}, date={release_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
