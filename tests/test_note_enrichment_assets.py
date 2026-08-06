from pathlib import Path

from scripts.validate_note_enrichment_assets import checklist_state, main


def test_note_enrichment_static_assets_pass() -> None:
    assert main() == 0


def test_checklist_state_accepts_only_pending_or_complete() -> None:
    assert checklist_state("- [ ] item\n" * 17) == "pending"
    assert checklist_state("- [x] item\n" * 17) == "complete"


def test_public_sample_directory_is_tracked_location() -> None:
    config = Path("config/note_enrichment.json").read_text(encoding="utf-8")
    assert '"public_sample_directory": "data/samples/note_enrichment"' in config
