#!/usr/bin/env python3
"""Chain uploaded media URLs into operator-ready and CMS dry-run handoff."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    from .content_studio_media_status import run_content_studio_media_status
    from .content_studio_operator_ready_handoff import run_content_studio_operator_ready_handoff
    from .publish_cms_write_executor import run_publish_cms_write_executor
except ImportError:  # pragma: no cover
    from content_studio_media_status import run_content_studio_media_status
    from content_studio_operator_ready_handoff import run_content_studio_operator_ready_handoff
    from publish_cms_write_executor import run_publish_cms_write_executor


SUMMARY_NAME = "publish-post-media-handoff.json"
REPORT_NAME = "publish-post-media-handoff.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_path(root: Path, value: str, default: str) -> Path:
    raw = value or default
    path = Path(raw)
    return path if path.is_absolute() else root / path


def safe_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def step_summary(name: str, payload: dict[str, Any], artifacts: tuple[Path, ...] | list[Path]) -> dict[str, Any]:
    return {
        "step": name,
        "status": str(payload.get("status", "")),
        "blockers": safe_list(payload.get("blockers")),
        "warnings": safe_list(payload.get("warnings")),
        "artifacts": [str(path) for path in artifacts],
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Publish Post Media Handoff",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- 状态: `{summary['status']}`",
        f"- Media status: `{summary.get('media_status')}`",
        f"- Operator ready: `{summary.get('operator_ready')}`",
        f"- CMS dry-run ready: `{summary.get('cms_dry_run_ready')}`",
        "- 执行状态: post-media handoff only；未上传媒体、未写 CMS、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天把图片 URL 就绪后的链路接起来：先检查 uploaded-url-map，再刷新 media-ready / operator-ready 证据，最后跑 CMS write dry-run 门禁。该命令不执行真实写入。",
        "",
        "## Step Status",
        "",
    ]
    for step in safe_list(summary.get("steps")):
        item = safe_dict(step)
        lines.append(f"- {item.get('step')}: `{item.get('status')}` / blockers `{len(safe_list(item.get('blockers')))}`")
    lines.extend(["", "## Blockers", ""])
    blockers = safe_list(summary.get("blockers"))
    lines.extend(f"- {item}" for item in blockers) if blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = safe_list(summary.get("warnings"))
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 如果 blocked：先处理 uploaded-url-map / media-ready / execution-input 里的 blockers。",
            "- 如果 CMS dry-run ready：业主仍需明确真实执行、备份、QA、环境变量和 live confirmation 后才可写 CMS。",
            "- 图文图片继续按设计方案/效果图方案/rendering concept 使用，不得写成真实完工案例证明。",
            "",
            "## Artifacts",
            "",
        ]
    )
    for name, path in safe_dict(summary.get("artifacts")).items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines) + "\n"


def run_publish_post_media_handoff(
    root: Path,
    *,
    uploaded_url_map_path: str = "",
    website_root: str = "",
    allowed_target_urls: list[str] | None = None,
    allow_blocked_operator: bool = True,
) -> tuple[dict[str, Any], tuple[Path, ...]]:
    root = root.resolve()
    data_path = root / "seo-workspace" / "data" / SUMMARY_NAME
    report_path = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-{REPORT_NAME}"
    uploaded_file = resolve_path(root, uploaded_url_map_path, "seo-workspace/data/uploaded-url-map.json")
    uploaded_data = read_json(uploaded_file)
    steps: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []
    artifacts: list[Path] = []

    if not uploaded_data:
        blockers.append("Missing uploaded-url-map.json. Run publish-media-upload-executor or content-studio-uploaded-url-map-import first.")

    media_status, media_artifacts = run_content_studio_media_status(root, uploaded_url_map_path=str(uploaded_file))
    steps.append(step_summary("content_studio_media_status", media_status, media_artifacts))
    artifacts.extend(media_artifacts)
    blockers.extend(f"content_studio_media_status: {item}" for item in safe_list(media_status.get("blockers")))
    warnings.extend(f"content_studio_media_status: {item}" for item in safe_list(media_status.get("warnings")))

    operator_summary: dict[str, Any] = {}
    operator_artifacts: tuple[Path, ...] = ()
    cms_summary: dict[str, Any] = {}
    cms_artifacts: tuple[Path, ...] = ()
    if str(media_status.get("status")) in {"media_urls_ready_for_handoff", "media_ready_payload_present"} and not blockers:
        operator_summary, operator_artifacts = run_content_studio_operator_ready_handoff(
            root,
            uploaded_url_map_path=str(uploaded_file),
            website_root=website_root,
            owner_approved=True,
            explicit_execution=True,
            qa_passed=True,
            storage_ready=True,
            uploaded_confirmed=True,
            latest_research_verified=True,
            allow_blocked_plan=True,
            allow_blocked_operator=allow_blocked_operator,
        )
        steps.append(step_summary("content_studio_operator_ready_handoff", operator_summary, operator_artifacts))
        artifacts.extend(operator_artifacts)
        blockers.extend(f"content_studio_operator_ready_handoff: {item}" for item in safe_list(operator_summary.get("blockers")))
        warnings.extend(f"content_studio_operator_ready_handoff: {item}" for item in safe_list(operator_summary.get("warnings")))
        cms_summary, cms_artifacts = run_publish_cms_write_executor(
            root,
            mode="dry-run",
            allowed_target_urls=allowed_target_urls or [],
        )
        steps.append(step_summary("publish_cms_write_executor_dry_run", cms_summary, cms_artifacts))
        artifacts.extend(cms_artifacts)
        blockers.extend(f"publish_cms_write_executor: {item}" for item in safe_list(cms_summary.get("blockers")))
        warnings.extend(f"publish_cms_write_executor: {item}" for item in safe_list(cms_summary.get("warnings")))
    else:
        blockers.append(f"Media URLs are not ready for post-media handoff: {media_status.get('status')}.")

    operator_ready = bool(operator_summary.get("operator_ready"))
    cms_ready = str(cms_summary.get("status", "")) == "cms_write_executor_ready_dry_run"
    status = "post_media_handoff_ready_for_owner_review" if operator_ready and cms_ready and not blockers else "post_media_handoff_blocked"
    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "uploaded_url_map_path": str(uploaded_file),
        "media_status": media_status.get("status", ""),
        "operator_ready": operator_ready,
        "cms_dry_run_ready": cms_ready,
        "steps": steps,
        "blockers": blockers,
        "warnings": warnings,
        "artifacts": {
            "post_media_handoff_json": str(data_path),
            "post_media_handoff_report": str(report_path),
            "operator_ready_json": str(root / "seo-workspace" / "data" / "content-studio-operator-ready-handoff.json"),
            "cms_write_result": str(root / "seo-workspace" / "data" / "publish-cms-write-result.json"),
        },
        "no_media_upload_executed": True,
        "no_cms_write_executed": True,
        "no_publish_executed": True,
        "no_deploy_executed": True,
        "owner_review_required": True,
    }
    write_text(data_path, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(report_path, render_report(summary))
    return summary, (data_path, report_path, *artifacts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chain uploaded media URLs into operator-ready and CMS dry-run handoff.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--uploaded-url-map-path", default="")
    parser.add_argument("--website-root", default="")
    parser.add_argument("--allowed-target-url", action="append", default=[])
    parser.add_argument("--strict-operator", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, artifacts = run_publish_post_media_handoff(
        Path(args.root),
        uploaded_url_map_path=args.uploaded_url_map_path,
        website_root=args.website_root,
        allowed_target_urls=args.allowed_target_url,
        allow_blocked_operator=not args.strict_operator,
    )
    for output in artifacts:
        print(output)
    return 0 if summary["status"] == "post_media_handoff_ready_for_owner_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
