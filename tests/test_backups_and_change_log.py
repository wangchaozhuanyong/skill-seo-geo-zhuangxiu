from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_backups, load_change_log


backups = load_backups()
change_log = load_change_log()


def test_create_file_backup_copies_file_and_manifest(tmp_path):
    source = tmp_path / "seo-workspace" / "reports" / "report.md"
    source.parent.mkdir(parents=True)
    source.write_text("report", encoding="utf-8")

    backup_dir = backups.create_file_backup(["seo-workspace/reports/report.md"], root=tmp_path)

    assert (backup_dir / "seo-workspace" / "reports" / "report.md").read_text(encoding="utf-8") == "report"
    assert (backup_dir / "manifest.json").exists()


def test_write_live_change_log_creates_report(tmp_path):
    path = change_log.write_live_change_log(
        changes=["Updated service page"],
        rollback_plan=["Restore backup"],
        root=tmp_path,
        status="verified",
    )

    text = Path(path).read_text(encoding="utf-8")
    assert "Updated service page" in text
    assert "Restore backup" in text
    assert "verified" in text
