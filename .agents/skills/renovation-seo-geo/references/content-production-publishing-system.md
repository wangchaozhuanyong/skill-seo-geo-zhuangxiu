# Content Production And Publishing System

Use this reference when the owner asks the skill to produce website content end to end, including latest-source research, image-rich pages, design renderings, rich text, publishing plans, and scheduled SEO/GEO automation.

## Operating Goal

The skill can prepare all publishable website content types for the renovation site:

- service pages
- service hub pages
- local area pages
- case study pages
- design concept / rendering concept pages
- old article refreshes
- new educational articles when a real gap exists
- homepage and conversion page copy
- FAQ, metadata, schema, internal links, CTA, image alt text, captions, and rich-text section structure

Default output remains draft-only unless the owner approves a specific draft and asks to execute it.

## Latest Internet Research

Use web search when the content depends on current facts, current industry guidance, search-engine policy, local authority guidance, material guidance, or recent data.

Rules:

- Use authoritative sources first: official search-engine docs, official government/local authority pages, manufacturer docs, standards bodies, or reputable industry publications.
- Do not copy competitor renovation pages as content sources.
- Save or include a source log when external facts are used.
- Distinguish external general guidance from FLASH CAST business facts.
- Never use external sources to invent FLASH CAST prices, awards, reviews, credentials, project counts, warranty terms, or service areas.

## Image-Rich Content

Every image-rich draft should include:

- image placement
- image purpose
- image generation prompt or asset brief
- Chinese alt text
- English alt text
- caption
- concept label when the image is generated or illustrative
- file name suggestion
- whether owner proof is required

Allowed labels:

- `设计方案`
- `效果图方案`
- `概念设计`
- `规划示例`
- `参考方案`
- `design concept`
- `rendering concept`
- `planning example`

Generated or illustrative images may support renovation content, but they are not factual proof. Do not describe them as completed real projects, real customer homes, before/after proof, real customer photos, reviews, fixed prices, fixed timelines, or warranty evidence.

## Real Case Editing

If owner-approved real project facts exist, create a real case study using only the confirmed facts.

If proof is incomplete, convert the page to a clearly labeled planning or rendering concept:

- `真实案例` only when project facts and public-use permission are available.
- `设计方案 / 效果图方案 / 概念设计` when generated images or planning examples are used.
- `NEEDS OWNER INPUT` only for factual claims required before publishing, not for missing photos or missing reviews.

## Rich Text Structure

For CMS or source execution, prepare content as structured sections, not one flat block:

- hero
- quick answer
- service scope
- planning examples
- process
- budget/timeline factors without fake numbers
- image blocks with alt/caption
- FAQ
- internal links
- CTA
- schema fields

When the website supports full rich text, preserve paragraph order, image placement, captions, and alt text. When it only supports simpler fields, create a field mapping and note what cannot be represented.

For owner review before publishing, use `rich-editor`:

- edit bilingual blocks locally without CMS login
- drag/reorder existing sections
- insert new text, image, and CTA blocks
- add multiple generated design/rendering concept images with filename, upload placeholder, alt text, caption, concept label, and claim boundary
- export JSON for `rich-editor-apply`
- keep all generated visuals labeled as design concepts/rendering concepts until real owner-provided proof exists

Use `rich-editor-apply` to convert the editor export into `rich-content-cms-payload.editor-applied.json`. This still does not publish; it only prepares the richer payload for later owner-approved execution gates. Editor export QA blocks image blocks that lose alt text, captions, concept labels, or claim boundaries, and blocks unsupported factual claims such as real cases, reviews, fixed prices, fixed timelines, warranties, or customer proof. Later publishing gates must keep `rich-content-editor-apply-summary.json` at `editor_applied_payload_ready_for_owner_review` before an editor-applied payload, or media-ready payload generated from it, can be treated as ready.

After editor edits, run `media-assets` again. It reads the editor-applied payload by default, detects newly inserted `NEEDS_MEDIA_UPLOAD:*` images from the edited rich HTML, adds them to `media-asset-plan.json`, and requires the URL map to cover those new images before a media-ready CMS payload can be generated.

## Publishing Execution

Publishing is a separate step.

Before execution:

- owner approves a specific draft or plan
- owner asks Codex to execute that exact plan
- target CMS/source path is confirmed
- backup exists
- QA passes
- changelog path exists
- rollback plan exists
- bilingual scope is handled

Preferred execution path:

1. existing admin/backend service layer
2. source edit following website conventions
3. direct database/API writes are not allowed for publishable content; use the website management admin UI or existing admin service layer so the customer-facing site and admin data stay synchronized

Scheduled automation may generate drafts daily. Scheduled live publishing requires an exact authorization profile that names the allowed content types, target paths, time window, QA gates, rollback process, and whether bilingual page pairs are required.

