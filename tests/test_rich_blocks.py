import json
from datetime import date
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_rich_blocks


rich_blocks = load_rich_blocks()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_rich_package(tmp_path: Path) -> Path:
    draft = tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-services-kitchen-rich-content-package.md"
    write(
        draft,
        "\n".join(
            [
                "# Rich Content Publishing Package",
                "",
                "- 品牌: FLASH CAST",
                "- 目标页面: `https://flashcast.com.my/en/services/kitchen`",
                "- 配对页面: `https://flashcast.com.my/zh/services/kitchen`",
                "- 页面类型: service",
                "- 目标关键词: kitchen renovation malaysia",
                "- 主题: Kitchen Renovation Malaysia",
                "",
                "## 图文内容块 / Image-Rich Blocks",
                "",
                "### Image Block 1: hero rendering concept",
                "",
                "- 中文图位：服务页效果图方案主图",
                "- English slot: service page rendering concept",
                "- 标签：`概念设计 / 效果图方案 / 规划示例` + `design concept / rendering concept / planning example`",
                "- 中文 alt：FLASH CAST 服务页效果图方案主图，用于装修内容规划说明",
                "- English alt: FLASH CAST service page rendering concept for renovation planning content",
                "- 图注：此图为规划/效果图方案，不作为真实完工案例或客户照片。",
                "- Suggested filename: `flash-cast-hero-rendering-concept.webp`",
                "",
                "### Image Block 2: material mood board",
                "",
                "- 中文图位：材料 mood board",
                "- English slot: material mood board",
                "- 标签：`概念设计 / 效果图方案 / 规划示例` + `design concept / rendering concept / planning example`",
                "- 中文 alt：FLASH CAST 材料 mood board，用于装修内容规划说明",
                "- English alt: FLASH CAST material mood board for renovation planning content",
                "- 图注：此图为规划/效果图方案，不作为真实完工案例或客户照片。",
                "- Suggested filename: `flash-cast-material-mood-board.webp`",
            ]
        )
        + "\n",
    )
    return draft


def test_rich_blocks_generates_structured_json_html_and_cms_payload(tmp_path):
    seed_rich_package(tmp_path)

    blocks_path, cms_path, preview_path, report_path = rich_blocks.run_rich_blocks(
        tmp_path,
        target_url="https://flashcast.com.my/en/services/kitchen",
    )

    payload = json.loads(blocks_path.read_text(encoding="utf-8"))
    cms = json.loads(cms_path.read_text(encoding="utf-8"))
    preview = preview_path.read_text(encoding="utf-8")
    report = report_path.read_text(encoding="utf-8")

    assert payload["status"] == "draft_only_no_cms_write"
    assert payload["no_cms_write_executed"] is True
    assert payload["metadata"]["target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert payload["blocks_zh"][0]["type"] == "hero"
    assert payload["blocks_en"][0]["image"]["concept_label"]
    assert payload["html"]["content_zh"].count("<figure>") >= 1
    assert payload["media_placeholders"][0]["filename"] == "flash-cast-hero-rendering-concept.webp"
    assert "真实完工案例" in payload["media_placeholders"][0]["caption_zh"]
    assert "customer photo" in payload["media_placeholders"][0]["caption"]
    assert "customer photo" in payload["media_placeholders"][0]["caption_en"]
    assert "customer photo" in payload["html"]["content_en"]
    assert cms["table"] == "services"
    assert cms["admin_helper"] == "saveAdminService"
    assert cms["payload"]["status"] == "draft"
    assert "NEEDS_MEDIA_UPLOAD" in cms["payload"]["image_url"]
    assert "English Preview" in preview
    assert "未写入 CMS、未发布、未部署" in report


def test_rich_blocks_falls_back_to_safe_concept_images(tmp_path):
    write(
        tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-en-blog-topic-rich-content-package.md",
        "\n".join(
            [
                "# Rich Content Publishing Package",
                "",
                "- 目标页面: `https://flashcast.com.my/en/blog/kitchen-planning`",
                "- 配对页面: `https://flashcast.com.my/zh/blog/kitchen-planning`",
                "- 页面类型: article",
                "- 主题: Kitchen Planning",
            ]
        )
        + "\n",
    )

    blocks_path, cms_path, _, _ = rich_blocks.run_rich_blocks(
        tmp_path,
        target_url="https://flashcast.com.my/en/blog/kitchen-planning",
    )

    payload = json.loads(blocks_path.read_text(encoding="utf-8"))
    cms = json.loads(cms_path.read_text(encoding="utf-8"))

    assert payload["media_placeholders"]
    assert all("concept" in item["concept_label"] for item in payload["media_placeholders"])
    assert cms["target_kind"] == "cms_dynamic_or_blog"
