#!/usr/bin/env python3
"""Auto-record trusted research-discovery candidates into the source log."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path

try:
    from .latest_research import run_latest_research
except ImportError:  # pragma: no cover - direct script execution
    from latest_research import run_latest_research


INTAKE_JSON_NAME = "research-intake.json"
DEFAULT_ALLOWED_SOURCE_TYPES = ["official", "government", "search_engine", "standards", "manufacturer", "industry"]


@dataclass
class ResearchIntakeResult:
    status: str
    candidates_checked: int = 0
    selected_source_count: int = 0
    fetched_source_count: int = 0
    source_log_path: str = ""
    selected_sources: list[dict[str, str]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def safe_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return default


def safe_candidate_rows(payload: dict[str, object]) -> list[dict[str, str]]:
    raw = payload.get("candidates", [])
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, str]] = []
    for item in raw:
        if isinstance(item, dict):
            rows.append({str(key): str(value or "").strip() for key, value in item.items()})
    return rows


def existing_source_keys(root: Path) -> set[tuple[str, str]]:
    rows = read_csv_rows(root / "seo-workspace" / "data" / "research-source-log.csv")
    return {(row.get("target_url", ""), row.get("source_url", "").rstrip("/")) for row in rows}


def source_arg(row: dict[str, str]) -> str:
    existing = row.get("latest_research_source_arg", "").strip()
    if existing:
        return existing
    return "|".join(
        [
            row.get("source_type", "external") or "external",
            row.get("candidate_url", ""),
            row.get("usage_note", "") or "Use for current general guidance only.",
            row.get("claim_boundary", "") or "general guidance only; not a FLASH CAST business claim",
            row.get("query", ""),
        ]
    )


def select_candidates(
    root: Path,
    rows: list[dict[str, str]],
    *,
    target_url: str = "",
    limit: int = 2,
    min_score: int = 60,
    allowed_source_types: list[str] | None = None,
) -> tuple[list[dict[str, str]], list[str]]:
    warnings: list[str] = []
    allowed = set(allowed_source_types or DEFAULT_ALLOWED_SOURCE_TYPES)
    existing = existing_source_keys(root)
    selected: list[dict[str, str]] = []
    for row in sorted(rows, key=lambda item: safe_int(item.get("score")), reverse=True):
        candidate_url = row.get("candidate_url", "").rstrip("/")
        row_target = row.get("target_url", "")
        source_type = row.get("source_type", "")
        score = safe_int(row.get("score"))
        if target_url and row_target and row_target.rstrip("/") != target_url.rstrip("/"):
            continue
        if not candidate_url:
            warnings.append("Skipped candidate with empty URL.")
            continue
        if source_type not in allowed:
            warnings.append(f"Skipped {candidate_url}: source_type `{source_type}` is not auto-intake allowed.")
            continue
        if score < min_score:
            warnings.append(f"Skipped {candidate_url}: score {score} below min_score {min_score}.")
            continue
        if (row_target, candidate_url) in existing:
            warnings.append(f"Skipped {candidate_url}: already present in research-source-log.csv.")
            continue
        selected.append(row)
        if len(selected) >= limit:
            break
    return selected, warnings


def render_report(result: ResearchIntakeResult) -> str:
    lines = [
        "# Research Source Intake Report",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Candidates checked: {result.candidates_checked}",
        f"- Selected sources: {result.selected_source_count}",
        f"- Fetched sources: {result.fetched_source_count}",
        "- 执行状态: research-intake only；只更新本地 source log/研究报告，未发布、未写 CMS、未修改网站源码",
        "",
        "## 今日决策",
        "",
        "今天把可信 research-discovery 候选自动转入 latest-research 抓取和 source log，让后续图文内容包能自动使用最新资料证据链。该步骤只接受高分可信来源，不把第三方资料写成 FLASH CAST 的业务承诺。",
        "",
        "## Selected Sources",
        "",
    ]
    if result.selected_sources:
        for row in result.selected_sources:
            lines.append(
                f"- score={row.get('score', '')} | `{row.get('source_type', '')}` | {row.get('publisher', '')} | {row.get('candidate_url', '')}"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- 自动 intake 只记录外部来源作为一般行业、搜索规则、材料、设计或政策背景。",
            "- source log 不能证明价格、资质、奖项、服务区域、真实案例、客户评价、保修或工期。",
            "- 该步骤不复制来源正文、不发布页面、不调用 CMS、不上传媒体、不部署。",
            "",
            "## Artifacts",
            "",
        ]
    )
    lines.extend(f"- {name}: `{path}`" for name, path in result.artifacts.items()) if result.artifacts else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_outputs(root: Path, result: ResearchIntakeResult) -> tuple[Path, Path]:
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    json_path = data_dir / INTAKE_JSON_NAME
    report_path = reports_dir / f"{today}-research-intake-report.md"
    result.artifacts.update({"intake_json": str(json_path), "report": str(report_path)})
    write_text(
        json_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "candidates_checked": result.candidates_checked,
                "selected_source_count": result.selected_source_count,
                "fetched_source_count": result.fetched_source_count,
                "source_log_path": result.source_log_path,
                "selected_sources": result.selected_sources,
                "blockers": result.blockers,
                "warnings": result.warnings,
                "artifacts": result.artifacts,
                "source_log_write_executed": result.fetched_source_count > 0,
                "no_cms_write_executed": True,
                "no_source_page_write_executed": True,
                "no_media_upload_executed": True,
                "no_live_actions_executed": True,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result))
    return json_path, report_path


def run_research_intake(
    root: Path,
    *,
    candidates_path: str = "",
    target_url: str = "",
    limit: int = 2,
    min_score: int = 60,
    allowed_source_types: list[str] | None = None,
    timeout: int = 10,
) -> tuple[ResearchIntakeResult, tuple[Path, Path]]:
    root = root.resolve()
    candidate_file = resolve_path(root, candidates_path) if candidates_path else root / "seo-workspace" / "data" / "research-discovery-candidates.json"
    payload = read_json(candidate_file)
    blockers: list[str] = []
    warnings: list[str] = []
    if not payload:
        blockers.append("Missing research-discovery-candidates.json. Run research-discovery first.")
    rows = safe_candidate_rows(payload)
    if payload and not rows:
        blockers.append("Research discovery payload has no candidates array.")
    selected_target = target_url or str(payload.get("target_url", "") or "")

    selected: list[dict[str, str]] = []
    latest_sources = []
    fetched_count = 0
    source_log_path = str(root / "seo-workspace" / "data" / "research-source-log.csv")
    if not blockers:
        selected, selection_warnings = select_candidates(
            root,
            rows,
            target_url=selected_target,
            limit=limit,
            min_score=min_score,
            allowed_source_types=allowed_source_types,
        )
        warnings.extend(selection_warnings)
        if selected:
            queries = sorted({row.get("query", "") for row in selected if row.get("query", "")})
            latest_result, latest_artifacts = run_latest_research(
                root,
                target_url=selected_target,
                queries=queries,
                sources=[source_arg(row) for row in selected],
                timeout=timeout,
            )
            warnings.extend(latest_result.warnings)
            blockers.extend(latest_result.blockers)
            latest_sources = [source.latest_row() for source in latest_result.sources]
            fetched_count = len([source for source in latest_result.sources if not source.fetch_status.startswith("failed")])
            source_log_path = str(root / "seo-workspace" / "data" / "research-source-log.csv")
            if latest_artifacts:
                latest_path, latest_report, latest_brief = latest_artifacts
                warnings.append(f"latest-research artifacts updated: {latest_path}, {latest_report}, {latest_brief}")
        else:
            warnings.append("No candidates passed auto-intake filters; source log was not changed.")

    status = "research_intake_blocked" if blockers else "research_sources_recorded_for_content" if fetched_count else "research_intake_no_sources_recorded"
    result = ResearchIntakeResult(
        status=status,
        candidates_checked=len(rows),
        selected_source_count=len(selected),
        fetched_source_count=fetched_count,
        source_log_path=source_log_path,
        selected_sources=selected,
        blockers=blockers,
        warnings=warnings,
    )
    if latest_sources:
        result.artifacts["latest_research_sources"] = str(root / "seo-workspace" / "data" / "latest-research-sources.csv")
        result.artifacts["research_source_log"] = source_log_path
    artifacts = write_outputs(root, result)
    return result, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-record trusted discovery candidates into latest-research source log.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--candidates-path", default="")
    parser.add_argument("--target-url", default="")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--min-score", type=int, default=60)
    parser.add_argument("--allowed-source-type", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_research_intake(
        Path(args.root),
        candidates_path=args.candidates_path,
        target_url=args.target_url,
        limit=args.limit,
        min_score=args.min_score,
        allowed_source_types=args.allowed_source_type or None,
        timeout=args.timeout,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
