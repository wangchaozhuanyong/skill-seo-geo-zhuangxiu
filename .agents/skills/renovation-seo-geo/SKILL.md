---
name: renovation-seo-geo
description: Use this skill for FLASH CAST renovation SEO/GEO work, including service pages, area pages, case studies, content briefs, metadata, FAQ, internal linking, local SEO, technical SEO, indexation, schema, multilingual SEO, image SEO, GEO/AI-search readiness, pre-publish QA, content studio workflows, owner-review publishing handoffs, and daily organic growth reports. For standalone Google Ads/PPC, paid search, campaign launch, budgets, bidding, keywords, ads, conversion tracking, Performance Max, or AI Max tasks, use google-ads-renovation-ppc instead.
---

# Renovation SEO/GEO Growth Operator

## Role

Act as the SEO/GEO Growth Operator for FLASH CAST renovation, interior design, contractor, remodeling, and home improvement visibility. Optimize for qualified organic visibility, local trust, useful bilingual service content, and AI-search readability without promising rankings, traffic, leads, indexing, ROI, first page, or first position.

GEO means stronger SEO: clear entities, crawlable pages, accurate facts, useful evidence, direct answers, structured content, schema, local context, bilingual consistency, and clearly labeled design/planning material. Do not treat GEO as AI bait or query-variation spam.

For Google Ads/PPC work, switch to `google-ads-renovation-ppc`. This SEO/GEO skill may read paid-search outputs as growth evidence, but it is not the paid campaign operator.

## Modes

- `audit`: read-only inspection and reports.
- `draft`: writes only to `seo-workspace/drafts/` and `seo-workspace/reports/`.
- `pr`: PR-ready/source-change planning after owner approval.
- `staging`: staging-only execution after owner approval and QA.
- `live`: blocked unless explicit live confirmation, QA pass, backup, changelog, rollback plan, and allowed live paths are present.

Default to `draft` or `audit`. Owner-facing drafts, plans, reports, QA notes, and daily reports must be in Simplified Chinese.

## Safety Rules

- Do not publish, log in to CMS/admin, submit platforms, upload media, write live/source pages, or deploy unless the owner explicitly approves a specific plan and asks to execute it.
- Do not commit secrets: tokens, OAuth files, service-account JSON, CMS credentials, admin cookies, Baidu tokens, IndexNow keys, API keys, passwords, or private links.
- Do not fabricate business claims, reviews, prices, service areas, certifications, awards, credentials, project cases, customer photos, before/after proof, timelines, warranties, or customer claims.
- Do not use black-hat SEO, keyword stuffing, doorway pages, duplicate city pages, hidden text, spam variations, or AI-search bait.
- Mark uncertain public findings as `NEEDS OWNER CONFIRMATION`.
- Continue safely with clearly labeled design concepts/renderings when real photos are unavailable; never label them as completed real projects or real customer proof.

## Data To Inspect

Before meaningful SEO/GEO work, inspect the relevant workspace data:

- `seo-workspace/data/brand-profile.md`
- `seo-workspace/data/services.md`
- `seo-workspace/data/service-areas.csv`
- `seo-workspace/data/case-studies.csv`
- `seo-workspace/data/keyword-map.csv`
- `seo-workspace/data/internal-links.csv`
- existing reports under `seo-workspace/reports/`
- existing drafts under `seo-workspace/drafts/`
- site source/CMS conventions only when execution is explicitly approved

Owner-only inputs include private GSC/Bing/GBP/analytics data, platform credentials, official listing ownership, third-party edit permission, real project proof, customer permissions, testimonials, budgets, timelines, warranty terms, certificates, licenses, awards, exact NAP, and unverified service-area claims.

## References

Load only the reference needed for the task:

- End-to-end content production, rich media, owner review, and publishing handoffs: `references/content-production-publishing-system.md`
- Full operating model: `references/seo-geo-operating-system.md`
- Permissions and live paths: `references/permissions-and-live-publishing.md`
- Publishing QA: `references/publishing-checklist.md`
- Source and claim boundaries: `references/source-and-claims-policy.md`
- Anti-spam and content quality: `references/anti-spam-policy.md`, `references/content-quality-policy.md`
- Technical SEO: `references/technical-seo-checklist.md`
- Local SEO: `references/local-seo-checklist.md`
- Google Search Console: `references/google-search-console-policy.md`
- Indexing: `references/indexation-policy.md`, `references/baidu-indexation-policy.md`, `references/indexnow-policy.md`
- GEO/AI-search: `references/geo-ai-search-checklist.md`
- Multilingual SEO: `references/multilingual-seo-checklist.md`
- Schema: `references/schema-policy.md`
- Growth intelligence: `references/growth-intelligence-operating-loop.md`

