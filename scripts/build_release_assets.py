"""Build optional local distribution assets without committing binary files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("config/release.json")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load version and local distribution settings."""
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    """Calculate a file SHA-256 checksum."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, minimum_size: int) -> None:
    """Require a local source file with a plausible minimum size."""
    if not path.is_file():
        raise RuntimeError(f"Required distribution source is missing: {path}")
    size = path.stat().st_size
    if size < minimum_size:
        raise RuntimeError(f"Distribution source is unexpectedly small: {path} ({size} bytes)")


def build_assets(pbix_source: Path, output_directory: Path) -> list[Path]:
    """Create optional local PBIX, PDF, evidence and checksum outputs."""
    config = load_config()
    version = str(config["version"])
    pdf_source = Path(str(config["dashboard_pdf"]))
    require_file(pbix_source, 10_000)
    require_file(pdf_source, 1_000)

    output_directory.mkdir(parents=True, exist_ok=True)
    pbix_output = output_directory / f"industrial-service-dashboard-v{version}.pbix"
    pdf_output = output_directory / f"industrial-service-dashboard-v{version}.pdf"
    notes_output = output_directory / "VERSION_NOTES.md"
    evidence_output = output_directory / f"industrial-service-platform-evidence-v{version}.zip"

    shutil.copy2(pbix_source, pbix_output)
    shutil.copy2(pdf_source, pdf_output)
    shutil.copy2(Path(f"docs/release_notes_v{version}.md"), notes_output)

    evidence_sources = [
        Path("dashboards/power_bi/screenshots/service_operations_overview.png"),
        Path("dashboards/power_bi/screenshots/asset_customer_analysis.png"),
        Path("data/samples/note_enrichment/evaluation_summary.json"),
        Path("data/samples/note_enrichment/sample_predictions.csv"),
        Path("data/samples/operations/health_summary.json"),
        Path("data/samples/operations/recovery_drill_summary.json"),
        Path("docs/portfolio_summary.md"),
    ]
    missing = [str(path) for path in evidence_sources if not path.is_file()]
    if missing:
        raise RuntimeError(f"Evidence sources are missing: {missing}")

    with zipfile.ZipFile(
        evidence_output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for source in evidence_sources:
            archive.write(source, arcname=source.as_posix())

    outputs = [pbix_output, pdf_output, evidence_output, notes_output]
    checksum_path = output_directory / "SHA256SUMS.txt"
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in outputs),
        encoding="utf-8",
        newline="\n",
    )
    outputs.append(checksum_path)
    return outputs


def parse_args() -> argparse.Namespace:
    """Read optional portable local paths from arguments or configuration."""
    config = load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pbix",
        type=Path,
        default=Path(str(config["power_bi_source"])),
        help="Path to the local Power BI working file.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path(str(config["external_asset_directory"])),
        help="Ignored local directory for optional distribution assets.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs = build_assets(args.pbix, args.output_directory)
    print("Optional distribution assets created:")
    for path in outputs:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
