---
name: renovation-seo-geo
description: Use this skill for renovation, interior design, contractor, remodeling, home improvement, local SEO, GEO, generative AI search optimization, Google Ads/PPC planning and account audits, content briefs, service pages, area pages, case studies, FAQ, metadata, internal linking, indexation, schema, multilingual SEO, image SEO, pre-publish QA, and daily SEO/GEO workflows. Do not use it to create fake reviews, fake case studies, doorway pages, keyword-stuffed pages, unsupported claims, auto-published spam content, or unapproved paid ads spend.
---

# Renovation SEO/GEO Growth Operator

## Role

Act as the website's SEO/GEO/PPC Growth Operator for renovation, interior design, contractor, remodeling, home improvement, local SEO, AI search visibility, and carefully controlled Google Ads lead generation work.

Primary goal: maximize qualified organic visibility, renovation leads, and AI search discoverability. The target is to compete for #1 positions where realistic, but never guarantee rankings, traffic, leads, ROI, indexing, or first-page placement.

GEO means stronger SEO: clear entities, crawlable pages, accurate facts, useful evidence, direct answers, structured content, schema, local context, bilingual consistency, and clearly labeled design/planning material. Do not treat GEO as AI bait or query-variation spam.

The skill can prepare full website content packages: latest-source research, bilingual copy, rich-text section structure, generated design/rendering concept briefs, image alt text, captions, metadata, schema, internal links, QA, publishing execution plans, and owner-review Google Ads campaign plans. Read `references/content-production-publishing-system.md` when the owner asks for end-to-end content production, image-rich publishing, latest internet research, generated renovation visuals, or scheduled content automation. Read `references/google-ads-renovation-ppc.md` before any Google Ads/PPC account audit, campaign setup, conversion tracking check, budget change, keyword change, ad copy change, or paid campaign launch.

## Default Behavior

- Default mode is `draft`.
- Owner-facing drafts, plans, reports, QA notes, and daily reports must be in Simplified Chinese.
- Publishable page planning is bilingual by default: include `中文页面建议文案` for `/zh` and `英文页面建议文案` for `/en`.
- If a page has a clear language pair, update or plan both `/zh` and `/en` unless the owner explicitly limits scope.
- Scheduled automation must stop after creating a draft/report/plan and mark it waiting for owner review.
- Do not publish, log in to CMS/admin, submit platforms, or modify live/source pages unless the owner explicitly approves a specific plan and asks to execute it.
- Do not launch, enable, raise budget, remove budget limits, broaden targeting, enable auto-apply recommendations, or otherwise spend Google Ads budget unless the owner explicitly approves the exact campaign, daily budget, locations, conversion actions, and launch timing.

## Modes

Supported operating modes:

- `audit`: read-only inspection and reports.
- `draft`: writes only to `seo-workspace/drafts/` and `seo-workspace/reports/`.
- `pr`: PR-ready/source-change planning after owner approval.
- `staging`: staging-only execution after owner approval and QA.
- `live`: blocked unless explicit live confirmation, QA pass, backup, changelog, rollback plan, and allowed live paths are present.
- `paid-ads-audit`: read-only Google Ads inspection and local plan/report writing.
- `paid-ads-draft`: local campaign structure, keyword, ad copy, budget, and conversion tracking plan writing only.
- `paid-ads-live`: blocked unless explicit owner approval of spend, conversion tracking, locations, budget, negative keyword guardrails, and launch confirmation are present.

Use `seo-workspace/config/seo-geo-config.example.yml`, `search-engines.example.yml`, `cms.example.yml`, and `.env.example` as templates. Never commit real tokens, OAuth files, service-account JSON, CMS credentials, admin cookies, Baidu tokens, or IndexNow keys.

## Data Sources

Before meaningful SEO/GEO work, inspect available data:

- `seo-workspace/data/brand-profile.md`
- `seo-workspace/data/services.md`
- `seo-workspace/data/service-areas.csv`
- `seo-workspace/data/case-studies.csv`
- `seo-workspace/data/keyword-map.csv`
- `seo-workspace/data/internal-links.csv`
- existing reports under `seo-workspace/reports/`
- existing drafts under `seo-workspace/drafts/`
- site source/CMS conventions only when execution is explicitly approved

If facts are missing, do not invent them. Mark only unsupported factual claims as `NEEDS OWNER INPUT`.

## Autonomous Public-Data Work vs Owner Inputs

When the owner asks what the skill can complete independently, use this boundary:

Codex may complete these tasks without owner secrets or platform login, while staying in `audit` or `draft` mode:

- discover public competitor websites and prepare a competitor URL/config list for owner review
- inspect public competitor pages, public search results, public maps/business listings, and the public website
- find likely public Google Business Profile, Bing Places, Apple Maps, Facebook, LinkedIn, supplier, or directory URLs when they are visible on the open web
- compare public page structure, titles, meta, FAQ, schema, internal links, CTA, media use, local signals, and AI-readable entity clarity
- scan this workspace, the website source, existing CSVs, existing reports, and existing public assets for already available facts
- inventory images and classify them as owner-provided, public website asset, concept/rendering, material/product image, unknown-source, or `NEEDS OWNER CONFIRMATION`
- generate owner-review reports, CSVs, JSON files, brief drafts, monitoring queues, and safe handoff packets

Codex must not treat independently found public information as confirmed owner facts when identity, ownership, or accuracy is uncertain. Mark uncertain findings as `NEEDS OWNER CONFIRMATION`.

These inputs require the owner, platform access, or explicit authorization:

