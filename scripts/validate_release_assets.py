"""Validate public documentation, version metadata and repository hygiene."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Iterable
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

ROOT = Path(".")
CONFIG_PATH = ROOT / "config/release.json"
CHECKLIST_PATH = ROOT / "docs/final_verification.md"
EXPECTED_CHECKS = 13
TEXT_SUFFIXES = {
    ".cff",
    ".csv",
    ".dax",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
FORBIDDEN_TRACKED_PATHS = {
    ".env",
    "BUNDLE_MANIFEST.txt",
    "dbt/.gitkeep",
    "dbt/.user.yml",
    "dbt/profiles.yml",
    "resolution_due_at",
    "t",
}
FORBIDDEN_PATH_PREFIXES = (
    "data/generated/",
    "dbt/logs/",
    "dbt/target/",
)
REQUIRED_FILES = (
    Path("README.md"),
    Path("CHANGELOG.md"),
    Path("CITATION.cff"),
    Path("CONTRIBUTING.md"),
    Path("SECURITY.md"),
    Path("LICENSE"),
    Path("docs/architecture.md"),
    Path("docs/reproducibility.md"),
    Path("docs/portfolio_summary.md"),
    Path("docs/release_notes_v1.0.0.md"),
    Path("docs/final_verification.md"),
    Path("dashboards/power_bi/screenshots/service_operations_overview.png"),
    Path("dashboards/power_bi/screenshots/asset_customer_analysis.png"),
    Path("dashboards/power_bi/exports/industrial_service_dashboard.pdf"),
)


def load_config(path: Path = CONFIG_PATH) -> dict[str, object]:
    """Load version metadata and optional local asset settings."""
    return json.loads(path.read_text(encoding="utf-8"))


def tracked_files() -> list[Path]:
    """Return Git-tracked files, falling back to repository files in tests."""
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if completed.returncode == 0 and completed.stdout:
        return [Path(value.decode("utf-8")) for value in completed.stdout.split(b"\0") if value]

    return sorted(
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )


def checklist_state(text: str) -> str:
    """Return pending or complete while rejecting partial checklists."""
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")
    total = unchecked + checked

    if total != EXPECTED_CHECKS:
        raise RuntimeError(f"Expected {EXPECTED_CHECKS} version checks, found {total}")
    if unchecked == EXPECTED_CHECKS:
        return "pending"
    if checked == EXPECTED_CHECKS:
        return "complete"

    raise RuntimeError(
        f"Final version checklist is partially completed: checked={checked}, unchecked={unchecked}"
    )


def check_required_files() -> None:
    missing = [str(path) for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing final version files: {missing}")


def check_versions(config: dict[str, object]) -> None:
    version = str(config["version"])
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    actual = str(project["project"]["version"])
    if actual != version:
        raise RuntimeError(f"Project version mismatch: expected={version}, actual={actual}")

    citation = Path("CITATION.cff").read_text(encoding="utf-8")
    required = (
        f"version: {version}",
        f"date-released: {config['release_date']}",
    )
    missing = [value for value in required if value not in citation]
    if missing:
        raise RuntimeError(f"Citation metadata mismatch: {missing}")


def check_readme() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    required = (
        "107,724",
        "12 operational KPIs",
        "5,000 technician notes",
        "docs/architecture.md",
        "docs/reproducibility.md",
        "service_operations_overview.png",
        "asset_customer_analysis.png",
        "v1.0.0",
        "No GitHub Release is published",
    )
    missing = [value for value in required if value not in text]
    if missing:
        raise RuntimeError(f"README is missing version evidence: {missing}")

    forbidden = (
        "## Planned scope",
        "## Planned data flow",
        "The remaining work is",
        "The finished project will include",
        "distributed with the GitHub release",
    )
    found = [value for value in forbidden if value in text]
    if found:
        raise RuntimeError(f"README contains outdated wording: {found}")


def check_publication_consistency(config: dict[str, object]) -> None:
    """Reject claims that a GitHub Release exists and machine-specific paths."""
    files = (
        Path("README.md"),
        Path("SECURITY.md"),
        Path("docs/final_verification.md"),
        Path("docs/release_notes_v1.0.0.md"),
    )
    forbidden = (
        "distributed with the GitHub release",
        "ready for the `v1.0.0` release commit, tag and GitHub release",
        "latest published release",
    )

    failures: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            if phrase in text:
                failures.append(f"{path}: {phrase}")

    drive_path = re.compile(r"^[A-Za-z]:[/\\]")
    for key in ("external_asset_directory", "power_bi_source"):
        value = str(config[key])
        if drive_path.match(value) or value.startswith(("/", "\\")):
            failures.append(f"config/release.json: non-portable {key}={value}")

    if failures:
        raise RuntimeError(f"Version-publication inconsistencies: {failures}")


def check_public_planning_labels(files: Iterable[Path]) -> None:
    word = "ph" + "ase"
    pattern = re.compile(rf"{word}[ _-]*[0-9]+", re.IGNORECASE)
    failures: list[str] = []

    for path in files:
        posix = path.as_posix()
        if pattern.search(posix):
            failures.append(posix)
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            failures.append(posix)

    if failures:
        raise RuntimeError(f"Numbered planning labels found: {failures}")


def check_repository_hygiene(files: list[Path]) -> None:
    names = {path.as_posix() for path in files}
    forbidden = sorted(FORBIDDEN_TRACKED_PATHS & names)
    forbidden.extend(
        name
        for name in sorted(names)
        if name.lower().endswith(".pbix")
        or any(name.startswith(prefix) for prefix in FORBIDDEN_PATH_PREFIXES)
    )
    if forbidden:
        raise RuntimeError(f"Private or generated files are tracked: {forbidden}")

    secret_failures: list[str] = []
    private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
    password_prefix = "SNOWFLAKE_" + "PASSWORD="

    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if private_key_marker in text:
            secret_failures.append(path.as_posix())
        for line in text.splitlines():
            if line.startswith(password_prefix):
                value = line.partition("=")[2].strip()
                if value and value.lower() not in {
                    "your_snowflake_password",
                    "your-password",
                }:
                    secret_failures.append(path.as_posix())
                    break

    if secret_failures:
        raise RuntimeError(
            f"Possible credentials found in tracked files: {sorted(set(secret_failures))}"
        )


def check_text_quality(files: Iterable[Path]) -> None:
    failures: list[str] = []
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not text.endswith("\n"):
            failures.append(f"missing newline: {path}")
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            failures.append(f"trailing whitespace: {path}")

    if failures:
        raise RuntimeError(f"Text-quality failures: {failures}")


def main() -> int:
    """Run the final repository and version audit."""
    config = load_config()
    check_required_files()
    check_versions(config)
    check_readme()
    check_publication_consistency(config)

    files = tracked_files()
    check_repository_hygiene(files)
    check_public_planning_labels(files)
    check_text_quality(files)
    state = checklist_state(CHECKLIST_PATH.read_text(encoding="utf-8"))

    print(
        "Repository version validation passed: "
        f"version={config['version']}, tracked_files={len(files)}, state={state}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
