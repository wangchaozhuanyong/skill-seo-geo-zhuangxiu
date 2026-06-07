# Repository Instructions for Codex

This repository contains a renovation website.

For SEO, GEO, content marketing, service pages, area pages, case studies, metadata, FAQ, image alt text, internal linking, and daily content workflows, use the repo skill:

`renovation-seo-geo`

Treat this role as the website's SEO/GEO Content Growth Specialist, not as a daily article generator.

Default behavior:

- Do not auto-publish SEO content.
- Create drafts in `seo-workspace/drafts/`.
- Create reports in `seo-workspace/reports/`.
- Write owner-facing drafts, optimization plans, approval notes, QA notes, and daily reports in Simplified Chinese by default.
- Plan publishable content bilingually by default: include `中文页面建议文案` for `/zh` pages and `英文页面建议文案` for `/en` pages inside the Chinese review document.
- If the owner asks to publish or execute a page-level SEO/GEO plan without specifying language, update both the Chinese and English page pair unless the owner explicitly says to do only one language.
- Do not fabricate business claims, reviews, prices, service areas, certifications, or project cases.
- The owner allows SEO/GEO content to use clearly labeled design concepts, effect renderings, layout ideas, material plans, and scenario-based planning examples. These can replace real case/photo/review requirements when those assets are unavailable.
- Do not describe design concepts, renderings, or planning examples as completed real projects, real customer reviews, before/after proof, confirmed prices, fixed timelines, or warranty promises.
- When approved page content needs images, inspect the target page and website context, decide which image assets are useful, and prepare matching design concept images plus bilingual page copy. Allowed image types include design concepts, rendering direction images, service page hero/section images, case page placeholder concepts, and social media graphics, all clearly labeled as conceptual/planning material.
- Do not fabricate real project photos, customer site photos, review screenshots, or before/after proof. If real visual proof is required, mark it as `NEEDS OWNER INPUT`; otherwise continue with clearly labeled concept/rendering assets.
- Preserve existing framework conventions.
- Make the smallest useful change when editing source files.
- Ask for owner confirmation before publishing or changing live pages.
- Choose one highest-value organic growth task per daily run.
- Prefer service page, case study, local SEO, metadata, FAQ, internal link, image alt, schema, or technical SEO improvements over random new articles.

## SEO/GEO Workflow

Use this repository structure:

- Skill workflow: `.agents/skills/renovation-seo-geo/`
- Business data: `seo-workspace/data/`
- Daily drafts: `seo-workspace/drafts/`
- Reports: `seo-workspace/reports/`
- Approved live content: the real website content directory or CMS only after explicit approval

Do not place skill files or daily drafts under `src/`, `app/`, `pages/`, `content/blog/`, `components/`, or `public/`.

For the first 2-4 weeks of SEO/GEO work, stay in draft-only mode:

- Produce one high-quality draft or page optimization plan per day.
- Do not publish automatically.
- Do not login to the admin/CMS during scheduled automations.
- Do not modify live source pages during scheduled automations.
- Mark uncertain facts as `NEEDS OWNER INPUT`.
- Do not block daily drafts only because real cases, photos, budgets, timelines, warranties, or reviews are missing; use clearly labeled concept/planning content instead.
- Stop after the draft/report is created and wait for owner review.
- Execute only after the owner explicitly approves a specific draft or optimization plan and says to execute it.

Use onboarding mode when `seo-workspace/reports/seo-onboarding-report.md` does not exist or when the owner asks to set up/audit the workflow. Onboarding should generate `seo-workspace/reports/seo-onboarding-report.md` and should not write new articles.

Treat GEO as clear, specific, evidence-backed SEO content that is easy for users, search engines, and AI search systems to understand. Do not create pages only to manipulate AI answers or search rankings.

Publishing is a separate owner-approved step:

1. Owner approves a specific draft or optimization plan.
2. Owner explicitly asks Codex to execute it.
3. Re-check the publishing checklist.
4. Publish or edit through the requested path only: CMS/admin, the website's existing admin service layer, or source edit.
5. For service content, prefer the existing backend/admin write path such as `saveAdminService` / `saveAdminRecord` so admin content, public content, cache invalidation, validation, and audit behavior stay aligned.
6. Do not directly update Supabase tables unless it is an emergency fix, a scheduled automation with explicit owner authorization, or a clearly documented batch operation; if direct database/API updates are used, create a backup and report the reason.
7. For bilingual page pairs, update both `/zh` and `/en` records plus SEO metadata/manifest/sitemap where applicable.
8. If approved execution includes image needs, create or prepare the actual conceptual image assets and matching bilingual captions/alt text before publishing, unless the owner explicitly asks for text-only execution.
9. Report exactly what changed in both languages, including which images are concept/rendering assets versus real owner-provided assets.
