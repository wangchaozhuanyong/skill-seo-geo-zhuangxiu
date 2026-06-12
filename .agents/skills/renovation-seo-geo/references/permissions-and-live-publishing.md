# Permissions And Live Publishing

Modes:

- `audit`: read-only
- `draft`: write only drafts/reports
- `pr`: prepare source-change proposal
- `staging`: staging-only after approval
- `live`: requires explicit live preconditions

Live mode requires:

- owner approval of a specific plan
- `SEO_GEO_ALLOW_LIVE=1`
- `--confirm-live`
- pre-publish QA pass
- backup path exists
- rollback plan exists
- changelog path exists
- path is not disallowed

Do not write `.env`, `.env.local`, `.env.production`, credentials, tokens, cookies, or secrets.

Publishing preference:

1. existing admin/backend service layer
2. source edit following framework conventions
3. direct database/API writes are not allowed for publishable content; use the website management admin UI or existing admin service layer so admin data, public content, validation, cache invalidation, and audit records stay synchronized

For bilingual page pairs, update both `/zh` and `/en` unless owner explicitly limits scope.