## Recommended CLI

Run:

```bash
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-system
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-queue
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-orchestrator
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-postrun
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-next --no-fetch-research-remote --owner-review-package
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio --target-url https://flashcast.com.my/en/services/kitchen --pipeline rich-content
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py service-pattern-package --service-slug kitchen
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-calendar --days 14
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py automation-schedule
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-authorization
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-runner
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-orchestrator
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-postrun
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline brief
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline rich-content --research-search-provider hybrid-rss
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-search --target-url https://flashcast.com.my/en/services/kitchen
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-search --target-url https://flashcast.com.my/en/services/kitchen --provider trusted-rss
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-discovery --target-url https://flashcast.com.my/en/services/kitchen
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-intake --target-url https://flashcast.com.my/en/services/kitchen
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py latest-research --target-url https://flashcast.com.my/en/services/kitchen --query "kitchen renovation malaysia" --source "official|https://example.com/source|Use for general guidance only|not a FLASH CAST claim|kitchen renovation malaysia"
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-content --target-url https://flashcast.com.my/en/services/kitchen
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-blocks --target-url https://flashcast.com.my/en/services/kitchen
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-editor
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-editor-apply --editor-export-path seo-workspace/data/edited-export.json
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-assets
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py concept-assets
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-upload-plan
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-upload-executor
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-review-package
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-uploaded-url-map-draft
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-status
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py media-url-map --asset-dir seo-workspace/media/generated --public-base-url https://example.com/uploads
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-queue --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py website-publish-adapter --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-plan --target-url https://flashcast.com.my/en/services/kitchen --owner-approved --explicit-execution --qa-passed
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-executor --owner-approved --explicit-execution --qa-passed --media-ready
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-readiness
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-bundle
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-approved-executor --owner-approved --explicit-execution --qa-passed
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-approved-execution-input
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-implementation-package --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-operator-package
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-operator-ready-handoff --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-execution-receipt
```

This creates:

