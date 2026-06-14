"""AI crawler, robots.txt, and llms.txt readiness audit."""

from __future__ import annotations

import csv
import datetime as dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin

try:
    from .http_checks import fetch_url
    from .robots_sitemap import robots_allowed, robots_url_for
    from .seo_findings import (
        SeoFinding,
        count_by_severity,
        dedupe_findings,
        format_counts,
        write_findings_csv,
        write_findings_json,
    )
except ImportError:  # pragma: no cover
    from http_checks import fetch_url
    from robots_sitemap import robots_allowed, robots_url_for
    from seo_findings import (
        SeoFinding,
        count_by_severity,
        dedupe_findings,
        format_counts,
        write_findings_csv,
        write_findings_json,
    )


DEFAULT_AI_POLICY_PATHS = ["/", "/en/", "/zh/", "/llms.txt", "/sitemap.xml"]
AI_CRAWLER_POLICY_FIELDS = [
    "user_agent",
    "crawler_type",
    "path",
    "allowed",
    "evidence",
    "recommendation",
]

BOT_PROFILES = [
    {"user_agent": "OAI-SearchBot", "crawler_type": "ai_search_index", "sensitivity": "visibility"},
    {"user_agent": "ChatGPT-User", "crawler_type": "user_triggered_fetch", "sensitivity": "visibility"},
    {"user_agent": "GPTBot", "crawler_type": "training", "sensitivity": "training_opt_out"},
    {"user_agent": "Claude-SearchBot", "crawler_type": "ai_search_index", "sensitivity": "visibility"},
    {"user_agent": "Claude-User", "crawler_type": "user_triggered_fetch", "sensitivity": "visibility"},
    {"user_agent": "ClaudeBot", "crawler_type": "training", "sensitivity": "training_opt_out"},
    {"user_agent": "PerplexityBot", "crawler_type": "ai_search_index", "sensitivity": "visibility"},
    {"user_agent": "Perplexity-User", "crawler_type": "user_triggered_fetch", "sensitivity": "visibility"},
    {"user_agent": "Googlebot", "crawler_type": "search", "sensitivity": "search_visibility"},
    {"user_agent": "Bingbot", "crawler_type": "search", "sensitivity": "search_visibility"},
    {"user_agent": "Google-Extended", "crawler_type": "ai_training_control", "sensitivity": "training_opt_out"},
    {"user_agent": "CCBot", "crawler_type": "training", "sensitivity": "training_opt_out"},
    {"user_agent": "Bytespider", "crawler_type": "training_or_ai", "sensitivity": "training_opt_out"},
]

SOURCE_REFERENCES = [
    {
        "name": "OpenAI crawler docs",
        "url": "https://developers.openai.com/api/docs/bots",
        "note": "OpenAI documents OAI-SearchBot, ChatGPT-User, and GPTBot controls.",
    },
    {
        "name": "Google crawler docs",
        "url": "https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers",
        "note": "Google documents Google-Extended as a robots.txt control token.",
    },
    {
        "name": "Perplexity crawler docs",
        "url": "https://docs.perplexity.ai/docs/resources/perplexity-crawlers",
        "note": "Perplexity documents crawler and user-triggered access agents.",
    },
    {
        "name": "Anthropic crawler support",
        "url": "https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler",
        "note": "Anthropic documents ClaudeBot, Claude-User, and Claude-SearchBot controls.",
    },
]


@dataclass(frozen=True)
class AiCrawlerPolicyRow:
    user_agent: str
    crawler_type: str
    path: str
    allowed: str
    evidence: str
    recommendation: str


def _today() -> str:
    return dt.date.today().isoformat()


def _read_brand_website(root: Path) -> str:
    path = root / "seo-workspace" / "data" / "brand-profile.md"
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("- Website:"):
            return line.split(":", 1)[1].strip()
    return ""


