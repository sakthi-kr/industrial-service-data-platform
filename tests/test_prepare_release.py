from pathlib import Path

from scripts.prepare_release import update_project_version


def test_update_project_version_changes_only_project_table(tmp_path: Path) -> None:
    path = tmp_path / "pyproject.toml"
    path.write_text(
        "\n".join(
            [
                "[build-system]",
                'requires = ["setuptools"]',
                "",
                "[project]",
                'name = "example"',
                'version = "0.1.0"',
                "",
                "[tool.example]",
                'version = "unchanged"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    update_project_version(path, "1.0.0")
    text = path.read_text(encoding="utf-8")

    assert 'version = "1.0.0"' in text
    assert 'version = "unchanged"' in text
    assert text.endswith("\n")
