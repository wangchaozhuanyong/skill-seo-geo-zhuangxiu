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
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py competitor-weekly-monitor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-seo-verification
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py weekly-growth-control
```

`growth-ops-audit` may be used to run the broader safe operating report set.

`weekly-growth-control` also refreshes `post-publish-feedback` and writes `post-publish-opportunity-feedback.csv`. The next `opportunities` or `daily-automation` scoring run reads that feedback signal so 7/30-day post-publish review, index/GSC gaps, and owner-confirmed lead quality can influence daily prioritization.

## Data Rules

- Use owner-confirmed exports or platform views for private performance data.
- Do not store passwords, cookies, tokens, billing details, OAuth files, or private credentials.
- If a data source is missing, mark it `missing`, `empty`, or `needs_owner_input`; do not infer performance.
- Do not describe page visits as leads unless they map to WhatsApp, phone, form submit, or CRM outcomes.
- Do not fabricate revenue, lead quality, project value, customer feedback, reviews, or conversion quality.

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
