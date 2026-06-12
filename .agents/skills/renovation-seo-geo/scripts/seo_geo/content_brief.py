#!/usr/bin/env python3
"""Generate bilingual SEO/GEO content briefs from the highest scored opportunity."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


SEO_GEO_DIR = Path(__file__).resolve().parent
if str(SEO_GEO_DIR) not in sys.path:
    sys.path.insert(0, str(SEO_GEO_DIR))

from hreflang import expected_pair_url  # noqa: E402
from page_audit import audit_to_markdown, load_page_audit, read_csv_rows  # noqa: E402


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "seo-content-brief"


def output_slug(score_row: dict[str, str]) -> str:
    url = score_row.get("url", "")
    if "/services/renovation" in url:
        return "residential-renovation"
    if "/services/" in url:
        return slugify(url.rsplit("/services/", 1)[-1])
    service_slug = slugify(score_row.get("service", ""))
    return service_slug if service_slug != "seo-content-brief" else slugify(score_row.get("keyword", ""))


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")


def url_matches(candidate_url: str, target_url: str) -> bool:
    candidate = normalize_url(candidate_url)
    target = normalize_url(target_url)
    if not candidate or not target:
        return False
    return candidate == target or normalize_url(expected_pair_url(candidate)) == target


def top_opportunity(root: Path, target_url: str = "") -> dict[str, str]:
    rows = read_csv_rows(root / "seo-workspace" / "data" / "seo-opportunity-scores.csv")
    if target_url:
        for row in rows:
            if url_matches(row.get("url", ""), target_url):
                return row
    return rows[0] if rows else {}


def brand_value(root: Path, label: str, fallback: str = "") -> str:
    path = root / "seo-workspace" / "data" / "brand-profile.md"
    if not path.exists():
        return fallback
    prefix = f"- {label}:"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip() or fallback
    return fallback


def service_context(score_row: dict[str, str]) -> dict[str, str]:
    service = score_row.get("service") or "Residential renovation"
    location = score_row.get("location") or "Kuala Lumpur; Selangor"
    return {
        "service": service,
        "location": location,
        "keyword": score_row.get("keyword", ""),
        "zh_url": score_row.get("url", "") if "/zh/" in score_row.get("url", "") else "",
        "en_url": score_row.get("url", "") if "/en/" in score_row.get("url", "") else "",
    }


def zh_page_copy() -> str:
    return """### 中文页面建议文案

#### Hero
H1：吉隆坡住宅装修与旧屋翻新规划

FLASH CAST 为吉隆坡、雪兰莪与巴生谷业主提供住宅装修、旧屋翻新、空间规划、材料建议与施工协调支持。这个页面建议重点说明：适合哪些屋主、装修前要准备什么、如何判断工程范围、材料与预算会受哪些因素影响，以及为什么先做现场测量和清楚报价比直接比较单项价格更可靠。

#### 适合的装修需求
本页可覆盖公寓装修、有地住宅翻新、旧屋局部翻新、厨房与浴室配套更新、客餐厅收纳规划、墙面与地面更新、灯光与木作协调等需求。所有案例或视觉内容应清楚标注为“概念设计 / 效果图方案 / 规划示例”，除非业主提供真实项目资料。

#### 建议新增内容区块
- 装修前准备：照片、平面图、面积、屋况、管理处要求、预算方向和入住时间。
- 现场评估重点：水电、防水、墙地面、木作、照明、收纳、动线和材料耐用度。
- 预算因素：面积、拆除量、基础工程、材料等级、木作数量、现场限制和管理要求。
- 设计规划示例：旧屋客餐厅改善、收纳不足改善、厨房动线改善、浴室防水重做。
- 下一步 CTA：提交照片、位置、面积和装修目标，安排初步咨询或报价。
"""


def en_page_copy() -> str:
    return """### 英文页面建议文案

#### Hero
H1: Residential Renovation in Kuala Lumpur and Selangor

FLASH CAST supports homeowners across Kuala Lumpur, Selangor, and the Klang Valley with residential renovation planning, space review, material advice, and project coordination. This page should help visitors understand what to prepare before renovation, how scope is defined, which factors affect cost and timeline, and why site measurement and a clear quotation process matter before comparing item prices.

