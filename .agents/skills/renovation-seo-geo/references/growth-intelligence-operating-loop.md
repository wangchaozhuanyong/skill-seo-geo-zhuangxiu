# Growth Intelligence Operating Loop

Use this reference when upgrading the skill from planning/reporting into a data-led SEO/GEO/PPC growth operator.

## Goal

The operating loop must connect verified data to decisions:

1. Search visibility data: GSC pages and queries.
2. Paid search data: Google Ads search terms, keyword performance, spend, clicks, and conversions.
3. Lead quality data: real WhatsApp, phone, form, or CRM outcomes confirmed by the owner.
4. Local trust data: GBP, Bing Places, NAP, photos, reviews, service areas, and citation consistency.
5. Competitor data: fixed public competitor set and weekly page/local/search gap checks.

Clicks, impressions, and AI-generated ideas are not enough to judge ROI. Real lead quality is the highest-priority decision input.

## Required Commands

Run these for the local growth loop:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-data-health
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py lead-quality-tracker
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ads-decision-review
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-learning-memory
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py competitor-weekly-monitor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-seo-verification
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py weekly-growth-control
```

`growth-ops-audit` may be used to run the broader safe operating report set.

`weekly-growth-control` also refreshes `post-publish-feedback` and writes `post-publish-opportunity-feedback.csv`. The next `opportunities` or `daily-automation` scoring run reads that feedback signal so 7/30-day post-publish review, index/GSC gaps, and owner-confirmed lead quality can influence daily prioritization.

`growth-learning-memory` is the local learning layer. It converts Google Ads decisions, owner-confirmed lead quality, and post-publish feedback into `growth-learning-memory.csv` and `growth-learning-memory.json`. Future reviews should inspect this memory before recommending keyword expansion, negative keywords, landing-page work, content priorities, or escalation to owner approval.

## Data Rules

- Use owner-confirmed exports or platform views for private performance data.
- Do not store passwords, cookies, tokens, billing details, OAuth files, or private credentials.
- If a data source is missing, mark it `missing`, `empty`, or `needs_owner_input`; do not infer performance.
- Do not describe page visits as leads unless they map to WhatsApp, phone, form submit, or CRM outcomes.
- Do not fabricate revenue, lead quality, project value, customer feedback, reviews, or conversion quality.

## Learning Memory Rules

The skill should not only obey static rules; it should keep a local evidence memory from repeated observations.

Memory types:

- `qualified_lead_signal`: a keyword, search term, page, channel, or service produced owner-confirmed high/medium quality or won leads.
- `poor_lead_signal`: a term or source produced low-quality, spam, or irrelevant leads.
- `avoid_search_intent`: a search term matches job/course/DIY/software/template/second-hand or similar waste patterns.
- `winner_candidate`: a term or page deserves closer alignment or owner-reviewed scaling because real quality signals exist.
- `waste_or_quality_risk`: spend/clicks exist but lead quality is missing or poor.
- `observe_low_volume_chinese_term`: a tightly relevant Chinese local term has low volume but is not wasting spend.
- `organic_page_feedback`: a page's 7/30-day feedback should affect future SEO/GEO prioritization.
- `data_gap`: the skill lacks enough data to learn or optimize.

Allowed action levels:

- `auto_report_only`: write reports and ask for data; do not optimize.
- `auto_observe_only`: continue monitoring; do not change account/source.
- `auto_prioritize_draft_only`: use evidence to rank draft SEO/GEO work only.
- `auto_suggest_only`: propose negatives, pauses, fixes, or page improvements, but do not execute without approval when account/source changes are involved.
- `owner_approval_required`: ask before account, budget, targeting, campaign, conversion, publish, or source changes.
- `owner_approval_required_for_scaling`: ask before budget increases, bidding changes, broader targeting, new campaigns, or more aggressive expansion.

The memory is evidence input, not permission to spend or publish. Fresh owner approval is still required for budget, bidding, targeting, conversion goals, campaign status, publishing, platform submissions, and billing.

## Paid Ads Decision Rules

- Keep or isolate keywords only when search terms are relevant and lead quality is owner-confirmed.
- Add negatives or pause candidates when search terms show job, course, DIY, software, template, second-hand, or other low-intent patterns.
- Review landing pages when clicks exist but no qualified lead is confirmed.
- Hold tightly relevant low-volume Chinese local terms when they are not wasting spend.
- Treat broad match drift as a tightening issue during Chinese-first launch.
- Do not increase budget, broaden location targeting, enable PMax/AI Max/Display/Search partners, change bidding, switch to broad match, or change billing without fresh owner approval.

## Local SEO Verification

Track these as truth-verification assets:

- Google Business Profile
- Bing Places
- Google Ads location asset
- website NAP and schema
- directory/citation profiles
- real photos and real reviews

Apple Maps remains out of scope unless the owner explicitly reopens it.

## Competitor Monitoring

Use a fixed competitor list. Each weekly pass should check:

- new or changed service pages
- titles, meta descriptions, FAQ, schema, and internal links
- local SEO and maps signals
- real proof, photos, reviews, and project evidence
- Chinese search coverage and local Chinese hybrid terms

Do not copy competitor content. Competitor findings become owner-review tasks, not direct claims or ad copy.

## Weekly Output

The weekly report should produce a short action queue:

- what data is ready or missing
- what post-publish feedback changed in the daily opportunity score input
- which paid terms should be kept, reviewed, tightened, or paused
- which SEO page or local asset has the highest value next
- which competitor gap is worth acting on
- what owner input blocks better decisions

Prefer 1-3 high-value actions per week over random articles or broad expansion.
