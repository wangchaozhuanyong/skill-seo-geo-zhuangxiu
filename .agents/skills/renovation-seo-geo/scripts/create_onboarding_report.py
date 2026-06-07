#!/usr/bin/env python3
"""Create the first-run SEO/GEO onboarding report.

The script is read-only for website source files. It writes:
seo-workspace/reports/seo-onboarding-report.md
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from pathlib import Path


DATA_DIR = Path("seo-workspace/data")
REPORTS_DIR = Path("seo-workspace/reports")
OUTPUT_PATH = REPORTS_DIR / "seo-onboarding-report.md"
SOURCE_EXTENSIONS = {".md", ".mdx", ".tsx", ".jsx", ".ts", ".js", ".html"}
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
    "case-studies",
    "content",
    "pages",
    "posts",
    "projects",
    "services",
    "src",
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def bullet(items: list[str], empty: str = "None found.", limit: int = 80) -> str:
    if not items:
        return f"- {empty}\n"
    visible = items[:limit]
    output = "".join(f"- {item}\n" for item in visible)
    if len(items) > limit:
        output += f"- ...and {len(items) - limit} more\n"
    return output


def code_bullet(items: list[str], empty: str = "None found.", limit: int = 80) -> str:
    return bullet([f"`{item}`" for item in items], empty=empty, limit=limit)


def detect_framework(root: Path) -> list[str]:
    signals: list[str] = []
    package_path = root / "package.json"
    if package_path.exists():
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            package = {}
        deps = {}
        deps.update(package.get("dependencies", {}))
        deps.update(package.get("devDependencies", {}))
        if "next" in deps:
            signals.append("Next.js")
        if "vite" in deps:
            signals.append("Vite")
        if "react" in deps:
            signals.append("React")
        if "astro" in deps:
            signals.append("Astro")
        if "gatsby" in deps:
            signals.append("Gatsby")
        if "vue" in deps or "nuxt" in deps:
            signals.append("Vue/Nuxt")
    config_signals = {
        "next.config.js": "Next.js config",
        "next.config.mjs": "Next.js config",
        "vite.config.js": "Vite config",
        "vite.config.ts": "Vite config",
        "astro.config.mjs": "Astro config",
        "gatsby-config.js": "Gatsby config",
    }
    for filename, label in config_signals.items():
        if (root / filename).exists() and label not in signals:
            signals.append(label)
    return signals


def scan_source(root: Path) -> dict[str, list[str]]:
    content_dirs: set[str] = set()
    page_files: list[str] = []
    service_files: list[str] = []
    blog_files: list[str] = []
    case_files: list[str] = []
    local_files: list[str] = []
    metadata_files: list[str] = []
    cta_files: list[str] = []
    schema_files: list[str] = []
    image_files: list[str] = []

    for path in root.rglob("*"):
        if should_skip(path):
            continue
        if path.is_dir() and path.name in CONTENT_DIR_NAMES:
            content_dirs.add(rel(path, root))
            continue
        if (
            not path.is_file()
            or path.name in NON_CONTENT_FILENAMES
            or path.suffix.lower() not in SOURCE_EXTENSIONS
        ):
            continue

        relative = rel(path, root)
        lowered = relative.lower()
        text = read_text(path)
        lower_text = text.lower()

        if any(part in lowered.split("/") for part in ("app", "pages", "content", "blog", "posts", "services", "projects")):
            page_files.append(relative)
        if "/services/" in lowered or lowered.startswith("services/"):
            service_files.append(relative)
        if "/blog/" in lowered or "/posts/" in lowered or lowered.startswith("blog/") or lowered.startswith("posts/"):
            blog_files.append(relative)
        if "/projects/" in lowered or "/case" in lowered or lowered.startswith("projects/"):
            case_files.append(relative)
        if "/locations/" in lowered or "/areas/" in lowered or "/service-areas/" in lowered:
            local_files.append(relative)
        if any(signal in lower_text for signal in ("metadata", "meta description", "name=\"description\"", "title:", "<title")):
            metadata_files.append(relative)
        if any(signal in lower_text for signal in ("contact", "quote", "whatsapp", "consultation", "cta", "request")):
            cta_files.append(relative)
        if "schema.org" in lower_text or "application/ld+json" in lower_text or "jsonld" in lower_text:
            schema_files.append(relative)
        if any(signal in lower_text for signal in ("<img", "next/image", "alt=", "image_url", "srcset")):
            image_files.append(relative)

    return {
        "content_dirs": sorted(content_dirs),
        "page_files": sorted(page_files),
        "service_files": sorted(service_files),
        "blog_files": sorted(blog_files),
        "case_files": sorted(case_files),
        "local_files": sorted(local_files),
        "metadata_files": sorted(metadata_files),
        "cta_files": sorted(cta_files),
        "schema_files": sorted(schema_files),
        "image_files": sorted(image_files),
    }


def missing_business_facts(brand_profile: str, services: str, rows: dict[str, list[dict[str, str]]]) -> list[str]:
    missing: list[str] = []
    for line in (brand_profile + "\n" + services).splitlines():
        if "NEEDS OWNER INPUT" in line:
            clean = line.strip("- ").strip()
            if clean and clean not in missing:
                missing.append(clean)
    if not rows["case_studies"]:
        missing.append("No case studies found in case-studies.csv.")
    if not any(row.get("testimonial", "").strip() for row in rows["case_studies"]):
        missing.append("No real testimonials recorded in case-studies.csv.")
    if not any(row.get("verified", "").lower() == "yes" for row in rows["service_areas"]):
        missing.append("No verified service areas recorded in service-areas.csv.")
    return missing[:40]


def priority_keywords(rows: list[dict[str, str]]) -> list[str]:
    def score(row: dict[str, str]) -> tuple[int, int]:
        priority = {"high": 3, "medium": 2, "low": 1}.get(row.get("priority", "").lower(), 0)
        intent = 1 if row.get("search_intent", "").lower() in {"commercial", "transactional"} else 0
        return priority, intent

    selected = sorted(rows, key=score, reverse=True)[:10]
    return [
        f"{row.get('keyword', 'NEEDS OWNER INPUT')} -> `{row.get('target_url') or row.get('current_url') or 'NEEDS OWNER INPUT'}`"
        for row in selected
    ]


def priority_links(rows: list[dict[str, str]]) -> list[str]:
    selected = [row for row in rows if row.get("priority", "").lower() == "high"][:10]
    return [
        f"`{row.get('source_url')}` -> `{row.get('target_url')}` with anchor `{row.get('anchor_text')}`"
        for row in selected
    ]


def main() -> None:
    root = Path.cwd()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    brand_profile = read_text(DATA_DIR / "brand-profile.md")
    services = read_text(DATA_DIR / "services.md")
    rows = {
        "keywords": read_csv(DATA_DIR / "keyword-map.csv"),
        "internal_links": read_csv(DATA_DIR / "internal-links.csv"),
        "case_studies": read_csv(DATA_DIR / "case-studies.csv"),
        "service_areas": read_csv(DATA_DIR / "service-areas.csv"),
    }
    scan = scan_source(root)
    frameworks = detect_framework(root)
    public_report = read_text(REPORTS_DIR / "2026-06-05-public-site-data.md")
    scan_report = read_text(REPORTS_DIR / "seo-content-scan.md")

    service_pages = sorted({
        row.get("target_url") or row.get("current_url")
        for row in rows["keywords"]
        if row.get("page_type", "").lower() in {"service", "service-hub"} and (row.get("target_url") or row.get("current_url"))
    })
    local_pages = sorted({
        row.get("existing_url")
        for row in rows["service_areas"]
        if row.get("existing_url")
    })
    case_pages = sorted({
        row.get("related_url")
        for row in rows["case_studies"]
        if row.get("related_url")
    })

    missing = missing_business_facts(brand_profile, services, rows)
    no_local_source = not scan["content_dirs"] and not frameworks
    today = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

    strengths = [
        "Repo-specific SEO/GEO skill is installed under `.agents/skills/renovation-seo-geo/`.",
        "SEO workspace exists with data, drafts, and reports directories.",
        f"Keyword map has {len(rows['keywords'])} rows.",
        f"Internal link map has {len(rows['internal_links'])} rows.",
        f"Service areas table has {len(rows['service_areas'])} rows.",
        f"Case studies table has {len(rows['case_studies'])} rows.",
    ]
    if public_report:
        strengths.append("Public website data report exists and can support safer drafting.")

    weaknesses = []
    if no_local_source:
        weaknesses.append("No local website source framework or content directories were detected in this workspace.")
    if not scan["metadata_files"]:
        weaknesses.append("No local metadata implementation pattern detected.")
    if not scan["schema_files"]:
        weaknesses.append("No local schema implementation pattern detected.")
    if missing:
        weaknesses.append("Some owner-confirmed business facts are still missing.")
    if not any(Path("seo-workspace/data").glob("*search*console*.csv")):
        weaknesses.append("No Search Console export detected in `seo-workspace/data/`.")

    content_gaps = [
        "Add or confirm exact budget ranges if the owner wants price guidance.",
        "Add exact warranty scope and duration before making warranty claims.",
        "Add Google Business Profile URL and SSM registration details.",
        "Add real testimonials only if owner-approved and published/verified.",
        "Expand case-study data with project year, challenge, solution, and before/after photo notes.",
        "Add Search Console exports for query, page, clicks, impressions, CTR, and average position analysis.",
    ]

    technical_issues = [
        "Verify sitemap and robots from the deployed site during recurring audits.",
        "Confirm canonical, hreflang, and indexation behavior in the live site.",
        "Confirm image optimization and alt text on service, project, and location pages.",
        "Confirm schema accuracy before publishing FAQPage, Service, LocalBusiness, or Review schema.",
    ]
    if no_local_source:
        technical_issues.insert(0, "Local source code is not present here, so publish directories and framework conventions cannot be fully learned from this workspace.")

    plan = [
        "Week 1: Complete onboarding audit, verify business facts, and optimize one high-intent service page draft.",
        "Week 1: Improve kitchen, bathroom, renovation, or office service page metadata/FAQ/internal links.",
        "Week 2: Build or improve real case study drafts using owner-approved project facts.",
        "Week 2: Add local proof and internal links to Kuala Lumpur and Selangor pages.",
        "Week 3: Refresh existing budget, approval, kitchen cabinet, and bathroom waterproofing articles.",
        "Week 3: Review internal links from articles to service pages and quote pages.",
        "Week 4: Review Search Console exports if available and identify CTR/ranking opportunities.",
        "Week 4: Prepare monthly service page, local SEO, case coverage, and technical SEO review.",
    ]

    report = f"""# SEO/GEO Onboarding Report