- `seo-workspace/data/content-publishing-system-map.csv`
- `seo-workspace/reports/YYYY-MM-DD-content-publishing-system-report.md`
- `seo-workspace/data/daily-content-calendar.json`
- `seo-workspace/data/daily-content-calendar.csv`
- `seo-workspace/reports/YYYY-MM-DD-daily-content-calendar.md`
- `seo-workspace/config/daily-automation.example.yml`
- `seo-workspace/config/daily-automation.cron.example`
- `seo-workspace/config/com.flashcast.daily-seo-geo.plist.example`
- `seo-workspace/data/daily-automation-schedule-plan.json`
- `seo-workspace/reports/YYYY-MM-DD-daily-automation-schedule.md`
- `seo-workspace/config/scheduled-publish-authorization.example.yml`
- `seo-workspace/data/scheduled-publish-authorization.json`
- `seo-workspace/reports/YYYY-MM-DD-scheduled-publish-authorization.md`
- `seo-workspace/data/scheduled-publish-run-request.json`
- `seo-workspace/data/scheduled-publish-run-log.csv`
- `seo-workspace/reports/YYYY-MM-DD-scheduled-publish-run-request.md`
- `seo-workspace/data/scheduled-publish-orchestration.json`
- `seo-workspace/reports/YYYY-MM-DD-scheduled-publish-orchestration.md`
- `seo-workspace/data/scheduled-publish-postrun-summary.json`
- `seo-workspace/reports/YYYY-MM-DD-scheduled-publish-postrun-report.md`
- `seo-workspace/data/daily-automation-run.json`
- `seo-workspace/reports/YYYY-MM-DD-daily-automation-run.md`
- `seo-workspace/data/research-search-candidates.csv`
- `seo-workspace/data/research-search-candidates.json`
- `seo-workspace/reports/YYYY-MM-DD-research-search-report.md`
- `seo-workspace/drafts/YYYY-MM-DD-research-search-handoff.md`
- `seo-workspace/config/research-sources.example.yml`
- `seo-workspace/data/research-discovery-candidates.csv`
- `seo-workspace/data/research-discovery-candidates.json`
- `seo-workspace/reports/YYYY-MM-DD-research-discovery-report.md`
- `seo-workspace/drafts/YYYY-MM-DD-research-source-selection.md`
- `seo-workspace/data/latest-research-sources.csv`
- `seo-workspace/reports/YYYY-MM-DD-latest-research-report.md`
- `seo-workspace/drafts/YYYY-MM-DD-latest-research-brief.md`
- `seo-workspace/drafts/YYYY-MM-DD-<target>-rich-content-package.md`
- `seo-workspace/data/research-source-log.csv`
- `seo-workspace/data/rich-content-blocks.json`
- `seo-workspace/data/rich-content-cms-payload.json`
- `seo-workspace/drafts/YYYY-MM-DD-<target>-rich-content-preview.html`
- `seo-workspace/reports/YYYY-MM-DD-<target>-rich-content-blocks-report.md`
- `seo-workspace/data/rich-content-editor-manifest.json`
- `seo-workspace/drafts/YYYY-MM-DD-rich-content-editor.html`
- `seo-workspace/reports/YYYY-MM-DD-rich-content-editor-report.md`
- `seo-workspace/data/rich-content-cms-payload.editor-applied.json`
- `seo-workspace/data/rich-content-editor-apply-summary.json`
- `seo-workspace/reports/YYYY-MM-DD-rich-editor-apply-report.md`
- `seo-workspace/data/<slug>-service-pattern-content-package-summary.json`
- `seo-workspace/data/service-pattern-content-package-index.json`
- `seo-workspace/reports/YYYY-MM-DD-<slug>-service-pattern-content-package.md`
- `seo-workspace/data/media-asset-plan.json`
- `seo-workspace/data/concept-asset-manifest.json`
- `seo-workspace/media/generated/*.svg`
- `seo-workspace/data/media-upload-queue.csv`
- `seo-workspace/data/media-upload-plan.json`
- `seo-workspace/reports/YYYY-MM-DD-media-upload-plan.md`
- `seo-workspace/data/media-upload-execution-request.json`
- `seo-workspace/reports/YYYY-MM-DD-media-upload-executor-dry-run.md`
- `seo-workspace/data/content-studio-media-review-package.json`
- `seo-workspace/drafts/YYYY-MM-DD-content-studio-media-review-gallery.html`
- `seo-workspace/reports/YYYY-MM-DD-content-studio-media-review-package.md`
- `seo-workspace/data/content-studio-media-status.json`
- `seo-workspace/reports/YYYY-MM-DD-content-studio-media-status.md`
- `seo-workspace/data/media-url-map.example.json`
- `seo-workspace/data/media-file-manifest.csv`
- `seo-workspace/data/media-url-map.json` when local files and public base URL are complete
- `seo-workspace/drafts/YYYY-MM-DD-media-generation-prompts.md`
- `seo-workspace/reports/YYYY-MM-DD-media-url-map-report.md`
- `seo-workspace/reports/YYYY-MM-DD-media-asset-plan.md`
- `seo-workspace/data/rich-content-cms-payload.media-ready.json` when a complete URL map is provided
- `seo-workspace/data/publishing-field-map.json`
- `seo-workspace/data/approved-publish-queue.csv`
- `seo-workspace/reports/YYYY-MM-DD-publishing-queue-report.md`
- `seo-workspace/data/website-publish-adapter.json`
- `seo-workspace/reports/YYYY-MM-DD-website-publish-adapter.md`
- `seo-workspace/data/publish-execution-plan.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-execution-plan.md`
- `seo-workspace/reports/YYYY-MM-DD-publish-change-log-draft.md`
- `seo-workspace/reports/YYYY-MM-DD-publish-rollback-plan-draft.md`
- `seo-workspace/data/cms-write-request.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-executor-dry-run.md`
- `seo-workspace/data/publish-readiness.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-readiness-report.md`
- `seo-workspace/data/publish-execution-bundle.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-execution-bundle.md`
- `seo-workspace/data/publish-approved-execution-record.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-approved-executor-dry-run.md`
- `seo-workspace/data/publish-implementation-package.json`
- `seo-workspace/data/publish-admin-helper-call.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-implementation-package.md`
- `seo-workspace/data/publish-operator-command.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-operator-command.md`
- `seo-workspace/config/publish-execution-result.example.json`
- `seo-workspace/data/publish-execution-receipt.json`
- `seo-workspace/reports/YYYY-MM-DD-publish-execution-receipt.md`

Use the map to decide what each page can produce, whether it needs latest-source research, what image slots are allowed, and what publishing gate applies.

Use `content-studio-queue` after `content-system` when the owner wants the skill to cover all website publishing content:

- deduplicates bilingual `/en` and `/zh` page pairs into one production queue item
- assigns a recommended `content-studio` pipeline and copyable command for each page
- adds a `service-pattern-package` command for service pages
- records rich media slots, latest research policy, and owner-input requirements per page
- writes queue JSON/CSV/report only; it does not generate every page body at once, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy

Use `content-studio-next` for fixed-time or manual queue consumption:

- selects one unprocessed queue item from `content-studio-queue`
- runs `content-studio` for that single target page
- can build the complete no-write owner-review package with `--owner-review-package` or schedule `owner_review_package: true`, including owner review dashboard, media review gallery output, owner-fillable URL draft, and media status report
- appends `content-studio-history.csv` so future runs avoid immediate repeats
- writes `content-studio-next-run.json` and an owner-facing report
- does not call CMS/admin helpers, upload media, write source pages, regenerate SEO assets, publish, run npm, or deploy

