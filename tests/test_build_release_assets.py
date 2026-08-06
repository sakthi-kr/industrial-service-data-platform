from pathlib import Path

from pytest import MonkeyPatch

from scripts.build_release_assets import build_assets


def write_bytes(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_build_release_assets_creates_expected_outputs(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    Path("config").mkdir()
    Path("config/release.json").write_text(
        """{
  "version": "1.0.0",
  "dashboard_pdf": "dashboards/power_bi/exports/industrial_service_dashboard.pdf"
}
""",
        encoding="utf-8",
    )
    Path("docs").mkdir()
    Path("docs/release_notes_v1.0.0.md").write_text(
        "# Notes\n",
        encoding="utf-8",
    )
    Path("docs/portfolio_summary.md").write_text(
        "# Portfolio\n",
        encoding="utf-8",
    )

    write_bytes(
        Path("dashboards/power_bi/exports/industrial_service_dashboard.pdf"),
        2_000,
    )
    write_bytes(
        Path("dashboards/power_bi/screenshots/service_operations_overview.png"),
        100,
    )
    write_bytes(
        Path("dashboards/power_bi/screenshots/asset_customer_analysis.png"),
        100,
    )
    Path("data/samples/note_enrichment").mkdir(parents=True)
    Path("data/samples/note_enrichment/evaluation_summary.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    Path("data/samples/note_enrichment/sample_predictions.csv").write_text(
        "note_id\n",
        encoding="utf-8",
    )
    Path("data/samples/operations").mkdir(parents=True)
    Path("data/samples/operations/health_summary.json").write_text(
        "{}\n",
        encoding="utf-8",
    )
    Path("data/samples/operations/recovery_drill_summary.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    pbix = tmp_path / "dashboard.pbix"
    write_bytes(pbix, 20_000)
    output = tmp_path / "release"

    outputs = build_assets(pbix, output)
    names = {path.name for path in outputs}

    assert names == {
        "industrial-service-dashboard-v1.0.0.pbix",
        "industrial-service-dashboard-v1.0.0.pdf",
        "industrial-service-platform-evidence-v1.0.0.zip",
        "RELEASE_NOTES.md",
        "SHA256SUMS.txt",
    }
    assert all(path.is_file() for path in outputs)
