# Repository Instructions for Codex

This repository contains the Flash Cast renovation SEO/GEO workspace.

For SEO, GEO, content marketing, service pages, area pages, case studies, metadata, FAQ, image alt text, internal linking, local SEO, indexation, schema, multilingual SEO, technical SEO, Google Ads/PPC planning, publishing QA, and daily content workflows, use the repo skill:

```text
renovation-seo-geo
```

Treat this role as the website's SEO/GEO Growth Operator, not as a daily article generator.

## Mandatory Rules

- Default mode is not live. Use `draft` or `audit` unless the owner explicitly approves a specific plan and asks to execute it.
- Google Ads/PPC default mode is audit or draft only. Do not launch, enable, unpause, raise budget, broaden targeting, enable auto-apply recommendations, change bidding, or spend advertising budget unless the owner explicitly approves the exact campaign, daily budget, locations, conversion actions, and launch timing.
- Live execution requires backup, QA pass, changelog, rollback plan, allowed live path, and explicit live confirmation.
- Do not guarantee rankings, indexing, traffic, leads, ROI, first page, or first position.
- Do not use black-hat SEO, keyword stuffing, doorway pages, duplicate city pages, AI-search bait, hidden text, or spammy page variations.
- Do not fabricate business claims, reviews, prices, service areas, certifications, awards, credentials, project cases, photos, before/after proof, timelines, warranty terms, or customer claims.
- Do not use fake urgency, fake discounts, cheapest/#1/best claims, guaranteed lead/ranking claims, competitor-trademark ad copy, or unverified license/certification/award claims in ads.
- Do not commit real secrets: tokens, OAuth files, service-account JSON, CMS credentials, admin cookies, Baidu tokens, IndexNow keys, or API keys.
- Scheduled automation must not publish, log in to admin/CMS, submit platforms, or modify live/source pages unless explicitly authorized for that exact action.
- Owner-facing drafts, optimization plans, approval notes, QA notes, reports, and daily reports must be in Simplified Chinese by default.
- Publishable page planning is bilingual by default: include `中文页面建议文案` for `/zh` and `英文页面建议文案` for `/en`.
- If an approved page-level execution has a clear `/zh` and `/en` pair, update both language versions unless the owner explicitly limits scope.
- Codex may independently use public web/search/maps/listing data and local workspace/source files to find competitors, public business listing URLs, page gaps, existing facts, and asset inventories, but uncertain identity/ownership/facts must be marked `NEEDS OWNER CONFIRMATION`.
- Owner-only inputs include private GSC/Bing/GBP/analytics data, platform credentials, official listing confirmation, third-party edit/submit permission, real project proof, customer permissions, testimonials, budgets, timelines, warranty terms, certificates, licenses, awards, exact NAP, and unverified service-area claims.
- Owner-approved AI renderings can be used as `效果图案例` / `设计方案案例` / `rendering concept case` assets. They are allowed for renovation content, but must not be labeled as completed real projects, real customer photos, or real before/after proof without separate owner-confirmed evidence.

## Repository Structure

- Skill workflow: `.agents/skills/renovation-seo-geo/`
- Skill scripts: `.agents/skills/renovation-seo-geo/scripts/`
- Skill policies: `.agents/skills/renovation-seo-geo/references/`
- Google Ads / PPC policy: `.agents/skills/renovation-seo-geo/references/google-ads-renovation-ppc.md`
- Business data: `seo-workspace/data/`
- Daily drafts: `seo-workspace/drafts/`
- Reports: `seo-workspace/reports/`
- Config examples: `seo-workspace/config/`
- Approved live content: real website content directory or CMS only after explicit approval

Do not place skill files or daily drafts under `src/`, `app/`, `pages/`, `content/blog/`, `components/`, or `public/`.

## Common Commands

Validate workspace:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py validate
python3 validate_workspace.py
```

Check config:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py config
```

Crawl and technical audit:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py crawl --site https://www.example.com
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py technical-audit
```

Search engine workflows:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py gsc-sync
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py google-index-status --urls changed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py google-submit-sitemap
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py baidu-submit --urls changed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py indexnow-submit --urls changed
```