Use `content-studio-orchestrator` as the fixed-time guarded queue entrypoint:

- reads the automation schedule and requires `executor: content-studio-next`
- checks enabled state, local schedule window, same-day duplicate completion, and no-publish gates
- runs `content-studio-next` only when gates pass, including the owner-review package handoff when `owner_review_package: true`
- writes `content-studio-orchestration.json`, `content-studio-orchestration-log.csv`, and an owner-facing report
- does not install schedules, call CMS/admin helpers, upload media, write source pages, regenerate SEO assets, publish, run npm, or deploy

Use `content-studio-postrun` after a queued content run:

- reads orchestration, next-run, queue, and history artifacts
- reports the latest processed page, content status, next queue item, blockers, and owner review actions
- writes `content-studio-postrun-summary.json` and an owner-facing report
- does not run automation, call CMS/admin helpers, upload media, write source pages, regenerate SEO assets, publish, run npm, or deploy

Use `content-studio` when the owner asks to create or prepare a complete content package for one specific page:

- wraps the safe daily orchestrator with an explicit target URL
- supports `brief`, `rich-content`, and `publish-prep` pipelines
- produces current research candidates, rich content, structured blocks, local editor, editor-applied CMS payload, media/concept asset plans, service-pattern package when available, and publish-prep gates
- writes `content-studio-run.json` plus an owner-facing report so a single-page production run is easy to review
- does not log in, call CMS/admin helpers, upload media, write source pages, regenerate SEO assets, publish, run npm, or deploy

Use `research-search` before drafting source-dependent current content:

- generates target-page search queries from keyword, service, location, and page type
- can fetch Google News RSS candidates, trusted RSS/Atom feed candidates from `research-search-feeds.example.yml`, or both with `--provider hybrid-rss`, without storing search API credentials in the repository
- writes candidate JSON/CSV in the same shape used by `research-intake`
- does not write `research-source-log.csv`, draft page copy, call CMS/admin helpers, upload media, publish, or deploy
- search results are only candidates; use `research-intake` or `latest-research --source` before citing or using them in a content package

Use `content-calendar` when planning more than one unattended daily run:

- reads opportunity scoring plus the full-site content system map
- groups `/en` and `/zh` as one bilingual task
- penalizes recently selected URLs from daily automation or scheduled postrun history
- gives `daily-automation` a rotating default target when no explicit `--target-url` is passed
- outputs a ranked multi-day owner-review calendar only
- does not draft copy, call CMS/admin helpers, upload media, write source pages, regenerate SEO assets, publish, or deploy

For scheduled daily operation, first use `automation-schedule` to generate the fixed-time plan and safety validation:

- writes owner-review schedule config and plan artifacts
- creates cron and launchd examples without installing them
- supports `executor: daily-automation` for opportunity/calendar selection and `executor: content-studio-next` for consuming one queued page per run; set `owner_review_package: true` to make each queued run generate the owner review dashboard, publish-candidate, publish-prep, approval-packet, media review gallery, media URL template, owner-fillable URL draft, and media status report, with generated cron/launchd routed through `content-studio-orchestrator`
- writes scheduled publish authorization evidence without installing or running anything
- blocks scheduled publishing unless exact owner authorization IDs, bilingual allowed target URLs, QA, media/storage, backup, changelog, rollback, expiry, live confirmation when applicable, and one-task-per-run limits are present

Use `scheduled-publish-authorization` when the owner wants fixed-time publish-prep to become eligible for future execution:

- validates `seo-workspace/config/scheduled-publish-authorization.yml`
- requires `max_pages_per_run: 1` and bilingual `/en` plus `/zh` URL scope unless the owner explicitly authorizes otherwise
- requires `website_root` evidence so later publish implementation can use the real website adapter
- writes blocked/ready JSON and report only
- does not install cron/launchd, run daily automation, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy

Use `scheduled-publish-runner` at each scheduled window before any recurring publish-prep automation:

- consumes the same authorization profile and checks whether the current local weekday/time is inside the authorized window
- selects one allowed target URL, verifies the bilingual paired URL, and blocks target URLs outside the authorization scope
- blocks duplicate ready run requests for the same local date and target URL unless an operator explicitly bypasses it
- writes `scheduled-publish-run-request.json`, `scheduled-publish-run-log.csv`, and a report only
- does not run daily automation, install schedules, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy

Use `scheduled-publish-orchestrator` as the actual safe scheduled entrypoint after the run request layer:

