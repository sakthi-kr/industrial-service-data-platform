"""Train and evaluate the technician-note enrichment model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from industrial_service_platform.enrichment.config import EnrichmentConfig
from industrial_service_platform.enrichment.pipeline import train_and_evaluate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/note_enrichment.json"),
    )
    args = parser.parse_args()
    config = EnrichmentConfig.from_json(args.config)
    evaluation = train_and_evaluate(config)
    print(json.dumps(evaluation, indent=2, sort_keys=True))
    return 0 if evaluation["all_thresholds_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