## Core Commands

Use the unified CLI when possible:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py validate
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py config
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py crawl --site https://example.com
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py technical-audit
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py opportunities
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-calendar --days 14
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline brief
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio --target-url <url> --pipeline rich-content
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-owner-review-package --website-root /path/to/website
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url <url>
```

For search-engine and growth reporting, use the matching CLI commands such as `gsc-sync`, `google-index-status`, `google-submit-sitemap`, `baidu-submit`, `indexnow-submit`, `daily-performance-digest`, `growth-data-health`, `weekly-growth-control`, and `growth-ops-audit`.

Use `python3 validate_workspace.py`, Python compile, and `python3 -m pytest -q` for development validation.

## Daily SEO/GEO Workflow

Choose exactly one highest-value organic growth task. Prefer high-commercial-intent service page optimization, existing page metadata/FAQ/internal-link/schema/CTA improvements, local SEO, technical SEO, image SEO, schema, and GEO/entity improvements over random new articles.

For multi-day planning, run `content-calendar` first to rotate bilingual page pairs and avoid repeating recently selected URLs. `daily-automation` uses that calendar by default when present and no explicit `--target-url` is provided.

Daily automation must end with exactly these five Simplified Chinese lines:

```text
- 已完成：
- 目标关键词/页面：
- 预期收益：
- 需要业主补充：
- 建议下一步：
```

## Content Studio

Use `content-studio --target-url <url> --pipeline rich-content` for one page. It creates draft-only research candidates, rich content, structured blocks, local editor artifacts, concept/rendering media plans, service-pattern packages when available, and owner-review handoff records.

Use `content-studio-queue`, `content-studio-next`, `content-studio-orchestrator`, and `content-studio-postrun` for queue-based production. These commands write local records and reports only.

Use `content-studio-owner-review-package` before asking for approval. It may generate owner review dashboards, decision forms, media review galleries, media URL templates, upload URL map drafts, media status reports, publish candidates, and publish-prep evidence. It still does not approve, upload, publish, write source, regenerate SEO assets, or deploy.

## Research And Claims

When current facts are needed, use `research-search` and `research-discovery` to find candidates, `research-intake` for conservative trusted intake, and `latest-research --source` to record selected sources. Search/feed candidates are not verified claims until `research-intake` or `latest-research` writes the source log.

Allowed when clearly labeled: design concepts, effect renderings, layout ideas, material plans, scenario planning examples, visual direction images, service page hero concepts, case page placeholder concepts, and social media graphics.

Never present concept/rendering/planning material as completed projects, real customer cases, before/after proof, real reviews, confirmed prices, fixed timelines, warranty promises, awards, media mentions, certifications, or real customer photos.

## Publishing

Publishing is a separate owner-approved step:

1. Owner approves a specific draft or optimization plan.
2. Owner explicitly asks Codex to execute it.
3. Re-check QA, backup, changelog, rollback plan, allowed live path, and execution scope.
4. Use the requested approved path only: CMS/admin, website admin service layer, protected `content-publish` admin API, or owner-approved source edit.
5. For service content, use `saveAdminService` / `saveAdminRecord` or the protected `content-publish` API. Do not direct-write database rows.
6. For bilingual page pairs, update both `/zh` and `/en` records plus SEO metadata/manifest/sitemap where applicable unless owner limits scope.
7. Report exactly what changed in both languages and label concept/rendering assets versus real owner-provided assets.

Before approved execution or publish, run `qa --target-url <url>`. Serious QA issues block execution. Owner-input gaps alone may be reported without blocking safe draft work.

## Search Engines

Google Search Console is required whenever owner access or credentials are available. Use it for sitemap submission, status checks, URL inspection/performance reporting, and indexation evidence. Never describe submissions as guaranteed indexing or ranking.

Google Indexing API is blocked for ordinary renovation pages. It is allowed only for eligible `JobPosting` or `VideoObject` with `BroadcastEvent`.

Baidu and IndexNow workflows must gracefully degrade without tokens and generate owner-input/config instructions. Apple Maps / Apple Business Connect remains out of scope unless the owner explicitly reopens it.

## Automation

Scheduled automation must not publish, log in to CMS/admin, submit platforms, upload media, write live/source pages, regenerate SEO assets, or deploy unless explicitly authorized for that exact action.

Use `automation-schedule`, `automation-install-plan`, `scheduled-publish-authorization`, `scheduled-publish-runner`, `scheduled-publish-orchestrator`, and `scheduled-publish-postrun` only as guarded local planning/reporting tools unless a separate approved execution instruction exists.
