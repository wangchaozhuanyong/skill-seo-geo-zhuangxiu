#!/usr/bin/env python3
"""Convert a rich-content Markdown package into structured blocks and CMS payload drafts."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


BLOCKS_JSON_NAME = "rich-content-blocks.json"
CMS_PAYLOAD_JSON_NAME = "rich-content-cms-payload.json"


@dataclass
class ImageSpec:
    slot: str
    zh_slot: str
    en_slot: str
    labels: str
    alt_zh: str
    alt_en: str
    caption: str
    filename: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def extract_value(text: str, label: str) -> str:
    pattern = rf"^- {re.escape(label)}:\s*`?([^`\n]+)`?"
    match = re.search(pattern, text, flags=re.M)
    return match.group(1).strip() if match else ""


def slug_from_url(url: str) -> str:
    path = urlsplit(url).path or url
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return slug or "rich-content"


def infer_slug(target_url: str) -> str:
    path = urlsplit(target_url).path.strip("/")
    return path.split("/")[-1] if path else "home"


def find_source_draft(root: Path, *, target_url: str = "", draft_path: str = "") -> Path:
    if draft_path:
        path = Path(draft_path)
        return path if path.is_absolute() else root / path
    drafts = sorted((root / "seo-workspace" / "drafts").glob("*rich-content-package.md"))
    if target_url:
        for draft in drafts:
            text = read_text(draft)
            if target_url in {extract_value(text, "目标页面"), extract_value(text, "配对页面")}:
                return draft
    if not drafts:
        raise RuntimeError("No rich-content package found. Run rich-content first.")
    return drafts[-1]


def parse_image_specs(text: str) -> list[ImageSpec]:
    specs: list[ImageSpec] = []
    pattern = re.compile(r"^### Image Block\s+\d+:\s*(?P<slot>.+?)\n(?P<body>.*?)(?=^### Image Block|\Z)", re.M | re.S)
    for match in pattern.finditer(text):
        body = match.group("body")
        spec = ImageSpec(
            slot=match.group("slot").strip(),
            zh_slot=extract_bullet(body, "中文图位") or "效果图方案",
            en_slot=extract_bullet(body, "English slot") or "rendering concept",
            labels=extract_bullet(body, "标签") or "概念设计 / rendering concept",
            alt_zh=extract_bullet(body, "中文 alt") or "FLASH CAST 装修效果图方案",
            alt_en=extract_bullet(body, "English alt") or "FLASH CAST renovation rendering concept",
            caption=extract_bullet(body, "图注") or "此图为规划/效果图方案，不作为真实完工案例或客户照片。",
            filename=extract_bullet(body, "Suggested filename").strip("`") or f"flash-cast-{slug_from_url(match.group('slot'))}.webp",
        )
        specs.append(spec)
    return specs


def extract_bullet(text: str, label: str) -> str:
    pattern = rf"^- {re.escape(label)}[:：]\s*(.+)$"
    match = re.search(pattern, text, flags=re.M)
    return match.group(1).strip() if match else ""


def fallback_images(page_type: str) -> list[ImageSpec]:
    slots = [
        ("hero rendering concept", "服务页效果图方案主图", "service page rendering concept"),
        ("layout planning concept", "布局规划示例图", "layout planning concept"),
        ("material mood board", "材料与饰面方向图", "material and finish mood board"),
    ]
    if page_type == "article":
        slots = [
            ("article hero concept", "文章主题说明图", "article hero concept"),
            ("step planning graphic", "步骤规划图", "step planning graphic"),
            ("service CTA visual", "服务咨询 CTA 图", "service CTA visual"),
        ]
    return [
        ImageSpec(
            slot=slot,
            zh_slot=zh_slot,
            en_slot=en_slot,
            labels="概念设计 / 效果图方案 / 规划示例 + design concept / rendering concept / planning example",
            alt_zh=f"FLASH CAST {zh_slot}，用于装修内容规划说明",
            alt_en=f"FLASH CAST {en_slot} for renovation planning content",
            caption="此图为规划/效果图方案，不作为真实完工案例或客户照片。",
            filename=f"flash-cast-{slug_from_url(slot)}.webp",
        )
        for slot, zh_slot, en_slot in slots
    ]


def image_prompt(spec: ImageSpec, *, language: str, topic: str) -> str:
    if language == "zh":
        return (
            f"为 FLASH CAST 装修网站生成 {spec.zh_slot}：{topic}。"
            "现代马来西亚住宅/商业装修视觉，真实材质质感，清晰空间动线，适合网页图文排版。"
            "必须是概念设计/效果图方案，不要包含真实客户、真实门牌、评价截图、价格或完工证明。"
        )
    return (
        f"Create a FLASH CAST renovation {spec.en_slot} for {topic}. "
        "Modern Malaysia renovation visual, realistic materials, clear layout flow, suitable for image-rich web content. "
        "This must be a design concept/rendering concept, not a real client photo, review, price proof, or completed-project evidence."
    )


def block(block_id: str, block_type: str, **values: object) -> dict[str, object]:
    return {"id": block_id, "type": block_type, **values}


def is_shop_renovation_page(topic: str, keyword: str, target_url: str) -> bool:
    text = " ".join([topic, keyword, target_url]).lower()
    return "shop-renovation" in text or "shop renovation" in text or "retail fit-out" in text


def shop_renovation_copy(is_zh: bool) -> dict[str, object]:
    if is_zh:
        return {
            "heading": "马来西亚店铺装修与零售空间图文方案",
            "intro": "这是一份用于店铺装修服务页的图文内容结构，重点说明开店前准备、展示动线、柜台与收纳、材料方向、效果图方案、FAQ 和咨询路径。",
            "quick_heading": "快速答案",
            "quick_body": "适合准备装修 shoplot、零售门店、展示空间、beauty 或 clinic 前场、小型餐饮与商业空间的业主。页面应先帮助访客确认店面照片、面积、营业类型、租约交付状态、管理方要求和预计开业时间。",
            "scope_heading": "店铺装修规划范围",
            "scope_body": "正文可覆盖顾客动线、展示区、收银柜台、后场收纳、员工操作区、门头入口、照明、材料饰面、机电协调和报价前资料准备。不要写固定价格、固定工期、保修承诺或未确认服务区域。",
            "image_body": "店铺装修规划/效果图方案说明图。",
            "process_heading": "建议店铺装修流程",
            "process_items": ["整理店面照片、面积与营业类型", "确认顾客动线、展示区和柜台收纳", "选择材料方向与效果图方案", "通过报价或联系页面提交开店前需求"],
            "links_heading": "相关服务",
            "links": [
                {"label": "商业空间与办公室装修", "href": "/zh/services/office-renovation"},
                {"label": "柜台木作与定制收纳", "href": "/zh/services/builtin"},
                {"label": "装修申请与图纸协调", "href": "/zh/services/approval"},
            ],
            "faq_heading": "常见问题",
            "faq_items": [
                {"question": "店铺装修前需要准备什么资料？", "answer": "建议先准备店面照片、面积、营业类型、租约交付状态、管理方要求和预计开业时间，方便判断动线、柜台、展示和施工协调重点。"},
                {"question": "这些图片是真实完工案例吗？", "answer": "不是。这里的图片按概念设计、效果图方案或规划示例使用，不能作为真实客户案例或完工证明。"},
                {"question": "哪些因素会影响店铺装修报价与安排？", "answer": "面积、拆改、照明机电、柜台木作、展示系统、门头、施工时段限制和目标开业时间都会影响范围与安排。"},
            ],
            "cta_heading": "获取店铺装修规划建议",
            "cta_body": "提交店面照片、面积、营业类型和预计开业时间，先确认适合的 retail fit-out 规划方向。",
            "cta_label": "获取店铺装修报价 / 咨询",
        }
    return {
        "heading": "Shop Renovation Malaysia Retail Fit-Out Plan",
        "intro": "This image-rich service page structure explains pre-opening preparation, customer flow, display planning, counter and storage needs, material direction, rendering concepts, FAQ, and consultation paths for shop renovation.",
        "quick_heading": "Quick Answer",
        "quick_body": "This page is for owners planning a shoplot, retail store, showroom, beauty or clinic front area, small F&B outlet, or commercial fit-out. It should help visitors prepare shop photos, floor area, business type, tenancy handover status, landlord or mall requirements, and target opening date.",
        "scope_heading": "Shop Fit-Out Planning Scope",
        "scope_body": "The copy can cover customer flow, product display, cashier counter, back-of-house storage, staff workflow, frontage visibility, lighting, material finishes, M&E coordination, and quotation preparation. Do not state fixed prices, fixed timelines, warranty promises, or unsupported service areas.",
        "image_body": "Shop renovation planning/rendering concept image.",
        "process_heading": "Suggested Shop Renovation Flow",
        "process_items": ["Prepare shop photos, floor area, and business type", "Confirm customer flow, display zones, counter, and storage needs", "Select material direction and rendering concept", "Submit pre-opening requirements through quote or contact"],
        "links_heading": "Related Services",
        "links": [
            {"label": "office renovation and commercial fit-out", "href": "/en/services/office-renovation"},
            {"label": "counter carpentry and custom built-in storage", "href": "/en/services/builtin"},
            {"label": "approval and drawing support", "href": "/en/services/approval"},
        ],
        "faq_heading": "FAQ",
        "faq_items": [
            {"question": "What should I prepare before starting a shop renovation?", "answer": "Prepare current shop photos, floor area, business type, tenancy handover status, landlord or mall requirements, and target opening date so the fit-out scope can be reviewed clearly."},
            {"question": "Are these images completed real projects?", "answer": "No. These images are design concepts, rendering concepts, or planning examples, not real customer cases or proof of completion."},
            {"question": "What affects quotation and scheduling for a retail fit-out?", "answer": "Floor area, demolition, lighting and M&E works, counter carpentry, display systems, frontage work, access restrictions, and target opening date all affect scope and scheduling."},
        ],
        "cta_heading": "Request Shop Renovation Planning Advice",
        "cta_body": "Share your shop photos, floor area, business type, and opening target to confirm a suitable retail fit-out planning direction.",
        "cta_label": "Request a Shop Renovation Quote",
    }


def build_language_blocks(language: str, *, topic: str, keyword: str, target_url: str, paired_url: str, images: list[ImageSpec]) -> list[dict[str, object]]:
    is_zh = language == "zh"
    quote_url = "/zh/quote" if is_zh else "/en/quote"
    service_url = paired_url if is_zh and "/zh/" in paired_url else target_url
    profile = shop_renovation_copy(is_zh) if is_shop_renovation_page(topic, keyword, target_url) else {}
    heading = str(profile.get("heading") or (f"{topic} 图文装修方案" if is_zh else f"{topic} Image-Rich Renovation Plan"))
    intro = str(
        profile.get("intro")
        or (
            f"这是一份用于 {topic} 的页面级图文内容结构，重点说明服务范围、规划逻辑、效果图方案、FAQ 和咨询路径。"
            if is_zh
            else f"This page-ready structure for {topic} explains service scope, planning logic, rendering concepts, FAQ, and consultation paths."
        )
    )
    blocks: list[dict[str, object]] = [
        block(
            "hero",
            "hero",
            heading=heading,
            body=intro,
            target_url=service_url,
            keyword=keyword,
            image=media_placeholder(images[0], language=language, topic=topic) if images else {},
        ),
        block(
            "quick-answer",
            "text",
            heading=str(profile.get("quick_heading") or ("快速答案" if is_zh else "Quick Answer")),
            body=str(
                profile.get("quick_body")
                or (
                    "适合准备改造厨房、浴室、住宅或商业空间的业主。页面应先帮助访客理解可以规划什么、如何沟通需求，以及为什么需要先确认空间、材料和动线。"
                    if is_zh
                    else "This is for owners planning kitchen, bathroom, residential, or commercial renovation. The page should first clarify what can be planned, how requirements are discussed, and why layout, materials, and workflow matter."
                )
            ),
        ),
        block(
            "scope",
            "text",
            heading=str(profile.get("scope_heading") or ("服务与规划范围" if is_zh else "Service and Planning Scope")),
            body=str(
                profile.get("scope_body")
                or (
                    "正文可覆盖布局规划、收纳、照明、材料方向、施工沟通和报价前准备。不要写固定价格、固定工期、保修承诺或未确认服务区域。"
                    if is_zh
                    else "The copy can cover layout planning, storage, lighting, material direction, construction coordination, and quote preparation. Do not state fixed prices, fixed timelines, warranty promises, or unsupported service areas."
                )
            ),
        ),
    ]
    for index, spec in enumerate(images[1:] or images[:1], start=1):
        blocks.append(
            block(
                f"image-{index}",
                "image",
                heading=spec.zh_slot if is_zh else spec.en_slot,
                body=str(profile.get("image_body") or ("规划/效果图方案说明图。" if is_zh else "Planning/rendering concept image.")),
                image=media_placeholder(spec, language=language, topic=topic),
            )
        )
    blocks.extend(
        [
            block(
                "process",
                "steps",
                heading=str(profile.get("process_heading") or ("建议页面流程" if is_zh else "Suggested Page Flow")),
                items=(
                    profile.get("process_items")
                    or ["理解需求", "确认空间与材料方向", "输出设计/效果图方案", "引导咨询或报价"]
                    if is_zh
                    else profile.get("process_items")
                    or ["Understand requirements", "Confirm space and material direction", "Prepare design/rendering concept", "Guide consultation or quote request"]
                ),
            ),
            block(
                "internal-links",
                "links",
                heading=str(profile.get("links_heading") or ("相关服务" if is_zh else "Related Services")),
                items=profile.get("links") or [],
            ),
            block(
                "faq",
                "faq",
                heading=str(profile.get("faq_heading") or ("常见问题" if is_zh else "FAQ")),
                items=(
                    profile.get("faq_items")
                    or [
                        {"question": "这些图片是真实完工案例吗？", "answer": "不是。这里的图片按概念设计、效果图方案或规划示例使用，不能作为真实客户案例或完工证明。"},
                        {"question": "可以用真实案例资料吗？", "answer": "可以，但必须使用业主确认的真实项目事实、图片和边界说明。"},
                    ]
                    if is_zh
                    else profile.get("faq_items")
                    or [
                        {"question": "Are these images completed real projects?", "answer": "No. These images are design concepts, rendering concepts, or planning examples, not real customer cases or proof of completion."},
                        {"question": "Can real case material be used?", "answer": "Yes, but only with owner-confirmed project facts, images, and clear claim boundaries."},
                    ]
                ),
            ),
            block(
                "cta",
                "cta",
                heading=str(profile.get("cta_heading") or ("获取装修规划建议" if is_zh else "Request Renovation Planning Advice")),
                body=str(profile.get("cta_body") or ("发送空间需求，先确认适合的装修规划方向。" if is_zh else "Share your space requirements to confirm a suitable renovation planning direction.")),
                href=quote_url,
                label=str(profile.get("cta_label") or ("获取报价 / 咨询" if is_zh else "Request a Quote")),
            ),
        ]
    )
    return blocks


def media_placeholder(spec: ImageSpec, *, language: str, topic: str) -> dict[str, object]:
    return {
        "filename": spec.filename,
        "slot": spec.zh_slot if language == "zh" else spec.en_slot,
        "alt": spec.alt_zh if language == "zh" else spec.alt_en,
        "caption": caption_for_language(spec, language),
        "concept_label": "概念设计 / 效果图方案 / design concept / rendering concept",
        "prompt": image_prompt(spec, language=language, topic=topic),
        "status": "needs_generation_or_owner_asset_selection",
    }


def caption_for_language(spec: ImageSpec, language: str) -> str:
    if language == "zh":
        return spec.caption
    return "This image is a planning/rendering concept, not a completed real project or customer photo."


def render_html(blocks: list[dict[str, object]], *, language: str) -> str:
    parts: list[str] = []
    for item in blocks:
        block_type = item.get("type")
        heading = html.escape(str(item.get("heading", "")))
        body = html.escape(str(item.get("body", "")))
        if block_type == "hero":
            parts.append(f"<section class=\"seo-rich-block seo-rich-hero\"><h1>{heading}</h1><p>{body}</p>{render_figure(item)}</section>")
        elif block_type == "text":
            parts.append(f"<section class=\"seo-rich-block\"><h2>{heading}</h2><p>{body}</p></section>")
        elif block_type == "image":
            parts.append(f"<section class=\"seo-rich-block seo-rich-image\"><h2>{heading}</h2><p>{body}</p>{render_figure(item)}</section>")
        elif block_type == "steps":
            steps = "".join(f"<li>{html.escape(str(step))}</li>" for step in item.get("items", []))
            parts.append(f"<section class=\"seo-rich-block\"><h2>{heading}</h2><ol>{steps}</ol></section>")
        elif block_type == "faq":
            faq_items = []
            for faq in item.get("items", []):
                if isinstance(faq, dict):
                    faq_items.append(f"<details><summary>{html.escape(str(faq.get('question', '')))}</summary><p>{html.escape(str(faq.get('answer', '')))}</p></details>")
            parts.append(f"<section class=\"seo-rich-block seo-rich-faq\"><h2>{heading}</h2>{''.join(faq_items)}</section>")
        elif block_type == "links":
            links = []
            for link in item.get("items", []):
                if isinstance(link, dict):
                    href = html.escape(str(link.get("href", "")))
                    label = html.escape(str(link.get("label", "")))
                    if href and label:
                        links.append(f"<li><a href=\"{href}\">{label}</a></li>")
            if links:
                parts.append(f"<section class=\"seo-rich-block seo-rich-internal-links\"><h2>{heading}</h2><ul>{''.join(links)}</ul></section>")
        elif block_type == "cta":
            href = html.escape(str(item.get("href", "")))
            label = html.escape(str(item.get("label", "")))
            parts.append(f"<section class=\"seo-rich-block seo-rich-cta\"><h2>{heading}</h2><p>{body}</p><a href=\"{href}\">{label}</a></section>")
    note = "以上图片为概念设计/效果图方案，不代表真实完工案例。" if language == "zh" else "Images above are design/rendering concepts, not completed real project proof."
    parts.append(f"<p class=\"seo-rich-disclaimer\">{html.escape(note)}</p>")
    return "\n".join(parts)


def render_figure(item: dict[str, object]) -> str:
    image = item.get("image", {})
    if not isinstance(image, dict) or not image:
        return ""
    src = html.escape(str(image.get("filename", "")))
    alt = html.escape(str(image.get("alt", "")))
    caption = html.escape(str(image.get("caption", "")))
    label = html.escape(str(image.get("concept_label", "")))
    return f"<figure><img src=\"{src}\" alt=\"{alt}\" loading=\"lazy\" /><figcaption>{caption} <strong>{label}</strong></figcaption></figure>"


def page_metadata(text: str) -> dict[str, str]:
    return {
        "target_url": extract_value(text, "目标页面"),
        "paired_url": extract_value(text, "配对页面"),
        "page_type": extract_value(text, "页面类型"),
        "keyword": extract_value(text, "目标关键词"),
        "topic": extract_value(text, "主题"),
        "brand": extract_value(text, "品牌") or "FLASH CAST",
    }


def build_structured_payload(source_draft: Path, text: str) -> dict[str, object]:
    meta = page_metadata(text)
    topic = meta["topic"] or meta["keyword"] or meta["target_url"]
    images = parse_image_specs(text) or fallback_images(meta["page_type"])
    blocks_zh = build_language_blocks("zh", topic=topic, keyword=meta["keyword"], target_url=meta["target_url"], paired_url=meta["paired_url"], images=images)
    blocks_en = build_language_blocks("en", topic=topic, keyword=meta["keyword"], target_url=meta["target_url"], paired_url=meta["paired_url"], images=images)
    html_zh = render_html(blocks_zh, language="zh")
    html_en = render_html(blocks_en, language="en")
    media = [
        media_placeholder(spec, language="en", topic=topic)
        | {
            "alt_zh": spec.alt_zh,
            "alt_en": spec.alt_en,
            "caption_zh": caption_for_language(spec, "zh"),
            "caption_en": caption_for_language(spec, "en"),
        }
        for spec in images
    ]
    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source_draft": str(source_draft),
        "status": "draft_only_no_cms_write",
        "no_cms_write_executed": True,
        "metadata": meta,
        "blocks_zh": blocks_zh,
        "blocks_en": blocks_en,
        "html": {"content_zh": html_zh, "content_en": html_en},
        "media_placeholders": media,
        "cms_payload_draft": build_cms_payload(meta, html_zh=html_zh, html_en=html_en, media=media),
    }


def build_cms_payload(meta: dict[str, str], *, html_zh: str, html_en: str, media: list[dict[str, object]]) -> dict[str, object]:
    topic = meta["topic"] or meta["keyword"] or "Renovation Planning"
    brand = meta["brand"] or "FLASH CAST"
    first_media = media[0] if media else {}
    if is_shop_renovation_page(topic, meta.get("keyword", ""), meta.get("target_url", "")):
        title_zh = "马来西亚店铺装修与零售空间图文方案"
        title_en = "Shop Renovation Malaysia Retail Fit-Out Plan"
        excerpt_zh = f"{brand} 店铺装修图文内容草案，包含开店前准备、展示动线、柜台收纳、材料方向、效果图方案、FAQ 和咨询 CTA。"
        excerpt_en = f"{brand} image-rich draft for shop renovation and retail fit-out planning, including pre-opening preparation, customer flow, counter and storage planning, rendering concepts, FAQ, and consultation CTA."
        seo_title_zh = f"{brand} | 马来西亚店铺装修与零售空间规划"
        seo_title_en = f"{brand} | Shop Renovation Malaysia | Retail Fit-Out Planning"
        seo_description_zh = "FLASH CAST 店铺装修双语图文草案，覆盖 shoplot、零售门店、展示空间、柜台收纳、开店前准备、效果图方案、FAQ 和咨询路径。"
        seo_description_en = "Bilingual shop renovation and retail fit-out draft for FLASH CAST, covering shoplot planning, customer flow, display zones, counter storage, rendering concepts, FAQ, and quote path."
    else:
        title_zh = f"{topic} 图文装修方案"
        title_en = f"{topic} Image-Rich Renovation Plan"
        excerpt_zh = f"{brand} {topic} 页面图文内容草案，包含概念设计、效果图方案、FAQ 和咨询 CTA。"
        excerpt_en = f"{brand} image-rich draft for {topic}, including design concepts, rendering concepts, FAQ, and consultation CTA."
        seo_title_zh = f"{brand} | {topic} | 图文装修方案"
        seo_title_en = f"{brand} | {topic} | Image-Rich Renovation Plan"
        seo_description_zh = f"{topic} 的双语图文装修内容草案，包含规划示例、效果图方案、FAQ、图片 alt 和咨询路径。"
        seo_description_en = f"Bilingual image-rich renovation draft for {topic}, including planning examples, rendering concepts, FAQ, image alt text, and consultation path."
    return {
        "target_kind": "service" if "/services/" in meta["target_url"] else "cms_dynamic_or_blog",
        "table": "services" if "/services/" in meta["target_url"] else "cms_pages_or_blog_posts",
        "admin_helper": "saveAdminService" if "/services/" in meta["target_url"] else "saveAdminRecord_or_saveAdminBlogPost",
        "payload": {
            "slug": infer_slug(meta["target_url"]),
            "title_zh": title_zh,
            "title_en": title_en,
            "excerpt_zh": excerpt_zh,
            "excerpt_en": excerpt_en,
            "content_zh": html_zh,
            "content_en": html_en,
            "image_url": f"NEEDS_MEDIA_UPLOAD:{first_media.get('filename', '')}",
            "alt_zh": first_media.get("alt_zh", ""),
            "alt_en": first_media.get("alt_en", ""),
            "seo_title_zh": seo_title_zh,
            "seo_title_en": seo_title_en,
            "seo_description_zh": seo_description_zh,
            "seo_description_en": seo_description_en,
            "status": "draft",
        },
    }


def render_preview(payload: dict[str, object]) -> str:
    meta = payload.get("metadata", {})
    html_payload = payload.get("html", {})
    target = html.escape(str(meta.get("target_url", ""))) if isinstance(meta, dict) else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Rich Content Preview</title>
  <style>
    body {{ font-family: Georgia, serif; max-width: 980px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1b1b18; }}
    figure {{ margin: 24px 0; padding: 18px; background: #f4efe6; border: 1px solid #dbcdb8; }}
    img {{ display: block; width: 100%; max-height: 360px; object-fit: cover; background: #d8d0c2; }}
    figcaption {{ margin-top: 10px; font-size: 0.95rem; }}
    section {{ margin: 36px 0; }}
    .seo-rich-cta {{ padding: 24px; background: #17352d; color: white; }}
    .seo-rich-cta a {{ color: #ffe0a3; }}
    .seo-rich-disclaimer {{ font-size: 0.9rem; border-top: 1px solid #ddd; padding-top: 16px; }}
  </style>
</head>
<body>
  <p><strong>Target:</strong> {target}</p>
  <h1>中文预览</h1>
  {html_payload.get("content_zh", "") if isinstance(html_payload, dict) else ""}
  <hr>
  <h1>English Preview</h1>
  {html_payload.get("content_en", "") if isinstance(html_payload, dict) else ""}
</body>
</html>
"""


