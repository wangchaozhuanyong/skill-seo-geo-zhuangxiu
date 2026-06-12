import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_publish_candidate


content_studio_publish_candidate = load_content_studio_publish_candidate()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_latest_run(tmp_path: Path, *, include_draft: bool = True) -> None:
    target_url = "https://flashcast.com.my/en/services/kitchen"
    paired_url = "https://flashcast.com.my/zh/services/kitchen"
    draft = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    if include_draft:
        write(
            draft,
            "\n".join(
                [
                    "# Rich Content Package",
                    "",
                    f"- 目标页面: `{target_url}`",
                    f"- 配对页面: `{paired_url}`",
                    "- 页面类型: service",
                    "",
                    "## Publishing Field Map",
                    "",
                    "- content_en: Kitchen renovation design concept",
                    "- content_zh: 厨房装修设计方案",
                ]
            )
            + "\n",
        )
    write(
        tmp_path / "seo-workspace" / "data" / "content-studio-postrun-summary.json",
        json.dumps(
            {
                "status": "content_studio_postrun_ready_for_owner_review",
                "latest_run": {
                    "target_url": target_url,
                    "paired_url": paired_url,
                    "pipeline": "rich-content",
                    "content_status": "rich_content_package_waiting_owner_review",
                },
            },
            ensure_ascii=False,
        ),
    )
    write(
        tmp_path / "seo-workspace" / "data" / "content-studio-run.json",
        json.dumps(
            {
                "status": "rich_content_package_waiting_owner_review",
                "requested_target_url": target_url,
                "content_outputs": [str(draft)],
            },
            ensure_ascii=False,
        ),
    )


def test_content_studio_publish_candidate_selects_owner_review_row(tmp_path):
    seed_latest_run(tmp_path)

    summary, artifacts = content_studio_publish_candidate.run_content_studio_publish_candidate(tmp_path)

    assert summary["status"] == "content_studio_publish_candidate_waiting_owner_review"
    assert summary["target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert summary["candidate_row"]["target_kind"] == "service"
    assert summary["candidate_row"]["admin_helper"] == "saveAdminService"
    assert summary["candidate_row"]["status"] == "owner_review_required"
    assert summary["no_live_actions_executed"] is True
    assert summary["owner_review_required"] is True
    assert len(artifacts) == 5

    report = (tmp_path / "seo-workspace" / "reports" / f"{date.today().isoformat()}-content-studio-publish-candidate.md").read_text(encoding="utf-8")
    assert "等待业主审核和明确执行指令" in report
    assert "未调用 CMS / Supabase / admin helper" in report
    assert "未修改网站源码或线上页面" in report


def test_content_studio_publish_candidate_blocks_without_matching_draft(tmp_path):
    seed_latest_run(tmp_path, include_draft=False)

    summary, _ = content_studio_publish_candidate.run_content_studio_publish_candidate(tmp_path)

    assert summary["status"] == "content_studio_publish_candidate_blocked"
    assert any("No matching rich-content package" in blocker for blocker in summary["blockers"])