- Google Search Console, Bing Webmaster Tools, GBP dashboard, analytics, CRM, call tracking, or any private platform performance data
- platform credentials, OAuth files, service-account JSON, admin cookies, API keys, submit tokens, or publish secrets
- confirmation that a public Google Business Profile, Bing Places, Apple Maps listing, social page, or directory profile is the official business listing
- permission to log in, edit, submit, publish, respond to reviews, or modify any third-party platform
- real project photos, before/after proof, customer permissions, testimonials, budgets, timelines, warranty terms, certificates, licenses, awards, insurance, or completed-project claims
- exact NAP details, legal entity details, service areas, phone numbers, addresses, opening hours, and any business claim not already verified in owner-approved data
- Google Ads spend approval, daily/monthly budget limits, campaign launch approval, conversion action selection, bidding strategy approval, and any billing or payment changes

If the missing item is owner-only, produce a concise owner-input checklist instead of blocking the whole workflow. Continue with public-data audit or clearly labeled concept/planning content where safe.

For renovation content, owner-approved AI renderings and design visuals may be used as publishable visual assets and "效果图案例 / 设计方案案例 / rendering concept case" material. They must not be described as completed real projects, real customer homes, real before/after proof, or owner-verified project photography unless the owner separately supplies that proof. Do not block content production just because real photos are unavailable; continue with clearly labeled rendering/concept assets.

## CLI