- first runs the same runner gate and blocks if the profile, time window, target URL, paired URL, or duplicate-run checks fail
- when the run request is ready, runs only `daily-automation --pipeline publish-prep` to generate local content/prep artifacts
- records the daily automation status, steps, artifacts, warnings, and handoff blockers in `scheduled-publish-orchestration.json`
- does not call CMS/admin helpers, upload media, write live/source pages, publish, regenerate SEO assets, or deploy

Use `scheduled-publish-postrun` after every scheduled run or blocked run:

- reads `scheduled-publish-orchestration.json`, `scheduled-publish-run-request.json`, `daily-automation-run.json`, `publish-readiness.json`, `publish-implementation-package.json`, `publish-operator-command.json`, and `publish-execution-receipt.json`
- categorizes blockers into authorization, schedule window, owner approval, QA, media, source research, implementation, and other
- writes a machine-readable summary and owner-facing next-action report
- does not fetch research, run daily automation, call CMS/admin helpers, upload media, publish, regenerate SEO assets, or deploy

Then use `daily-automation` as the recurring orchestrator:

- `--pipeline brief`: select one highest-value task and write a daily owner-review draft/report.
- `--pipeline rich-content`: run candidate source discovery, optionally auto-intake high-trust sources when remote fetching is enabled, then extend the selected task into rich text, local rich editor artifacts, editor-applied CMS payload draft, media plan, generated concept assets, and media upload queue.
- `--pipeline publish-prep`: run candidate source discovery, optionally auto-intake high-trust sources when remote fetching is enabled, then extend the selected task into full dry-run publish handoff artifacts, including editor-applied CMS payload draft, queue, plan, executor request, media upload request, and readiness report.
- `--pipeline publish-prep` also writes scheduled publish authorization status; missing authorization is a handoff blocker, not permission to publish.

All pipelines remain draft/prep-only. They do not log in to CMS/admin, upload media, write Supabase, edit source pages, publish, regenerate live SEO assets, or deploy.

Use `--skip-research-discovery` only when the run must rely on existing `research-source-log.csv` rows. Use `--no-fetch-research-remote` for deterministic local tests or offline scheduled dry-runs. Discovery candidates are selection inputs only; `research-intake` can record high-trust candidates into `research-source-log.csv` only after fetching them through `latest-research`, and it still treats them as general external guidance rather than FLASH CAST business facts.

For latest-source work, use `research-discovery` or Codex/web search first, then record selected URLs before drafting or refreshing page copy:

```bash
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-discovery \
  --target-url https://flashcast.com.my/en/services/kitchen

python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-intake \
  --target-url https://flashcast.com.my/en/services/kitchen
```

`research-intake` is allowed to update only local research evidence files: `research-source-log.csv`, `latest-research-sources.csv`, `research-intake.json`, and an owner-facing report. It must not publish, call CMS, edit website source, upload media, or present external guidance as company proof.

`research-discovery` reads trusted source seeds, optionally fetches those pages, scores candidate URLs, and writes a candidate selection handoff. It does not write `research-source-log.csv`; candidates become source-log rows only after `research-intake` accepts and fetches trusted candidates, or after an explicit `latest-research --source` run.

```bash
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py latest-research \
  --target-url https://flashcast.com.my/en/services/kitchen \
  --query "kitchen renovation malaysia planning guidance" \
  --source "official|https://example.com/source|Use only for general guidance|general guidance only; not a FLASH CAST business claim|kitchen renovation malaysia planning guidance"
```

The `latest-research --source` format is:

`type|url|usage note|claim boundary|query`

`latest-research` does not invent sources or search results. Query-only runs are intentionally blocked until Codex/web search or owner-provided URLs supply source URLs.

After `latest-research` writes `research-source-log.csv`, `rich-content` automatically attaches matching target-page source rows unless `--no-use-research-log` is passed. `publish-plan` also includes `latest_research.valid_source_count` and source summaries in `publish-execution-plan.json`; if a draft still contains `NEEDS LIVE SEARCH` and no matching source log exists, the plan remains blocked before publish.

For article packages that already have selected sources, pass those sources into the package:

```bash
python3 .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py rich-content \
  --target-url https://flashcast.com.my/en/blog/kitchen-cabinet-price-malaysia \
  --source "manufacturer|Cabinet hardware guide|https://example.com/source|Publisher|2026-06-10|Use only for general material guidance"
```

The `--source` format is:

`type|title|url|publisher|published_or_accessed_date|usage note`

If no sources are provided for an article page, the package must mark `NEEDS LIVE SEARCH` before publishing.

`rich-blocks` converts the approved Markdown content package into:

- bilingual structured blocks for `/zh` and `/en`
- HTML body strings for CMS fields such as `content_zh` and `content_en`
- image/media placeholders with bilingual alt, captions, concept labels, and generation prompts
- CMS payload draft with `status: draft`
- an HTML preview for owner review