- Generated: {today}
- Repository: `{root}`
- Skill: `renovation-seo-geo`
- Mode: onboarding
- Publishing status: draft-only; no live page changes

## 1. Website framework

{bullet(frameworks, "No local website framework detected in this workspace.")}
## 2. Content directories

{code_bullet(scan["content_dirs"], "No local content directories detected.")}
## 3. Formal publishing directories

{code_bullet(scan["content_dirs"], "No formal publishing directory could be confirmed from local source. Use CMS or actual website source after owner approval.")}
## 4. Existing service pages

From local source:

{code_bullet(scan["service_files"], "No local service page files detected.")}
From keyword/data files:

{code_bullet(service_pages, "No service URLs found in keyword map.")}
## 5. Existing blog/article pages

{code_bullet(scan["blog_files"], "No local blog/article files detected. Public sitemap should be used until source is available.")}
## 6. Existing case study pages

From local source:

{code_bullet(scan["case_files"], "No local case study files detected.")}
From case data:

{code_bullet(case_pages, "No case study URLs found in case-studies.csv.")}
## 7. Existing local pages

From local source:

{code_bullet(scan["local_files"], "No local local-area files detected.")}
From service-area data:

{code_bullet(local_pages[:30], "No local area URLs found in service-areas.csv.")}
## 8. Metadata conventions

