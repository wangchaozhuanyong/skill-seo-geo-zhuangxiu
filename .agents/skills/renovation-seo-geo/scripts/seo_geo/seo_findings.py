"""Shared SEO/GEO finding helpers for auditable reports."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path


SEVERITY_ORDER = {
    "critical": 4,
    "error": 3,
    "warning": 2,
    "info": 1,
}

FINDING_FIELDS = [
    "severity",
    "category",
    "url",
    "evidence",
    "recommendation",
    "publish_blocker",
    "owner_input_required",
    "source",
]


@dataclass(frozen=True)
class SeoFinding:
    severity: str
    category: str
    url: str
    evidence: str
    recommendation: str
    publish_blocker: bool = False
    owner_input_required: bool = False
    source: str = ""


def severity_rank(severity: str) -> int:
    return SEVERITY_ORDER.get((severity or "").strip().lower(), 0)


def finding_key(finding: SeoFinding) -> tuple[str, str, str, str]:
    return (
        finding.url.strip(),
        finding.category.strip().lower(),
        finding.evidence.strip().lower(),
        finding.recommendation.strip().lower(),
    )


def dedupe_findings(findings: list[SeoFinding]) -> list[SeoFinding]:
    best_by_key: dict[tuple[str, str, str, str], SeoFinding] = {}
    for finding in findings:
        key = finding_key(finding)
        previous = best_by_key.get(key)
        if previous is None or severity_rank(finding.severity) > severity_rank(previous.severity):
            best_by_key[key] = finding
    return sorted(
        best_by_key.values(),
        key=lambda item: (
            -severity_rank(item.severity),
            item.publish_blocker is False,
            item.url,
            item.category,
            item.evidence,
        ),
    )


def finding_to_row(finding: SeoFinding) -> dict[str, str]:
    return {
        "severity": finding.severity,
        "category": finding.category,
        "url": finding.url,
        "evidence": finding.evidence,
        "recommendation": finding.recommendation,
        "publish_blocker": "yes" if finding.publish_blocker else "no",
        "owner_input_required": "yes" if finding.owner_input_required else "no",
        "source": finding.source,
    }


def write_findings_csv(path: Path, findings: list[SeoFinding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINDING_FIELDS)
        writer.writeheader()
        for finding in findings:
            writer.writerow(finding_to_row(finding))


def write_findings_json(path: Path, findings: list[SeoFinding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "finding_count": len(findings),
        "publish_blocker_count": sum(1 for finding in findings if finding.publish_blocker),
        "findings": [asdict(finding) for finding in findings],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count_by_severity(findings: list[SeoFinding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        severity = finding.severity or "unknown"
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
