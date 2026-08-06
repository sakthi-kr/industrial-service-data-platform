import json
import re
from pathlib import Path


def test_public_docs_match_tag_only_distribution_choice() -> None:
    documents = {
        path: path.read_text(encoding="utf-8")
        for path in (
            Path("README.md"),
            Path("SECURITY.md"),
            Path("docs/final_verification.md"),
            Path("docs/release_notes_v1.0.0.md"),
        )
    }

    forbidden = (
        "distributed with the GitHub release",
        "ready for the `v1.0.0` release commit, tag and GitHub release",
        "latest published release",
    )

    failures = [
        f"{path}: {phrase}"
        for path, text in documents.items()
        for phrase in forbidden
        if phrase in text
    ]

    assert not failures
    assert "No GitHub Release is published" in documents[Path("README.md")]
    assert "annotated Git tag" in documents[Path("docs/release_notes_v1.0.0.md")]


def test_optional_asset_paths_are_portable() -> None:
    config = json.loads(Path("config/release.json").read_text(encoding="utf-8"))
    drive_path = re.compile(r"^[A-Za-z]:[/\\]")

    for key in ("external_asset_directory", "power_bi_source"):
        value = str(config[key])
        assert not drive_path.match(value)
        assert not value.startswith(("/", "\\"))
