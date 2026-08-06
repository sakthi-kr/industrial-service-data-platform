from scripts.update_operations_readme import insert_before_section, replace_section


def test_readme_section_helpers_are_idempotent() -> None:
    original = "# Project\n\n## Project status\nOld\n\n## Data and credentials\nSafe\n"
    updated = replace_section(original, "Project status", "New status")
    section = "## Operational controls\nControls\n"
    updated = insert_before_section(updated, "Data and credentials", section)
    repeated = insert_before_section(updated, "Data and credentials", section)

    assert "Old" not in updated
    assert "New status" in updated
    assert repeated.count("## Operational controls") == 1