#### Suitable Renovation Needs
This page can cover condo renovation, landed house refurbishment, old house updates, kitchen and bathroom upgrades, living and dining storage planning, wall and floor finishes, lighting coordination, and built-in carpentry planning. Visual examples should be clearly labeled as design concepts or rendering concepts unless the owner provides real completed-project material.

#### Recommended New Sections
- Before renovation: photos, layout plan, property size, current condition, management rules, budget direction, and move-in needs.
- Site review priorities: wiring, plumbing, waterproofing, wall/floor condition, carpentry, lighting, storage, circulation, and material durability.
- Budget factors: area, demolition, base works, material grade, carpentry quantity, site restrictions, and management requirements.
- Design planning examples: old-house living upgrade, storage improvement, kitchen workflow planning, bathroom waterproofing refresh.
- Next CTA: share photos, location, size, and renovation goals to request an initial consultation or quotation.
"""


def build_brief(root: Path, score_row: dict[str, str]) -> str:
    zh_url = score_row.get("url", "")
    en_url = zh_url.replace("/zh/", "/en/", 1) if "/zh/" in zh_url else score_row.get("url", "")
    if "/en/" in zh_url:
        en_url = zh_url
        zh_url = zh_url.replace("/en/", "/zh/", 1)
    company = brand_value(root, "Company name", "FLASH CAST SDN. BHD.")
    website = brand_value(root, "Website", "https://flashcast.com.my/")
    audit = load_page_audit(root, score_row.get("url", ""))
    today = dt.date.today().isoformat()

    return f"""# Residential Renovation Service Page Content Brief

- 生成日期: {today}
- 执行模式: draft-only
- 品牌: {company}
- 网站: {website}
- 目标页面: `{zh_url}` + `{en_url}`
- 目标关键词: {score_row.get("keyword", "住宅装修 吉隆坡")}
- 内容类型: {score_row.get("task_type", "high-commercial-intent page optimization")}
- 机会分: {score_row.get("total_score", "")}
- 执行状态: 等待业主审核和明确执行指令

## 今日决策

今天选择住宅装修服务页优化，而不是随机写新文章。原因是第七阶段评分系统显示该页面具备高商业意图、本地商业意图和服务页转化价值，同时存在 FAQ、CTA 和内链优化空间。

## 目标页面/关键词

- 中文页面: `{zh_url}`
- 英文页面: `{en_url}`
- 中文关键词: 住宅装修 吉隆坡
- 英文关键词: home renovation malaysia / residential renovation Kuala Lumpur

## Page Audit

{audit_to_markdown(audit)}

{zh_page_copy()}

{en_page_copy()}

## Bilingual SEO Title

- 中文 SEO title: 吉隆坡住宅装修与旧屋翻新 | FLASH CAST
- English SEO title: Residential Renovation Kuala Lumpur & Selangor | FLASH CAST

## Bilingual Meta Description

- 中文 meta description: FLASH CAST 提供吉隆坡、雪兰莪与巴生谷住宅装修、旧屋翻新、空间规划、材料建议与报价咨询。先提交照片、面积和装修目标，获取下一步建议。
- English meta description: Plan residential renovation in Kuala Lumpur or Selangor with FLASH CAST. Review scope, materials, site condition, budget factors, and quotation steps before starting.

## Bilingual Slug

- 中文 slug: `/zh/services/renovation`
- English slug: `/en/services/renovation`

## Bilingual H1/H2/H3

- 中文 H1: 吉隆坡住宅装修与旧屋翻新规划
- English H1: Residential Renovation in Kuala Lumpur and Selangor
- 中文 H2: 适合哪些住宅装修需求 / 装修前要准备什么 / 现场评估重点 / 预算影响因素 / 设计方案与效果图规划 / 常见问题
- English H2: Suitable Renovation Needs / What to Prepare / Site Review Priorities / Budget Factors / Design and Rendering Concepts / FAQ
- 中文 H3: 公寓装修 / 有地住宅翻新 / 旧屋局部更新 / 厨房浴室配套 / 收纳与木作规划
- English H3: Condo Renovation / Landed House Refurbishment / Old House Updates / Kitchen and Bathroom Upgrades / Storage and Carpentry Planning

## Bilingual FAQ