It does not generate or upload images, write CMS records, publish pages, or deploy.

`rich-editor` converts the structured blocks and media/concept metadata into an editable local review package:

- draggable bilingual block order for Chinese and English page copy
- contenteditable headings, body text, CTA labels/URLs, image alt text, and captions
- generated concept asset preview when local SVG concept files exist
- machine-readable `rich-content-editor-manifest.json`
- browser-side JSON export for a later approved execution step

It is not a CMS editor and it does not save changes to the website. Treat exported edits as owner-review input only until a specific draft is approved and execution is explicitly requested.

`rich-editor-apply` consumes a browser-exported `rich-editor` JSON file and creates a new CMS payload draft:

- rebuilds `content_zh` and `content_en` from edited block order and edited fields
- applies edited headings, body text, CTA labels/URLs, image alt text, and captions
- preserves media placeholders such as `NEEDS_MEDIA_UPLOAD:*` until URL mapping is complete
- writes `rich-content-cms-payload.editor-applied.json` without overwriting the base payload

It still does not write CMS/source, upload media, publish, or approve the content. Later dry-run publishing uses the editor-applied payload by default when no media-ready payload or explicit `--cms-payload-path` is present.

`service-pattern-package` builds the complete owner-review package for service-pattern pages:

- accepts `--target-url`, `--service-slug`, or `--all`
- creates the bilingual service brief, local rich text/image editor, CMS payload draft, media asset plan, concept SVG assets, URL map example, prompt pack, and reports
- is draft-only and does not search external webpages, call image APIs, upload media, write CMS/source, publish, regenerate SEO assets, or deploy

`media-assets` converts media placeholders into:

- generated design/rendering asset records
- image generation prompts and negative prompts
- media library field drafts such as `file_url`, `file_path`, `file_name`, `mime_type`, `usage_type`, `folder`, `alt_zh`, `alt_en`
- URL map example for owner-selected or uploaded assets
- media-ready CMS payload only when every required filename has a URL

When an editor-applied payload exists and no explicit `--cms-payload-path` is provided, media-ready payload generation uses the editor-applied payload so reviewed rich-text edits are preserved. It does not generate images, upload files, call media APIs, or claim generated visuals are real project photos.

`concept-assets` converts `media-asset-plan.json` into local SVG planning visuals:

- one generated SVG file per media placeholder under `seo-workspace/media/generated/`
- a `concept-asset-manifest.json` mapping original placeholders to generated SVG files
- a concept-assets report for owner review
- embedded labels stating the asset is a design/rendering concept, not a real project photo

It does not upload files, call CMS, call Supabase, publish, or claim the generated visual is real proof.

`media-upload-plan` converts local concept files into an owner-review upload handoff:

- upload queue rows with local file path, target bucket, object path, MIME type, alt, usage type, and execution gate
- `media_assets` record drafts matching the website media library fields
- references to the website's approved media helpers such as `uploadAdminMediaObject` and `createAdminMediaAsset`

It does not upload files, call Supabase, create media records, or make media public. A later real media publish must go through the website admin media library or existing admin media helper, with owner approval, explicit upload instruction, QA, and rollback notes.

`media-upload-executor` turns the upload queue into a gated execution request:

- blocks unless owner approval, explicit execution, QA, and storage readiness flags are present
- records planned `uploadAdminMediaObject` and `createAdminMediaAsset` operations
- consumes an owner-confirmed uploaded URL map only when `--uploaded-confirmed` is present
- writes `media-url-map.json` and `rich-content-cms-payload.media-ready.json` from confirmed uploaded URLs

When an editor-applied payload exists and no explicit `--cms-payload-path` is provided, the media-ready payload is generated from the editor-applied payload. It still does not upload files, call Supabase, create media records, or publish by itself.

`media-url-map` scans generated/selected local files and creates:

- `media-file-manifest.csv` showing each expected file, local path, existence, URL, usage type, and alt fields
- `media-url-map.json` only when every expected file exists and `--public-base-url` is provided
- media-ready CMS payload through `media-assets --url-map-path` once the URL map is complete

It can map original `.webp` placeholders to generated `.svg` concept assets when the SVG files exist locally. It does not upload files, validate CDN availability, or make media public.

`publish-queue` creates a field map from rich content packages to the website's known publishing paths:

- service pages -> `services` through `saveAdminService`
- articles -> `blog_posts` through `saveAdminBlogPost`
- project/case pages -> `projects` plus `project_images`
- page hubs/conversion pages -> `site_pages`
- true section-rich pages -> `cms_pages` + `cms_sections`
- media files -> `media_assets`

It does not upload media, call Supabase, publish records, regenerate SEO manifests, or deploy. Treat `approved-publish-queue.csv` as an owner-review queue until the owner explicitly approves a row and asks to execute it.