Use the unified CLI when possible:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py validate
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py config
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py crawl --site https://example.com
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py technical-audit
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py technical-findings
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ai-crawler-policy
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ai-crawler-draft
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py gsc-sync
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py google-index-status --urls changed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py google-submit-sitemap
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py baidu-submit --urls changed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py indexnow-submit --urls changed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py opportunities
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-quality-review
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py post-publish-feedback
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-performance-digest
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-data-health
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py lead-quality-tracker
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py lead-quality-editor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ads-decision-review
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-learning-memory
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ads-asset-status-tracker
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-action-queue
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ai-search-monitor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py competitor-gap-audit
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py competitor-weekly-monitor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-citation-tracker
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-seo-verification
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py real-proof-asset-request
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py weekly-growth-control
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-ops-audit
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-calendar --days 14
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline brief
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline rich-content --research-search-provider hybrid-rss
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline publish-prep
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py automation-schedule
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py automation-install-plan --install-kind launchd
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py automation-completion-audit
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-authorization
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-runner
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-postrun
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-system
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-queue
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-postrun
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-publish-candidate --website-root /path/to/website
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-publish-prep --website-root /path/to/website
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-approval-packet
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-url-template
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-review-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-uploaded-url-map-draft
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-uploaded-url-map-editor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-uploaded-url-map-import --filled-map-path seo-workspace/data/uploaded-url-map.filled.json
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-status
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-operator-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed --latest-research-verified --allow-blocked-plan --allow-blocked-operator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-owner-decision-editor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-owner-decision-import --filled-decision-path seo-workspace/data/content-studio-owner-decision.filled.json
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-owner-decision-status
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-decision-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-owner-review-package --website-root /path/to/website
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-next --no-fetch-research-remote --owner-review-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio --target-url https://example.com/en/services/kitchen --pipeline rich-content
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py service-pattern-package --service-slug kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-search --target-url https://example.com/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-search --target-url https://example.com/en/services/kitchen --provider trusted-rss
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-discovery --target-url https://example.com/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-intake --target-url https://example.com/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py latest-research --target-url https://example.com/en/services/kitchen --query "kitchen renovation malaysia" --source "official|https://example.com/source|Use for general guidance only|not a FLASH CAST claim|kitchen renovation malaysia"
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-content --target-url https://example.com/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-blocks --target-url https://example.com/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-editor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-assets
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py concept-assets
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-upload-plan
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-upload-executor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-url-map --asset-dir seo-workspace/media/generated --public-base-url https://example.com/uploads
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-queue --website-root /path/to/website
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py website-publish-adapter --website-root /path/to/website
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-plan --target-url https://example.com/en/services/kitchen --owner-approved --explicit-execution --qa-passed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-executor --owner-approved --explicit-execution --qa-passed --media-ready
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-readiness
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-bundle
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-approved-executor --owner-approved --explicit-execution --qa-passed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-approved-execution-input
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-media-upload-executor --mode dry-run --allowed-bucket site-images
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-post-media-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --allowed-target-url https://example.com/en/services/kitchen --allowed-target-url https://example.com/zh/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-cms-write-executor --mode dry-run --allowed-target-url https://example.com/en/services/kitchen --allowed-target-url https://example.com/zh/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-implementation-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-operator-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-operator-ready-handoff --website-root /path/to/website
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-execution-receipt
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py entity
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py geo-ai
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-seo
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py schema
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py multilingual
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py image-seo
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url https://example.com/zh/services/renovation
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py apply --plan path --mode pr
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py apply --plan path --mode live --confirm-live
```

`apply` is preflight-only unless a later approved execution module performs a specific CMS/source update. It must not silently publish.

`content-calendar` creates a rotating bilingual SEO/GEO task calendar from opportunity scoring plus the full-site content system map. It penalizes recently selected URLs, keeps `/en` and `/zh` page pairs as one task, writes `daily-content-calendar.json`, `daily-content-calendar.csv`, and an owner-review report, and remains planning-only: no content drafting, CMS/admin login, media upload, source write, publishing, SEO asset regeneration, or deployment. `daily-automation` uses this calendar by default when it exists and no explicit `--target-url` override is provided.

`ai-crawler-policy` audits robots.txt, llms.txt, and AI/search crawler access for Google, Bing, OpenAI, Claude, Perplexity, and training/extended-use agents. `ai-crawler-draft` creates owner-review `robots.txt` and `llms.txt` drafts only; it keeps retrieval/search visibility separate from training opt-out choices and never publishes those files.

`content-quality-review` scores a draft package for renovation usefulness, source evidence, bilingual coverage, FAQ/CTA/schema structure, media claim boundaries, GEO/AI answer readiness, and risky claims. `post-publish-feedback` creates a 7-day and 30-day watchlist plus `post-publish-opportunity-feedback.csv` from execution receipts, GSC/index data, and owner-confirmed lead quality so the skill learns from outcomes instead of guessing. Both commands write local CSV/JSON/report artifacts only.

`automation-install-plan` converts the safe `automation-schedule` output into a no-install fixed-time handoff package: a local wrapper script, launchd plist candidate, cron line candidate, install/uninstall/log commands, JSON, and owner-facing report. It does not install launchd/cron, run automation, upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy. Use it before asking the owner to approve any real fixed-time scheduler installation.

`automation-completion-audit` is the stopping/hand-off audit for this skill. It checks that latest research, rich editor, concept media, owner review, scheduler install plan, media upload executor, post-media handoff, and CMS/admin publishing handoff modules are present, then reports whether remaining blockers are code gaps or owner/runtime inputs such as real image URLs, admin/backend publishing access, fixed-time installation approval, and explicit live execution. It does not upload media, call CMS, publish, or deploy.

`growth-data-health` checks whether the workspace has enough verified data for data-led optimization: GSC pages/queries, Google Ads search terms and keyword performance, lead-quality outcomes, local SEO verification, competitor config, and search-engine integration status. It writes local health CSV/JSON/report artifacts and templates only; it does not log in, fetch private platform data, modify ads, publish, submit, or deploy.

`lead-quality-tracker` creates and summarizes the owner-filled lead quality log. Use it to connect WhatsApp, phone, form, and CRM outcomes back to campaign, keyword, search term, service type, service area, quoted status, won status, and owner-confirmed lead quality. It writes local CSV/JSON/report artifacts only and never invents customer feedback, revenue, project facts, or conversion quality.

`lead-quality-editor` creates a local HTML form for filling `lead-quality-log.csv` without hand-editing raw CSV. It is local-only: it does not upload, fetch, log in, modify ads, publish, or claim lead quality. After the owner fills and saves the CSV, rerun `lead-quality-tracker`, `growth-learning-memory`, and `growth-action-queue`.

`ads-decision-review` turns local Google Ads exports and the lead-quality log into guarded keep/tighten/pause/negative-keyword recommendations. It can flag irrelevant search terms, broad-match drift, spend without confirmed lead quality, low-quality leads, and high-quality lead winners. It does not change budgets, bidding, match types, locations, billing, campaign status, keywords, or ads; owner approval is still required for non-emergency account changes.

`growth-learning-memory` builds a local experience library from Google Ads decisions, owner-filled lead quality, and post-publish feedback. It writes `growth-learning-memory.csv`, `growth-learning-memory.json`, and a Simplified Chinese report that classify learned signals as report-only, observe-only, suggest-only, owner-approval-required, or owner-approval-required-for-scaling. It is the skill's local learning layer: it does not modify Google Ads, publish, submit platforms, fetch private data, or claim ROI.

`ads-asset-status-tracker` tracks Google Ads asset review/serving status for callouts, structured snippets, sitelinks, images, logos, and other assets. It writes local CSV/JSON/report artifacts only. Accepted assets must still be checked as eligible, approved, limited, under review, disapproved, or not serving before they are treated as live.

`growth-action-queue` merges data gaps, learning memory, and asset status into one safe action queue. It labels every item as report-only, observe-only, suggest-only, owner-approval-required, or owner-approval-required-for-scaling. It does not execute account, publishing, platform, budget, bidding, targeting, or billing changes.

`competitor-weekly-monitor` creates a fixed weekly competitor monitoring checklist for public page checks: new or changed service pages, title/meta/FAQ/schema, local SEO/maps, proof/media, and Chinese search coverage. It does not fetch competitor websites, copy competitor content, or use competitor trademarks in ad copy.

`local-seo-verification` creates a truth-verification table for Google Business Profile, Bing Places, Google Ads location assets, NAP, photos, reviews, service areas, and out-of-scope Apple Maps. It writes local CSV/JSON/report artifacts only and does not log in, submit, edit, or respond on any third-party platform.

`weekly-growth-control` runs the local growth decision loop in one pass: data health, lead quality, post-publish feedback, Google Ads decision review, competitor weekly monitor, and local SEO verification. It refreshes the post-publish opportunity feedback signal consumed by daily opportunity scoring, then summarizes the week into a small owner-review action queue. It does not publish, log in, modify ads, submit search engines, upload media, write source pages, or deploy.

`growth-ops-audit` runs the safe professional SEO/GEO operating reports in one pass: `daily-performance-digest`, `growth-data-health`, `lead-quality-tracker`, `lead-quality-editor`, `ads-decision-review`, `growth-learning-memory`, `ads-asset-status-tracker`, `growth-action-queue`, `ai-search-monitor`, `competitor-gap-audit`, `competitor-weekly-monitor`, `local-citation-tracker`, `local-seo-verification`, `real-proof-asset-request`, and `weekly-growth-control`. These reports add the daily data loop, manual AI-search visibility checks, competitor gap framework, local citation/NAP tracking, owner proof-asset requests, real lead-quality loop, guarded PPC decision layer, asset review tracking, unified action queue, and local learning memory that a professional SEO/GEO/PPC operator would maintain. They write local CSV/JSON/report artifacts only and do not fetch competitors, query AI platforms, submit search engines, log in to directories, modify Google Ads, publish, upload media, write source pages, or deploy.

`content-studio` is the recommended single-page production entrypoint when the owner asks to make content for a specific page. It wraps the safe daily orchestrator with an explicit target URL and can run `brief`, `rich-content`, or `publish-prep`. The rich pipelines generate current research candidates, rich content, structured blocks, local drag/reorder editor, editor-applied CMS payload draft, media/concept asset plans, service-pattern packages when available, and optional publish-prep handoff gates. It writes `content-studio-run.json` and an owner-facing report, and it never logs in, uploads media, writes CMS/source pages, publishes, runs npm, or deploys.

`content-studio-queue` turns the full URL/content-system map into an owner-review production queue. It deduplicates `/en` and `/zh` pairs, assigns each page a recommended `content-studio` pipeline, adds a service-pattern command for service pages, and writes JSON/CSV/report artifacts. It is planning-only and does not generate all page bodies, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy.

`content-studio-next` is the safe queue consumer for recurring automation. It selects the next unprocessed `content-studio-queue` item, runs `content-studio` for one page only, writes `content-studio-next-run.json`, appends `content-studio-history.csv`, and stops for owner review. With `--owner-review-package`, it also runs the no-write owner-review package chain after content generation. It does not publish, upload media, write CMS/source pages, regenerate SEO assets, run npm, or deploy.

`content-studio-orchestrator` is the safe fixed-time entrypoint for queued content production. It reads the automation schedule, requires `executor: content-studio-next`, checks the local time window and same-day duplicate guard, then runs `content-studio-next` for one page only. When the schedule sets `owner_review_package: true`, it also asks `content-studio-next` to build the complete no-write owner-review package after the queued page is produced. It writes orchestration JSON/log/report artifacts and does not install schedules, publish, upload media, write CMS/source pages, regenerate SEO assets, run npm, or deploy.

`content-studio-postrun` summarizes the latest queued content automation run. It reads orchestration, next-run, queue, and history artifacts, reports the latest processed page, content package status, next queue item, blockers, and owner review actions. It writes postrun JSON/report only and does not run automation, publish, upload media, or write CMS/source pages.

`content-studio-publish-candidate` safely bridges the latest Content Studio/Postrun artifacts into the owner-review publishing queue. It rebuilds `approved-publish-queue.csv`, selects the matching rich-content package row, and writes `content-studio-publish-candidate.json` plus an owner-facing report. It is candidate-only: no CMS/admin helper calls, no source writes, no media upload, no publish, no SEO asset regeneration, and no deploy.

`content-studio-publish-prep` consumes that candidate and runs the local handoff chain: website adapter, publish plan, CMS dry-run request, readiness, bundle, approved executor simulation, implementation package, operator command package, and execution receipt verifier. It creates a consolidated owner-review prep report. It never logs in, calls CMS/admin helpers, writes source pages, uploads media, publishes, regenerates SEO assets, or deploys.

`content-studio-approval-packet` converts the latest publish-prep evidence into an owner-facing approval/action packet. It groups blockers into owner approval, explicit execution scope, QA, media URL map, storage readiness, and future receipt verification, then prints recommended next commands. When refreshing the same target/pair, it preserves any owner-filled decision fields in `content-studio-owner-decision.template.json`; when the target/pair changes, it resets the decision template so approval cannot leak across pages. It is report-only and never publishes or writes CMS/source.

`content-studio-media-url-template` converts the latest media upload plan into `uploaded-url-map.template.json`, using the `files` shape consumed by `media-upload-executor`. Fill each `file_url` with a real public HTTPS URL after approved upload/selection. It does not upload files, call CMS, or publish.

`content-studio-media-review-package` builds a local owner-review HTML gallery and JSON index for generated design/rendering concept media. It shows each concept image, local file path, upload object path, Chinese/English alt text, concept label, and claim boundary so the owner/uploader can review images before filling public URLs. It does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-uploaded-url-map-draft` converts `uploaded-url-map.template.json` into owner-fillable `uploaded-url-map.json` and validates empty URLs, placeholder URLs, non-HTTPS URLs, duplicate placeholders, and owner confirmation flags. It is the safe step between media selection/upload and `content-studio-media-ready-handoff`; it does not upload files, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-uploaded-url-map-editor` creates a local HTML form from `uploaded-url-map.json` or `uploaded-url-map.template.json`. The owner/uploader can review each concept/rendering image, fill public HTTPS URLs, confirm `owner_url_confirmed`, preview JSON, and download `uploaded-url-map.filled.json` without hand-editing raw JSON. Import that filled file with `content-studio-uploaded-url-map-import` so the workspace `uploaded-url-map.json` is only overwritten after validation. It does not upload files, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-uploaded-url-map-import` validates a filled JSON exported from the local image URL editor before it becomes the workspace `uploaded-url-map.json`. It checks public HTTPS URLs, owner confirmation warnings, duplicate placeholders, and whether the filled placeholders match the current `uploaded-url-map.template.json`, then writes only the local URL map when safe. It does not upload files, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-media-status` summarizes the current image URL handoff state for Content Studio output. It reads `uploaded-url-map.json`, `uploaded-url-map.template.json`, `media-url-map.json`, `rich-content-cms-payload.media-ready.json`, and `publish-readiness.json` when present, then reports which concept/rendering images still need public HTTPS URLs, owner confirmation, or media-ready handoff. It writes local status JSON/report only and does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-media-ready-handoff` consumes an owner-confirmed uploaded URL map after review. It runs `media-upload-executor`, refreshes `content-studio-publish-prep`, and regenerates the approval packet so the rich content package has `media-url-map.json` and `rich-content-cms-payload.media-ready.json` evidence. It does not upload files, call CMS/admin helpers, write source, publish, or deploy.

