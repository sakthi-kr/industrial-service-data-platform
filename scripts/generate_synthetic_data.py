"""Generate the Phase 2 synthetic source datasets."""

import sys

from industrial_service_platform.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["generate-data", *sys.argv[1:]]))