def render_report(payload: dict[str, object], blocks_path: Path, cms_path: Path, preview_path: Path) -> str:
    meta = payload.get("metadata", {})
    media = payload.get("media_placeholders", [])
    cms_payload = payload.get("cms_payload_draft", {})
    return "\n".join(
        [
            "# Structured Rich Content Blocks Report",
            "",
            f"- 生成日期: {dt.date.today().isoformat()}",
            f"- Target URL: `{meta.get('target_url', 'N/A') if isinstance(meta, dict) else 'N/A'}`",
            f"- Paired URL: `{meta.get('paired_url', 'N/A') if isinstance(meta, dict) else 'N/A'}`",
            "- 执行状态: draft-only；未写入 CMS、未发布、未部署",
            f"- Blocks JSON: `{blocks_path}`",
            f"- CMS payload draft: `{cms_path}`",
            f"- HTML preview: `{preview_path}`",
            "",
            "## 今日决策",
            "",
            "今天把 Markdown 图文草稿升级为结构化图文 blocks、HTML 正文和 CMS payload 草案，为后续真实发布器提供稳定输入。",
            "",
            "## Media Placeholders",
            "",
            *(f"- `{item.get('filename')}` | {item.get('concept_label')} | status: {item.get('status')}" for item in media if isinstance(item, dict)),
            "",
            "## CMS Mapping",
            "",
            f"- Target kind: `{cms_payload.get('target_kind', 'N/A') if isinstance(cms_payload, dict) else 'N/A'}`",
            f"- Table: `{cms_payload.get('table', 'N/A') if isinstance(cms_payload, dict) else 'N/A'}`",
            f"- Admin helper: `{cms_payload.get('admin_helper', 'N/A') if isinstance(cms_payload, dict) else 'N/A'}`",
            "",
            "## Safety Notes",
            "",
            "- 所有图片仍是待生成或待业主选择的媒体占位。",
            "- 生成图片必须保留 `概念设计 / 效果图方案 / design concept / rendering concept` 标签。",
            "- 该 payload 只能作为审核和后续执行输入，不能视为已经发布。",
            "",
        ]
    )


