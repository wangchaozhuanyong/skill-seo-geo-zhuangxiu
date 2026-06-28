#!/usr/bin/env python3
"""Validate the SEO/GEO workspace foundation.

This is the phase-one guardrail for the renovation SEO/GEO operating system.
It checks that core scripts compile, data CSV files are readable, required
business-data files exist, and repository Markdown/Python/CSV files are not
accidentally collapsed into one-line blobs.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import py_compile
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SKILL_DIR = ROOT / ".agents" / "skills" / "renovation-seo-geo"
SCRIPTS_DIR = SKILL_DIR / "scripts"
DATA_DIR = ROOT / "seo-workspace" / "data"
REPORTS_DIR = ROOT / "seo-workspace" / "reports"

REQUIRED_SCRIPTS = [
    SCRIPTS_DIR / "scan_seo_content.py",
    SCRIPTS_DIR / "create_onboarding_report.py",
    SCRIPTS_DIR / "create_daily_seo_brief.py",
    SCRIPTS_DIR / "seo_geo" / "permissions.py",
    SCRIPTS_DIR / "seo_geo" / "backups.py",
    SCRIPTS_DIR / "seo_geo" / "change_log.py",
    SCRIPTS_DIR / "seo_geo" / "cli_command_registry.py",
    SCRIPTS_DIR / "seo_geo" / "crawl.py",
    SCRIPTS_DIR / "seo_geo" / "url_inventory.py",
    SCRIPTS_DIR / "seo_geo" / "robots_sitemap.py",
    SCRIPTS_DIR / "seo_geo" / "http_checks.py",
    SCRIPTS_DIR / "seo_geo" / "canonical.py",
    SCRIPTS_DIR / "seo_geo" / "hreflang.py",
    SCRIPTS_DIR / "seo_geo" / "integrations" / "google_search_console.py",
    SCRIPTS_DIR / "seo_geo" / "indexation" / "google.py",
    SCRIPTS_DIR / "seo_geo" / "integrations" / "baidu.py",
    SCRIPTS_DIR / "seo_geo" / "indexation" / "baidu.py",
    SCRIPTS_DIR / "seo_geo" / "indexation" / "indexnow.py",
    SCRIPTS_DIR / "seo_geo" / "scoring.py",
    SCRIPTS_DIR / "seo_geo" / "opportunity_finder.py",
    SCRIPTS_DIR / "seo_geo" / "page_audit.py",
    SCRIPTS_DIR / "seo_geo" / "content_brief.py",
    SCRIPTS_DIR / "seo_geo" / "content_refresh.py",
    SCRIPTS_DIR / "seo_geo" / "entity_profile.py",
    SCRIPTS_DIR / "seo_geo" / "geo_ai.py",
    SCRIPTS_DIR / "seo_geo" / "growth_ops.py",
    SCRIPTS_DIR / "seo_geo" / "citations.py",
    SCRIPTS_DIR / "seo_geo" / "local_seo.py",
    SCRIPTS_DIR / "seo_geo" / "schema_generator.py",
    SCRIPTS_DIR / "seo_geo" / "schema_validator.py",
    SCRIPTS_DIR / "seo_geo" / "language_pairs.py",
    SCRIPTS_DIR / "seo_geo" / "hreflang_validator.py",
    SCRIPTS_DIR / "seo_geo" / "visual_brief.py",
    SCRIPTS_DIR / "seo_geo" / "image_seo.py",
    SCRIPTS_DIR / "seo_geo" / "qa.py",
    SCRIPTS_DIR / "seo_geo" / "config.py",
    SCRIPTS_DIR / "qa_content.py",
    SCRIPTS_DIR / "seo_geo_cli.py",
]

REQUIRED_TEXT_FILES = [
    DATA_DIR / "brand-profile.md",
    DATA_DIR / "services.md",
    ROOT / "seo-workspace" / "config" / "seo-geo-config.example.yml",
    ROOT / "seo-workspace" / "config" / "search-engines.example.yml",
    ROOT / "seo-workspace" / "config" / "cms.example.yml",
    ROOT / ".env.example",
]

REQUIRED_CSV_FIELDS = {
    DATA_DIR / "keyword-map.csv": [
        "keyword",
        "search_intent",
        "customer_stage",
        "target_url",
        "current_url",
        "page_type",
        "priority",
        "service",
        "location",
        "notes",
    ],
    DATA_DIR / "internal-links.csv": [
        "source_url",
        "target_url",
        "anchor_text",
        "context",
        "priority",
    ],
    DATA_DIR / "service-areas.csv": [
        "area",
        "country",
        "state_or_region",
        "city",
        "neighborhoods",
        "services_available",
        "existing_url",
        "local_project_examples",
        "notes",
        "verified",
    ],
    DATA_DIR / "case-studies.csv": [
        "project_name",
        "location",
        "property_type",
        "size",
        "budget_range",
        "timeline",
        "service",
        "year",
        "client_goal",
        "main_problem",
        "scope",
        "materials",
        "challenge",
        "solution",
        "result",
        "photos_available",
        "testimonial",
        "related_url",
        "notes",
    ],
}

SCAN_SUFFIXES = {".py", ".md", ".csv"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}


@dataclass
class ValidationResult:
    checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_check(self, message: str) -> None:
        self.checks.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        self.errors.append(message)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]
        return list(reader.fieldnames or []), rows


def validate_scripts(result: ValidationResult) -> None:
    for path in REQUIRED_SCRIPTS:
        if not path.exists():
            result.add_error(f"Missing required script: {path.relative_to(ROOT)}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            result.add_error(f"Python compile failed: {path.relative_to(ROOT)}: {exc.msg}")
        else:
            result.add_check(f"Python compile passed: {path.relative_to(ROOT)}")


def validate_text_files(result: ValidationResult) -> None:
    for path in REQUIRED_TEXT_FILES:
        if not path.exists():
            result.add_error(f"Missing required data file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            result.add_error(f"Required data file is empty: {path.relative_to(ROOT)}")
        else:
            result.add_check(f"Required data file present: {path.relative_to(ROOT)}")


def validate_csv_files(result: ValidationResult) -> None:
    for path, required_fields in REQUIRED_CSV_FIELDS.items():
        if not path.exists():
            result.add_error(f"Missing required CSV: {path.relative_to(ROOT)}")
            continue
        try:
            fields, rows = read_csv(path)
        except csv.Error as exc:
            result.add_error(f"CSV parse failed: {path.relative_to(ROOT)}: {exc}")
            continue
        missing = [field for field in required_fields if field not in fields]
        extra_none_key = any(None in row for row in rows)
        if missing:
            result.add_error(
                f"CSV missing fields: {path.relative_to(ROOT)}: {', '.join(missing)}"
            )
        elif extra_none_key:
            result.add_error(f"CSV has malformed extra columns: {path.relative_to(ROOT)}")
        elif not rows:
            result.add_warning(f"CSV has no data rows: {path.relative_to(ROOT)}")
        else:
            result.add_check(
                f"CSV readable: {path.relative_to(ROOT)} ({len(rows)} rows)"
            )


def validate_not_single_line_blobs(result: ValidationResult) -> None:
    for path in ROOT.rglob("*"):
        if should_skip(path) or not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue
        line_count = len(text.splitlines())
        if line_count <= 1:
            if path.suffix.lower() == ".csv":
                try:
                    fields, rows = read_csv(path)
                except csv.Error:
                    result.add_error(f"File appears collapsed into one line: {path.relative_to(ROOT)}")
                    continue
                if fields and not rows:
                    result.add_warning(f"CSV has header only: {path.relative_to(ROOT)}")
                else:
                    result.add_error(f"File appears collapsed into one line: {path.relative_to(ROOT)}")
            else:
                result.add_error(f"File appears collapsed into one line: {path.relative_to(ROOT)}")
    result.add_check("No collapsed one-line .py/.md/.csv files found")


def build_report(result: ValidationResult) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    lines = [
        "# SEO/GEO Workspace Validation Report",
        "",
        f"- Generated: {now}",
        f"- Repository: `{ROOT}`",
        f"- Status: {'PASS' if result.ok else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {item}" for item in result.checks)
    lines.extend([
        "",
        "## Warnings",
        "",
    ])
    lines.extend(f"- {item}" for item in result.warnings) if result.warnings else lines.append("- None")
    lines.extend([
        "",
        "## Errors",
        "",
    ])
    lines.extend(f"- {item}" for item in result.errors) if result.errors else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def run_validation(write_report: bool = True) -> ValidationResult:
    result = ValidationResult()
    validate_scripts(result)
    validate_text_files(result)
    validate_csv_files(result)
    validate_not_single_line_blobs(result)
    if write_report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / f"{dt.date.today().isoformat()}-workspace-validation-report.md"
        report_path.write_text(build_report(result), encoding="utf-8")
        result.add_check(f"Validation report written: {report_path.relative_to(ROOT)}")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the SEO/GEO workspace foundation.")
    parser.add_argument("--no-report", action="store_true", help="Run checks without writing a validation report.")
    parser.add_argument("--check-only", action="store_true", help="Alias for --no-report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_validation(write_report=not (args.no_report or args.check_only))
    print(build_report(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
