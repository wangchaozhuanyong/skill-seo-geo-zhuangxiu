from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_quality_review


content_quality_review = load_content_quality_review()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


GOOD_DRAFT = """
# Rich Content Publishing Package

- 目标页面: `https://example.com/en/services/kitchen`
- 配对页面: `https://example.com/zh/services/kitchen`
- 研究状态: source_log_attached (3 source rows)

## 最新资料 / Source Log

- Google Search Central | https://developers.google.com/search/docs | general guidance only.
- Schema.org Service | https://schema.org/Service | schema guidance only.

## 中文页面建议文案

快速答案：FLASH CAST 可以为 Kuala Lumpur 和 Selangor 的厨房装修客户规划服务范围、材料选择、流程、报价准备和咨询路径。

## 英文页面建议文案

Quick answer: the page explains kitchen renovation service scope, customer problems, material trade-offs, planning process, quotation preparation, FAQ, and CTA.

## Image Block

- 标签：`概念设计 / 效果图方案 / 规划示例` + `design concept / rendering concept / planning example`
- alt: kitchen renovation planning image
- 图注：此图为规划/效果图方案，不作为真实完工案例或客户照片。

## FAQ

## CTA

## Schema 建议

- Do not add Review, AggregateRating, price, openingHours, award, certification, or warranty schema unless owner-confirmed and visible on page.
"""


def test_content_quality_review_scores_good_rich_content_package(tmp_path):
    draft_path = tmp_path / "seo-workspace" / "drafts" / "good-rich-content-package.md"
    write(draft_path, GOOD_DRAFT)

    summary, artifacts = content_quality_review.run_content_quality_review(tmp_path, draft_path=str(draft_path))

    assert summary["status"] == "content_quality_ready_for_owner_review"
    assert summary["total_score"] >= 80
    assert all(path.exists() for path in artifacts)


def test_content_quality_review_blocks_risky_claims_and_unlabeled_media(tmp_path):
    draft_path = tmp_path / "seo-workspace" / "drafts" / "bad-rich-content-package.md"
    write(
        draft_path,
        """
        # Draft
        - 目标页面: `https://example.com/en/services/kitchen`
        We are the #1 best renovation contractor with guaranteed ranking and cheapest price.
        Image Block: real customer review photo.
        FAQ
        CTA
        Schema
        """,
    )

    summary, _artifacts = content_quality_review.run_content_quality_review(tmp_path, draft_path=str(draft_path))

    assert summary["status"] == "blocked_before_owner_review"
    blocked_metrics = [item for item in summary["metrics"] if item["status"] == "blocked"]
    assert {item["metric"] for item in blocked_metrics} >= {"claim_safety", "media_claim_boundary"}
