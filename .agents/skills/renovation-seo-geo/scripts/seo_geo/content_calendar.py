#!/usr/bin/env python3
"""Generate a rotating daily SEO/GEO content calendar without publishing."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from .content_system import build_rows
    from .hreflang import expected_pair_url
    from .opportunity_finder import OpportunityScore, run_opportunity_finder
except ImportError:  # pragma: no cover - direct script execution
    from content_system import build_rows
    from hreflang import expected_pair_url
    from opportunity_finder import OpportunityScore, run_opportunity_finder


CALENDAR_JSON_NAME = "daily-content-calendar.json"
CALENDAR_CSV_NAME = "daily-content-calendar.csv"
CALENDAR_REPORT_NAME = "daily-content-calendar.md"
DEFAULT_DAYS = 14
RECENT_REPEAT_PENALTY = 35
CALENDAR_FIELDS = [
    "date",
    "slot",
    "target_url",
    "paired_url",
    "keyword",
    "page_type",
    "content_priority",
    "task_type",
    "calendar_score",
    "rotation_notes",
    "recommended_pipeline",
    "owner_review_required",
]


@dataclass
class CalendarCandidate:
    target_url: str
    paired_url: str
    keyword: str
    page_type: str
    content_priority: str
    task_type: str
    opportunity_score: int
    calendar_score: int
    rotation_notes: list[str] = field(default_factory=list)

    def as_row(self, date: str, slot: int) -> dict[str, str]:
        return {
            "date": date,
            "slot": str(slot),
            "target_url": self.target_url,
            "paired_url": self.paired_url,
            "keyword": self.keyword,
            "page_type": self.page_type,
            "content_priority": self.content_priority,
            "task_type": self.task_type,
            "calendar_score": str(self.calendar_score),
            "rotation_notes": "; ".join(self.rotation_notes),
            "recommended_pipeline": recommended_pipeline(self),
            "owner_review_required": "yes",
        }


@dataclass
class ContentCalendarResult:
    status: str
    calendar: list[dict[str, str]] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.blockers


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CALENDAR_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CALENDAR_FIELDS})


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def str_value(value: object, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def language_pair_key(url: str) -> str:
    return url.rstrip("/").replace("/en/", "/{lang}/").replace("/zh/", "/{lang}/")


def priority_points(priority: str) -> int:
    return {
        "high": 25,
        "medium-high": 16,
        "medium": 9,
        "review": 2,
    }.get(priority, 0)


def page_type_points(page_type: str) -> int:
    if page_type in {"service", "service-hub", "home", "conversion"}:
        return 18
    if page_type in {"local", "case-study", "case-study-hub"}:
        return 10
    if page_type == "article":
        return 6
    return 0


def preferred_url(url: str, paired_url: str) -> str:
    if "/en/" in url or url.rstrip("/").endswith("/en"):
        return url
    if paired_url and ("/en/" in paired_url or paired_url.rstrip("/").endswith("/en")):
        return paired_url
    return url


def recommended_pipeline(candidate: CalendarCandidate) -> str:
    if candidate.page_type in {"service", "service-hub", "home", "case-study", "local"}:
        return "rich-content"
    if candidate.page_type == "article":
        return "rich-content with latest-research"
    return "brief"


def content_system_index(root: Path) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in build_rows(root):
        data = row.as_dict()
        output[row.target_url.rstrip("/")] = data
        if row.paired_url:
            output.setdefault(row.paired_url.rstrip("/"), data)
    return output


def recent_urls(root: Path, history_path: str = "", lookback: int = 10) -> set[str]:
    urls: list[str] = []
    explicit_history = Path(history_path) if history_path else root / "seo-workspace" / "data" / "daily-content-calendar-history.csv"
    if not explicit_history.is_absolute():
        explicit_history = root / explicit_history
    for row in read_csv_rows(explicit_history):
        url = row.get("target_url") or row.get("url") or row.get("paired_url")
        if url:
            urls.append(url.rstrip("/"))
    daily_payload = read_json(root / "seo-workspace" / "data" / "daily-automation-run.json")
    selected = daily_payload.get("selected_task", {}) if isinstance(daily_payload.get("selected_task"), dict) else {}
    if selected.get("target_url"):
        urls.append(str(selected["target_url"]).rstrip("/"))
    postrun_payload = read_json(root / "seo-workspace" / "data" / "scheduled-publish-postrun-summary.json")
    summary = postrun_payload.get("summary", {}) if isinstance(postrun_payload.get("summary"), dict) else {}
    if summary.get("target_url"):
        urls.append(str(summary["target_url"]).rstrip("/"))
    return set(urls[-lookback:])


def candidate_from_score(score: OpportunityScore, content_index: dict[str, dict[str, str]], recent: set[str]) -> CalendarCandidate:
    paired = expected_pair_url(score.url)
    target = preferred_url(score.url, paired).rstrip("/")
    paired = expected_pair_url(target).rstrip("/")
    content_row = content_index.get(target) or content_index.get(score.url.rstrip("/")) or {}
    page_type = content_row.get("page_type") or score.page_type
    priority = content_row.get("content_priority", "")
    points = int(score.total_score) + priority_points(priority) + page_type_points(page_type)
    notes: list[str] = [f"opportunity_score={score.total_score}"]
    if priority:
        notes.append(f"content_priority={priority}")
    if target in recent or score.url.rstrip("/") in recent or (paired and paired in recent):
        points -= RECENT_REPEAT_PENALTY
        notes.append(f"recent_repeat_penalty=-{RECENT_REPEAT_PENALTY}")
    if paired:
        notes.append("bilingual_pair_planned")
    else:
        notes.append("NEEDS OWNER INPUT: paired URL missing")
    return CalendarCandidate(
        target_url=target,
        paired_url=paired,
        keyword=score.keyword,
        page_type=page_type,
        content_priority=priority,
        task_type=score.task_type,
        opportunity_score=int(score.total_score),
        calendar_score=points,
        rotation_notes=notes,
    )


def build_candidates(root: Path, history_path: str = "", lookback: int = 10) -> list[CalendarCandidate]:
    scores = run_opportunity_finder(root)
    content_index = content_system_index(root)
    recent = recent_urls(root, history_path=history_path, lookback=lookback)
    by_pair: dict[str, CalendarCandidate] = {}
    for score in scores:
        candidate = candidate_from_score(score, content_index, recent)
        key = language_pair_key(candidate.target_url)
        existing = by_pair.get(key)
        if existing is None or candidate.calendar_score > existing.calendar_score:
            by_pair[key] = candidate
    return sorted(by_pair.values(), key=lambda item: (item.calendar_score, item.opportunity_score, item.target_url), reverse=True)


def calendar_rows(candidates: list[CalendarCandidate], *, days: int, start_date: dt.date) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    used_keys: set[str] = set()
    slot = 0
    for candidate in candidates:
        if slot >= days:
            break
        key = language_pair_key(candidate.target_url)
        if key in used_keys:
            continue
        slot += 1
        used_keys.add(key)
        rows.append(candidate.as_row((start_date + dt.timedelta(days=slot - 1)).isoformat(), slot))
    return rows


def render_report(result: ContentCalendarResult, *, days: int) -> str:
    lines = [
        "# Daily SEO/GEO Content Calendar",
        "",
        f"- 生成日期: {dt.date.today().isoformat()}",
        f"- Status: `{result.status}`",
        f"- Calendar days requested: `{days}`",
        f"- Calendar rows: `{len(result.calendar)}`",
        "- 执行状态: calendar-only；未生成正文、未登录 CMS、未上传媒体、未写页面、未发布、未部署",
        "",
        "## 今日决策",
        "",
        "今天新增全站内容排期层：把每日 SEO/GEO 从单次最高分页面扩展为可轮转的多日内容日历，避免长期重复同一个 URL，同时保持每次只做一个最高价值任务。",
        "",
        "## Scheduled Tasks",
        "",
    ]
    for row in result.calendar:
        lines.append(
            f"- {row['date']} | `{row['target_url']}` + `{row['paired_url'] or 'N/A'}` | score={row['calendar_score']} | pipeline={row['recommended_pipeline']}"
        )
    if not result.calendar:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in result.blockers) if result.blockers else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend(
        [
            "",
            "## QA Checklist",
            "",
            "- [ ] 每一天仍只对应一个任务，不批量发布。",
            "- [ ] `/en` 与 `/zh` 页面作为同一个任务配对处理。",
            "- [ ] 近期已处理页面被降权，避免重复写同一个页面。",
            "- [ ] 文章类页面需要 latest-research/source log 后再写正文。",
            "- [ ] 所有 concept/rendering 内容仍必须标注为设计方案或效果图方案。",
            "",
            "## Artifacts",
            "",
            *(f"- {name}: `{path}`" for name, path in result.artifacts.items()),
            "",
        ]
    )
    return "\n".join(lines)


def run_content_calendar(
    root: Path,
    *,
    days: int = DEFAULT_DAYS,
    start_date: str = "",
    history_path: str = "",
    lookback: int = 10,
) -> tuple[ContentCalendarResult, tuple[Path, Path, Path]]:
    root = root.resolve()
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    start = dt.date.fromisoformat(start_date) if start_date else dt.date.today()
    blockers: list[str] = []
    warnings: list[str] = []
    if days < 1:
        blockers.append("days must be at least 1.")
        days = 1
    candidates = build_candidates(root, history_path=history_path, lookback=lookback)
    if not candidates:
        blockers.append("No content calendar candidates found. Check keyword-map.csv and url-inventory.csv.")
    rows = calendar_rows(candidates, days=days, start_date=start)
    if len(rows) < days:
        warnings.append(f"Only {len(rows)} unique bilingual/page candidates available for {days} requested days.")
    status = "content_calendar_ready_for_owner_review" if not blockers else "content_calendar_blocked"
    result = ContentCalendarResult(status=status, calendar=rows, blockers=blockers, warnings=warnings)
    json_path = data_dir / CALENDAR_JSON_NAME
    csv_path = data_dir / CALENDAR_CSV_NAME
    report_path = reports_dir / f"{dt.date.today().isoformat()}-{CALENDAR_REPORT_NAME}"
    result.artifacts.update({"calendar_json": str(json_path), "calendar_csv": str(csv_path), "report": str(report_path)})
    write_csv(csv_path, rows)
    write_text(
        json_path,
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "status": result.status,
                "days": days,
                "start_date": start.isoformat(),
                "calendar": rows,
                "blockers": blockers,
                "warnings": warnings,
                "no_live_actions_executed": True,
                "safety_note": "Content calendar is planning-only. It does not draft, upload media, call CMS/admin helpers, publish, regenerate SEO assets, or deploy.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(report_path, render_report(result, days=days))
    return result, (json_path, csv_path, report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a rotating daily SEO/GEO content calendar.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--start-date", default="")
    parser.add_argument("--history-path", default="")
    parser.add_argument("--lookback", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result, artifacts = run_content_calendar(
        Path(args.root),
        days=args.days,
        start_date=args.start_date,
        history_path=args.history_path,
        lookback=args.lookback,
    )
    for output in artifacts:
        print(output)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
