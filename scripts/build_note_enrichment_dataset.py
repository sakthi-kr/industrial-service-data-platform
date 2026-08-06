"""Build the generated labelled technician-note dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from industrial_service_platform.enrichment.config import EnrichmentConfig
from industrial_service_platform.enrichment.dataset import build_labeled_notes, write_labeled_notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/note_enrichment.json"),
    )
    args = parser.parse_args()
    config = EnrichmentConfig.from_json(args.config)
    examples = build_labeled_notes(config.source_directory)
    write_labeled_notes(config.labeled_dataset_path, examples)
    print(
        "Labelled technician-note dataset written: "
        f"{len(examples)} rows to {config.labeled_dataset_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