def _read_brand_fact(root: Path, label: str, fallback: str = "") -> str:
    path = root / "seo-workspace" / "data" / "brand-profile.md"
    prefix = f"- {label}:"
    if not path.exists():
        return fallback
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip() or fallback
    return fallback


def _read_core_service_urls(root: Path, base_url: str, limit: int = 10) -> list[str]:
    path = root / "seo-workspace" / "data" / "seo-opportunity-scores.csv"
    urls: list[str] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                url = (row.get("url") or "").strip()
                if not url or url in urls:
                    continue
                if "/services/" in url or row.get("page_type") == "service":
                    urls.append(url)
                if len(urls) >= limit:
                    return urls
    fallback_urls = [urljoin(base_url, "en/services/renovation"), urljoin(base_url, "zh/services/renovation")]
    return urls or fallback_urls


def _local_text(root: Path, filename: str) -> tuple[str, str]:
    for path in (root / "public" / filename, root / "dist" / filename, root / filename):
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace"), str(path)
    return "", ""


def _remote_text(url: str, *, fetch_remote: bool, timeout: int) -> tuple[str, str]:
    if not fetch_remote or not url:
        return "", ""
    result = fetch_url(url, read_body=True, timeout=timeout)
    if result.status_code == 200 and result.body:
        return result.body, url
    evidence = f"{url} status={result.status_code or 'unavailable'}"
    if result.error:
        evidence += f" error={result.error}"
    return "", evidence


def _load_robots_text(root: Path, base_url: str, *, fetch_remote: bool, timeout: int) -> tuple[str, str]:
    text, source = _local_text(root, "robots.txt")
    if text:
        return text, source
    return _remote_text(robots_url_for(base_url), fetch_remote=fetch_remote, timeout=timeout)


def _load_llms_text(root: Path, base_url: str, *, fetch_remote: bool, timeout: int) -> tuple[str, str]:
    text, source = _local_text(root, "llms.txt")
    if text:
        return text, source
    return _remote_text(urljoin(base_url.rstrip("/") + "/", "llms.txt"), fetch_remote=fetch_remote, timeout=timeout)


def _content_signals(robots_text: str) -> list[str]:
    signals: list[str] = []
    for raw_line in robots_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        if key.lower() == "content-signal" and value:
            signals.append(value)
    return signals


def _visibility_recommendation(profile: dict[str, str], allowed: bool) -> str:
    sensitivity = profile["sensitivity"]
    if sensitivity in {"search_visibility", "visibility"}:
        if allowed:
            return "保持允许抓取；发布前仍需确认页面 200、可索引、canonical self 和 sitemap。"
        return "如目标是提升搜索/AI 搜索可见性，复核是否应允许该 retrieval/search agent 访问核心公开页面。"
    if allowed:
        return "训练/扩展类 crawler 当前允许；如业主希望拒绝训练用途，可在 robots.txt 单独限制，不影响普通搜索抓取规则。"
    return "训练/扩展类 crawler 当前被限制；这可能是合规选择，不等同于 SEO 错误。"


def build_ai_crawler_policy_rows(
    *,
    robots_text: str,
    robots_source: str,
    base_url: str,
    paths: list[str],
) -> list[AiCrawlerPolicyRow]:
    rows: list[AiCrawlerPolicyRow] = []
    source_label = robots_source or "robots.txt missing; default allow by robots convention"
    for profile in BOT_PROFILES:
        for path in paths:
            target_url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
            allowed = robots_allowed(target_url, robots_text, user_agent=profile["user_agent"])
            rows.append(
                AiCrawlerPolicyRow(
                    user_agent=profile["user_agent"],
                    crawler_type=profile["crawler_type"],
                    path=path,
                    allowed="yes" if allowed else "no",
                    evidence=source_label,
                    recommendation=_visibility_recommendation(profile, allowed),
                )
            )
    return rows


