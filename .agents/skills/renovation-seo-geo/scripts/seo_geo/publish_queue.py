#!/usr/bin/env python3
"""Create an owner-approved publishing queue and CMS/source field map."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


QUEUE_FIELDS = [
    "draft_path",
    "target_url",
    "paired_url",
    "page_type",
    "target_kind",
    "table",
    "admin_helper",
    "status",
    "language_scope",
    "rich_text_ready",
    "image_strategy",
    "required_gate",
    "notes",
]


FIELD_MAP = {
    "service": {
        "table": "services",
        "admin_helper": "saveAdminService",
        "source_files": [
            "src/backend/modules/services/service/serviceService.ts",
            "src/backend/modules/services/repository/serviceRepository.ts",
            "src/pages/admin/AdminServiceEditor.tsx",
        ],
        "content_fields": [
            "slug",
            "title_zh",
            "title_en",
            "excerpt_zh",
            "excerpt_en",
            "content_zh",
            "content_en",
            "suitable_for_zh",
            "suitable_for_en",
            "common_projects_zh",
            "common_projects_en",
            "scope_items_zh",
            "scope_items_en",
            "process_steps_zh",
            "process_steps_en",
            "faqs_zh",
            "faqs_en",
            "seo_title_zh",
            "seo_title_en",
            "seo_description_zh",
            "seo_description_en",
            "status",
        ],
        "image_fields": ["image_url", "alt_zh", "alt_en"],
        "rich_text_support": "content_zh/content_en can store HTML text rendered by public pages; additional image blocks need embedded HTML, media assets, or future structured section support.",
        "publish_notes": "Preferred path for service pages. Use saveAdminService so slug cleanup, arrays, FAQ/process JSON, audit, conflict checks, and cache invalidation stay aligned.",
    },
    "blog": {
        "table": "blog_posts",
        "admin_helper": "saveAdminBlogPost",
        "source_files": [
            "src/backend/modules/blog/service/blogService.ts",
            "src/backend/modules/blog/repository/blogRepository.ts",
            "src/pages/admin/AdminBlogEditor.tsx",
            "src/pages/BlogDetail.tsx",
        ],
        "content_fields": [
            "slug",
            "title_zh",
            "title_en",
            "excerpt_zh",
            "excerpt_en",
            "content_zh",
            "content_en",
            "category",
            "tags",
            "seo_title_zh",
            "seo_title_en",
            "seo_description_zh",
            "seo_description_en",
            "status",
            "published_at",
        ],
        "image_fields": ["cover_image_url", "alt_zh", "alt_en"],
        "rich_text_support": "BlogDetail renders HTML content through sanitizeHtml, so multi-section HTML and inline image markup can be represented in content_zh/content_en after QA.",
        "publish_notes": "Article pages require a research source log when using current facts. Use saveAdminBlogPost for audit and publish timestamps.",
    },
    "project": {
        "table": "projects",
        "admin_helper": "saveAdminProject + project_images helpers",
        "source_files": [
            "src/backend/modules/projects/service/projectService.ts",
            "src/backend/modules/projects/repository/projectRepository.ts",
            "src/pages/admin/AdminProjectEditor.tsx",
            "src/pages/admin/AdminProjectImages.tsx",
        ],
        "content_fields": [
            "slug",
            "title_zh",
            "title_en",
            "excerpt_zh",
            "excerpt_en",
            "content_zh",
            "content_en",
            "image_url",
            "location",
            "area",
            "duration",
            "budget",
            "project_type",
            "materials",
            "scope",
            "highlights_zh",
            "highlights_en",
            "client_need_zh",
            "client_need_en",
            "seo_title_zh",
            "seo_title_en",
            "seo_description_zh",
            "seo_description_en",
            "status",
        ],
        "image_fields": ["projects.image_url", "project_images.image_url", "project_images.alt_zh", "project_images.alt_en", "project_images.image_type"],
        "rich_text_support": "Project body fields support text/HTML; gallery images must use project_images records. Generated visuals must be labeled as design/rendering concepts unless real proof exists.",
        "publish_notes": "Use real case wording only with owner-approved facts. Generated visuals can support concept/design pages but cannot be proof photos.",
    },
    "site_page": {
        "table": "site_pages",
        "admin_helper": "saveAdminRecord",
        "source_files": [
            "src/pages/admin/AdminSimpleCms.tsx",
            "src/lib/adminMutation.ts",
            "src/pages/Services.tsx",
            "src/pages/CmsDynamicPage.tsx",
        ],
        "content_fields": [
            "page_key",
            "path",
            "title_zh",
            "title_en",
            "subtitle_zh",
            "subtitle_en",
            "description_zh",
            "description_en",
            "content_zh",
            "content_en",
            "cta_title_zh",
            "cta_title_en",
            "cta_description_zh",
            "cta_description_en",
            "seo_title_zh",
            "seo_title_en",
            "seo_description_zh",
            "seo_description_en",
            "seo_keywords_zh",
            "seo_keywords_en",
            "items_zh",
            "items_en",
            "status",
        ],
        "image_fields": ["image_url", "alt_zh", "alt_en"],
        "rich_text_support": "site_pages content fields are page-level text/HTML; complex repeated sections should use cms_pages/cms_sections where the route supports them.",
        "publish_notes": "Best for hub pages, homepage-like page content, and conversion pages that already read site_pages.",
    },
    "cms_dynamic": {
        "table": "cms_pages + cms_sections",
        "admin_helper": "saveAdminRecord",
        "source_files": [
            "src/pages/admin/AdminCmsBuilder.tsx",
            "src/pages/CmsDynamicPage.tsx",
            "supabase/migrations/202605300001_professional_admin_foundation.sql",
        ],
        "content_fields": [
            "cms_pages.page_key",
            "cms_pages.path",
            "cms_pages.title_zh",
            "cms_pages.title_en",
            "cms_pages.seo_title_zh",
            "cms_pages.seo_title_en",
            "cms_pages.seo_description_zh",
            "cms_pages.seo_description_en",
            "cms_sections.section_key",
            "cms_sections.section_type",
            "cms_sections.title_zh",
            "cms_sections.title_en",
            "cms_sections.content_zh",
            "cms_sections.content_en",
            "cms_sections.settings",
            "cms_sections.status",
        ],
        "image_fields": ["cms_sections.settings.image_url", "cms_sections.content_zh.items[].image", "cms_sections.content_en.items[].image"],
        "rich_text_support": "Best fit for true rich-text section structure: hero, text, item lists, image blocks, and repeated sections.",
        "publish_notes": "Use when a page needs structured sections beyond one cover image plus body. Preserve image alt/caption data inside section JSON.",
    },
    "media": {
        "table": "media_assets",
        "admin_helper": "media upload + media_assets record",
        "source_files": [
            "src/pages/admin/AdminMediaLibrary.tsx",
            "src/components/admin/MediaPicker.tsx",
            "supabase/migrations/202605280002_media_and_home_content.sql",
        ],
        "content_fields": ["file_url", "file_path", "file_name", "mime_type", "size_bytes", "width", "height", "folder", "usage_type", "processing_status"],
        "image_fields": ["alt_zh", "alt_en", "poster_url"],
        "rich_text_support": "Media assets provide reusable files; page records still need image_url/cover_image_url/project_images/cms section references.",
        "publish_notes": "JPG, PNG, or WebP only; keep generated visuals labeled in page captions/alt text.",
    },
}


@dataclass
class QueueItem:
    draft_path: str
    target_url: str
    paired_url: str
    page_type: str
    target_kind: str
    table: str
    admin_helper: str
    status: str
    language_scope: str
    rich_text_ready: str
    image_strategy: str
    required_gate: str
    notes: str

    def as_dict(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in QUEUE_FIELDS}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def extract_value(text: str, label: str) -> str:
    pattern = rf"^- {re.escape(label)}:\s*`?([^`\n]+)`?"
    match = re.search(pattern, text, flags=re.M)
    return match.group(1).strip() if match else ""


def infer_target_kind(target_url: str, page_type: str) -> str:
    path = urlsplit(target_url).path
    if "/services/" in path:
        return "service"
    if "/blog/" in path:
        return "blog"
    if "/projects/" in path:
        return "project"
    if page_type in {"home", "service-hub", "conversion"} or path in {"/en", "/zh", "/en/services", "/zh/services", "/en/quote", "/zh/quote"}:
        return "site_page"
    if page_type in {"local", "article", "case-study-hub"}:
        return "cms_dynamic"
    return "cms_dynamic"


def language_scope(target_url: str, paired_url: str) -> str:
    if target_url and paired_url:
        return "bilingual_pair_required"
    return "single_language_needs_owner_approval"


def image_strategy(kind: str) -> str:
    if kind == "project":
        return "cover image_url plus project_images gallery; generated visuals require concept/rendering labels"
    if kind == "blog":
        return "cover_image_url plus inline rich text images or media assets; source log required for current facts"
    if kind == "service":
        return "primary image_url plus HTML/media image blocks if supported; concept labels required"
    if kind == "cms_dynamic":
        return "cms_sections settings/content JSON can preserve multiple image blocks, captions, and labels"
    if kind == "site_page":
        return "image_url plus content/items JSON; use cms_dynamic if more section-level image control is needed"
    return "media_assets record plus page-specific references"


def build_queue_item(root: Path, draft: Path) -> QueueItem:
    text = read_text(draft)
    target_url = extract_value(text, "目标页面") or extract_value(text, "Target URL")
    paired_url = extract_value(text, "配对页面") or extract_value(text, "Paired URL")
    page_type = extract_value(text, "页面类型")
    kind = infer_target_kind(target_url, page_type)
    mapping = FIELD_MAP[kind]
    return QueueItem(
        draft_path=str(draft.relative_to(root)),
        target_url=target_url,
        paired_url=paired_url,
        page_type=page_type,
        target_kind=kind,
        table=mapping["table"],
        admin_helper=mapping["admin_helper"],
        status="owner_review_required",
        language_scope=language_scope(target_url, paired_url),
        rich_text_ready="yes: package contains Publishing Field Map" if "Publishing Field Map" in text else "partial: convert draft into rich-content package first",
        image_strategy=image_strategy(kind),
        required_gate="owner approval + explicit execution + QA pass + backup + changelog + rollback plan",
        notes=mapping["publish_notes"],
    )


def build_publish_queue(root: Path) -> list[QueueItem]:
    drafts_dir = root / "seo-workspace" / "drafts"
    items: list[QueueItem] = []
    for draft in sorted(drafts_dir.glob("*rich-content-package.md")):
        items.append(build_queue_item(root, draft))
    return items


def website_evidence(website_root: Path | None = None) -> dict[str, object]:
    if not website_root:
        return {"website_root": "", "status": "not_checked"}
    files = []
    for kind, mapping in FIELD_MAP.items():
        present = []
        for source in mapping.get("source_files", []):
            if (website_root / source).exists():
                present.append(source)
        files.append({"target_kind": kind, "present_source_files": present})
    return {"website_root": str(website_root), "status": "checked", "files": files}


def write_field_map(root: Path, website_root: Path | None = None) -> Path:
    output = root / "seo-workspace" / "data" / "publishing-field-map.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "mode": "mapping_only_no_publish",
        "default_gate": "owner approval + explicit execution + QA pass + backup + changelog + rollback plan",
        "field_map": FIELD_MAP,
        "website_evidence": website_evidence(website_root),
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_publish_queue(root: Path) -> Path:
    output = root / "seo-workspace" / "data" / "approved-publish-queue.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    items = build_publish_queue(root)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(item.as_dict() for item in items)
    return output


def render_report(root: Path, queue: list[QueueItem], field_map_path: Path, queue_path: Path, website_root: Path | None = None) -> str:
    today = dt.date.today().isoformat()
    counts: dict[str, int] = {}
    for item in queue:
        counts[item.target_kind] = counts.get(item.target_kind, 0) + 1
    lines = [
        "# Publishing Queue And CMS Field Map",
        "",
        f"- 生成日期: {today}",
        "- 执行模式: mapping / queue-only / no publish",
        f"- Field map: `{field_map_path}`",
        f"- Queue: `{queue_path}`",
        f"- Website root checked: `{website_root or 'not provided'}`",
        "- 执行状态: 等待业主审核和明确执行指令",
        "",
        "## 今日决策",
        "",
        "今天把图文富文本内容包连接到网站实际 CMS/source 字段：先形成审核队列和字段映射，不执行发布。",
        "",
        "## Queue Summary",
        "",
        f"- Rich content packages queued: {len(queue)}",
    ]
    for kind, count in sorted(counts.items()):
        lines.append(f"- {kind}: {count}")
    lines.extend(
        [
            "",
            "## Confirmed Publishing Paths",
            "",
            "- Service pages: `services` table through `saveAdminService`.",
            "- Blog/article pages: `blog_posts` table through `saveAdminBlogPost`; `content_zh/content_en` can carry sanitized HTML.",
            "- Project/case pages: `projects` table through `saveAdminProject`, with gallery records in `project_images`.",
            "- Hub/conversion pages: `site_pages` via `saveAdminRecord` where the public page reads page-level content.",
            "- True section-rich pages: `cms_pages` + `cms_sections` via `saveAdminRecord` when multiple image/text sections must be preserved.",
            "- Media: `media_assets` and page-specific image references; generated visuals must keep concept/rendering labels.",
            "",
            "## Hard Gate Before Any Publish",
            "",
            "- Owner approves the exact queued package.",
            "- Owner explicitly asks to execute it.",
            "- Target record and bilingual scope are confirmed.",
            "- Pre-publish QA passes.",
            "- Backup, changelog, and rollback plan exist.",
            "- SEO manifest, sitemap, llms, and deployment path are regenerated where the website requires it.",
            "",
            "## Not Done Yet",
            "",
            "- This command does not upload media.",
            "- This command does not call Supabase or CMS.",
            "- This command does not publish or deploy.",
            "- A later executor must consume `approved-publish-queue.csv` only after explicit authorization.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_publish_queue_report(root: Path, field_map_path: Path, queue_path: Path, website_root: Path | None = None) -> Path:
    output = root / "seo-workspace" / "reports" / f"{dt.date.today().isoformat()}-publishing-queue-report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(root, build_publish_queue(root), field_map_path, queue_path, website_root), encoding="utf-8")
    return output


def run_publish_queue(root: Path, website_root: str = "") -> tuple[Path, Path, Path]:
    root = root.resolve()
    site_root = Path(website_root).resolve() if website_root else None
    field_map = write_field_map(root, site_root)
    queue = write_publish_queue(root)
    report = write_publish_queue_report(root, field_map, queue, site_root)
    return field_map, queue, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate publishing field map and owner-review queue.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--website-root", default="", help="Optional website source root for evidence checks.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for output in run_publish_queue(Path(args.root), website_root=args.website_root):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
