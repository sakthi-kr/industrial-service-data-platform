"""Validate the synthetic source datasets."""

import sys

from industrial_service_platform.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["validate-data", *sys.argv[1:]]))
