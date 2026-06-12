#!/usr/bin/env python3
"""Build a full draft-only service-pattern content package from workspace tools."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

try:  # pragma: no cover - package import path differs between CLI and tests
    from .service_pattern_workspace_tools import load_service_pattern_tool
except ImportError:  # pragma: no cover
    from service_pattern_workspace_tools import load_service_pattern_tool


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def safe_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "service"


def service_slug_from_url(target_url: str) -> str:
    match = re.search(r"/services/([^/?#]+)", target_url)
    return slugify(match.group(1)) if match else ""


def load_patterns(root: Path) -> dict[str, object]:
    return read_json(root / "seo-workspace" / "data" / "service-content-patterns.json")


def target_from_slug(patterns: dict[str, object], service_slug: str) -> str:
    services = safe_dict(patterns.get("services"))
    service = safe_dict(services.get(service_slug))
    urls = safe_dict(service.get("urls"))
    return str(urls.get("en") or urls.get("zh") or "")


def targets_from_args(root: Path, *, target_url: str, service_slug: str, all_services: bool) -> list[str]:
    patterns = load_patterns(root)
    services = safe_dict(patterns.get("services"))
    if all_services:
        targets = []
        for raw in services.values():
            service = safe_dict(raw)
            urls = safe_dict(service.get("urls"))
            target = str(urls.get("en") or urls.get("zh") or "").strip()
            if target:
                targets.append(target)
        return targets
    if service_slug:
        target = target_from_slug(patterns, service_slug)
        if not target:
            raise RuntimeError(f"No service pattern found for slug: {service_slug}")
        return [target]
    if target_url:
        return [target_url]
    raise RuntimeError("Provide one of --target-url, --service-slug, or --all.")


def slug_for_target(root: Path, target_url: str) -> str:
    slug = service_slug_from_url(target_url)
    if slug:
        return slug
    patterns = load_patterns(root)
    for candidate_slug, raw in safe_dict(patterns.get("services")).items():
        urls = safe_dict(safe_dict(raw).get("urls"))
        if target_url in {str(urls.get("en", "")), str(urls.get("zh", ""))}:
            return str(candidate_slug)
    return "service"


def run_one(root: Path, target_url: str, today: str, public_base_url: str) -> dict[str, object]:
    brief_tool = load_service_pattern_tool(root, "service_pattern_brief_preview")
    editor_tool = load_service_pattern_tool(root, "service_pattern_rich_editor")
    publish_tool = load_service_pattern_tool(root, "service_pattern_publish_payload")
    media_tool = load_service_pattern_tool(root, "service_pattern_media_assets")

    slug = slug_for_target(root, target_url)
    brief_path = brief_tool.run(root, target_url, today)
    editor_artifacts = editor_tool.run(root, target_url, today)
    publish_artifacts = publish_tool.run(root, str(editor_artifacts["payload"]))
    media_artifacts = media_tool.run(root, str(publish_artifacts["cms_payload"]), public_base_url)
    media_summary = read_json(media_artifacts["summary"])
    editor_payload = read_json(editor_artifacts["payload"])
    safety = safe_dict(editor_payload.get("safety"))

    return {
        "service_slug": slug,
        "target_url": target_url,
        "paired_url": editor_payload.get("paired_url", ""),
        "status": "owner_review_package_ready",
        "media_status": media_summary.get("status", ""),
        "media_count": media_summary.get("media_count", 0),
        "public_base_url": public_base_url,
        "artifacts": {
            "brief": str(brief_path),
            "rich_editor_payload": str(editor_artifacts["payload"]),
            "rich_editor_html": str(editor_artifacts["editor_html"]),
            "rich_editor_report": str(editor_artifacts["report"]),
            "cms_payload": str(publish_artifacts["cms_payload"]),
            "publish_payload_summary": str(publish_artifacts["summary"]),
            "publish_payload_report": str(publish_artifacts["report"]),
            **{f"media_{name}": str(path) for name, path in media_artifacts.items()},
        },
        "safety": {
            "no_cms_write_executed": True,
            "no_source_write_executed": True,
            "no_media_upload_executed": True,
            "no_live_actions_executed": True,
            "editor_no_live_actions_executed": safety.get("no_live_actions_executed", True),
        },
    }


def render_report(summary: dict[str, object]) -> str:
    packages = [safe_dict(item) for item in safe_list(summary.get("packages"))]
    lines = [
        "# Service Pattern Full Content Package Report",
        "",
        f"- 生成日期: {summary.get('date')}",
        f"- Package count: {len(packages)}",
        f"- Status: `{summary.get('status')}`",
        "- 执行状态: draft-only；未搜索外部网页、未调用图片 API、未上传媒体、未登录 CMS、未写源站、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把动态服务页 brief、富文本图文编辑器、CMS payload 草稿和概念媒体资产串成正式 CLI 内容包能力。这样单个服务页或全部 service pattern 都能进入同一套 owner-review 产出链。",
        "",
        "## 为什么这一步重要",
        "",
        "这一步把“能写内容”推进到“能按服务页生成完整图文发布准备包”：业主可以审核文案、富文本结构、多张概念图、alt/caption、媒体占位、CMS 字段草稿和后续执行门禁。它比随机新文章更接近网站长期 SEO/GEO 自动化发布系统。",
        "",
        "## Packages",
        "",
    ]
    for package in packages:
        artifacts = safe_dict(package.get("artifacts"))
        lines.extend(
            [
                f"### {package.get('service_slug')}",
                "",
                f"- Target URL: `{package.get('target_url')}`",
                f"- Paired URL: `{package.get('paired_url')}`",
                f"- Media status: `{package.get('media_status')}`",
                f"- Media count: {package.get('media_count')}",
                f"- Owner review editor: `{artifacts.get('rich_editor_html')}`",
                f"- CMS payload draft: `{artifacts.get('cms_payload')}`",
                f"- Media plan: `{artifacts.get('media_media_plan')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## QA Checklist",
            "",
            "- [x] 本命令只生成本地草稿与审核包。",
            "- [x] 生成图片明确标注为概念设计/效果图方案。",
            "- [x] 未创建真实案例、评价、价格、工期、保修、资质或完工证明。",
            "- [x] 未登录 CMS/admin，未上传媒体，未写源站，未发布。",
            "- [ ] 业主确认目标页面、文案、图片 URL、CTA/contact 后，才能进入明确执行指令。",
            "",
        ]
    )
    return "\n".join(lines)


def run_service_pattern_content_package(
    root: Path,
    *,
    target_url: str = "",
    service_slug: str = "",
    all_services: bool = False,
    today: str = "",
    public_base_url: str = "",
) -> tuple[dict[str, object], tuple[Path, Path, Path]]:
    root = root.resolve()
    today = today or dt.date.today().isoformat()
    targets = targets_from_args(root, target_url=target_url, service_slug=service_slug, all_services=all_services)
    packages = [run_one(root, target, today, public_base_url) for target in targets]
    scope = "all-services" if all_services else str(packages[0].get("service_slug", "service"))
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    summary_path = data_dir / f"{scope}-service-pattern-content-package-summary.json"
    index_path = data_dir / "service-pattern-content-package-index.json"
    report_path = reports_dir / f"{today}-{scope}-service-pattern-content-package.md"
    summary: dict[str, object] = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "date": today,
        "status": "owner_review_package_ready",
        "scope": scope,
        "public_base_url": public_base_url,
        "package_count": len(packages),
        "no_external_search_executed": True,
        "no_image_api_called": True,
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_source_write_executed": True,
        "no_live_actions_executed": True,
        "packages": packages,
    }
    write_text(summary_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(index_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (summary_path, index_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a full draft-only service-pattern content package.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--target-url", default="", help="Target /zh or /en service URL.")
    parser.add_argument("--service-slug", default="", help="Service slug from service-content-patterns.json.")
    parser.add_argument("--all", action="store_true", help="Build packages for all service patterns.")
    parser.add_argument("--date", default="", help="Optional YYYY-MM-DD output date.")
    parser.add_argument("--public-base-url", default="", help="Optional owner-confirmed public URL prefix for media-ready payload drafts.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _, artifacts = run_service_pattern_content_package(
        Path(args.root),
        target_url=args.target_url,
        service_slug=args.service_slug,
        all_services=args.all,
        today=args.date,
        public_base_url=args.public_base_url,
    )
    for path in artifacts:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
