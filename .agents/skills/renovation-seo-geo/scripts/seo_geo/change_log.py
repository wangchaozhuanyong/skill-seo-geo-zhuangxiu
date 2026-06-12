"""Change-log helpers for live SEO/GEO operations."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List, Optional


def write_live_change_log(
    *,
    changes: List[str],
    rollback_plan: List[str],
    root: Optional[Path] = None,
    report_path: Optional[Path] = None,
    title: str = "SEO/GEO Live Change Log",
    status: str = "pending verification",
) -> Path:
    repo_root = (root or Path.cwd()).resolve()
    reports_dir = repo_root / "seo-workspace" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path = report_path or reports_dir / f"{dt.date.today().isoformat()}-live-change-log.md"
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

    lines = [
        f"# {title}",
        "",
        f"- Generated: {now}",
        f"- Status: {status}",
        "",
        "## Changes",
        "",
    ]
    lines.extend(f"- {item}" for item in changes) if changes else lines.append("- None recorded")
    lines.extend([
        "",
        "## Rollback Plan",
        "",
    ])
    lines.extend(f"- {item}" for item in rollback_plan) if rollback_plan else lines.append("- NEEDS OWNER INPUT: rollback plan missing")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
