import pytest

from tests.agents.skills.renovation_seo_geo_import import load_permissions


permissions = load_permissions()


def test_live_mode_requires_env_confirm_backup_qa_changelog_and_rollback(tmp_path):
    ctx = permissions.PermissionContext(
        mode=permissions.SeoGeoMode.LIVE,
        root=tmp_path,
        allow_live_env=False,
        confirm_live=False,
        qa_passed=False,
    )
    with pytest.raises(permissions.SeoGeoPermissionError) as exc:
        permissions.validate_live_preconditions(ctx)
    message = str(exc.value)
    assert "SEO_GEO_ALLOW_LIVE=1" in message
    assert "--confirm-live" in message
    assert "backup created" in message
    assert "qa passed" in message


def test_live_mode_allows_when_all_gates_exist(tmp_path):
    backup = tmp_path / "backup"
    changelog = tmp_path / "changelog.md"
    rollback = tmp_path / "rollback.md"
    backup.mkdir()
    changelog.write_text("log", encoding="utf-8")
    rollback.write_text("rollback", encoding="utf-8")
    ctx = permissions.PermissionContext(
        mode=permissions.SeoGeoMode.LIVE,
        root=tmp_path,
        allow_live_env=True,
        confirm_live=True,
        qa_passed=True,
        backup_path=backup,
        changelog_path=changelog,
        rollback_plan_path=rollback,
    )
    permissions.validate_write_path("seo-workspace/reports/live.md", ctx)