- 问: 住宅装修前要准备什么？ 答: 建议先准备房屋照片、面积、位置、平面图、屋况问题、预算方向和希望完成的范围。
- Q: What should I prepare before residential renovation? A: Prepare photos, size, location, layout plan, current issues, budget direction, and the renovation scope you want to discuss.
- 问: 可以先看设计方案或效果图方向吗？ 答: 可以规划概念设计、效果图方案和材料方向，但必须清楚标注为规划示例，不当作真实完工案例。
- Q: Can I review design or rendering concepts first? A: Yes. Concept designs, rendering concepts, and material directions can be prepared as planning examples, not completed project proof.
- 问: 报价为什么需要现场资料？ 答: 面积、拆除量、水电、防水、木作、材料等级和管理处要求都会影响范围和报价。
- Q: Why does quotation need site information? A: Area, demolition, wiring, plumbing, waterproofing, carpentry, material grade, and management requirements affect the scope and quotation.

## Bilingual Internal Links

- `/zh/services/kitchen` -> 锚文本: 厨房装修与橱柜规划
- `/zh/services/bathroom` -> 锚文本: 浴室装修与防水工程
- `/zh/projects` -> 锚文本: 装修案例与设计参考
- `/zh/quote` -> 锚文本: 获取住宅装修报价
- `/en/services/kitchen` -> Anchor: kitchen renovation and cabinet planning
- `/en/services/bathroom` -> Anchor: bathroom renovation and waterproofing
- `/en/projects` -> Anchor: renovation project references
- `/en/quote` -> Anchor: request a residential renovation quotation

## Bilingual Image Brief

- 中文 hero 图: 住宅客餐厅与收纳规划的概念设计图，标注“概念设计 / 效果图方案”。
- English hero image: residential living and dining renovation design concept, labeled "design concept / rendering concept".
- 中文材料图: 木饰面、石纹、灯光、地面材料和五金的 mood board。
- English material image: mood board with wood finish, stone texture, lighting, flooring, and hardware.

## Bilingual Alt Text

- 中文 alt: 吉隆坡住宅装修客餐厅概念设计效果图方案
- English alt: residential renovation living and dining design concept in Kuala Lumpur
- 中文 alt: 住宅装修材料选择与收纳规划参考方案
- English alt: residential renovation material selection and storage planning concept

## CTA

- 中文 CTA: 上传房屋照片、面积、位置和装修目标，获取住宅装修初步建议。
- English CTA: Share your property photos, size, location, and renovation goals to request an initial renovation consultation.

## Schema 建议

- `Service`: residential renovation service, provider as FLASH CAST SDN. BHD.
- `FAQPage`: only for the FAQ content published on the page.
- `BreadcrumbList`: keep current breadcrumb structure.
- `ImageObject`: use only concept/rendering labels unless real photos are confirmed.

## Owner Approval Notes

- NEEDS OWNER INPUT: 是否确认 WhatsApp CTA 使用当前公开电话。
- 不需要补真实案例、真实照片、固定预算、固定工期或保修条款才能发布此优化；可使用明确标注的设计方案和效果图方案。
- 不得把概念图、规划示例或效果图说成真实完工案例。

## QA Checklist

- [ ] 中文和英文页面同步更新。
- [ ] 页面不承诺固定价格、固定工期、保修范围或 guaranteed ranking。
- [ ] 概念设计和效果图方案明确标注，不冒充真实案例。
- [ ] FAQ 与页面正文一致，FAQPage schema 只标记页面可见问题。
- [ ] 内链指向真实存在页面，锚文本自然。
- [ ] CTA 不改变电话/WhatsApp，除非业主确认。
- [ ] 发布前重新跑 technical SEO audit，确认 200、indexable、canonical self、hreflang pair。

## 执行状态

等待业主审核和明确执行指令。当前文件是 draft-only，不自动发布。
"""


def run_content_brief(root: Path, target_url: str = "") -> Path:
    root = root.resolve()
    row = top_opportunity(root, target_url=target_url)
    if not row:
        raise RuntimeError("No opportunity scores found. Run opportunity_finder.py first.")
    keyword_slug = output_slug(row)
    output_path = root / "seo-workspace" / "drafts" / f"{dt.date.today().isoformat()}-{keyword_slug}-content-brief.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_brief(root, row), encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a bilingual SEO/GEO content brief for the top opportunity.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--target-url", default="", help="Optional target URL override from scored opportunities.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = run_content_brief(Path(args.root), target_url=args.target_url)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
