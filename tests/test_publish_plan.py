import csv
import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_plan


publish_plan = load_publish_plan()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_publish_plan_workspace(tmp_path: Path) -> None:
    draft_path = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    write(
        draft_path,
        "\n".join(
            [
                "# Rich Content Package",
                "",
                "- 目标页面: `https://flashcast.com.my/en/services/kitchen`",
                "- 配对页面: `https://flashcast.com.my/zh/services/kitchen`",
                "- 页面类型: service",
                "",
                "## 图文内容块 / Image-Rich Blocks",
                "",
                "- 概念设计: 厨房动线规划效果图方案",
                "- design concept / rendering concept: kitchen workflow visual",
                "",
                "## Publishing Field Map",
                "",
                "- content_en: Kitchen renovation design concept",
                "- content_zh: 厨房装修设计方案",
            ]
        )
        + "\n",
    )
    queue_path = tmp_path / "seo-workspace" / "data" / "approved-publish-queue.csv"
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "draft_path",
                "target_url",
                "paired_url",
                "page_type",
                "target_kind",
                "table",
                "admin_helper",
                "status",
                "language_scope",
                "rich_text_ready",
                "image_strategy",
                "required_gate",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "draft_path": draft_path.relative_to(tmp_path).as_posix(),
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "paired_url": "https://flashcast.com.my/zh/services/kitchen",
                "page_type": "service",
                "target_kind": "service",
                "table": "services",
                "admin_helper": "saveAdminService",
                "status": "owner_review_required",
                "language_scope": "bilingual_pair_required",
                "rich_text_ready": "yes: package contains Publishing Field Map",
                "image_strategy": "primary image_url plus HTML/media image blocks if supported; concept labels required",
                "required_gate": "owner approval + explicit execution + QA pass + backup + changelog + rollback plan",
                "notes": "Use saveAdminService.",
            }
        )
    write(
        tmp_path / "seo-workspace" / "data" / "publishing-field-map.json",
        json.dumps(
            {
                "mode": "mapping_only_no_publish",
                "field_map": {
                    "service": {
                        "table": "services",
                        "admin_helper": "saveAdminService",
                        "content_fields": ["slug", "title_zh", "title_en", "content_zh", "content_en"],
                        "image_fields": ["image_url", "alt_zh", "alt_en"],
                        "rich_text_support": "content_zh/content_en can store HTML text.",
                    }
                },
                "website_evidence": {
                    "status": "checked",
                    "files": [
                        {
                            "target_kind": "service",
                            "present_source_files": ["src/backend/modules/services/service/serviceService.ts"],
                        }
                    ],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )


def test_publish_plan_blocks_without_owner_approval_or_execution(tmp_path):
    seed_publish_plan_workspace(tmp_path)

    result, artifacts = publish_plan.run_publish_plan(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
    )

    assert not result.ok
    assert result.status == "blocked_before_publish"
    assert any("--owner-approved" in blocker for blocker in result.blockers)
    assert any("--explicit-execution" in blocker for blocker in result.blockers)
    assert any("--qa-passed" in blocker for blocker in result.blockers)
    json_path, _, _, report_path = artifacts
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["no_publish_executed"] is True
    assert payload["payload_plan"]["table"] == "services"
    assert "不调用 CMS、不发布、不部署" in report_path.read_text(encoding="utf-8")


def test_publish_plan_prefers_exact_draft_path_when_target_url_has_duplicates(tmp_path):
    seed_publish_plan_workspace(tmp_path)
    queue_path = tmp_path / "seo-workspace" / "data" / "approved-publish-queue.csv"
    with queue_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "draft_path",
                "target_url",
                "paired_url",
                "page_type",
                "target_kind",
                "table",
                "admin_helper",
                "status",
                "language_scope",
                "rich_text_ready",
                "image_strategy",
                "required_gate",
                "notes",
            ],
        )
        writer.writerow(
            {
                "draft_path": "seo-workspace/drafts/older-en-services-kitchen-rich-content-package.md",
                "target_url": "https://flashcast.com.my/en/services/kitchen",
                "paired_url": "https://flashcast.com.my/zh/services/kitchen",
                "page_type": "service",
                "target_kind": "service",
                "table": "services",
                "admin_helper": "saveAdminService",
                "status": "owner_review_required",
                "language_scope": "bilingual_pair_required",
                "rich_text_ready": "yes: package contains Publishing Field Map",
                "image_strategy": "primary image_url plus HTML/media image blocks if supported; concept labels required",
                "required_gate": "owner approval + explicit execution + QA pass + backup + changelog + rollback plan",
                "notes": "Older same-URL queue item.",
            }
        )
    exact_draft = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"

    result, _ = publish_plan.run_publish_plan(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        draft_path=str(exact_draft),
        mode="pr",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert result.ok
    assert result.queue_item["draft_path"] == exact_draft.relative_to(tmp_path).as_posix()
    assert not any("Multiple queue items matched" in blocker for blocker in result.blockers)


def test_publish_plan_ready_after_required_pr_gates(tmp_path):
    seed_publish_plan_workspace(tmp_path)

    result, artifacts = publish_plan.run_publish_plan(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        mode="pr",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert result.ok
    assert result.status == "ready_for_approved_execution_plan"
    assert result.payload_plan["admin_helper"] == "saveAdminService"
    assert result.payload_plan["language_scope"] == "bilingual_pair_required"
    assert result.payload_plan["content_fields_to_map"] == ["slug", "title_zh", "title_en", "content_zh", "content_en"]
    assert all(path.exists() for path in artifacts)


def test_publish_plan_does_not_block_on_owner_input_policy_language(tmp_path):
    seed_publish_plan_workspace(tmp_path)
    draft_path = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    write(
        draft_path,
        draft_path.read_text(encoding="utf-8")
        + "\n- NEEDS OWNER INPUT only for unsupported factual claims, final CTA/contact display, or true case proof.\n",
    )

    result, _ = publish_plan.run_publish_plan(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        mode="pr",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert result.ok
    assert not any("NEEDS OWNER INPUT" in blocker for blocker in result.blockers)


def test_publish_plan_blocks_on_explicit_owner_input_item(tmp_path):
    seed_publish_plan_workspace(tmp_path)
    draft_path = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    write(draft_path, draft_path.read_text(encoding="utf-8") + "\n- NEEDS OWNER INPUT: confirm final phone number before publish.\n")

    result, _ = publish_plan.run_publish_plan(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        mode="pr",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert not result.ok
    assert any("NEEDS OWNER INPUT" in blocker for blocker in result.blockers)


def test_publish_plan_blocks_live_search_without_source_log(tmp_path):
    seed_publish_plan_workspace(tmp_path)
    draft_path = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    write(draft_path, draft_path.read_text(encoding="utf-8") + "\n- NEEDS LIVE SEARCH: schema guidance requires current source verification.\n")

    result, _ = publish_plan.run_publish_plan(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        mode="pr",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert not result.ok
    assert any("Run latest-research" in blocker for blocker in result.blockers)
    assert result.payload_plan["latest_research"]["valid_source_count"] == 0


def test_publish_plan_accepts_live_search_with_source_log(tmp_path):
    seed_publish_plan_workspace(tmp_path)
    draft_path = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    write(draft_path, draft_path.read_text(encoding="utf-8") + "\n- NEEDS LIVE SEARCH: schema guidance requires current source verification.\n")
    source_log_path = tmp_path / "seo-workspace" / "data" / "research-source-log.csv"
    write(
        source_log_path,
        "\n".join(
            [
                "date_added,target_url,source_type,source_title,source_url,publisher,published_or_accessed_date,usage_note,claim_boundary",
                "2026-06-10,https://flashcast.com.my/en/services/kitchen,official,Google structured data,https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data,Google Search Central,2026-06-10,Use only for schema guidance,general guidance only; not a FLASH CAST business claim",
            ]
        )
        + "\n",
    )

    result, artifacts = publish_plan.run_publish_plan(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
        mode="pr",
        owner_approved=True,
        explicit_execution=True,
        qa_passed=True,
    )

    assert result.ok
    assert result.payload_plan["latest_research"]["valid_source_count"] == 1
    assert result.payload_plan["latest_research"]["sources"][0]["source_title"] == "Google structured data"
    assert "Valid source count: `1`" in artifacts[3].read_text(encoding="utf-8")