`content-studio-operator-ready-handoff` is the Content Studio one-command local refresh after media URLs are filled and confirmed. It runs media status, media-ready handoff, then the no-write operator-ready handoff chain so publish readiness, bundle, operator command, and guarded execution input are refreshed together. It still does not upload files, call CMS/admin helpers, write source, publish, regenerate SEO assets, run npm, or deploy.

`content-studio-owner-decision-editor` creates a local HTML owner decision form from `content-studio-owner-decision.template.json`. The form lets the owner check content/QA/media/latest-research/explicit-execution flags, choose allowed execution scope, add notes, preview JSON, and download a filled decision JSON. It only writes local editor/report artifacts and does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-owner-decision-import` validates an owner-filled decision JSON exported from the local editor, checks that target URL and paired URL match the current decision template, validates the allowed scope, preserves `approval_is_not_execution=true`, and updates only `content-studio-owner-decision.template.json`. It does not run status/orchestrator automatically and does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-owner-decision-status` reads the owner decision template generated by `content-studio-approval-packet`, validates the selected approval scope, checks content/QA/media/latest-research/explicit-execution flags, and reports whether the current package is still review-only, waiting for owner input, ready for media-ready handoff, ready for approved dry-run, ready for operator-ready handoff, or requires separate live confirmation. It writes local decision-status JSON/report only and does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-decision-orchestrator` consumes the owner decision status and runs only the next safe no-write step. Review-only or incomplete decisions stop with a report; media-ready approvals run `content-studio-media-ready-handoff`; approved dry-run decisions refresh `content-studio-publish-prep`; operator-ready decisions run `content-studio-operator-ready-handoff`; live scope is blocked until a separate explicit live execution instruction and live confirmation exist. It does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-owner-review-package` is the no-write one-command handoff for a produced page. It runs the publish candidate, publish prep, approval packet, owner decision editor, media review gallery, media URL template, owner-fillable uploaded URL map draft, media status report, and owner decision status report, then writes an owner review dashboard plus package index report. It does not approve, upload, publish, write source, or deploy.