{code_bullet(scan["metadata_files"], "No local metadata pattern detected. Inspect actual source/CMS before publishing.")}
## 9. CTA patterns

{code_bullet(scan["cta_files"], "No local CTA component or copy pattern detected. Use public site data and owner-approved CTAs.")}
## 10. Schema usage

{code_bullet(scan["schema_files"], "No local schema implementation detected. Use schema suggestions only until source/CMS is available.")}
## 11. Image patterns

{code_bullet(scan["image_files"], "No local image pattern detected. Use public project image references and owner-approved alt text.")}
## 12. Sitemap and robots

- Local sitemap/robots files detected: {", ".join(path.as_posix() for path in root.glob("**/sitemap*") if not should_skip(path)) or "None"}
- Public data report available: {"yes" if public_report else "no"}
- SEO content scan report available: {"yes" if scan_report else "no"}

## 13. SEO strengths

{bullet(strengths)}
## 14. SEO weaknesses

{bullet(weaknesses)}
## 15. Content gaps

{bullet(content_gaps)}
## 16. Missing business facts

{bullet(missing, "No obvious missing business facts found. Manual owner review still required.")}
## 17. Priority service pages

{code_bullet(service_pages[:10], "No priority service pages detected.")}
## 18. Priority local pages

{code_bullet(local_pages[:10], "No priority local pages detected.")}
## 19. Priority case studies

{code_bullet(case_pages[:10], "No priority case study URLs detected.")}
## 20. Keyword opportunities

{bullet(priority_keywords(rows["keywords"]), "No keyword opportunities detected.")}
## 21. Internal linking opportunities

{bullet(priority_links(rows["internal_links"]), "No internal linking opportunities detected.")}
## 22. Technical SEO issues

{bullet(technical_issues)}
## 23. Recommended 30-day SEO/GEO plan

{bullet(plan)}
## 24. Next action

Run the daily SEO/GEO workflow in draft-only mode. Start with a high-intent service page optimization plan before creating new articles.
"""
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
