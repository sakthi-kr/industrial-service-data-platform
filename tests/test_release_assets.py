import pytest

from scripts.validate_release_assets import checklist_state, main


def test_release_static_validation_passes() -> None:
    assert main() == 0


def test_checklist_state_accepts_pending_and_complete() -> None:
    pending = "\n".join("- [ ] item" for _ in range(13))
    complete = "\n".join("- [x] item" for _ in range(13))

    assert checklist_state(pending) == "pending"
    assert checklist_state(complete) == "complete"


def test_checklist_state_rejects_partial() -> None:
    partial = "\n".join(["- [x] item", *("- [ ] item" for _ in range(12))])
    with pytest.raises(RuntimeError, match="partially completed"):
        checklist_state(partial)