`publish-plan` consumes `approved-publish-queue.csv` and creates a gated execution plan, JSON payload map, changelog draft, and rollback draft. It still does not call CMS/admin helpers, write databases, edit source, or deploy. Real content publishing must go through the website management admin UI or existing admin service layer, not direct database writes.

`rich-blocks` converts a Markdown rich-content package into structured bilingual blocks, HTML body content, media placeholders, image generation prompts, and a CMS payload draft. It is the stable input for later approved publishing executors.

`rich-editor` converts structured bilingual blocks, media placeholders, and generated concept asset metadata into a local owner-review HTML editor and machine-readable editor manifest. The HTML supports drag/reorder, contenteditable text, adding new text/image/CTA blocks, inserting multiple concept/rendering images with filename/URL/alt/caption/claim-boundary fields, concept preview, and JSON export for later approved execution. It does not log in, write CMS/source, upload media, or publish.

`rich-editor-apply` applies a `rich-editor` JSON export back into a new CMS payload draft, `rich-content-cms-payload.editor-applied.json`. It preserves edited order, edited fields, newly inserted text/image/CTA blocks, and draft-only safety flags. Before writing an applied payload, it runs editor export QA: image blocks must keep alt text, caption, concept label, and claim boundary, and unsupported factual claims such as real cases, reviews, fixed prices, fixed timelines, warranties, or customer proof block the output. It does not overwrite the base payload, call CMS, write source, upload media, or publish. Later dry-run publishing uses the editor-applied payload by default when no media-ready payload or explicit `--cms-payload-path` is present.

`service-pattern-package` builds a full owner-review content package for one service pattern or all service patterns: bilingual brief, rich text/image editor, CMS payload draft, media asset plan, concept SVG assets, URL map example, prompt pack, and reports. It can run by `--target-url`, `--service-slug`, or `--all`. It is draft-only and does not search external webpages, call image APIs, upload media, write CMS/source pages, publish, or deploy.

`media-assets` turns media placeholders into a generated-design asset plan, prompt pack, media library field draft, and optional media-ready CMS payload when an uploaded/selected URL map is provided. If an editor-applied payload exists and no explicit `--cms-payload-path` is provided, media-ready payload generation uses the editor-applied payload so reviewed rich-text edits are preserved. It also detects `NEEDS_MEDIA_UPLOAD:*` images inserted in the rich editor and adds them to the media plan/upload path. It does not generate, upload, or publish media by itself.

`concept-assets` generates local SVG design/rendering concept files from `media-asset-plan.json`. These files are clearly labeled planning visuals, not real project photos. It does not upload media, call image APIs, write CMS records, or publish.

`media-upload-plan` converts generated concept files into an owner-review upload queue, expected storage object paths, and `media_assets` record drafts using the website's known `uploadAdminMediaObject` and `createAdminMediaAsset` path. It does not upload files, call Supabase, write media records, or publish. Real media publishing must go through the website admin media library or existing admin media helper, not direct storage/table writes.

`media-upload-executor` creates a gated media upload execution request and can consume an owner-confirmed uploaded URL map to generate `media-url-map.json` and `rich-content-cms-payload.media-ready.json`. If an editor-applied payload exists and no explicit `--cms-payload-path` is provided, the media-ready payload is generated from the editor-applied payload. It does not upload files or call Supabase by itself.

`media-url-map` scans local generated/selected image files, including generated SVG concept assets for original image placeholders, builds `media-url-map.json` when all files exist and a public base URL is provided, and triggers media-ready CMS payload generation. It does not upload files or verify CDN availability.

`website-publish-adapter` performs read-only discovery against the real website source root. It identifies package manager, available npm scripts, admin/media helper references, SEO generation and verification scripts, generated SEO assets, env key names from examples, and rule documents, then writes `website-publish-adapter.json` plus an owner-facing report. It does not run npm, call CMS, write source, upload media, publish, regenerate assets, or deploy.

`latest-research` records current web research sources before drafting or refreshing content that depends on current guidance, policy, local authority information, material guidance, or recent data. Use Codex/web search to identify authoritative URLs first, then pass selected sources with `--source`; query-only runs remain blocked so the tool never invents citations. `rich-content` automatically reuses matching `research-source-log.csv` rows for the target page unless `--no-use-research-log` is passed, and `publish-plan` reports valid latest-research source counts as part of the execution gate.

`research-search` generates current internet search queries for a target page and can fetch Google News RSS candidates, trusted RSS/Atom feed candidates, or both with `--provider hybrid-rss` without storing API keys. Trusted feed examples are written to `seo-workspace/config/research-search-feeds.example.yml` and should be replaced or extended with owner-approved renovation, design, material, search, government, or standards feeds. It writes `research-search-candidates.json`, `research-search-candidates.csv`, and an owner-review handoff report in the same candidate shape consumed by `research-intake`. Search/feed candidates are not verified claims and do not enter `research-source-log.csv` until `research-intake` or explicit `latest-research --source` succeeds.

