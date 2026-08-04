"""Discover CSV sources and separate valid records from rejected records."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from industrial_service_platform.generation.validation import (
    Row,
    Tables,
    ValidationIssue,
    validate_tables,
)
from industrial_service_platform.ingestion.models import (
    DatasetDefinition,
    PreparationResult,
    PreparedDataset,
    PreparedRecord,
    RejectedSourceRecord,
)

UTC = timezone.utc


class PreparationError(RuntimeError):
    """Raised when source discovery or validation cannot be completed safely."""


@dataclass(frozen=True)
class _IndexedRow:
    original_row_number: int
    values: Row


def load_source_catalogue(path: Path) -> tuple[dict[str, Any], tuple[DatasetDefinition, ...]]:
    """Load the source schema and convert dataset entries into typed definitions."""
    schema = json.loads(path.read_text(encoding="utf-8"))
    definitions: list[DatasetDefinition] = []

    for name, spec in schema["datasets"].items():
        raw_target = str(spec["raw_table"])
        raw_parts = raw_target.split(".")
        if len(raw_parts) != 2:
            raise PreparationError(f"Raw target must use SCHEMA.TABLE format: {raw_target}")
        definitions.append(
            DatasetDefinition(
                name=name,
                source_area=str(spec["source_area"]),
                file_name=str(spec["file_name"]),
                raw_schema=raw_parts[0],
                raw_table=raw_parts[1],
                business_key=tuple(str(value) for value in spec["business_key"]),
                field_names=tuple(str(field["name"]) for field in spec["fields"]),
            )
        )
    return schema, tuple(definitions)


def _read_csv(path: Path) -> list[_IndexedRow]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise PreparationError(f"Source file has no header: {path}")

        rows: list[_IndexedRow] = []
        for row_number, source_row in enumerate(reader, start=2):
            if None in source_row:
                raise PreparationError(
                    f"Source row has more values than header columns: {path}:{row_number}"
                )
            values: Row = {
                str(key): "" if value is None else str(value) for key, value in source_row.items()
            }
            rows.append(_IndexedRow(row_number, values))
        return rows


def _business_identifier(row: Row, key_fields: tuple[str, ...]) -> str:
    return "|".join(row.get(field, "") for field in key_fields)


def _record_hash(row: Row, field_names: tuple[str, ...]) -> str:
    canonical = json.dumps(
        {field: row.get(field, "") for field in field_names},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _issue_identity(issue: ValidationIssue) -> tuple[str, str, str]:
    return issue.field, issue.code, issue.message


def prepare_source_directory(
    source_directory: Path,
    schema_path: Path,
    selected_datasets: tuple[str, ...] | None = None,
) -> PreparationResult:
    """Validate all source files and prepare selected datasets for loading."""
    schema, definitions = load_source_catalogue(schema_path)
    definition_by_name = {definition.name: definition for definition in definitions}

    if selected_datasets is None:
        selected_names = tuple(definition.name for definition in definitions)
    else:
        unknown = sorted(set(selected_datasets) - set(definition_by_name))
        if unknown:
            raise PreparationError(f"Unknown dataset selection: {', '.join(unknown)}")
        selected_set = set(selected_datasets)
        selected_names = tuple(
            definition.name for definition in definitions if definition.name in selected_set
        )

    indexed_tables: dict[str, list[_IndexedRow]] = {}
    missing_files: list[str] = []
    for definition in definitions:
        source_path = source_directory / definition.file_name
        if not source_path.exists():
            missing_files.append(str(source_path))
            continue
        indexed_tables[definition.name] = _read_csv(source_path)

    if missing_files:
        raise PreparationError("Required source files are missing: " + ", ".join(missing_files))

    rejected_issues: dict[tuple[str, int], list[ValidationIssue]] = {}
    while True:
        current_indexed = {
            name: [
                indexed
                for indexed in rows
                if (name, indexed.original_row_number) not in rejected_issues
            ]
            for name, rows in indexed_tables.items()
        }
        current_tables: Tables = {
            name: [indexed.values for indexed in rows] for name, rows in current_indexed.items()
        }
        report = validate_tables(current_tables, schema)

        new_rejection_found = False
        for issue in report.issues:
            if issue.row_number < 2:
                raise PreparationError(
                    f"Dataset-level validation failed for {issue.dataset}: {issue.message}"
                )
            current_rows = current_indexed.get(issue.dataset, [])
            current_index = issue.row_number - 2
            if current_index >= len(current_rows):
                raise PreparationError(
                    f"Validation row mapping failed for {issue.dataset}:{issue.row_number}"
                )
            original_row_number = current_rows[current_index].original_row_number
            key = issue.dataset, original_row_number
            existing = rejected_issues.setdefault(key, [])
            identity = _issue_identity(issue)
            if all(_issue_identity(item) != identity for item in existing):
                existing.append(issue)
                new_rejection_found = True

        if not new_rejection_found:
            break

    prepared_datasets: list[PreparedDataset] = []
    for dataset_name in selected_names:
        definition = definition_by_name[dataset_name]
        accepted: list[PreparedRecord] = []
        rejected: list[RejectedSourceRecord] = []

        for indexed in indexed_tables[dataset_name]:
            key = dataset_name, indexed.original_row_number
            issues = tuple(
                sorted(
                    rejected_issues.get(key, []),
                    key=lambda item: (item.code, item.field, item.message),
                )
            )
            business_identifier = _business_identifier(
                indexed.values,
                definition.business_key,
            )
            if issues:
                rejected.append(
                    RejectedSourceRecord(
                        row_number=indexed.original_row_number,
                        values=indexed.values,
                        business_identifier=business_identifier,
                        issues=issues,
                    )
                )
            else:
                accepted.append(
                    PreparedRecord(
                        row_number=indexed.original_row_number,
                        values=indexed.values,
                        business_identifier=business_identifier,
                        record_hash=_record_hash(indexed.values, definition.field_names),
                    )
                )

        prepared_datasets.append(
            PreparedDataset(
                definition=definition,
                source_path=source_directory / definition.file_name,
                accepted=tuple(accepted),
                rejected=tuple(rejected),
            )
        )

    return PreparationResult(
        source_directory=source_directory,
        datasets=tuple(prepared_datasets),
        prepared_at=datetime.now(UTC),
    )