def write_outputs(root: Path, payload: dict[str, object]) -> tuple[Path, Path, Path, Path]:
    meta = payload.get("metadata", {})
    target_url = meta.get("target_url", "rich-content") if isinstance(meta, dict) else "rich-content"
    slug = slug_from_url(str(target_url))
    data_dir = root / "seo-workspace" / "data"
    drafts_dir = root / "seo-workspace" / "drafts"
    reports_dir = root / "seo-workspace" / "reports"
    today = dt.date.today().isoformat()
    blocks_path = data_dir / BLOCKS_JSON_NAME
    cms_path = data_dir / CMS_PAYLOAD_JSON_NAME
    preview_path = drafts_dir / f"{today}-{slug}-rich-content-preview.html"
    report_path = reports_dir / f"{today}-{slug}-rich-content-blocks-report.md"
    write_text(blocks_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_text(cms_path, json.dumps(payload["cms_payload_draft"], ensure_ascii=False, indent=2) + "\n")
    write_text(preview_path, render_preview(payload))
    write_text(report_path, render_report(payload, blocks_path, cms_path, preview_path))
    return blocks_path, cms_path, preview_path, report_path


def run_rich_blocks(root: Path, *, target_url: str = "", draft_path: str = "") -> tuple[Path, Path, Path, Path]:
    root = root.resolve()
    source_draft = find_source_draft(root, target_url=target_url, draft_path=draft_path)
    payload = build_structured_payload(source_draft, read_text(source_draft))
    return write_outputs(root, payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert rich-content Markdown into structured blocks and CMS payload drafts.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="", help="Target or paired URL from a rich-content package.")
    parser.add_argument("--draft-path", default="", help="Specific rich-content Markdown package.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for output in run_rich_blocks(Path(args.root), target_url=args.target_url, draft_path=args.draft_path):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
