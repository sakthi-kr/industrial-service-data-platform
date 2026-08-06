"""Publish evaluated note-enrichment outputs to Snowflake."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from industrial_service_platform.enrichment.config import EnrichmentConfig
from industrial_service_platform.enrichment.snowflake_repository import publish_predictions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/note_enrichment.json"),
    )
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    config = EnrichmentConfig.from_json(args.config)
    result = publish_predictions(config, env_file=args.env_file)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
