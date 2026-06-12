import json
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import (
    load_automation_install_plan,
    load_automation_schedule,
)


automation_install_plan = load_automation_install_plan()
automation_schedule = load_automation_schedule()


def test_automation_install_plan_generates_no_install_handoff(tmp_path: Path):
    schedule_result, _ = automation_schedule.run_automation_schedule(tmp_path)
    assert schedule_result.status == "schedule_plan_ready_for_owner_review"

    summary, artifacts = automation_install_plan.run_automation_install_plan(tmp_path, install_kind="both")

    assert summary["status"] == "automation_install_plan_ready_for_owner_review"
    assert summary["no_schedule_installed"] is True
    assert summary["no_publish_executed"] is True
    assert summary["install_kind"] == "both"
    assert any(command["step"] == "install_launchd_macos" for command in summary["install_commands"])
    assert any(command["step"] == "install_cron_server" for command in summary["install_commands"])

    wrapper = tmp_path / "seo-workspace" / "tools" / "run-daily-seo-geo.sh"
    plist = tmp_path / "seo-workspace" / "config" / "com.flashcast.daily-seo-geo.plist"
    cron = tmp_path / "seo-workspace" / "config" / "daily-automation.install.cron"
    report = tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-automation-install-plan.md"
    summary_path = tmp_path / "seo-workspace" / "data" / "automation-install-plan.json"

    assert wrapper.exists()
    assert "seo_geo_cli.py" in wrapper.read_text(encoding="utf-8")
    assert plist.exists()
    assert str(wrapper) in plist.read_text(encoding="utf-8")
    assert cron.exists()
    assert str(wrapper) in cron.read_text(encoding="utf-8")
    assert "未安装 launchd/cron" in report.read_text(encoding="utf-8")
    assert json.loads(summary_path.read_text(encoding="utf-8"))["no_schedule_installed"] is True
    assert all(path.exists() for path in artifacts)


def test_automation_install_plan_blocks_without_schedule_plan(tmp_path: Path):
    summary, _ = automation_install_plan.run_automation_install_plan(tmp_path)

    assert summary["status"] == "automation_install_plan_blocked"
    assert any("Run automation-schedule first" in blocker for blocker in summary["blockers"])


def test_launchd_time_converts_target_timezone_to_host_local_time():
    schedule = {"time_local": "09:00", "timezone": "Asia/Kuala_Lumpur"}
    host_now = datetime(2026, 6, 11, 8, 0, tzinfo=timezone(timedelta(hours=-7)))

    hour, minute, note = automation_install_plan.local_launchd_time(schedule, host_now)

    assert (hour, minute) == (18, 0)
    assert "Asia/Kuala_Lumpur" in note
