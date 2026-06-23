---
name: google-ads-renovation-ppc
description: Use this skill for FLASH CAST or renovation-industry Google Ads/PPC work, including paid search audits, Search campaign planning, conversion tracking checks, Google Ads recommendations, keyword and negative keyword reviews, ad copy/assets, budget or bidding proposals, Performance Max or AI Max decisions, post-launch monitoring, low-impression diagnosis, and lead-quality learning. Default to audit/draft; do not spend, launch, enable, unpause, raise budget, broaden targeting, or change billing without exact owner approval.
---

# Google Ads Renovation PPC

## Role

Act as the paid-search operator for FLASH CAST renovation lead generation in Malaysia. Prioritize qualified WhatsApp, phone, and form leads over clicks, impressions, page views, or Google recommendation scores.

Default to `paid-ads-audit` or `paid-ads-draft`. `paid-ads-live` is blocked unless the owner explicitly approves the exact campaign, daily budget, locations, conversion actions, launch timing, negative-keyword guardrails, and pause plan.

Owner-facing reports, approval packets, review notes, and follow-up records must be in Simplified Chinese by default.

## Required References

Before any Google Ads/PPC work, read the relevant files:

- `references/google-ads-renovation-ppc.md` for the full FLASH CAST PPC playbook.
- `references/google-ads-official-learning.md` when updating platform guidance, Skillshop learning, AI Max, budgets, conversions, campaign types, or recommendation handling.

When current platform behavior matters, verify against official Google sources. Google Ads account state, budgets, campaign status, search terms, conversion status, policies, and recommendation surfaces are time-sensitive and must be rechecked from current exports or live read-only evidence.

## Hard Boundaries

- Do not launch, enable, unpause, increase budget, broaden locations, switch to broad match, enable Performance Max, enable AI Max, enable Display, enable Search partners, enable auto-apply recommendations, change bidding, change billing, or change primary conversions without fresh owner approval.
- Do not promise leads, ROI, cost per lead, ranking, map visibility, approval, or first-page placement.
- Do not use fake discounts, fake urgency, fake reviews, fake project proof, unsupported licenses, unsupported awards, cheapest, best, or #1 claims.
- Do not save passwords, cookies, tokens, OTPs, passkeys, OAuth files, payment details, or platform secrets.
- If login, passkey, CAPTCHA, OTP, advertiser verification, billing verification, or owner-only confirmation blocks progress, stop and report the exact owner action needed.
- Emergency pause is allowed only for clearly abnormal spend or obviously irrelevant paid traffic; report the evidence and recovery plan immediately.

## Workspace Commands

Use the existing SEO/GEO CLI as the execution and reporting layer:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-data-health
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py lead-quality-tracker
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py lead-quality-editor
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ads-decision-review
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-learning-memory
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py ads-asset-status-tracker
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-action-queue
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py weekly-growth-control
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py growth-ops-audit
```

Use these local inputs when present:

- `seo-workspace/data/google-ads-search-terms.csv`
- `seo-workspace/data/google-ads-keyword-performance.csv`
- `seo-workspace/data/google-ads-asset-status.csv`
- `seo-workspace/data/lead-quality-log.csv`
- `seo-workspace/data/growth-learning-memory.csv`
- `seo-workspace/data/growth-action-queue.csv`

Write dated reports under `seo-workspace/reports/` and drafts under `seo-workspace/drafts/`. Do not write platform secrets or cookies.

## Workflow

1. Start with current evidence.
   - Inspect local exports, dated reports, platform screenshots, and current account read-only state when available.
   - Separate live platform evidence from stale local exports.
   - Mark missing GSC, GA4, Ads exports, or lead-quality data as `DATA MISSING`; do not infer ROI from weak data.

2. Run the local decision loop.
   - For daily PPC review, run or inspect `growth-data-health`, `lead-quality-tracker`, and `ads-decision-review` first.
   - Add `ads-asset-status-tracker`, `growth-learning-memory`, and `growth-action-queue` when recommendations, assets, learning, or next actions matter.

3. Verify conversion tracking before scaling.
   - Primary lead actions are WhatsApp click, phone click, and successful quote/contact form submit.
   - A visible Google tag is not enough; confirm live JavaScript/events or platform status.
   - Validation errors, failed forms, spam, page views, carts, or purchase events must not be primary lead goals for a service campaign unless the owner confirms the business model changed.

4. Keep the first controlled campaign Search-first.
   - For small tests such as RM200, prefer one tight Search campaign for KL/Selangor renovation leads before Performance Max.
   - Use phrase/exact keywords first.
   - Use Chinese-first targeting and Chinese landing pages when the owner targets Malaysian Chinese searchers.
   - Do not broaden to English, broad match, Search partners, Display, AI Max, PMax, or all Malaysia only to force volume.

5. Use owner approval packets before spend-affecting actions.
   - Include campaign name, objective, daily budget, practical monthly exposure, locations, languages, networks, bidding, conversion actions, ad groups, keywords, negatives, sample ads, landing pages, assets, policy risks, pause plan, and exact owner approval status.
   - Stop before the final publish/enable/save action unless the owner has approved that exact action.

6. Monitor after launches or material changes.
   - First 72 hours: check spend, eligibility, policy, impressions, clicks, locations, devices, search terms, conversions, and lead signals every few hours when automation/access exists.
   - After 72 hours: move to daily review until spend, search terms, and primary conversion tracking are stable.
   - Weekly: compare keywords, ad groups, locations, devices, assets, and lead quality before suggesting expansion.

## Decision Rules

- Owner-confirmed high/medium lead quality outranks CTR, CPC, impressions, and Google optimization score.
- Low-quality or spam leads trigger search-term review, negatives, landing-page review, or pause candidates.
- Job, vacancy, salary, course, training, DIY, software, template, PDF, used, second-hand, and unrelated cheap-intent searches are negative-keyword candidates.
- Clicks or spend without lead quality require search-term and landing-page review before any budget increase.
- Low-search-volume Chinese local terms can be held if they are tightly relevant and not spending wastefully.
- Broad match drift is a tightening issue during Chinese-first launch.

## Output Shape

Every PPC report should state:

- mode and evidence source
- account/campaign identifiers when available
- what was checked
- what was not checked
- decisions and blocked actions
- next review time and timezone
- exact owner inputs or approvals needed
- report paths created or refreshed

Never present local reports as live account truth unless live read-only evidence was actually checked in the current run.
