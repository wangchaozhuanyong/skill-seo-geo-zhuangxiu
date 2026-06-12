#!/usr/bin/env python3
"""Build an owner-review queue for target-page content studio production."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path

try:  # pragma: no cover - package import path differs between CLI and tests
    from .content_calendar import recommended_pipeline
    from .content_system import ContentSystemRow, build_rows
    from .hreflang import expected_pair_url
    from .opportunity_finder import OpportunityScore, run_opportunity_finder
except ImportError:  # pragma: no cover
    from content_calendar import recommended_pipeline
    from content_system import ContentSystemRow, build_rows
    from hreflang import expected_pair_url
    from opportunity_finder import OpportunityScore, run_opportunity_finder


QUEUE_JSON_NAME = "content-studio-queue.json"
QUEUE_CSV_NAME = "content-studio-queue.csv"
QUEUE_FIELDS = [
    "slot",
    "target_url",
    "paired_url",
    "language",
    "page_type",
    "content_priority",
    "keyword",
    "opportunity_score",
    "recommended_pipeline",
    "content_studio_command",
    "service_pattern_command",
    "rich_media_slots",
    "latest_research_policy",
    "owner_input_required",
    "owner_review_required",
]


@dataclass
class QueueItem:
    slot: int
    row: ContentSystemRow
    keyword: str
    opportunity_score: int

    def target_url(self) -> str:
        return preferred_target_url(self.row.target_url, self.row.paired_url)

    def paired_url(self) -> str:
        target = self.target_url()
        pair = expected_pair_url(target)
        return pair or self.row.paired_url

    def pipeline(self) -> str:
        candidate = type(
            "QueueCandidate",
            (),
            {
                "page_type": self.row.page_type,
                "content_priority": self.row.content_priority,
                "target_url": self.target_url(),
                "paired_url": self.paired_url(),
                "keyword": self.keyword,
                "task_type": "",
                "opportunity_score": self.opportunity_score,
                "calendar_score": self.opportunity_score,
                "rotation_notes": [],
            },
        )()
        value = recommended_pipeline(candidate)
        return "rich-content" if "rich-content" in value else value

    def service_slug(self) -> str:
        match = re.search(r"/services/([^/?#]+)", self.target_url())
        return match.group(1) if match else ""

    def content_studio_command(self) -> str:
        return (
            "python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py "
            f"content-studio --target-url {self.target_url()} --pipeline {self.pipeline()}"
        )

    def service_pattern_command(self) -> str:
        slug = self.service_slug()
        if not slug:
            return ""
        return (
            "python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py "
            f"service-pattern-package --service-slug {slug}"
        )

    def as_row(self) -> dict[str, str]:
        return {
            "slot": str(self.slot),
            "target_url": self.target_url(),
            "paired_url": self.paired_url(),
            "language": self.row.language,
            "page_type": self.row.page_type,
            "content_priority": self.row.content_priority,
            "keyword": self.keyword,
            "opportunity_score": str(self.opportunity_score),
            "recommended_pipeline": self.pipeline(),
            "content_studio_command": self.content_studio_command(),
            "service_pattern_command": self.service_pattern_command(),
            "rich_media_slots": self.row.rich_media_slots,
            "latest_research_policy": self.row.latest_research_policy,
            "owner_input_required": self.row.owner_input_required,
            "owner_review_required": "yes",
        }


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def preferred_target_url(url: str, paired_url: str) -> str:
    if "/en/" in url or url.rstrip("/").endswith("/en"):
        return url.rstrip("/")
    if paired_url and ("/en/" in paired_url or paired_url.rstrip("/").endswith("/en")):
        return paired_url.rstrip("/")
    return url.rstrip("/")


def pair_key(url: str) -> str:
    return url.rstrip("/").replace("/en/", "/{lang}/").replace("/zh/", "/{lang}/")


def score_index(scores: list[OpportunityScore]) -> dict[str, OpportunityScore]:
    output: dict[str, OpportunityScore] = {}
    for score in scores:
        output[score.url.rstrip("/")] = score
        output.setdefault(expected_pair_url(score.url).rstrip("/"), score)
    return output


def build_queue(root: Path, *, limit: int = 0) -> list[QueueItem]:
    rows = build_rows(root)
    scores = score_index(run_opportunity_finder(root))
    seen: set[str] = set()
    items: list[QueueItem] = []
    for row in rows:
        target = preferred_target_url(row.target_url, row.paired_url)
        key = pair_key(target)
        if key in seen:
            continue
        seen.add(key)
        score = scores.get(target.rstrip("/")) or scores.get(row.target_url.rstrip("/")) or scores.get(row.paired_url.rstrip("/"))
        keyword = score.keyword if score else ""
        score_value = int(score.total_score) if score else 0
        items.append(QueueItem(slot=0, row=row, keyword=keyword, opportunity_score=score_value))
    priority_rank = {"high": 0, "medium-high": 1, "medium": 2, "review": 3}
    items.sort(key=lambda item: (priority_rank.get(item.row.content_priority, 9), -item.opportunity_score, item.target_url()))
    if limit > 0:
        items = items[:limit]
    for index, item in enumerate(items, start=1):
        item.slot = index
    return items


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in QUEUE_FIELDS})


def render_report(rows: list[dict[str, str]]) -> str:
    page_counts: dict[str, int] = {}
    for row in rows:
        page_type = row.get("page_type", "") or "unknown"
        page_counts[page_type] = page_counts.get(page_type, 0) + 1
    lines = [
        "# Content Studio Queue",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Queue items: {len(rows)}",
        "- 执行模式: planning / draft-only",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天把全站 URL 转成 Content Studio 生产队列。后续每天可以从队列里选择一个页面，自动生成最新资料候选、富文本图文、概念效果图和发布准备交接，而不是人工临时挑页面或随机写文章。",
        "",
        "## Page Type Coverage",
        "",
    ]
    lines.extend(f"- {page_type}: {count}" for page_type, count in sorted(page_counts.items()))
    lines.extend(["", "## Top Queue Items", ""])
    for row in rows[:20]:
        lines.extend(
            [
                f"### {row.get('slot')}. {row.get('target_url')}",
                "",
                f"- Paired URL: `{row.get('paired_url')}`",
                f"- Page type: {row.get('page_type')}",
                f"- Priority: {row.get('content_priority')}",
                f"- Pipeline: `{row.get('recommended_pipeline')}`",
                f"- Command: `{row.get('content_studio_command')}`",
                f"- Service pattern command: `{row.get('service_pattern_command') or 'N/A'}`",
                "",
            ]
        )
    lines.extend(
        [
            "## 安全边界",
            "",
            "- 本队列只生成计划，不自动生成所有页面正文，不登录 CMS，不上传媒体，不写源码，不发布，不部署。",
            "- 生成图片只能作为设计方案、效果图方案或 rendering concept，不能当作真实完工案例证明。",
            "- 每个页面仍需要业主审核具体文案、图片标签、CTA 和事实性声明。",
            "",
            "## QA checklist",
            "",
            "- [ ] 双语页面对已正确识别。",
            "- [ ] 服务页优先使用 rich-content / service-pattern package。",
            "- [ ] 文章和资料类页面在引用当前信息前先写入 source log。",
            "- [ ] 发布前仍走 owner approval、explicit execution、QA、media-ready、backup、changelog、rollback gates。",
        ]
    )
    return "\n".join(lines) + "\n"


def run_content_studio_queue(root: Path, *, limit: int = 0) -> tuple[dict[str, object], tuple[Path, Path, Path]]:
    root = root.resolve()
    queue = build_queue(root, limit=limit)
    rows = [item.as_row() for item in queue]
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    json_path = data_dir / QUEUE_JSON_NAME
    csv_path = data_dir / QUEUE_CSV_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-content-studio-queue.md"
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "content_studio_queue_ready_for_owner_review",
        "queue_count": len(rows),
        "queue": rows,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_media_upload_executed": True,
        "no_live_actions_executed": True,
        "owner_review_required": True,
    }
    write_text(json_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_csv(csv_path, rows)
    write_text(report_path, render_report(rows))
    return summary, (json_path, csv_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a draft-only content studio production queue.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--limit", type=int, default=0, help="Optional queue item limit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _, artifacts = run_content_studio_queue(Path(args.root), limit=args.limit)
    for artifact in artifacts:
        print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