`content-studio-publish-candidate` is the safe bridge from the latest Content Studio/Postrun package into that owner-review queue. It rebuilds the publish queue, selects the matching rich-content package row, and writes `content-studio-publish-candidate.json` plus a Chinese owner-facing report. It is not an approval and not a publish action: no CMS/admin helper calls, no source writes, no media upload, no SEO asset regeneration, and no deploy.

`content-studio-publish-prep` consumes the candidate and runs the local handoff chain for that exact page: website adapter, publish plan, CMS dry-run request, readiness, bundle, approved executor simulation, implementation package, operator command package, and execution receipt verifier. It writes `content-studio-publish-prep.json` plus a Chinese owner-facing summary. It is still no-live-write and does not call CMS/admin helpers, modify source, upload media, publish, regenerate SEO assets, or deploy.

`content-studio-approval-packet` turns the latest publish-prep evidence into an owner action checklist. It groups blockers into owner approval, explicit execution scope, QA, media URL map, storage readiness, and future execution receipt verification, and writes `content-studio-approval-packet.json` plus a Chinese owner-facing report. It is report-only and does not approve or execute anything.

`content-studio-media-url-template` converts the latest media upload plan into `uploaded-url-map.template.json`, using the `files` shape consumed by `media-upload-executor`. It keeps placeholder names, object paths, alt text, and claim boundaries so uploaded public URLs can be mapped back to rich-text image placeholders. It does not upload media, call CMS, write source, publish, or deploy.

`content-studio-media-review-package` converts generated concept media and the upload plan into a local owner-review HTML gallery plus JSON summary. It shows each generated design/rendering concept image, local source path, upload object path, bilingual alt text, concept label, and claim boundary before any public URL is filled. It does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-uploaded-url-map-draft` converts `uploaded-url-map.template.json` into an owner-fillable `uploaded-url-map.json` draft and validates empty URLs, placeholder URLs, public HTTPS requirements, duplicate placeholders, and owner confirmation flags. It is the safe no-write bridge between owner/media upload work and `content-studio-media-ready-handoff`; it does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-media-ready-handoff` is the owner-approved post-review bridge after `uploaded-url-map.json` has been filled with confirmed public HTTPS URLs. It runs `media-upload-executor`, refreshes `content-studio-publish-prep`, and regenerates `content-studio-approval-packet`, producing `media-url-map.json` and `rich-content-cms-payload.media-ready.json` evidence when all media URL gates pass. It does not upload media, call CMS/admin helpers, write source, publish, regenerate SEO assets, or deploy.

`content-studio-owner-review-package` is the one-command no-write owner handoff after a page has been produced. It runs the candidate, publish-prep, approval-packet, media review gallery, media-url-template, owner-fillable uploaded URL map draft, and media status steps, then writes `content-studio-owner-review-package.json`, an owner review dashboard HTML, and a Chinese index report. It is the recommended artifact bundle for owner review before any later approved execution.

`website-publish-adapter` performs read-only discovery against the real website source root. It records package manager, npm scripts, admin/media helper references, SEO generation scripts, generated SEO assets, `.env.example` key names, and publishing rule docs into `website-publish-adapter.json`. It does not run npm, call CMS/admin helpers, write source, upload media, publish, regenerate assets, or deploy.

`scheduled-publish-authorization` is the fixed-time publish gate. It validates `scheduled-publish-authorization.yml` for exact owner authorization IDs, bilingual URL scope, one-page-per-run limits, unexpired scope, QA/media/storage/backup/changelog/rollback gates, and live confirmation when applicable. It writes `scheduled-publish-authorization.json` and a report only. It does not install schedules, run the daily orchestrator, call CMS/admin helpers, upload media, publish, regenerate assets, or deploy.

`scheduled-publish-runner` is the per-window run gate. It checks the authorization profile, current local weekday/time, allowed target URL, bilingual pair, and duplicate ready requests before creating `scheduled-publish-run-request.json`. It is still no-execute: it does not run `daily-automation`, call CMS/admin helpers, upload media, publish, regenerate assets, or deploy.

`scheduled-publish-orchestrator` is the safe scheduled entrypoint that bridges a ready run request to local publish-prep artifact generation. It can run `daily-automation --pipeline publish-prep`, but that pipeline remains no-live-write and still ends at owner-review handoff blockers until explicit publishing approval and later gates are satisfied.

`scheduled-publish-postrun` is the after-action report for fixed-time automation. It consolidates scheduler, publish-prep, readiness, implementation, operator-command, and execution-receipt blockers into an owner-facing next-action list. It is read-only against local artifacts and never executes another workflow.

