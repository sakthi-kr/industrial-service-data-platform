"""Validate operational, recovery, security, and CI assets without live credentials."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".")
CONFIG_PATH = ROOT / "config/operational_health.json"
VERIFICATION_PATH = ROOT / "docs/operational_verification.md"
EXPECTED_CHECKLIST_ITEMS = 20
EXPECTED_RELATIONS = 17

REQUIRED_FILES = (
    CONFIG_PATH,
    ROOT / "SECURITY.md",
    ROOT / ".github/dependabot.yml",
    ROOT / ".github/workflows/ci.yml",
    ROOT / ".github/workflows/codeql.yml",
    ROOT / ".github/workflows/dependency-review.yml",
    ROOT / "docs/operations_runbook.md",
    ROOT / "docs/recovery_procedures.md",
    ROOT / "docs/security_and_cost_controls.md",
    VERIFICATION_PATH,
    ROOT / "scripts/check_platform_health.py",
    ROOT / "scripts/run_recovery_drills.py",
    ROOT / "scripts/complete_operational_verification.py",
    ROOT / "sql/operations/00_create_monitoring_views.sql",
    ROOT / "sql/operations/01_verify_monitoring_views.sql",
    ROOT / "sql/operations/02_verify_platform_counts.sql",
    ROOT / "sql/operations/03_verify_cost_controls.sql",
    ROOT / "sql/operations/04_verify_query_failures.sql",
    ROOT / "sql/operations/05_transaction_rollback_drill.sql",
)


def checklist_state(text: str) -> str:
    """Accept only an entirely pending or entirely completed checklist."""
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")
    total = unchecked + checked
    if total != EXPECTED_CHECKLIST_ITEMS:
        raise RuntimeError(f"Expected {EXPECTED_CHECKLIST_ITEMS} operational checks, found {total}")
    if unchecked == EXPECTED_CHECKLIST_ITEMS:
        return "pending"
    if checked == EXPECTED_CHECKLIST_ITEMS:
        return "complete"
    raise RuntimeError(
        f"Operational checklist is partially completed: checked={checked}, unchecked={unchecked}"
    )


def main() -> int:
    """Validate tracked operational assets and workflow wiring."""
    missing = [str(path) for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing operational assets: {missing}")
    if (ROOT / "BUNDLE_MANIFEST.txt").exists():
        raise RuntimeError("Root BUNDLE_MANIFEST.txt must not be committed")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    relations = config.get("relations")
    if not isinstance(relations, list) or len(relations) != EXPECTED_RELATIONS:
        raise RuntimeError(f"Expected {EXPECTED_RELATIONS} operational relation checks")
    relation_names = [str(item["relation"]) for item in relations]
    if len(relation_names) != len(set(relation_names)):
        raise RuntimeError("Operational relation checks contain duplicates")

    ci_text = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    required_ci_fragments = (
        'python -m mypy --python-version "${{ matrix.python-version }}" src',
        "python -m pip check",
        "python scripts/run_recovery_drills.py",
        "python scripts/validate_operational_assets.py",
    )
    for fragment in required_ci_fragments:
        if fragment not in ci_text:
            raise RuntimeError(f"CI workflow is missing: {fragment}")

    codeql = (ROOT / ".github/workflows/codeql.yml").read_text(encoding="utf-8")
    if "github/codeql-action/init@v4" not in codeql:
        raise RuntimeError("CodeQL workflow must use the current v4 action")
    if "security-extended" not in codeql:
        raise RuntimeError("CodeQL workflow must use the security-extended suite")

    dependency_review = (ROOT / ".github/workflows/dependency-review.yml").read_text(
        encoding="utf-8"
    )
    if "actions/dependency-review-action@v5" not in dependency_review:
        raise RuntimeError("Dependency review workflow must use v5")
    if "fail-on-severity: high" not in dependency_review:
        raise RuntimeError("Dependency review must reject new high-severity findings")

    dependabot = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
    for ecosystem in ("pip", "github-actions"):
        if f'package-ecosystem: "{ecosystem}"' not in dependabot:
            raise RuntimeError(f"Dependabot does not cover {ecosystem}")

    verification_text = VERIFICATION_PATH.read_text(encoding="utf-8")
    state = checklist_state(verification_text)
    if state == "complete":
        for path in (
            ROOT / "data/samples/operations/health_summary.json",
            ROOT / "data/samples/operations/recovery_drill_summary.json",
        ):
            if not path.is_file():
                raise RuntimeError(f"Completed verification is missing {path}")
        if "## Deployment result" not in verification_text:
            raise RuntimeError("Completed verification is missing a deployment result")

    for path in REQUIRED_FILES:
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            raise RuntimeError(f"File does not end with a newline: {path}")
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            raise RuntimeError(f"Trailing whitespace found in {path}")

    print(
        "Operational asset validation passed: "
        f"relations={EXPECTED_RELATIONS}, checks={EXPECTED_CHECKLIST_ITEMS}, state={state}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
