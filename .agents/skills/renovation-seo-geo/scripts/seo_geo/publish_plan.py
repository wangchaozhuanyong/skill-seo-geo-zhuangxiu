#!/usr/bin/env python3
"""Create a gated publishing execution plan from an approved queue item."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from permissions import PermissionContext, SeoGeoMode, parse_mode, validate_live_preconditions


PLAN_JSON_NAME = "publish-execution-plan.json"


@dataclass
class PublishPlanResult:
    status: str
    mode: str
    queue_item: dict[str, str]
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    payload_plan: dict[str, object] = field(default_factory=dict)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_workspace_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def infer_slug(target_url: str) -> str:
    path = urlsplit(target_url).path.strip("/")
    return path.split("/")[-1] if path else "home"


def find_queue_item(rows: list[dict[str, str]], *, target_url: str = "", draft_path: str = "") -> tuple[dict[str, str], list[str]]:
    blockers: list[str] = []
    if draft_path:
        matches = [row for row in rows if row.get("draft_path") == draft_path]
    elif target_url:
        matches = [row for row in rows if target_url in {row.get("target_url", ""), row.get("paired_url", "")}]
    elif len(rows) == 1:
        matches = rows
    else:
        matches = []

    if not rows:
        blockers.append("No approved-publish-queue.csv rows found. Run publish-queue first.")
        return {}, blockers
    if not matches:
        blockers.append("No unique queue item selected. Provide --target-url or --draft-path.")
        return {}, blockers
    if len(matches) > 1:
        blockers.append("Multiple queue items matched. Provide a more specific --target-url or --draft-path.")
        return {}, blockers
    return matches[0], blockers


def normalize_draft_path(root: Path, draft_path: str) -> str:
    if not draft_path:
        return ""
    path = Path(draft_path)
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def draft_has_concept_label(text: str) -> bool:
    lowered = text.lower()
    return "概念设计" in text and ("rendering concept" in lowered or "design concept" in lowered)


def source_files_checked(field_map: dict[str, object], kind: str) -> list[str]:
    evidence = field_map.get("website_evidence", {})
    if not isinstance(evidence, dict):
        return []
    files = evidence.get("files", [])
    if not isinstance(files, list):
        return []
    for item in files:
        if isinstance(item, dict) and item.get("target_kind") == kind:
            present = item.get("present_source_files", [])
            return [str(path) for path in present] if isinstance(present, list) else []
    return []


def field_mapping(field_map: dict[str, object], kind: str) -> dict[str, object]:
    raw = field_map.get("field_map", {})
    if not isinstance(raw, dict):
        return {}
    item = raw.get(kind, {})
    return item if isinstance(item, dict) else {}


def build_payload_plan(row: dict[str, str], mapping: dict[str, object], draft_text: str) -> dict[str, object]:
    content_fields = [str(field) for field in mapping.get("content_fields", [])] if isinstance(mapping.get("content_fields", []), list) else []
    image_fields = [str(field) for field in mapping.get("image_fields", [])] if isinstance(mapping.get("image_fields", []), list) else []
    target_url = row.get("target_url", "")
    paired_url = row.get("paired_url", "")
    slug = infer_slug(target_url)
    has_html = any(token in draft_text.lower() for token in ("<h2", "<section", "<img", "image-rich", "图文内容块"))
    return {
        "target_url": target_url,
        "paired_url": paired_url,
        "slug": slug,
        "target_kind": row.get("target_kind", ""),
        "table": row.get("table", ""),
        "admin_helper": row.get("admin_helper", ""),
        "status_to_write": "draft_or_published_only_after_owner_selected_mode",
        "language_scope": row.get("language_scope", ""),
        "rich_text_detected": has_html,
        "content_fields_to_map": content_fields,
        "image_fields_to_map": image_fields,
        "draft_source": row.get("draft_path", ""),
        "field_mapping_note": mapping.get("rich_text_support", ""),
        "image_strategy": row.get("image_strategy", ""),
        "write_path": "website admin UI or admin service layer only; direct database/API writes are disabled for publishable content",
    }


def valid_source_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def research_source_rows(root: Path, row: dict[str, str]) -> list[dict[str, str]]:
    targets = {row.get("target_url", ""), row.get("paired_url", "")}
    rows = read_csv_rows(root / "seo-workspace" / "data" / "research-source-log.csv")
    valid_rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source_row in rows:
        if source_row.get("target_url", "") not in targets:
            continue
        source_url = source_row.get("source_url", "")
        if not valid_source_url(source_url):
            continue
        key = (source_row.get("target_url", ""), source_url)
        if key in seen:
            continue
        valid_rows.append(source_row)
        seen.add(key)
    return valid_rows


def source_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "target_url": row.get("target_url", ""),
            "source_title": row.get("source_title", ""),
            "source_url": row.get("source_url", ""),
            "publisher": row.get("publisher", ""),
            "claim_boundary": row.get("claim_boundary", ""),
        }
        for row in rows
    ]


def has_unresolved_owner_input(draft_text: str) -> bool:
    markers = (
        "- NEEDS OWNER INPUT:",
        "* NEEDS OWNER INPUT:",
        "NEEDS OWNER INPUT -",
        "NEEDS OWNER INPUT —",
        "NEEDS OWNER INPUT:",
        "[ ] NEEDS OWNER INPUT",
    )
    return any(marker in draft_text for marker in markers)


def evaluate_gates(
    *,
    root: Path,
    row: dict[str, str],
    mapping: dict[str, object],
    draft_text: str,
    mode: str,
    owner_approved: bool,
    explicit_execution: bool,
    qa_passed: bool,
    owner_input_resolved: bool,
    latest_research_verified: bool,
    research_sources: list[dict[str, str]],
    single_language_approved: bool,
    confirm_live: bool,
    backup_path: str,
    changelog_path: str,
    rollback_plan_path: str,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    if not owner_approved:
        blockers.append("Owner has not approved this exact queued package (--owner-approved missing).")
    if not explicit_execution:
        blockers.append("Owner has not explicitly asked to execute this package (--explicit-execution missing).")
    if not qa_passed:
        blockers.append("Pre-publish QA is not marked passed (--qa-passed missing).")
    if not mapping:
        blockers.append("No field mapping exists for this target kind. Regenerate publish-queue and inspect website source.")
    if row.get("status") != "owner_review_required":
        warnings.append(f"Queue status is `{row.get('status', '')}`; expected owner_review_required before approval.")
    if row.get("rich_text_ready", "").startswith("partial"):
        blockers.append("Queue item is not rich-text ready. Convert draft into a rich-content package first.")
    if row.get("language_scope") == "single_language_needs_owner_approval" and not single_language_approved:
        blockers.append("Single-language execution needs explicit owner approval (--single-language-approved missing).")
    if has_unresolved_owner_input(draft_text) and not owner_input_resolved:
        blockers.append("Draft contains NEEDS OWNER INPUT. Resolve owner-input items or pass --owner-input-resolved.")
    if "NEEDS LIVE SEARCH" in draft_text and not latest_research_verified and not research_sources:
        blockers.append("Draft requires latest-source verification. Run latest-research for this target URL or pass --latest-research-verified with external evidence.")
    if latest_research_verified and not research_sources:
        warnings.append("--latest-research-verified was passed, but no matching research-source-log rows were found. Keep external evidence with the owner approval record.")
    if row.get("image_strategy") and not draft_has_concept_label(draft_text):
        warnings.append("Concept/rendering labels are not fully detected in the draft; confirm generated images are labeled before publish.")

    if mode == SeoGeoMode.LIVE.value:
        context = PermissionContext.from_env(
            SeoGeoMode.LIVE,
            root=root,
            confirm_live=confirm_live,
            qa_passed=qa_passed,
            backup_path=backup_path,
            changelog_path=changelog_path,
            rollback_plan_path=rollback_plan_path,
        )
        try:
            validate_live_preconditions(context)
        except Exception as exc:  # noqa: BLE001 - every live blocker must be surfaced in the plan
            blockers.append(f"Live mode blocked: {exc}")

    return blockers, warnings


def render_report(result: PublishPlanResult) -> str:
    row = result.queue_item
    lines = [
        "# Approved Queue Publishing Execution Plan",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Mode: {result.mode}",
        f"- Status: {result.status}",
        f"- Target URL: `{row.get('target_url', 'N/A')}`",
        f"- Paired URL: `{row.get('paired_url', 'N/A')}`",
        f"- Draft: `{row.get('draft_path', 'N/A')}`",
        f"- Table: `{row.get('table', 'N/A')}`",
        f"- Admin helper: `{row.get('admin_helper', 'N/A')}`",
        "- 执行状态: 等待业主审核和明确执行指令；本计划不调用 CMS、不发布、不部署",
        "",
        "## 今日决策",
        "",
        "今天把已排队的图文内容包转成发布执行计划：先验证批准门槛、字段映射、双语范围、富文本/图片策略和回滚要求，再进入真正 CMS/source 执行。",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Payload Plan",
            "",
            f"- Target kind: `{result.payload_plan.get('target_kind', 'N/A')}`",
            f"- Write path: {result.payload_plan.get('write_path', 'N/A')}",
            f"- Language scope: `{result.payload_plan.get('language_scope', 'N/A')}`",
            f"- Content fields: `{', '.join(result.payload_plan.get('content_fields_to_map', []))}`",
            f"- Image fields: `{', '.join(result.payload_plan.get('image_fields_to_map', []))}`",
            "",
            "## Latest Research Evidence",
            "",
            f"- Source log: `{result.payload_plan.get('latest_research', {}).get('source_log_path', 'N/A')}`",
            f"- Valid source count: `{result.payload_plan.get('latest_research', {}).get('valid_source_count', 0)}`",
            f"- Manual verified flag: `{result.payload_plan.get('latest_research', {}).get('manual_verified_flag', False)}`",
            "",
            "## Generated Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.extend(
        [
            "",
            "## Next Execution Gate",
            "",
            "- Owner approves the exact queue item.",
            "- Owner explicitly says to execute it.",
            "- Re-run pre-publish QA for the target URL and paired URL.",
            "- Create a real backup of the CMS/source record that will be edited.",
            "- Confirm changelog and rollback plan before live.",
            "- Execute through the website's admin/backend helper first.",
            "- Regenerate SEO manifest/sitemap/llms and deploy only when the approved execution path requires it.",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifacts(root: Path, result: PublishPlanResult) -> tuple[Path, Path, Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = data_dir / PLAN_JSON_NAME
    changelog_path = reports_dir / f"{today}-publish-change-log-draft.md"
    rollback_path = reports_dir / f"{today}-publish-rollback-plan-draft.md"
    report_path = reports_dir / f"{today}-publish-execution-plan.md"

    result.artifacts.update(
        {
            "json_plan": str(json_path),
            "change_log_draft": str(changelog_path),
            "rollback_plan_draft": str(rollback_path),
            "execution_report": str(report_path),
        }
    )
    json_payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": result.status,
        "mode": result.mode,
        "blockers": result.blockers,
        "warnings": result.warnings,
        "queue_item": result.queue_item,
        "payload_plan": result.payload_plan,
        "artifacts": result.artifacts,
        "no_publish_executed": True,
    }
    write_text(json_path, json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(
        changelog_path,
        "\n".join(
            [
                "# Publish Change Log Draft",
                "",
                f"- Status: {result.status}",
                f"- Target URL: `{result.queue_item.get('target_url', 'N/A')}`",
                f"- Paired URL: `{result.queue_item.get('paired_url', 'N/A')}`",
                "- No CMS/source/live change has been executed by this draft.",
                "",
                "## Planned Changes",
                "",
                f"- Map `{result.queue_item.get('draft_path', 'N/A')}` into `{result.queue_item.get('table', 'N/A')}` using `{result.queue_item.get('admin_helper', 'N/A')}`.",
                "- Preserve bilingual title/meta/content/FAQ/internal links/image alt where present in the approved package.",
                "- Keep generated images labeled as design concept/rendering concept/planning example.",
                "",
            ]
        ),
    )
    write_text(
        rollback_path,
        "\n".join(
            [
                "# Publish Rollback Plan Draft",
                "",
                f"- Status: {result.status}",
                f"- Target URL: `{result.queue_item.get('target_url', 'N/A')}`",
                "- This is a draft rollback plan, not a completed backup.",
                "",
                "## Required Before Live",
                "",
                "- Export or back up the exact CMS/source record before writing.",
                "- Record old title/meta/content/image fields and media references.",
                "- If deploy is required, keep the previous deploy identifier.",
                "- To roll back, restore the backed-up record/files, regenerate SEO assets, redeploy if needed, and run live smoke QA.",
                "",
            ]
        ),
    )
    write_text(report_path, render_report(result))
    return json_path, changelog_path, rollback_path, report_path


def run_publish_plan(
    root: Path,
    *,
    target_url: str = "",
    draft_path: str = "",
    mode: str = "pr",
    owner_approved: bool = False,
    explicit_execution: bool = False,
    qa_passed: bool = False,
    owner_input_resolved: bool = False,
    latest_research_verified: bool = False,
    single_language_approved: bool = False,
    confirm_live: bool = False,
    backup_path: str = "",
    changelog_path: str = "",
    rollback_plan_path: str = "",
) -> tuple[PublishPlanResult, tuple[Path, Path, Path, Path]]:
    root = root.resolve()
    parsed_mode = parse_mode(mode)
    if parsed_mode == SeoGeoMode.DRAFT:
        parsed_mode = SeoGeoMode.PR
    queue_rows = read_csv_rows(root / "seo-workspace" / "data" / "approved-publish-queue.csv")
    row, blockers = find_queue_item(queue_rows, target_url=target_url, draft_path=normalize_draft_path(root, draft_path))
    field_map = read_json(root / "seo-workspace" / "data" / "publishing-field-map.json")
    mapping = field_mapping(field_map, row.get("target_kind", "")) if row else {}
    draft_file = resolve_workspace_path(root, row.get("draft_path", "")) if row else root / "missing-draft.md"
    draft_text = read_text(draft_file)
    if row and not draft_file.exists():
        blockers.append(f"Draft file is missing: {draft_file}")
    payload_plan = build_payload_plan(row, mapping, draft_text) if row else {}
    research_sources = research_source_rows(root, row) if row else []
    if payload_plan:
        payload_plan["latest_research"] = {
            "source_log_path": "seo-workspace/data/research-source-log.csv",
            "valid_source_count": len(research_sources),
            "sources": source_summary(research_sources),
            "manual_verified_flag": latest_research_verified,
        }
    gate_blockers, warnings = evaluate_gates(
        root=root,
        row=row,
        mapping=mapping,
        draft_text=draft_text,
        mode=parsed_mode.value,
        owner_approved=owner_approved,
        explicit_execution=explicit_execution,
        qa_passed=qa_passed,
        owner_input_resolved=owner_input_resolved,
        latest_research_verified=latest_research_verified,
        research_sources=research_sources,
        single_language_approved=single_language_approved,
        confirm_live=confirm_live,
        backup_path=backup_path,
        changelog_path=changelog_path,
        rollback_plan_path=rollback_plan_path,
    )
    blockers.extend(gate_blockers)
    checked_sources = source_files_checked(field_map, row.get("target_kind", "")) if row else []
    if row and not checked_sources:
        warnings.append("Website source evidence for this target kind was not found in publishing-field-map.json.")
    status = "ready_for_approved_execution_plan" if not blockers else "blocked_before_publish"
    result = PublishPlanResult(
        status=status,
        mode=parsed_mode.value,
        queue_item=row,
        blockers=blockers,
        warnings=warnings,
        payload_plan=payload_plan,
    )
    artifacts = write_artifacts(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a gated publish execution plan from approved-publish-queue.csv.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="", help="Target or paired URL from the queue.")
    parser.add_argument("--draft-path", default="", help="Exact draft_path value from approved-publish-queue.csv.")
    parser.add_argument("--mode", default="pr", choices=["draft", "pr", "staging", "live"])
    parser.add_argument("--owner-approved", action="store_true")
    parser.add_argument("--explicit-execution", action="store_true")
    parser.add_argument("--qa-passed", action="store_true")
    parser.add_argument("--owner-input-resolved", action="store_true")
    parser.add_argument("--latest-research-verified", action="store_true")
    parser.add_argument("--single-language-approved", action="store_true")
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--backup-path", default="")
    parser.add_argument("--changelog-path", default="")
    parser.add_argument("--rollback-plan-path", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_publish_plan(
        Path(args.root),
        target_url=args.target_url,
        draft_path=args.draft_path,
        mode=args.mode,
        owner_approved=args.owner_approved,
        explicit_execution=args.explicit_execution,
        qa_passed=args.qa_passed,
        owner_input_resolved=args.owner_input_resolved,
        latest_research_verified=args.latest_research_verified,
        single_language_approved=args.single_language_approved,
        confirm_live=args.confirm_live,
        backup_path=args.backup_path,
        changelog_path=args.changelog_path,
        rollback_plan_path=args.rollback_plan_path,
    )
    for artifact in artifacts:
        print(artifact)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
