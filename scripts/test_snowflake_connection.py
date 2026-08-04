"""Test the configured Snowflake connection without exposing secrets."""

from industrial_service_platform.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["test-snowflake"]))