Growth workflows:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py opportunities
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-performance-digest
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ai-search-monitor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py competitor-gap-audit
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-citation-tracker
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py real-proof-asset-request
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-ops-audit
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-calendar --days 14
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline brief
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline rich-content --research-search-provider hybrid-rss
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline publish-prep
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py automation-schedule
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-authorization
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-runner
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-postrun
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-system
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-queue
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-postrun
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-publish-candidate --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-publish-prep --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-approval-packet
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-url-template
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-uploaded-url-map-draft
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-owner-review-package --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-next --no-fetch-research-remote --owner-review-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio --target-url https://flashcast.com.my/en/services/kitchen --pipeline rich-content
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py service-pattern-package --service-slug kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-search --target-url https://flashcast.com.my/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-search --target-url https://flashcast.com.my/en/services/kitchen --provider trusted-rss
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-discovery --target-url https://flashcast.com.my/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-intake --target-url https://flashcast.com.my/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py latest-research --target-url https://flashcast.com.my/en/services/kitchen --query "kitchen renovation malaysia" --source "official|https://example.com/source|Use for general guidance only|not a FLASH CAST claim|kitchen renovation malaysia"
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-content --target-url https://flashcast.com.my/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-blocks --target-url https://flashcast.com.my/en/services/kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-editor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-assets
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py concept-assets
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-upload-plan
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-upload-executor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-url-map --asset-dir seo-workspace/media/generated --public-base-url https://example.com/uploads
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-queue --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py website-publish-adapter --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-plan --target-url https://flashcast.com.my/en/services/kitchen --owner-approved --explicit-execution --qa-passed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-executor --owner-approved --explicit-execution --qa-passed --media-ready
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-readiness
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-bundle
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-approved-executor --owner-approved --explicit-execution --qa-passed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-approved-execution-input
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-implementation-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-operator-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-operator-ready-handoff --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-execution-receipt
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py entity
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py geo-ai
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-seo
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py schema
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py multilingual
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py image-seo
```

Google Ads / PPC workflow:

- Read `.agents/skills/renovation-seo-geo/references/google-ads-renovation-ppc.md` before entering Google Ads.
- First action is an account audit and local launch plan, not immediate launch.
- For a small RM200 test, prefer one tightly scoped Search campaign for KL/Selangor renovation leads before Performance Max.
- Confirm conversion tracking for WhatsApp, phone, and form submits before optimizing for conversions.
- Stop before the final publish/enable click and report campaign name, daily budget, locations, bidding, conversion actions, keywords, ads, negatives, landing pages, and pause plan for owner approval.
- After each paid ads execution or material optimization, write a follow-up time record: completed action, next review time, metrics to check, report path, blocked actions, and pause/tightening threshold.
- For newly launched or materially changed Google Ads campaigns, create or update a 72-hour short-term watch and a daily review cadence when automation is available.
- Paid ads review automation must write dated Simplified Chinese reports under `seo-workspace/reports/` and may inspect logged-in Google Ads pages only when access is already available.
- Do not store cookies, passwords, tokens, OTPs, passkeys, or platform secrets. If Google requires owner-only verification, stop and ask the owner to complete it.
- Monitoring must not automatically increase budget, broaden locations, enable Performance Max, enable AI Max, enable Display, enable Search partners, switch to broad match, enable auto-apply recommendations, change bidding, change billing, or promise ROI/leads. Emergency pause is allowed only for clear abnormal spend or obviously irrelevant traffic, and must be reported immediately.

Pre-publish QA:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url https://www.example.com/zh/services/renovation
```

