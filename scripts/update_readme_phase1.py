from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"

STATUS_SECTION = """## Project status

Phase 1 is complete. The business context, source entities, field definitions,
relationships, KPI rules, and source-to-target mappings are now fixed and
validated.

The next stage is Phase 2: generating reproducible synthetic service data that
conforms to the source schema and includes controlled data-quality defects.

"""


def main() -> None:
    text = README_PATH.read_text(encoding="utf-8")

    start_marker = "## Project status\n"
    end_marker = "## Planned data flow\n"

    if start_marker not in text:
        raise RuntimeError("README.md does not contain the project-status heading.")
    if end_marker not in text:
        raise RuntimeError("README.md does not contain the planned-data-flow heading.")

    start = text.index(start_marker)
    end = text.index(end_marker, start)

    updated = text[:start] + STATUS_SECTION + text[end:]
    README_PATH.write_text(updated, encoding="utf-8")

    print("README project status updated to Phase 1 complete.")


if __name__ == "__main__":
    main()
