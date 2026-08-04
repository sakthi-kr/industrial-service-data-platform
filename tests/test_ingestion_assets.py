from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ingestion_configuration_and_documentation_exist() -> None:
    config = json.loads((ROOT / "config" / "ingestion.json").read_text(encoding="utf-8"))

    assert config["source_directory"] == "data/generated"
    assert config["batch_size"] == 1000
    assert config["connection_attempts"] == 3
    assert (ROOT / "docs" / "ingestion_pipeline.md").is_file()
    assert (ROOT / "docs" / "ingestion_setup.md").is_file()
    assert (ROOT / "docs" / "ingestion_verification.md").is_file()


def test_ingestion_sql_files_are_complete() -> None:
    directory = ROOT / "sql" / "ingestion"
    paths = sorted(directory.glob("*.sql"))

    assert [path.name for path in paths] == [
        "00_verify_ingestion.sql",
        "01_verify_idempotency.sql",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.endswith(";\n")
        assert "\t" not in text
        assert not any(line.endswith((" ", "\t")) for line in text.splitlines())