`publish-plan` consumes one queue row after owner approval and creates a gated execution plan. Missing approval, missing explicit execution, missing QA, unresolved `NEEDS OWNER INPUT`, missing latest-source verification, or missing live preconditions keep the plan in `blocked_before_publish`. A ready plan is still not a publish action; it is the final machine-readable handoff before a later CMS/source executor.

`publish-executor` consumes the ready plan and CMS payload draft to create a dry-run CMS/source write request. Payload selection order is explicit `--cms-payload-path`, then `rich-content-cms-payload.media-ready.json`, then `rich-content-cms-payload.editor-applied.json`, then base `rich-content-cms-payload.json`. It blocks if the plan is not ready, approval/explicit execution/QA flags are missing, editor-applied QA is not ready for owner review, editor-applied safety metadata is missing, or media placeholders such as `NEEDS_MEDIA_UPLOAD:*` remain in the selected payload. Passing `--media-ready` does not bypass placeholder checks. It does not import website code, call CMS, write Supabase, upload media, publish pages, regenerate SEO assets, or deploy.

`publish-readiness` is the final machine-readable handoff gate before any approved publishing implementation. It checks:

- `publish-execution-plan.json` is ready
- `cms-write-request.json` is ready
- `media-upload-execution-request.json` has produced confirmed media-ready payload output
- `media-url-map.json` exists
- `rich-content-cms-payload.media-ready.json` exists
- editor-applied payload evidence and editor apply QA status are surfaced when `rich-content-cms-payload.editor-applied.json` exists
- matching `research-source-log.csv` rows exist for the target page pair
- dry-run safety flags still show no publish, CMS write, or media upload executed

It writes `publish-readiness.json` and `YYYY-MM-DD-publish-readiness-report.md`. It does not upload media, call CMS, write source files, regenerate SEO assets, publish, or deploy. If the status is not `ready_for_owner_approved_publish_handoff`, do not proceed to implementation.

`publish-bundle` is the final sealed input for a later approved executor. It consumes `publish-readiness.json` and `cms-write-request.json`, blocks unless both are ready and media placeholders are gone, then writes `publish-execution-bundle.json` plus an owner-facing bundle report. It still does not call CMS, write source, upload media, publish, or deploy.

`publish-approved-executor` is the final local simulation gate before any real executor implementation. It reads `publish-execution-bundle.json`, requires owner approval, explicit execution, QA pass, media URL evidence, media-ready payload evidence, clean safety flags, and no `NEEDS_MEDIA_UPLOAD:*` placeholders. Non-dry-run modes require existing backup, changelog, and rollback files; `live` also requires `--confirm-live`. It writes `publish-approved-execution-record.json` and a dry-run report only. It does not call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.

`publish-approved-execution-input` converts a ready `publish-operator-command.json`, `publish-admin-helper-call.json`, and `website-publish-adapter.json` into future execution inputs: `publish-approved-execution-input.json`, a guarded `seo-workspace/tools/publish-approved-execution-runner.mjs` template, and `publish-execution-result.template.json`. The generated runner refuses to proceed unless an explicit environment confirmation is set. The generator itself does not run the runner, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.

`publish-implementation-package` converts a ready `publish-approved-execution-record.json` into the local package a future real executor would consume. It reads `website-publish-adapter.json` by default, then writes `publish-implementation-package.json`, `publish-admin-helper-call.json`, and a runbook report containing the admin helper call, real website backup/SEO-generation/QA/build commands, execution order, rollback plan, SEO post-write tasks, and helper/source evidence. It is still no-write: it does not run npm, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.

`publish-operator-package` converts a ready implementation package and `publish-admin-helper-call.json` into a deterministic no-write command manifest for a future operator or executor. It writes `publish-operator-command.json` and an owner-facing report with backup, CMS helper call, SEO generation, QA, build, rollback, required confirmations, and dry-run command preview. It requires a ready website adapter and clean safety flags. It is still no-write: it does not run npm, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.

`publish-operator-ready-handoff` is the one-command no-write refresh after media-ready evidence exists. It reruns website adapter, publish-executor, readiness, bundle, approved executor simulation, implementation package, operator package, and guarded execution input generation, then writes `publish-operator-ready-handoff.json` and a Chinese summary. It is the recommended final local handoff before asking the owner for a specific execution instruction. It does not run npm, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.

`publish-execution-receipt` verifies the result of a future real approved execution. It reads `publish-operator-command.json` plus `publish-execution-result.json`, then checks the target URL pair, helper function, CMS record ID, backup evidence, CMS write evidence, SEO regeneration, QA, rollback evidence, command results, and live URL verification when the result says `publish_status=published`. It writes `publish-execution-receipt.json`, an example result JSON when missing, and an owner-facing report. It is still no-write: it does not run commands, call CMS/admin helpers, write source, upload media, publish, regenerate SEO assets, or deploy.
