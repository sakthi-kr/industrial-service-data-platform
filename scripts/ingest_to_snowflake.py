"""Run the configured CSV-to-Snowflake ingestion pipeline."""

from industrial_service_platform.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["ingest"]))