def build_ai_crawler_policy_findings(
    *,
    policy_rows: list[AiCrawlerPolicyRow],
    robots_text: str,
    robots_source: str,
    llms_text: str,
    llms_source: str,
    base_url: str,
) -> list[SeoFinding]:
    findings: list[SeoFinding] = []
    if not robots_text:
        findings.append(
            SeoFinding(
                severity="warning",
                category="robots_policy",
                url=urljoin(base_url.rstrip("/") + "/", "robots.txt"),
                evidence=robots_source or "robots.txt not found locally; remote fetch not enabled or not available",
                recommendation="添加 robots.txt，明确 sitemap、搜索引擎抓取、AI retrieval 与训练用途控制策略。",
                source="ai-crawler-policy",
            )
        )

    if not llms_text:
        findings.append(
            SeoFinding(
                severity="warning",
                category="llms_txt",
                url=urljoin(base_url.rstrip("/") + "/", "llms.txt"),
                evidence=llms_source or "llms.txt not found locally; remote fetch not enabled or not available",
                recommendation="准备 owner-review 版 llms.txt，概述公开服务、核心页面和不可伪造声明边界；不要自动发布。",
                source="ai-crawler-policy",
            )
        )

    signals = _content_signals(robots_text)
    if signals:
        findings.append(
            SeoFinding(
                severity="info",
                category="content_signal",
                url=urljoin(base_url.rstrip("/") + "/", "robots.txt"),
                evidence="; ".join(signals),
                recommendation="Content-Signal 可作为 AI 用途偏好声明；仍需结合 robots.txt 和业主合规意图复核。",
                source="ai-crawler-policy",
            )
        )

    for row in policy_rows:
        if row.allowed == "yes":
            continue
        if row.crawler_type in {"ai_search_index", "user_triggered_fetch", "search"} and row.path in {"/", "/en/", "/zh/"}:
            findings.append(
                SeoFinding(
                    severity="warning",
                    category="ai_search_access",
                    url=urljoin(base_url.rstrip("/") + "/", row.path.lstrip("/")),
                    evidence=f"{row.user_agent} blocked for {row.path}",
                    recommendation="如该页面需要被搜索/AI 搜索发现，复核 robots.txt 是否过度阻止 retrieval/search agent。",
                    source="ai-crawler-policy",
                )
            )
        elif row.crawler_type in {"training", "ai_training_control", "training_or_ai"} and row.path == "/":
            findings.append(
                SeoFinding(
                    severity="info",
                    category="training_opt_out",
                    url=urljoin(base_url.rstrip("/") + "/", row.path.lstrip("/")),
                    evidence=f"{row.user_agent} blocked for {row.path}",
                    recommendation="训练/扩展用途限制可能是业主合规选择；记录即可，不按 SEO 错误处理。",
                    source="ai-crawler-policy",
                )
            )
    return dedupe_findings(findings)