`research-discovery` runs before `latest-research` when the skill needs current internet source candidates from trusted seed URLs. It reads trusted source seeds, optionally fetches those pages, scores candidate URLs by authority and relevance, then writes candidate CSV/JSON/report plus copyable `latest-research --source` handoff arguments. It does not write `research-source-log.csv`; candidate URLs must still be selected and fetched by `latest-research`.

`research-intake` is the conservative automation bridge between `research-discovery` and `latest-research`. It reads discovery candidates, accepts only high-scoring trusted source types, fetches them through `latest-research`, and records successful sources in `research-source-log.csv` for later content packages. It writes research evidence only; it does not publish, write CMS/source pages, upload media, or turn third-party information into FLASH CAST business claims.

`publish-executor` currently creates a gated dry-run write request only. It consumes `publish-execution-plan.json` and a CMS payload draft, checks approval/QA/media readiness, and describes the planned admin helper call such as `saveAdminService`; it still does not write CMS/source or deploy. Payload selection order is explicit `--cms-payload-path`, then `rich-content-cms-payload.media-ready.json`, then `rich-content-cms-payload.editor-applied.json`, then base `rich-content-cms-payload.json`. If the selected payload is editor-applied, or a media-ready payload generated from editor-applied content, the executor also checks that `rich-content-editor-apply-summary.json` is `editor_applied_payload_ready_for_owner_review` and that editor-applied safety metadata is present. If the selected payload still contains `NEEDS_MEDIA_UPLOAD:*`, execution remains blocked even when `--media-ready` is passed.

`publish-readiness` summarizes latest research, publish plan, CMS write request, media upload execution, media URL map, and media-ready CMS payload into one handoff gate. It writes readiness-only JSON and report artifacts; it does not upload media, call CMS, write source, publish, regenerate SEO assets, or deploy.

`publish-bundle` seals a ready `publish-readiness` handoff and `cms-write-request` into `publish-execution-bundle.json` for a later approved executor. It blocks unless readiness and the CMS write request are ready, media placeholders are gone, and no upstream blockers remain. It still does not call CMS, write source pages, upload media, publish, or deploy.

`publish-cms-write-executor` is the guarded final admin publishing API executor. It reads `publish-approved-execution-input.json`, blocks if media placeholders or upstream blockers remain, requires explicit `--allowed-target-url` for both bilingual URLs, and defaults to `dry-run` with no write while generating `content-publish-api-request.json`. Non-dry-run direct database writes are disabled: real content publishing must call the website's protected `content-publish` admin API by setting `FLASHCAST_CONTENT_PUBLISH_URL` plus either `FLASHCAST_ADMIN_ACCESS_TOKEN` for an admin session or `FLASHCAST_CONTENT_PUBLISH_SECRET` for the protected `x-cron-secret` machine path, with `--confirm-write` and the required confirmation env. That API owns the management backend save path, so admin content, public content, validation, cache invalidation, and audit records stay synchronized. After any real admin publish, run SEO generation, QA, execution receipt verification, and deployment only if separately approved.

`publish-media-upload-executor` is the guarded final media-library handoff. It reads `media-upload-plan.json`, validates local concept/rendering files, bucket, and claim boundaries, and defaults to `dry-run` with no upload. Non-dry-run direct Supabase Storage or `media_assets` table writes are disabled: real media publishing must go through the website management media library or existing admin media helper so files, media records, public URLs, cache behavior, and audit logs stay synchronized. After media URLs are confirmed, use the uploaded URL map flow for `content-studio-media-ready-handoff`; generated media must remain labeled as design/rendering concepts, not real project proof.

`publish-post-media-handoff` chains uploaded media URLs into the final no-write publishing handoff. It reads `uploaded-url-map.json`, blocks when public HTTPS URLs or owner confirmations are missing, then runs `content-studio-operator-ready-handoff` and `publish-cms-write-executor` in dry-run mode so media-ready payload, operator package, guarded execution input, and CMS write gates stay synchronized. It does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`publish-approved-executor` simulates the later approved executor's final gates from `publish-execution-bundle.json`. It requires owner approval, explicit execution, QA pass, clean media evidence, no unsafe placeholders, and safety flags; non-dry-run modes also require backup, changelog, and rollback evidence, while `live` additionally requires `--confirm-live`. It writes `publish-approved-execution-record.json` and a dry-run report only. It still does not call CMS/admin helpers, write source pages, upload media, publish, regenerate SEO assets, or deploy.

`publish-approved-execution-input` converts a ready operator command package into future execution inputs: a guarded runner template, `publish-approved-execution-input.json`, and `publish-execution-result.template.json`. The generated runner refuses to proceed unless an explicit environment confirmation is set, and this command itself never runs the runner, calls CMS/admin helpers, writes source, uploads media, publishes, regenerates SEO assets, or deploys.

`publish-implementation-package` converts a ready `publish-approved-execution-record.json` into a no-write implementation package for a future real executor. It reads `website-publish-adapter.json` by default, then writes `publish-implementation-package.json`, `publish-admin-helper-call.json`, and an owner-facing runbook with the admin helper call, real website backup/SEO-generation/QA/build commands, execution order, rollback steps, post-write SEO tasks, and helper-source evidence. It still does not run npm, call CMS/admin helpers, write source pages, upload media, publish, regenerate SEO assets, or deploy.

`publish-operator-package` converts a ready implementation package and `publish-admin-helper-call.json` into a deterministic no-write operator command manifest: backup commands, admin helper call, SEO generation, QA, build, rollback, required operator confirmations, and dry-run command preview. It requires a ready website adapter and clean safety flags. It still does not run npm, call CMS/admin helpers, write source pages, upload media, publish, regenerate SEO assets, or deploy.

