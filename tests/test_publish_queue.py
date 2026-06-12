import csv
import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_publish_queue


publish_queue = load_publish_queue()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_rich_content_package(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md",
        "\n".join(
            [
                "# Rich Content Package",
                "",
                "- 目标页面: `https://flashcast.com.my/en/services/kitchen`",
                "- 配对页面: `https://flashcast.com.my/zh/services/kitchen`",
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


def seed_website_sources(tmp_path: Path) -> Path:
    website_root = tmp_path / "website"
    for source in publish_queue.FIELD_MAP["service"]["source_files"]:
        write(website_root / source, "// source marker\n")
    return website_root


def test_publish_queue_writes_mapping_queue_and_report(tmp_path):
    seed_rich_content_package(tmp_path)
    website_root = seed_website_sources(tmp_path)

    field_map_path, queue_path, report_path = publish_queue.run_publish_queue(tmp_path, website_root=str(website_root))

    assert field_map_path.name == "publishing-field-map.json"
    assert queue_path.name == "approved-publish-queue.csv"
    assert report_path.name == f"{date.today().isoformat()}-publishing-queue-report.md"

    payload = json.loads(field_map_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "mapping_only_no_publish"
    assert payload["field_map"]["service"]["table"] == "services"
    assert payload["field_map"]["service"]["admin_helper"] == "saveAdminService"
    assert payload["website_evidence"]["status"] == "checked"

    with queue_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    row = rows[0]
    assert row["target_kind"] == "service"
    assert row["table"] == "services"
    assert row["admin_helper"] == "saveAdminService"
    assert row["status"] == "owner_review_required"
    assert row["language_scope"] == "bilingual_pair_required"
    assert row["rich_text_ready"].startswith("yes")

    report = report_path.read_text(encoding="utf-8")
    assert "等待业主审核和明确执行指令" in report
    assert "This command does not call Supabase or CMS." in report
    assert "This command does not publish or deploy." in report


def test_publish_queue_marks_single_language_as_needing_owner_approval(tmp_path):
    write(
        tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-blog-rich-content-package.md",
        "\n".join(
            [
                "# Rich Content Package",
                "",
                "- 目标页面: `https://flashcast.com.my/en/blog/kitchen-planning`",
                "- 页面类型: article",
                "",
                "## Publishing Field Map",
            ]
        )
        + "\n",
    )

    _, queue_path, _ = publish_queue.run_publish_queue(tmp_path)

    with queue_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["target_kind"] == "blog"
    assert rows[0]["admin_helper"] == "saveAdminBlogPost"
    assert rows[0]["language_scope"] == "single_language_needs_owner_approval"
