#!/usr/bin/env python3
"""Scan likely SEO content in the current repository and write a Markdown report.

This script is intentionally read-only for website source files. It only writes:
seo-workspace/reports/seo-content-scan.md
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path


CONTENT_EXTENSIONS = {".md", ".mdx", ".tsx", ".jsx", ".ts", ".js", ".html"}
NON_CONTENT_FILENAMES = {"AGENTS.md", "README.md", "CHANGELOG.md", "LICENSE.md"}
SKIP_DIRS = {
    ".git",
    ".next",
    ".agents",
    "build",
    "dist",
    "node_modules",
    "out",
    "seo-workspace",
    "vendor",
}
CONTENT_DIR_NAMES = {
    "app",
    "articles",
    "blog",
    "content",
    "pages",
    "posts",
    "services",
    "src",
}
CTA_TERMS = (
    "contact",
    "quote",
    "consultation",
    "call",
    "whatsapp",
    "book",
    "schedule",
    "request",
    "enquire",
    "inquire",
    "estimate",
)
FAQ_TERMS = ("faq", "frequently asked", "questions")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def is_page_like(path: Path) -> bool:
    parts = set(path.parts)
    name = path.name.lower()
    if parts & {"app", "pages", "content", "blog", "posts", "articles", "services"}:
        return True
    return name in {
        "page.tsx",
        "page.jsx",
        "page.ts",
        "page.js",
        "index.tsx",
        "index.jsx",
        "index.html",
    }


def has_metadata(text: str, suffix: str) -> bool:
    lower = text.lower()
    checks = [
        "<title",
        "metadata",
        "meta description",
        "name=\"description\"",
        "name='description'",
        "description:",
        "title:",
        "seo title",
    ]
    if any(check in lower for check in checks):
        return True
    if suffix in {".md", ".mdx"} and re.search(r"(?ms)^---\s+.*?(title|description)\s*:", text):
        return True
    return False


def find_h1(text: str) -> list[str]:
    results: list[str] = []
    for match in re.finditer(r"(?m)^#\s+(.+)$", text):
        results.append(match.group(1).strip())
    for match in re.finditer(r"(?is)<h1[^>]*>(.*?)</h1>", text):
        clean = re.sub(r"<[^>]+>", "", match.group(1))
        clean = re.sub(r"\s+", " ", clean).strip()
        if clean:
            results.append(clean)
    return results[:3]


def has_faq(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in FAQ_TERMS)


def has_cta(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in CTA_TERMS)


def approximate_word_count(text: str) -> int:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[{}()[\\];,.:\"'`=<>/|-]", " ", text)
    return len([word for word in re.split(r"\s+", text) if len(word) > 2])


def bullet_list(items: list[str], empty: str = "None found.", limit: int = 80) -> str:
    if not items:
        return f"- {empty}\n"
    visible = items[:limit]
    output = "".join(f"- `{item}`\n" for item in visible)
    if len(items) > limit:
        output += f"- ...and {len(items) - limit} more\n"
    return output


def main() -> None:
    root = Path.cwd()
    report_path = root / "seo-workspace" / "reports" / "seo-content-scan.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    files: list[Path] = []
    content_dirs: set[str] = set()
    page_files: list[str] = []
    missing_meta: list[str] = []
    thin_files: list[str] = []
    h1_lines: list[str] = []
    faq_files: list[str] = []
    cta_files: list[str] = []

    for path in root.rglob("*"):
        if should_skip(path):
            continue
        if path.is_dir() and path.name in CONTENT_DIR_NAMES:
            content_dirs.add(rel(path, root))
            continue
        if (
            not path.is_file()
            or path.name in NON_CONTENT_FILENAMES
            or path.suffix.lower() not in CONTENT_EXTENSIONS
        ):
            continue

        files.append(path)
        text = read_text(path)
        relative = rel(path, root)
        page_like = is_page_like(path)

        if page_like:
            page_files.append(relative)
            if not has_metadata(text, path.suffix.lower()):
                missing_meta.append(relative)

        headings = find_h1(text)
        for heading in headings:
            h1_lines.append(f"{relative}: {heading}")

        if has_faq(text):
            faq_files.append(relative)
        if has_cta(text):
            cta_files.append(relative)

        if page_like and approximate_word_count(text) < 250:
            thin_files.append(relative)

    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    report = [
        "# SEO Content Scan",
        "",
        f"- Scan time: {now}",
        f"- Repository: `{root}`",
        f"- Files scanned: {len(files)}",
        "",
        "## Possible Content Directories",
        "",
        bullet_list(sorted(content_dirs), "No common content directories found."),
        "## Possible Page Files",
        "",
        bullet_list(sorted(page_files), "No likely page files found."),
        "## Files Missing Title/Meta Signals",
        "",
        bullet_list(sorted(missing_meta), "No suspicious missing metadata found."),
        "## Possible H1 Headings",
        "",
        bullet_list(sorted(h1_lines), "No H1 headings found."),
        "## Possible FAQ Files",
        "",
        bullet_list(sorted(faq_files), "No FAQ signals found."),
        "## Possible CTA Files",
        "",
        bullet_list(sorted(cta_files), "No CTA signals found."),
        "## Possibly Thin Content Files",
        "",
        bullet_list(sorted(thin_files), "No thin content candidates found."),
        "## Notes",
        "",
        "- This is a heuristic scan, not a full SEO audit.",
        "- It does not modify website source files.",
        "- Review any flagged files manually before editing live pages.",
        "",
    ]
    report_path.write_text("\n".join(report), encoding="utf-8")
    print(report_path)


if __name__ == "__main__":
    main()