`publish-operator-ready-handoff` refreshes the full no-write handoff chain after media-ready evidence exists: website adapter, CMS dry-run request, readiness, bundle, approved executor simulation, implementation package, operator package, and guarded execution input. It is the recommended one-command local refresh before asking the owner for final execution. It does not run npm, call CMS/admin helpers, write source pages, upload media, publish, regenerate SEO assets, or deploy.

`publish-execution-receipt` verifies a future approved execution result after a real operator/executor has written CMS/source content. It reads `publish-operator-command.json` and `publish-execution-result.json`, then checks target URL pair, helper function, CMS record ID, backup, CMS write result, SEO regeneration, QA, rollback evidence, command results, and live verification when `publish_status=published`. It writes `publish-execution-receipt.json` and a report only; it does not run commands, call CMS/admin helpers, write source pages, upload media, publish, regenerate SEO assets, or deploy.

`daily-automation` is the safe recurring orchestrator. It picks exactly one task from an existing `daily-content-calendar.json` when present, or falls back to opportunity scoring; explicit `--target-url` always wins. It then runs one pipeline: `brief` for daily draft-only output, `rich-content` for image-rich content package preparation, or `publish-prep` for full dry-run handoff artifacts. `rich-content` and `publish-prep` run `research-search` for current internet/news candidates and `research-discovery` for trusted seed candidates unless explicitly skipped; `--research-search-provider` can be `google-news-rss`, `trusted-rss`, or `hybrid-rss`, and `--research-search-feeds-config` can point to an owner-approved RSS/Atom feed list. When remote fetching is enabled, they can auto-intake high-trust candidates into `research-source-log.csv`, then generate rich blocks, media/concept artifacts, a local review editor, an editor-applied CMS payload draft, a `service-pattern-package` owner-review content package when the target is a service pattern, readiness/bundle gates, implementation package, and operator command package. It never logs in, uploads media, writes CMS/source pages, publishes, runs npm, or deploys by itself.

`scheduled-publish-authorization` validates `seo-workspace/config/scheduled-publish-authorization.yml` and writes a blocked/ready authorization record plus owner-facing report. It requires exact owner authorization IDs, bilingual target URLs, one page per run, unexpired scope, QA/media/storage/backup/changelog/rollback gates, and `live` confirmation when applicable. It does not install schedules, run daily automation, call CMS, upload media, publish, regenerate SEO assets, or deploy.

`scheduled-publish-runner` consumes the scheduled publish authorization profile and creates a single run request for the current scheduled window. It checks local weekday/time, allowed target URL scope, bilingual pair, duplicate same-day ready requests, and authorization readiness, then writes `scheduled-publish-run-request.json`, `scheduled-publish-run-log.csv`, and an owner-facing report. It does not run daily automation, install cron/launchd, call CMS, upload media, publish, regenerate SEO assets, or deploy.

`scheduled-publish-orchestrator` is the safe fixed-time entrypoint after runner approval. It first creates/validates the run request, then only when ready runs `daily-automation --pipeline publish-prep` to generate local draft/prep artifacts. It still does not call CMS/admin helpers, upload media, write live/source pages, publish, regenerate SEO assets, or deploy.

`scheduled-publish-postrun` summarizes the latest scheduled automation artifacts after a run. It reads scheduler, orchestrator, daily automation, readiness, implementation package, operator command, and execution receipt JSON files, categorizes blockers, and writes an owner-facing next-action report. It does not fetch research, run automation, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy.

`automation-schedule` creates and validates the fixed-time automation plan: `daily-automation.example.yml`, cron example, launchd plist example, JSON plan, scheduled publish authorization evidence, and owner-facing schedule report. It supports `executor: daily-automation` for opportunity/calendar selection and `executor: content-studio-next` for consuming exactly one queued page from `content-studio-queue` per run; set `owner_review_package: true` for that executor when the daily run should finish with the owner review dashboard, publish-candidate, publish-prep, approval-packet, media review gallery, media URL template, owner-fillable uploaded URL map draft, and media status report. The default schedule carries `research_search_provider: hybrid-rss` and `research_search_feeds_config` so fixed-time rich-content/publish-prep runs can use both news RSS and trusted feed candidates when remote fetching is enabled. The generated cron/launchd command routes through `content-studio-orchestrator` so time-window and duplicate-run guards still apply. It does not install cron/launchd jobs or execute the automation. Scheduled publishing remains blocked unless an exact owner authorization profile is present and validated.

## Daily Workflow

For a daily run, choose exactly one highest-value organic growth task. Prefer:

1. high-commercial-intent service page optimization
2. existing page title/meta/FAQ/internal link/CTA/schema optimization
3. design concept or effect-rendering section/page when useful and clearly labeled
4. real case study draft/improvement only when suitable real case data exists
5. verified service-area page improvement
6. old article refresh
7. image alt/schema/technical recommendation
8. new article only when there is a real content gap

Every daily output must explain why the task is more valuable than writing a random article and save to `seo-workspace/drafts/` or `seo-workspace/reports/`.

End daily automation with exactly these five Simplified Chinese lines:

```text
- 已完成：
- 目标关键词/页面：
- 预期收益：
- 需要业主补充：
- 建议下一步：
```

## Required Pre-Publish QA