Apply preflight:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py apply --plan seo-workspace/drafts/example.md --mode pr
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py apply --plan seo-workspace/drafts/example.md --mode live --confirm-live
```

Development validation:

```bash
python3 -m py_compile $(find .agents/skills/renovation-seo-geo/scripts -name '*.py' -print)
python3 -m pytest -q
python3 validate_workspace.py
```

## SEO/GEO Workflow

Before meaningful SEO/GEO work, inspect:

- `seo-workspace/data/brand-profile.md`
- `seo-workspace/data/services.md`
- `seo-workspace/data/service-areas.csv`
- `seo-workspace/data/case-studies.csv`
- `seo-workspace/data/keyword-map.csv`
- `seo-workspace/data/internal-links.csv`
- existing reports under `seo-workspace/reports/`
- existing drafts under `seo-workspace/drafts/`

Daily work must choose exactly one highest-value organic growth task. Prefer high-commercial-intent service page optimization, existing page metadata/FAQ/internal-link/schema/CTA improvements, local SEO, technical SEO, image SEO, schema, and GEO/entity improvements over random new articles. For multi-day planning, run `content-calendar` first to rotate bilingual page pairs and avoid repeating the same recently selected URL; it writes planning artifacts only and does not draft or publish. `daily-automation` uses that calendar by default when present and no explicit `--target-url` is provided. For recurring unattended operation, generate the fixed-time plan with `automation-schedule`; use `executor: daily-automation` for opportunity/calendar selection or `executor: content-studio-next` for consuming one queued page per run, and set `owner_review_package: true` when each queued run should also generate the publish-candidate, publish-prep, approval-packet, and media URL template handoff; validate the publish gate with `scheduled-publish-authorization`, create per-run requests with `scheduled-publish-runner`, use `scheduled-publish-orchestrator` as the safe fixed-time entrypoint when publish-prep should run, then summarize outcomes with `scheduled-publish-postrun`. Prefer `daily-automation --pipeline brief` by default; use `--pipeline rich-content` or `--pipeline publish-prep` only for owner-approved preparation depth. Those richer pipelines run `research-search` and `research-discovery` first unless skipped, can run conservative `research-intake` when remote fetching is enabled, generate local rich editor artifacts, and apply the editor manifest/export into an editor-applied CMS payload draft. Do not publish without a separate execution instruction.

For full-site content production, image-rich publishing, generated design/rendering concepts, and scheduled automation planning, run `content-system`; run `content-studio-queue` to convert all mapped URLs into a bilingual production queue with recommended commands; run `content-studio-orchestrator` as the fixed-time guarded entrypoint for queue consumption; run `content-studio-postrun` after queued automation to summarize latest processed page, next queue item, blockers, and owner review actions; run `content-studio-publish-candidate` to convert the latest Content Studio package into a safe owner-review publish candidate; run `content-studio-publish-prep` to build the consolidated local publish handoff for that candidate; run `content-studio-next` when a manual run should consume exactly one unprocessed queue item and append history; for one target page, prefer `content-studio --target-url <url> --pipeline rich-content` or `--pipeline publish-prep` to generate the research candidates, rich content, local editor, media/concept assets, service-pattern package when available, and owner-review handoff in one draft-only pass; for service-pattern pages, run `service-pattern-package --service-slug <slug>` or `--all` when only that service-pattern package is needed. When current facts are needed, use `research-search` for current internet/news candidates, use `research-discovery` for trusted seed-source candidates, use `research-intake` for high-trust auto intake when appropriate, then record selected sources with `latest-research`; for a single page's rich text/image/source-log package, run `rich-content`, which reuses matching `research-source-log.csv` rows by default; convert it into structured blocks and CMS payload draft with `rich-blocks`; create a local owner-review editor with `rich-editor` for drag/reorder, text edits, image edits, and inserting new text/image/CTA blocks; if the owner edits and exports JSON, convert that export into a new draft payload with `rich-editor-apply`; rerun `media-assets` after editor edits so newly inserted `NEEDS_MEDIA_UPLOAD:*` images enter the media plan and URL-map gate; generate local labeled SVG concept assets with `concept-assets`; create owner-review upload queue and media record drafts with `media-upload-plan`; build a gated upload execution request or consume confirmed uploaded URLs with `media-upload-executor`; map generated/selected files back to URLs with `media-url-map`; for owner-review publishing queue and CMS/source field mapping, run `publish-queue`; discover the real website helper/command adapter with `website-publish-adapter`; validate fixed-time publish authorization with `scheduled-publish-authorization`; create a per-window run request with `scheduled-publish-runner`; trigger safe publish-prep with `scheduled-publish-orchestrator` only when the run request is ready; summarize outcomes and next actions with `scheduled-publish-postrun`; for an approved queued item, run `publish-plan`, which reports latest-research evidence counts; build the gated CMS/source dry-run request with `publish-executor`; summarize final handoff readiness with `publish-readiness`; seal the final approved executor input with `publish-bundle`; simulate final approved-executor gates with `publish-approved-executor`; create a no-write future executor runbook with `publish-implementation-package`, which consumes `website-publish-adapter.json` for real backup/SEO/QA/build commands; create a deterministic no-write command manifest with `publish-operator-package`; verify any future real execution result with `publish-execution-receipt`; then follow `.agents/skills/renovation-seo-geo/references/content-production-publishing-system.md`. Payload selection order is explicit `--cms-payload-path`, media-ready payload, editor-applied payload, then base payload; media placeholders in the selected payload always block execution. `research-search` and `research-discovery` only create candidates; search results are not verified source facts until `research-intake` or `latest-research` writes the source log. `content-studio-publish-prep`, `content-studio-publish-candidate`, `content-studio-postrun`, `content-studio-orchestrator`, `content-studio-next`, `content-studio-queue`, `content-studio`, `service-pattern-package`, `scheduled-publish-authorization`, `scheduled-publish-runner`, `scheduled-publish-orchestrator`, `scheduled-publish-postrun`, `website-publish-adapter`, `publish-approved-executor`, `publish-implementation-package`, `publish-operator-package`, and `publish-execution-receipt` write local records/runbooks/manifests/receipts only and still do not install schedules, run npm, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.

Use onboarding mode when `seo-workspace/reports/seo-onboarding-report.md` does not exist or when the owner asks to set up/audit the workflow. Onboarding should generate `seo-workspace/reports/seo-onboarding-report.md` and should not write random articles.

## Search Engines And Indexation

- Google Search Console is a required search-engine workflow for this project when owner access/credentials are available: use it for sitemap submission, status checks, and inspection/performance data reporting. Do not treat Google work as optional.
- Google Search Console may be used for sitemap submission and inspection data when credentials are configured.
- Google Indexing API is blocked for ordinary renovation pages. It is allowed only for eligible `JobPosting` or `VideoObject` with `BroadcastEvent`.
- Baidu submit must gracefully degrade without token and generate owner-input/config instructions.
- IndexNow must gracefully degrade without key and generate key setup instructions.
- Apple Maps / Apple Business Connect is currently out of scope by owner decision. Do not continue Apple Maps work unless the owner explicitly reopens it.
- Indexation reports must use precise terms such as `checked`, `submitted`, `accepted`, `failed`, `not_checked`, or `needs_owner_input`; never write guaranteed indexed or guaranteed ranking.

## Content And Claims

The owner allows clearly labeled design concepts, effect renderings, layout ideas, material plans, scenario-based planning examples, visual direction images, service page hero concepts, case page placeholder concepts, and social media graphics.

Do not describe concept/rendering/planning material as completed real projects, real customer cases, before/after proof, customer reviews, confirmed prices, fixed timelines, warranty promises, awards, credentials, or real customer photos.

Do not mark missing real cases, real photos, fixed budget ranges, fixed timeline ranges, warranty terms, or customer reviews as blockers. Continue safely with clearly labeled concept/planning material. Use `NEEDS OWNER INPUT` only for unsupported factual business claims, service areas, CTA/contact changes, platform credentials, or publishing facts required before execution.

## Publishing Rules

Publishing is a separate owner-approved step:

1. Owner approves a specific draft or optimization plan.
2. Owner explicitly asks Codex to execute it.
3. Re-check the publishing checklist and run QA.
4. Confirm backup, changelog, and rollback plan.
5. Publish or edit through the requested path only: CMS/admin, the website's existing admin service layer, the protected `content-publish` admin API that wraps that service layer, or owner-approved source edit.
6. For service content, use `saveAdminService` / `saveAdminRecord` or the protected `content-publish` API so admin content, public content, cache invalidation, validation, and audit behavior stay aligned.
7. Do not directly update Supabase tables or website database rows for publishable content. Publishing must go through the website management admin UI, the existing admin service layer, or `content-publish` with admin Bearer token or `CONTENT_PUBLISH_SECRET` / `x-cron-secret`, so admin content, public content, validation, cache invalidation, and audit behavior stay synchronized.
8. For bilingual page pairs, update both `/zh` and `/en` records plus SEO metadata/manifest/sitemap where applicable.
9. If approved execution includes image needs, create or prepare conceptual image assets and matching bilingual captions/alt text before publishing, unless the owner explicitly asks for text-only execution.
10. Report exactly what changed in both languages, including which images are concept/rendering assets versus real owner-provided assets.
