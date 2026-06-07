#!/usr/bin/env python3
"""Create a safe daily SEO/GEO brief from local workspace data.

The script does not call external APIs, does not use the network, and does not
publish anything. It only writes a dated Markdown draft under seo-workspace.
"""

from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path


DATA_DIR = Path("seo-workspace/data")
DRAFTS_DIR = Path("seo-workspace/drafts")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def priority_score(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(value.lower().strip(), 0)


def is_placeholder(value: str) -> bool:
    lower = value.lower()
    return (
        not value
        or "needs owner input" in lower
        or "replace with real" in lower
        or lower.startswith("example ")
    )


def choose_keyword(rows: list[dict[str, str]]) -> dict[str, str]:
    if not rows:
        return {}

    def sort_key(row: dict[str, str]) -> tuple[int, int, int]:
        target = row.get("target_url") or row.get("current_url")
        commercial = row.get("search_intent", "").lower() in {"commercial", "transactional"}
        usable_target = bool(target and not is_placeholder(target))
        page_type = row.get("page_type", "").lower().strip()
        type_score = {
            "service": 7,
            "local": 6,
            "case-study": 5,
            "case-study-hub": 5,
            "service-hub": 4,
            "article": 3,
            "landing": 2,
            "home": 1,
        }.get(page_type, 0)
        return (
            priority_score(row.get("priority", "")),
            int(commercial),
            type_score,
            int(usable_target),
        )

    return sorted(rows, key=sort_key, reverse=True)[0]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "daily-seo-brief"


def language_pair_urls(target_url: str, keyword: str) -> tuple[str, str]:
    """Return zh/en URL pair when the site pattern is clear."""
    if target_url.startswith("/en/"):
        return target_url.replace("/en/", "/zh/", 1), target_url
    if target_url == "/en":
        return "/zh", "/en"
    if target_url.startswith("/zh/"):
        return target_url, target_url.replace("/zh/", "/en/", 1)
    if target_url == "/zh":
        return "/zh", "/en"
    fallback = f"/{slugify(keyword)}"
    return f"/zh{fallback}", f"/en{fallback}"


def keyword_for_url(rows: list[dict[str, str]], url: str, fallback: str) -> str:
    for row in rows:
        if (row.get("target_url") or row.get("current_url")) == url:
            keyword = row.get("keyword")
            if keyword:
                return keyword
    return fallback


def pick_related_links(rows: list[dict[str, str]], target_url: str) -> list[dict[str, str]]:
    scored: list[tuple[int, dict[str, str]]] = []
    for row in rows:
        score = priority_score(row.get("priority", ""))
        if target_url and row.get("target_url") == target_url:
            score += 2
        scored.append((score, row))
    return [row for _, row in sorted(scored, key=lambda item: item[0], reverse=True)[:5]]


def format_links(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "- NEEDS OWNER INPUT: 需要补充内链机会。\n"
    lines = []
    for row in rows:
        source = row.get("source_url") or "NEEDS OWNER INPUT"
        target = row.get("target_url") or "NEEDS OWNER INPUT"
        anchor = row.get("anchor_text") or "NEEDS OWNER INPUT"
        context = row.get("context") or ""
        lines.append(f"- 来源页面：`{source}` -> 目标页面：`{target}`；锚文本：`{anchor}`；场景：{context}")
    return "\n".join(lines) + "\n"


def contains_real_case(rows: list[dict[str, str]], service: str, location: str) -> bool:
    service = service.lower().strip()
    locations = [part.strip().lower() for part in re.split(r"[;,]", location) if part.strip()]
    for row in rows:
        if any(is_placeholder(row.get(field, "")) for field in ("project_name", "location", "scope", "result")):
            continue
        row_service = row.get("service", "").lower()
        row_location = row.get("location", "").lower()
        service_match = not service or service in row_service or row_service in service
        location_match = not locations or any(name in row_location for name in locations)
        if service_match and location_match:
            return True
    return False


def profile_value(text: str, label: str, fallback: str) -> str:
    prefix = f"- {label}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            value = line.split(":", 1)[1].strip()
            return value or fallback
    return fallback


def missing_profile_items(text: str) -> list[str]:
    items: list[str] = []
    optional_prefixes = (
        "google business profile:",
        "years in business:",
        "insurance/warranty:",
        "project types we do not want:",
        "budget range we accept:",
        "real testimonials:",
        "awards:",
        "media mentions:",
        "before/after photos:",
    )
    for line in text.splitlines():
        if "NEEDS OWNER INPUT" not in line:
            continue
        clean = line.strip("- ").strip()
        if clean.lower().startswith(optional_prefixes):
            continue
        if clean:
            items.append(clean)
    return items


def verified_location(rows: list[dict[str, str]], location: str) -> bool:
    if not location or "NEEDS OWNER INPUT" in location:
        return False
    names = [part.strip().lower() for part in re.split(r"[;,]", location) if part.strip()]
    if not names:
        return False
    verified = {
        row.get("area", "").lower().strip()
        for row in rows
        if row.get("verified", "").lower().strip() == "yes"
    }
    return any(name in verified for name in names)


def main() -> None:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    keyword_rows = read_csv(DATA_DIR / "keyword-map.csv")
    internal_link_rows = read_csv(DATA_DIR / "internal-links.csv")
    case_rows = read_csv(DATA_DIR / "case-studies.csv")
    area_rows = read_csv(DATA_DIR / "service-areas.csv")
    brand_profile = read_text(DATA_DIR / "brand-profile.md")
    services_doc = read_text(DATA_DIR / "services.md")

    selected = choose_keyword(keyword_rows)
    keyword = selected.get("keyword", "NEEDS OWNER INPUT: primary keyword")
    target_url = selected.get("target_url") or selected.get("current_url") or "NEEDS OWNER INPUT: target URL"
    page_type = selected.get("page_type") or "NEEDS OWNER INPUT: page type"
    service = selected.get("service") or "NEEDS OWNER INPUT: service"
    location = selected.get("location") or "NEEDS OWNER INPUT: location if local"
    display_location = location.replace("; ", " and ")
    search_intent = selected.get("search_intent") or "NEEDS OWNER INPUT: search intent"
    customer_stage = selected.get("customer_stage") or "NEEDS OWNER INPUT: customer stage"
    company_name = profile_value(brand_profile, "Company name", "NEEDS OWNER INPUT: Company Name")
    website = profile_value(brand_profile, "Website", "NEEDS OWNER INPUT")
    location_is_verified = verified_location(area_rows, location)
    today = dt.date.today().isoformat()
    filename = f"{today}-{slugify(keyword)}.md"
    output_path = DRAFTS_DIR / filename

    owner_notes = []
    if not keyword_rows:
        owner_notes.append("NEEDS OWNER INPUT: keyword-map.csv has no usable keyword rows.")
    if not brand_profile:
        owner_notes.append("NEEDS OWNER INPUT: Complete seo-workspace/data/brand-profile.md with real company facts.")
    for item in missing_profile_items(brand_profile)[:8]:
        owner_notes.append(f"NEEDS OWNER INPUT: {item}")
    if "Replace this" in services_doc or not services_doc:
        owner_notes.append("NEEDS OWNER INPUT: Complete seo-workspace/data/services.md with real services.")
    if location and "NEEDS OWNER INPUT" not in location and not location_is_verified:
        owner_notes.append(f"NEEDS OWNER INPUT: Confirm service area before publishing local claims for {location}.")
    elif not any(row.get("verified", "").lower() == "yes" for row in area_rows):
        owner_notes.append("NEEDS OWNER INPUT: Add verified service areas before publishing local claims.")
    has_real_case = contains_real_case(case_rows, selected.get("service", ""), selected.get("location", ""))
    content_mode = (
        "真实案例优化"
        if page_type.lower().strip() == "case-study" and has_real_case
        else "页面优化 + 设计方案 / 效果图方案"
    )

    if not owner_notes:
        owner_notes.append("没有阻塞项；但发布前仍需要人工审核。")

    links = pick_related_links(internal_link_rows, target_url if "NEEDS OWNER INPUT" not in target_url else "")
    recommended_slug = target_url if target_url.startswith("/") else f"/{slugify(keyword)}"
    zh_url, en_url = language_pair_urls(recommended_slug, keyword)
    zh_keyword = keyword_for_url(keyword_rows, zh_url, keyword)
    en_keyword = keyword_for_url(keyword_rows, en_url, keyword)

    bilingual_copy_note = f"""
## 4A. 中文页面建议文案

如果这次优化会用于中文页面，可先使用以下中文方向作为待审核素材：

- 建议 SEO title：{zh_keyword} | {company_name}
- 建议 meta description：了解 {zh_keyword} 的服务范围、设计方案、效果图方向、材料选择、施工流程，以及什么时候适合预约装修咨询。
- 建议 H1：{zh_keyword}
- 建议开头方向：帮助客户理解 `{service}`，重点说明服务范围、设计方案、效果图方向、材料选择、流程和下一步咨询方式。

NEEDS OWNER INPUT: 正式发布前请确认中文文案是否符合品牌语气和实际服务范围。

## 4B. 英文页面建议文案

如果这次优化会用于英文页面，可先使用以下英文方向作为待审核素材：

- Suggested SEO title: {en_keyword.title()} | {company_name}
- Suggested meta description: Explore {en_keyword} scope, design concepts, rendering direction, material choices, process, and when to request a renovation consultation.
- Suggested H1: {en_keyword.title()}
- Suggested opening angle: Help customers understand `{service}` with practical guidance on scope, design concepts, rendering direction, material choices, process, and next steps.

NEEDS OWNER INPUT: 正式发布前请确认英文文案是否符合品牌语气和实际服务范围。
"""

    brief = f"""# Daily SEO/GEO Recommendation

日期：{today}
网站：{website}
使用 Skill：renovation-seo-geo
语言：中文审核版

## 1. 今日决策

为 `{page_type}` 内容创建一份可审核的 SEO/GEO 草稿或优化方案。默认不发布、不修改正式页面。

## 2. 目标

- 页面或建议页面：`{target_url}`
- 中文页面：`{zh_url}`
- 英文页面：`{en_url}`
- 内容类型：{content_mode}
- Primary keyword：{en_keyword}
- 中文 primary keyword：{zh_keyword}
- Secondary keywords：NEEDS OWNER INPUT: 需要补充自然相关关键词
- Search intent：{search_intent}
- Customer stage：{customer_stage}

## 3. 为什么今天做这个

这个关键词来自 `seo-workspace/data/keyword-map.csv`，选择依据是优先级、搜索意图和已有目标 URL。这个任务比随机写新文章更有价值，因为它围绕已有页面或明确商业意图关键词，可以更直接支持服务页质量、询盘路径和后续转化。

正式发布前仍需要确认：该关键词、服务项目和 URL 是否仍是当前业务优先级。

## 4. 草稿或优化方案

### 建议内容角度

帮助真实装修客户理解 `{service}`，重点说明服务范围、设计方案、效果图方向、材料选择、预算/工期影响因素、流程、风险和下一步咨询方式。

### 建议 H1/H2/H3 结构

1. 开头直接回答搜索意图
2. 适合哪些客户
3. 服务包含什么
4. 常见客户问题
5. 装修流程
6. 预算和工期影响因素
7. 材料或设计选择
8. 效果图方案、概念设计或真实项目证明
9. FAQ
10. CTA

### 起草注意事项

- 只使用 `seo-workspace/data/services.md` 中已确认的真实服务。
- 只使用 `seo-workspace/data/service-areas.csv` 中已验证的真实地区。
- 如无真实案例，可使用明确标注为“效果图方案 / 概念设计 / 规划示例”的内容，不写成真实完工案例。
- 不确定的事实性声明统一标记为 `NEEDS OWNER INPUT`。
{bilingual_copy_note}

## 5. Metadata

- SEO title：{en_keyword.title()} | {company_name}
- Meta description：Explore {en_keyword} scope, design concepts, rendering direction, material choices, process, and when to request a renovation consultation.
- 中文 SEO title：{zh_keyword} | {company_name}
- 中文 meta description：了解 {zh_keyword} 的服务范围、设计方案、效果图方向、材料选择、施工流程，以及什么时候适合预约装修咨询。
- Suggested slug：`{recommended_slug}`
- 中文 slug：`{zh_url}`
- 英文 slug：`{en_url}`
- H1: {keyword.title()}

## 6. FAQ

### {zh_keyword} 通常多少钱？

页面不写未经确认的固定价格。建议说明影响报价的因素，例如空间大小、拆改范围、材料选择、柜体或定制项目、机电水路调整和现场条件，并引导客户预约咨询获取报价。

### {zh_keyword} 通常需要多久？

页面不承诺未经确认的固定工期。建议说明影响工期的因素，例如设计确认、材料供货、现场拆除、水电或防水工程、定制安装和验收安排。

### 联系装修公司前应该准备什么？

建议准备房屋类型、大致装修范围、期望时间、预算方向、现场照片，以及喜欢的布局或材料参考。

### 这个服务可以覆盖 {display_location} 吗？

{"可以。这个地区已经出现在 `seo-workspace/data/service-areas.csv` 的已验证服务区域中。" if location_is_verified else "NEEDS OWNER INPUT: 发布任何本地服务声明前，需要确认这个服务区域。"}

## 7. 内链建议

{format_links(links)}
## 8. 图片建议和 alt text

- 图片建议：使用 `{service}` 的效果图、3D 渲染图、布局方案图或材料搭配图，并在页面中标注为“效果图方案 / 概念设计 / 参考方案”。
- Alt text：`{service} rendering concept by {company_name}`
- 图片建议：使用与页面主题相关的材料、饰面、柜体、台面、瓷砖或空间规划细节图。
- Alt text：`{service} material and layout concept for renovation planning`

## 9. Schema 建议

- 服务页建议使用 `Service`。
- 教育文章建议使用 `Article`。
- 如果 FAQ 真实显示在页面上，可以使用 `FAQPage`。
- 如果页面有面包屑，可以使用 `BreadcrumbList`。
- 不要使用 `Review` schema，除非页面上真实展示了已确认的评价数据。

## 10. 业主审核备注

{chr(10).join(f"- {note}" for note in owner_notes)}

## 11. 执行状态

- 状态：等待业主审核。
- 执行规则：业主明确审核通过并要求 Codex 执行之前，不发布、不应用修改。

## 12. QA checklist

- 准确性已检查：等待业主审核
- 没有虚假声明：等待业主审核
- 没有虚假评价：是
- 没有虚假案例：是
- 如果使用效果图/概念设计，已经明确标注：是
- 没有不支持的服务区域：等待业主审核
- 没有关键词堆砌：是
- 对真实装修客户有帮助：等待最终草稿确认
- CTA 清楚：等待业主审核
- 已包含内链：是
- 已包含 metadata：是
- 已在适合位置加入 FAQ：是
- 缺失资料已清楚标记：是
- 发布前需要人工审核：是

## 5 行日报

- 已完成：已创建一份中文审核版 SEO/GEO brief 草稿。
- 目标关键词/页面：{zh_keyword} + {en_keyword} / `{zh_url}` + `{en_url}`
- 预期收益：围绕一个优先关键词和目标页面形成可审核的页面优化方向。
- 需要业主补充：如服务范围、服务区域或 CTA 有变化，请补充；真实案例、图片、预算、工期、保修和评价不是本草稿的阻塞项。
- 建议下一步：你先审核这份草稿；确认后再告诉 Codex 执行具体优化方案。
"""

    output_path.write_text(brief, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