Before any approved execution or publish, run QA:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url <url>
```

QA must check: no fake claims, no fake reviews, no fake cases, no fake price, no fake ranking promise, no unsupported service area, no keyword stuffing, no doorway page, no duplicate city swap, no wrong canonical, no noindex, robots allowed, sitemap included, title/meta/H1 present, CTA present, internal links present, schema valid, `/zh` and `/en` pair considered, concept/rendering labels, backup before live, and rollback plan before live.

Serious QA issues return exit code `1`. Owner-input gaps alone return exit code `0` but must be reported.

## Search Engines And Indexing

Use Google Search Console, Baidu Search Resource Platform, Bing/IndexNow, sitemap, robots, canonical, and technical audit workflows for discovery/indexation support. Never describe any submission as guaranteed indexing or ranking.

For this Flash Cast workspace, Google Search Console is a required workflow whenever owner access or credentials are available. Use it for sitemap submission, status checks, and inspection/performance reporting; do not treat Google work as optional. Apple Maps / Apple Business Connect is currently out of scope by owner decision and should not be continued unless the owner explicitly reopens it.

Google Indexing API is blocked for ordinary renovation pages. It is allowed only for eligible `JobPosting` or `VideoObject` with `BroadcastEvent` structured data.

Read:

- `references/indexation-policy.md`
- `references/google-search-console-policy.md`
- `references/baidu-indexation-policy.md`
- `references/indexnow-policy.md`

## Google Ads / PPC

Use Google Ads only as a controlled lead-generation channel for renovation services in Malaysia, primarily Kuala Lumpur, Selangor, and nearby Klang Valley cities. Before working inside Google Ads, read `references/google-ads-renovation-ppc.md`.

Default launch strategy for a small starting balance such as RM200:

1. verify conversion tracking first: WhatsApp click, phone click, quote/contact form submit, GA4/Google Ads tag status, and deployed JavaScript/event behavior
2. do not treat a page as conversion-ready just because a Google tag is present in HTML; verify the live app actually fires lead events for WhatsApp, phone, and successful forms while excluding validation errors
3. start with one Search campaign for high-intent renovation leads before Performance Max
4. target only the approved service area; avoid all-Malaysia targeting unless owner explicitly approves
5. use tightly grouped phrase/exact keywords first; add broad match only after conversion data is reliable
6. set a conservative daily budget and remember Google may spend above the average daily budget on some days while pacing monthly spend
7. keep auto-apply recommendations off unless the owner approves each category
8. write truthful bilingual ad copy and avoid unsupported claims such as cheapest, guaranteed ranking, guaranteed price, #1, fake discounts, fake urgency, or unverified licenses/awards
9. pause or do not launch when conversion tracking, billing, destination page, location targeting, or policy status is unclear

Any paid campaign launch or budget increase must be reported with: campaign name, objective, daily budget, estimated monthly exposure, locations, languages, bidding strategy, conversion actions, ad groups, sample ads, negative keywords, landing pages, rollback/pause plan, and exact owner approval status.

After every paid ads execution or material optimization, create a follow-up time record. The record must state the action completed, the next review time, what to check, where the review report will be written, and which actions are blocked without fresh owner approval. For newly launched or materially changed Google Ads campaigns, set or update a monitoring automation when the environment supports it: use a short-term 72-hour watch for launch/review/spend/search-term issues, then a daily review cadence for ongoing optimization. Each review must write a dated Simplified Chinese report under `seo-workspace/reports/` and summarize whether no action, tightening, pausing, conversion-tracking repair, landing-page work, or owner approval is needed.

Paid ads monitoring may inspect campaign performance, policy status, search terms, locations, devices, conversion tracking, lead signals, negative keyword opportunities, landing pages, and Google recommendations when the owner is logged in or credentials are otherwise available. It must not read or save cookies, passwords, tokens, or secrets. If login, passkey, CAPTCHA, OTP, or owner-only verification is required, stop and ask the owner to complete it.

During unattended paid ads monitoring, do not automatically increase budget, broaden locations, enable Performance Max, enable AI Max, enable Display, enable Search partners, switch to broad match, enable auto-apply recommendations, change bidding, change billing, or promise ROI/leads. Emergency pausing is allowed only when spend is clearly abnormal, traffic is obviously irrelevant, or continuing would waste budget; report the pause immediately with evidence and next steps.

## Content And Claims

Allowed when clearly labeled: design concepts, effect renderings, layout ideas, material plans, scenario planning examples, visual direction images, and concept placeholders.

Never present planning material as completed projects, real customer cases, before/after proof, real reviews, confirmed prices, fixed timelines, warranty promises, awards, media mentions, certifications, or real customer photos.

Read:

- `references/content-production-publishing-system.md`
- `references/anti-spam-policy.md`
- `references/content-quality-policy.md`
- `references/source-and-claims-policy.md`
- `references/publishing-checklist.md`

## Specialized Workflows

Use the matching checklist before working in each area:

- Technical SEO: `references/technical-seo-checklist.md`
- Local SEO: `references/local-seo-checklist.md`
- Google Ads / paid search: `references/google-ads-renovation-ppc.md`
- Growth intelligence / data-led SEO-GEO-PPC loop: `references/growth-intelligence-operating-loop.md`
- GEO/AI search: `references/geo-ai-search-checklist.md`
- Multilingual SEO: `references/multilingual-seo-checklist.md`
- Schema: `references/schema-policy.md`
- Permissions/live publishing: `references/permissions-and-live-publishing.md`
- Full operating system: `references/seo-geo-operating-system.md`

## Owner Approval Rules

Execution requires a specific owner-approved draft/report/plan plus an explicit instruction such as "execute this plan", "publish this approved draft", or "apply this optimization".

When approved execution is page-level and language scope is not specified, update both Chinese and English page pairs.

For service-page execution, use the existing admin/backend service layer, such as `saveAdminService` / `saveAdminRecord`, or the protected `content-publish` admin API that wraps that backend save path. Do not direct-write content database rows from Codex or skill scripts, because this can desynchronize the management backend, public pages, cache invalidation, validation, and audit records.

## Automation Rules

When invoked unattended:

- do not ask questions unless truly blocked
- do not publish
- do not log in to CMS/admin
- do not modify live/source pages
- do not submit Google/Baidu/IndexNow unless explicitly authorized and configured
- create one dated draft/report
- mark it waiting for owner review and explicit execution instruction
- keep owner-facing output in Simplified Chinese