def write_policy_csv(path: Path, rows: list[AiCrawlerPolicyRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AI_CRAWLER_POLICY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_policy_json(path: Path, rows: list[AiCrawlerPolicyRow], findings: list[SeoFinding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "policy_row_count": len(rows),
        "finding_count": len(findings),
        "publish_blocker_count": sum(1 for finding in findings if finding.publish_blocker),
        "source_references": SOURCE_REFERENCES,
        "rows": [asdict(row) for row in rows],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_ai_crawler_policy_report(
    *,
    root: Path,
    base_url: str,
    policy_csv: Path,
    policy_json: Path,
    findings_csv: Path,
    findings_json: Path,
    rows: list[AiCrawlerPolicyRow],
    findings: list[SeoFinding],
    robots_source: str,
    llms_source: str,
) -> str:
    now = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    blocked_visibility = [
        row
        for row in rows
        if row.allowed == "no" and row.crawler_type in {"ai_search_index", "user_triggered_fetch", "search"} and row.path in {"/", "/en/", "/zh/"}
    ]
    counts = count_by_severity(findings)
    lines = [
        "# AI Crawler Policy Readiness",
        "",
        f"- 生成时间: {now}",
        f"- 仓库: `{root}`",
        f"- 站点: `{base_url}`",
        f"- robots 来源: `{robots_source or 'missing/not fetched'}`",
        f"- llms.txt 来源: `{llms_source or 'missing/not fetched'}`",
        f"- Policy CSV: `{policy_csv}`",
        f"- Policy JSON: `{policy_json}`",
        f"- Findings CSV: `{findings_csv}`",
        f"- Findings JSON: `{findings_json}`",
        f"- Findings 数量: {len(findings)}",
        f"- 严重级别: {format_counts(counts)}",
        "",
        "## 结论",
        "",
    ]
    if blocked_visibility:
        lines.append("- 发现搜索/AI 搜索 retrieval agent 在核心路径被阻止；如果目标是 GEO/AI 搜索可见性，需要人工复核 robots 策略。")
    elif findings:
        lines.append("- 当前没有发现核心 retrieval/search agent 阻塞，但还有 robots/llms/policy 可完善项。")
    else:
        lines.append("- 当前 AI crawler policy 基础检查通过。")

    lines.extend(
        [
            "",
            "## Top Findings",
            "",
        ]
    )
    for finding in findings[:20]:
        lines.append(f"- [{finding.severity}] {finding.category} `{finding.url or 'N/A'}`: {finding.evidence} -> {finding.recommendation}")
    if not findings:
        lines.append("- 暂无 findings。")

    lines.extend(
        [
            "",
            "## Source References",
            "",
        ]
    )
    for ref in SOURCE_REFERENCES:
        lines.append(f"- {ref['name']}: {ref['url']} ({ref['note']})")

    lines.extend(
        [
            "",
            "## 使用边界",
            "",
            "- 这是 draft/audit 输出；不自动改 robots.txt，不发布 llms.txt，不保证 AI 引用、排名、索引或流量。",
            "- 训练/扩展类 crawler 被限制不一定是错误，可能是业主合规选择。",
            "- 搜索/用户触发访问类 crawler 被核心路径阻止，才进入 GEO/AI 搜索可见性复核队列。",
            "",
            "## 执行状态",
            "",
            "- 已生成本地策略检查文件；未发布、未提交索引、未登录 CMS、未修改 live 网站。",
            "",
        ]
    )
    return "\n".join(lines)


def render_robots_owner_review_draft(base_url: str) -> str:
    sitemap_url = urljoin(base_url.rstrip("/") + "/", "sitemap.xml")
    lines = [
        "# Owner-review draft only. Do not publish without approval.",
        "# Goal: keep public search and AI retrieval paths crawlable while giving the owner a clear training opt-out choice.",
        "",
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
        "",
        "# Explicit retrieval/search visibility agents",
        "User-agent: Googlebot",
        "Allow: /",
        "",
        "User-agent: Bingbot",
        "Allow: /",
        "",
        "User-agent: OAI-SearchBot",
        "Allow: /",
        "",
        "User-agent: ChatGPT-User",
        "Allow: /",
        "",
        "User-agent: Claude-SearchBot",
        "Allow: /",
        "",
        "User-agent: Claude-User",
        "Allow: /",
        "",
        "User-agent: PerplexityBot",
        "Allow: /",
        "",
        "User-agent: Perplexity-User",
        "Allow: /",
        "",
        "# Optional training / model-improvement controls. Uncomment only if the owner wants opt-out.",
        "# User-agent: GPTBot",
        "# Disallow: /",
        "",
        "# User-agent: ClaudeBot",
        "# Disallow: /",
        "",
        "# User-agent: Google-Extended",
        "# Disallow: /",
        "",
        "# User-agent: CCBot",
        "# Disallow: /",
        "",
        "# User-agent: Bytespider",
        "# Disallow: /",
        "",
    ]
    return "\n".join(lines)


def render_llms_owner_review_draft(root: Path, base_url: str) -> str:
    company = _read_brand_fact(root, "Company name", "FLASH CAST SDN. BHD.")
    website = _read_brand_fact(root, "Website", base_url)
    service_urls = _read_core_service_urls(root, base_url)
    lines = [
        "# FLASH CAST",
        "",
        "> Owner-review llms.txt draft for public renovation SEO/GEO visibility. Do not publish without owner approval.",
        "",
        f"- Company: {company}",
        f"- Website: {website}",
        "- Business category: Renovation, interior design, contractor, fit-out, custom built-in and home improvement services.",
        "- Primary market: Malaysia, especially Kuala Lumpur, Selangor, and Klang Valley only where service areas are owner-confirmed.",
        "",
        "## Core Public Pages",
        "",
    ]
    for url in service_urls:
        lines.append(f"- {url}")
    lines.extend(
        [
            "",
            "## Claim Boundaries",
            "",
            "- Design concepts, effect renderings, material plans, and planning examples are allowed only when clearly labeled.",
            "- Do not interpret concept/rendering images as completed projects, real customer homes, real photos, or before/after proof.",
            "- Do not infer exact prices, fixed timelines, warranties, awards, licenses, certifications, customer reviews, or completed-project counts unless owner-confirmed.",
            "- Use external sources for general guidance only; they are not FLASH CAST business claims.",
            "",
            "## Recommended Citation Preference",
            "",
            "- Prefer canonical service pages, bilingual `/en` and `/zh` pairs, visible FAQ sections, schema-supported service descriptions, and owner-confirmed contact/quote paths.",
            "- Prefer pages with clear service scope, local context, process explanation, materials/trade-offs, internal links, and CTA.",
            "",
            "## Owner Review Checklist",
            "",
            "- [ ] Confirm company/entity details.",
            "- [ ] Confirm public service-area language.",
            "- [ ] Confirm whether training/model-improvement crawlers should be allowed or blocked in robots.txt.",
            "- [ ] Confirm this file can be published at `/llms.txt`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_ai_crawler_owner_review_report(
    *,
    root: Path,
    base_url: str,
    robots_draft_path: Path,
    llms_draft_path: Path,
    json_path: Path,
) -> str:
    return "\n".join(
        [
            "# AI Crawler Owner Review Drafts",
            "",
            f"- 生成时间: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
            f"- 仓库: `{root}`",
            f"- 站点: `{base_url}`",
            f"- robots 草案: `{robots_draft_path}`",
            f"- llms.txt 草案: `{llms_draft_path}`",
            f"- JSON: `{json_path}`",
            "",
            "## 结论",
            "",
            "- 已生成 owner-review 草案，不会自动发布。",
            "- 默认草案保持 Google/Bing/OpenAI/Claude/Perplexity 的搜索与用户触发访问可抓取，避免影响 SEO/GEO 可见性。",
            "- 训练/模型改进类 crawler 的屏蔽规则只作为注释选项，必须由业主决定是否启用。",
            "",
            "## 业主需要确认",
            "",
            "- 是否同意发布 `/robots.txt` 草案。",
            "- 是否同意发布 `/llms.txt` 草案。",
            "- 是否要启用 GPTBot、ClaudeBot、Google-Extended、CCBot、Bytespider 的训练用途 opt-out。",
            "- 是否确认 llms.txt 中的公司、服务范围、服务区域和声明边界。",
            "",
            "## 执行状态",
            "",
            "- 本命令只写本地草案和报告；未写网站源码，未登录 CMS，未发布，未提交搜索引擎。",
            "",
        ]
    )


def run_ai_crawler_owner_review_draft(root: Path, *, base_url: str = "") -> tuple[dict[str, object], list[Path]]:
    root = root.resolve()
    base_url = (base_url or _read_brand_website(root) or "https://flashcast.com.my/").rstrip("/") + "/"
    drafts_dir = root / "seo-workspace" / "drafts"
    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    today = _today()
    robots_draft_path = drafts_dir / f"{today}-robots-owner-review.draft.txt"
    llms_draft_path = drafts_dir / f"{today}-llms-owner-review.draft.txt"
    json_path = data_dir / "ai-crawler-owner-review-draft.json"
    report_path = reports_dir / f"{today}-ai-crawler-owner-review-draft.md"
    robots_text = render_robots_owner_review_draft(base_url)
    llms_text = render_llms_owner_review_draft(root, base_url)
    drafts_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    robots_draft_path.write_text(robots_text, encoding="utf-8")
    llms_draft_path.write_text(llms_text, encoding="utf-8")
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "ai_crawler_owner_review_draft_ready",
        "base_url": base_url,
        "robots_draft_path": str(robots_draft_path),
        "llms_draft_path": str(llms_draft_path),
        "owner_approval_required_before_publish": True,
        "no_publish_executed": True,
        "no_source_write_executed": True,
        "no_cms_write_executed": True,
        "training_opt_out_is_owner_decision": True,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(
        build_ai_crawler_owner_review_report(
            root=root,
            base_url=base_url,
            robots_draft_path=robots_draft_path,
            llms_draft_path=llms_draft_path,
            json_path=json_path,
        ),
        encoding="utf-8",
    )
    return payload, [robots_draft_path, llms_draft_path, json_path, report_path]


def run_ai_crawler_policy_report(
    root: Path,
    *,
    base_url: str = "",
    fetch_remote: bool = False,
    timeout: int = 8,
    paths: list[str] | None = None,
) -> tuple[dict[str, object], list[Path]]:
    root = root.resolve()
    base_url = (base_url or _read_brand_website(root) or "https://flashcast.com.my/").rstrip("/") + "/"
    selected_paths = paths or DEFAULT_AI_POLICY_PATHS
    robots_text, robots_source = _load_robots_text(root, base_url, fetch_remote=fetch_remote, timeout=timeout)
    llms_text, llms_source = _load_llms_text(root, base_url, fetch_remote=fetch_remote, timeout=timeout)
    rows = build_ai_crawler_policy_rows(
        robots_text=robots_text,
        robots_source=robots_source,
        base_url=base_url,
        paths=selected_paths,
    )
    findings = build_ai_crawler_policy_findings(
        policy_rows=rows,
        robots_text=robots_text,
        robots_source=robots_source,
        llms_text=llms_text,
        llms_source=llms_source,
        base_url=base_url,
    )

    data_dir = root / "seo-workspace" / "data"
    reports_dir = root / "seo-workspace" / "reports"
    policy_csv = data_dir / "ai-crawler-policy.csv"
    policy_json = data_dir / "ai-crawler-policy.json"
    findings_csv = data_dir / "ai-crawler-policy-findings.csv"
    findings_json = data_dir / "ai-crawler-policy-findings.json"
    report_path = reports_dir / f"{dt.date.today().isoformat()}-ai-crawler-policy.md"
    write_policy_csv(policy_csv, rows)
    write_policy_json(policy_json, rows, findings)
    write_findings_csv(findings_csv, findings)
    write_findings_json(findings_json, findings)
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_ai_crawler_policy_report(
            root=root,
            base_url=base_url,
            policy_csv=policy_csv,
            policy_json=policy_json,
            findings_csv=findings_csv,
            findings_json=findings_json,
            rows=rows,
            findings=findings,
            robots_source=robots_source,
            llms_source=llms_source,
        ),
        encoding="utf-8",
    )
    summary = {
        "policy_row_count": len(rows),
        "finding_count": len(findings),
        "blocked_visibility_count": sum(
            1
            for row in rows
            if row.allowed == "no" and row.crawler_type in {"ai_search_index", "user_triggered_fetch", "search"} and row.path in {"/", "/en/", "/zh/"}
        ),
        "severity_counts": count_by_severity(findings),
    }
    return summary, [policy_csv, policy_json, findings_csv, findings_json, report_path]
