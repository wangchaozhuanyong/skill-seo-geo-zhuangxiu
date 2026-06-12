# SEO/GEO Operating System

The operating system combines:

- configuration validation
- URL inventory and technical SEO audit
- Google/Baidu/IndexNow indexation reporting
- opportunity scoring
- content/page audit
- bilingual content briefs
- entity profile and GEO/AI readiness
- local SEO and citation readiness
- schema generation and validation
- multilingual/hreflang validation
- image SEO and visual asset briefs
- pre-publish QA
- CLI orchestration
- regression tests

Core CLI:

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py validate
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py config
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url <url>
```

Default automation is draft/report only. Publishing is a separate owner-approved execution step.

Recommended sequence before execution:

1. `validate`
2. `technical-audit`
3. `opportunities`
4. content brief/report
5. `schema`
6. `multilingual`
7. `image-seo`
8. `qa`
9. owner approval
10. backup, rollback plan, changelog
11. approved execution path

