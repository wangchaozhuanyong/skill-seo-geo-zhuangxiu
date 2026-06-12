# Flash Cast Renovation SEO/GEO Skill Workspace

这是 Flash Cast 装修网站的 SEO/GEO 工作区，用于让 Codex 按专业 SEO/GEO 增长流程执行网站优化、内容规划、索引诊断、技术审计、本地 SEO、多语言 SEO、Schema、图片 SEO、发布前 QA 和每日增长任务。

核心 skill：

```text
renovation-seo-geo
```

目标是提升合格自然搜索曝光、装修询盘和 AI 搜索可见度。可以把目标设为竞争 Google、百度、Bing 和 AI 搜索结果中的高排名位置，但不能承诺第一名、收录、流量、询盘、ROI 或固定排名结果。

## 能做什么

- 生成每日 SEO/GEO 最高价值任务，不机械写随机文章。
- 输出双语 `/zh` 和 `/en` 页面草稿、服务页优化方案、FAQ、标题、meta、内链、CTA、Schema 和图片 alt 建议。
- 规划全站内容生产系统：最新资料研究、图文/效果图内容包、富文本结构、发布门槛和定时自动化地图。
- 做技术 SEO 审计：URL inventory、robots、sitemap、canonical、noindex、hreflang、状态码、页面基础信号。
- 做索引支持：Google Search Console、百度搜索资源平台、Bing/IndexNow、sitemap、robots 和 canonical 检查。
- 做 GEO/AI 搜索优化：品牌实体、服务实体、问答结构、证据链、直接答案、结构化内容和双语一致性。
- 做本地 SEO：服务区域、NAP 一致性、引用机会、Google Business Profile / 百度地图资料准备。
- 做发布前 QA：阻止 fake review、fake case、unsupported location、wrong canonical、noindex、doorway page、keyword stuffing 等高风险问题。

## 不能保证什么

- 不保证 Google、百度、Bing 或任何 AI 搜索平台收录。
- 不保证排名第一、首页排名、固定排名、固定流量或固定询盘。
- 不自动创建虚假案例、虚假评价、虚假价格、虚假工期、虚假奖项、虚假资质、虚假服务区域或真实项目证明。
- 不做黑帽 SEO、关键词堆砌、城市门页、批量同义改写页面或 AI 搜索诱导垃圾内容。
- 不把真实 token、OAuth 文件、service-account JSON、CMS 密码、admin cookie、百度 token 或 IndexNow key 写入 repo。

## 支持的搜索引擎

- Google：Search Console sitemap / URL Inspection 数据读取；普通装修页面不使用 Google Indexing API。
- Baidu：主动推送、死链文件、站点配置检查；没有 token 时只生成配置说明。
- Bing / IndexNow：URL 变更通知；没有 key 时生成 key setup 指南。
- AI Search / GEO：通过清晰实体、结构化内容、Schema、FAQ、证据链、本地语义和双语一致性提升可理解性。

## 工作模式

- `audit`：只读审计和报告。
- `draft`：只写入 `seo-workspace/drafts/` 和 `seo-workspace/reports/`。
- `pr`：业主批准后，准备 PR/source-change 级别执行。
- `staging`：业主批准后，只在 staging 执行并 QA。
- `live`：默认禁止；必须有明确 live 指令、QA 通过、backup、changelog、rollback plan 和 `--confirm-live`。

## 配置

复制示例配置并填入真实值。真实 secret 不要提交到 repo。

```bash
cp seo-workspace/config/seo-geo-config.example.yml seo-workspace/config/seo-geo-config.yml
cp seo-workspace/config/search-engines.example.yml seo-workspace/config/search-engines.yml
cp seo-workspace/config/cms.example.yml seo-workspace/config/cms.yml
cp .env.example .env
```

常见配置项：

- Google：`gsc_site_url`、OAuth/service-account 路径或环境变量。
- Baidu：`baidu_site`、主动推送 token、死链文件路径。
- IndexNow：endpoint、host、key、key 文件 URL。
- CMS：cms mode、admin service path、允许 live 的路径、禁止 live 的路径。
- Site：production URL、staging URL、sitemap、robots、`/zh` 和 `/en` 前缀。

检查配置：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py config
```

## 常用命令

验证工作区：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py validate
python3 validate_workspace.py
```

抓取 URL inventory：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py crawl --site https://www.example.com
```

生成技术 SEO 审计：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py technical-audit
```

同步或检查 Google Search Console：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py gsc-sync
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py google-index-status --urls changed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py google-submit-sitemap
```

百度与 IndexNow：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py baidu-submit --urls changed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py indexnow-submit --urls changed
```

每日最高价值任务：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-calendar --days 14
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline brief
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline publish-prep
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py automation-schedule
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-authorization
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-runner
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-postrun
```

`content-calendar` 用于多日排期：它从 opportunity scoring 和全站内容系统地图中选择双语页面对，降低近期已选 URL 的分数，生成 `daily-content-calendar.json`、CSV 和中文审核报告，避免 unattended automation 长期重复同一个页面。它只做排期，不写正文、不登录 CMS、不上传媒体、不写数据库、不发布、不部署。`daily-automation` 在没有显式 `--target-url` 时会优先使用这个日历的当天/最近未来任务。

`daily-automation` 是推荐的定时入口：每次只选择一个任务；已有内容日历时按日历轮转，否则按机会分选择最高价值任务。`brief` 只生成业主审核草稿；`rich-content` 继续生成图文富文本包、本地可拖拽编辑器、editor-applied CMS payload 草稿、媒体计划和概念图资产；`publish-prep` 继续生成发布队列、dry-run 执行请求和 readiness handoff。富文本编辑器支持拖拽排序、编辑已有图文块、新增文本块、新增图片块、新增 CTA 块，并导出 JSON 供后续 approved execution 使用。联网 research 打开时，rich pipelines 会先用 `research-search` 生成/抓取当前互联网候选，支持 `google-news-rss`、`trusted-rss`、`hybrid-rss`，再用 `research-discovery` 从可信种子源发现候选，并可用 `research-intake` 自动把高分可信候选来源抓取并写入本地 source log。所有 pipeline 默认不登录 CMS、不上传媒体、不写数据库、不发布、不部署。

`content-studio` 是指定单页内容生产入口：给一个目标 URL，它会复用安全 daily orchestrator 跑 `brief`、`rich-content` 或 `publish-prep`，并额外输出 `content-studio-run.json` 和中文审核报告。推荐用于“现在给这个服务页/文章/案例页做完整图文包”的场景；它会串起最新资料候选、富文本内容、可拖拽编辑器、概念效果图/媒体计划、service-pattern 内容包和发布准备门禁，但仍不登录 CMS、不上传媒体、不写数据库、不发布、不部署。

`content-studio-queue` 是整站内容生产队列：它读取全站 URL/content-system map，把 `/en` 与 `/zh` 配对去重，为每个页面给出推荐 `content-studio` pipeline、可复制执行命令、服务页的 `service-pattern-package` 命令、图文/效果图要求和审核门禁。它只生成队列 JSON/CSV/报告，不会一次性生成所有页面正文，也不会发布。

`content-studio-next` 是未来固定时间自动化可调用的安全队列消费者：每次只从 `content-studio-queue` 里选择一个未处理页面，运行一次 `content-studio`，写入 `content-studio-next-run.json`，并追加 `content-studio-history.csv`，防止连续重复同一页。使用 `--owner-review-package` 或在 schedule 中设置 `owner_review_package: true` 时，它会继续生成 owner review dashboard、发布候选、publish-prep、审批包、媒体审核 gallery、媒体 URL 模板、可填写 URL 草稿和媒体状态报告。它仍然只停在本地审核包，不发布、不上传、不写 CMS/source。

`content-studio-orchestrator` 是未来 cron/launchd 应调用的队列守门入口：它读取 `automation-schedule` 配置，要求 `executor: content-studio-next`，检查时间窗口和当天重复运行，然后才消费一个页面；当配置 `owner_review_package: true` 时，还会让本次队列消费生成完整业主审核总包。它会写 `content-studio-orchestration.json`、log 和中文报告；仍然不安装定时任务、不发布、不上传、不写 CMS/source。

`content-studio-postrun` 是队列自动化运行后的复盘入口：读取 orchestration、next-run、queue、history，汇总本次处理页面、内容包状态、下一个队列页面、阻断项和业主审核动作。它只写 JSON/中文报告，不重新运行自动化、不发布。

`content-studio-publish-candidate` 是 Content Studio 到发布链路之间的安全候选桥：读取最近一次 postrun/run 结果，重建本地 `approved-publish-queue.csv`，挑出匹配的 rich-content package 行，并写入候选 JSON 和中文审核报告。它只做候选整理，不调用 CMS/admin helper、不写源码、不上传媒体、不发布、不部署。

`content-studio-publish-prep` 会消费这个候选并串起本地发布准备链：website adapter、publish plan、CMS dry-run request、readiness、bundle、approved executor 模拟、implementation package、operator command package、execution receipt verifier，并输出中文总报告。它只是 handoff 编排，不登录 CMS、不调用 admin helper、不写源码、不上传媒体、不发布、不部署。

`content-studio-approval-packet` 会把 publish-prep 证据转换成业主审批行动包：把阻断项归类成内容批准、明确执行范围、QA、媒体公开 URL、storage readiness 和未来执行回执，并给出推荐下一步命令。它只写审核 JSON/中文报告，不发布。

`content-studio-media-url-template` 会把媒体上传计划转换成 `uploaded-url-map.template.json`，格式可被 `media-upload-executor` 直接消费。上传或选择概念效果图后，只需要把每个 `file_url` 填成真实公开 HTTPS URL；该命令不上传、不写 CMS、不发布。

`content-studio-media-review-package` 会把已生成的设计效果图/概念图整理成一个本地 HTML gallery 和 JSON 索引。打开 gallery 可以直接看每张图、对应本地文件、建议上传路径、中文/英文 alt、概念标签和 claim boundary；满意后再上传或选择图片并填写公开 HTTPS URL。它不上传、不写 CMS、不发布。

`content-studio-uploaded-url-map-draft` 会把 `uploaded-url-map.template.json` 转成业主/上传器可填写的 `uploaded-url-map.json`，并校验空 URL、占位 URL、非 HTTPS URL、重复 placeholder 和确认标记。它是“图片已上传/已选择”到 media-ready handoff 之间的安全草稿步骤，不上传、不写 CMS、不发布。

`content-studio-media-status` 会把当前图文媒体状态汇总成一份中文报告：读取 `uploaded-url-map.json`、`uploaded-url-map.template.json`、`media-url-map.json`、`rich-content-cms-payload.media-ready.json` 和 `publish-readiness.json`，说明哪些效果图/概念图还缺公开 HTTPS URL、哪些还没确认、是否已经有 media-ready CMS payload。它只写本地状态 JSON/报告，不上传、不写 CMS、不发布。

`content-studio-media-ready-handoff` 会在 `uploaded-url-map.json` 已由业主/上传器确认后，运行 media URL 消费、刷新 publish-prep、重新生成审批包，并产出 `rich-content-cms-payload.media-ready.json`。它不上传、不写 CMS、不发布，只把“图片 URL 已准备好”转成可审核的本地发布准备证据。

`automation-schedule` 只生成和校验固定时间运行计划，包括 `daily-automation.example.yml`、cron 示例、launchd 示例、授权门禁证据和审核报告；不会安装系统定时任务。它支持两种安全 executor：`daily-automation` 按机会分/内容日历选择任务，`content-studio-next` 每次从整站队列消费一个未处理页面并写 history；给 `content-studio-next` 配置 `owner_review_package: true` 后，定时运行会同时生成完整 owner-review handoff，包括 owner review dashboard、媒体审核 gallery、可填写 URL 草稿和媒体状态报告。生成的 cron/launchd 会通过 `content-studio-orchestrator` 调用，保留时间窗口和重复运行门禁。若未来要允许定时发布，必须先用 `scheduled-publish-authorization` 校验 `scheduled-publish-authorization.yml`，并填写 exact owner authorization、双语 allowed target URLs、QA、media/storage、backup、changelog、rollback、过期日期和 live confirmation 要求；到点运行前再用 `scheduled-publish-runner` 生成本次 run request，防止时间窗口错误、URL 越权或当天重复运行；真正定时入口使用 `scheduled-publish-orchestrator`，它只会在 run request ready 时触发 safe `daily-automation --pipeline publish-prep`；运行后用 `scheduled-publish-postrun` 生成阻断分类和下一步清单。

全站内容生产与发布自动化地图：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-system
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-queue
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-postrun
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-publish-candidate --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-publish-prep --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-approval-packet
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-url-template
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-review-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-uploaded-url-map-draft
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-status
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-media-ready-handoff --uploaded-url-map-path seo-workspace/data/uploaded-url-map.json --owner-approved --explicit-execution --qa-passed --storage-ready --uploaded-confirmed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-owner-review-package --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-next --no-fetch-research-remote --owner-review-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio --target-url https://flashcast.com.my/en/services/kitchen --pipeline rich-content
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py service-pattern-package --all
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-calendar --days 14
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
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-publish-prep --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py website-publish-adapter --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-authorization
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-runner
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-postrun
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
```

当内容依赖最新搜索引擎政策、行业新闻、行业资料、材料资料或本地官方信息时，先用 `research-search` 生成/抓取当前互联网搜索候选，或用 `research-discovery` 从可信种子源发现候选 URL，再用 `research-intake` / `latest-research` 记录来源边界；不要把 query、搜索结果或 feed 条目本身当作已验证引用来源。`research-search` 默认可抓取 Google News RSS 候选，也支持 `--provider trusted-rss` 从 `research-search-feeds.example.yml` 抓可信 RSS/Atom 资料源，或用 `--provider hybrid-rss` 同时跑新闻和可信 feed，无需把 API key 写进仓库；`research-discovery` 只生成可信种子候选；`research-intake` 会按分数和来源类型筛选可信候选，再通过 `latest-research` 抓取并写入本地 source log。`daily-automation --pipeline rich-content` 和 `daily-automation --pipeline publish-prep` 默认会先跑 discovery，联网抓取开启时会尝试 conservative auto-intake；如果使用 `--no-fetch-research-remote`，intake 会跳过。`rich-content` 默认会复用目标页已有 `research-source-log.csv` 来源，`publish-plan` 会把有效来源数量写入执行计划，`publish-readiness` 会把研究来源、编辑版 payload、媒体 URL、media-ready payload、发布计划和 dry-run 写入请求汇总成最终 handoff gate。

编辑版发布 payload 选择顺序：显式 `--cms-payload-path` 优先，其次 `rich-content-cms-payload.media-ready.json`，再其次 `rich-content-cms-payload.editor-applied.json`，最后才是基础 `rich-content-cms-payload.json`。`rich-editor-apply` 会保留拖拽排序、文本编辑、新增文本/图片/CTA 块、图片 alt、图注、概念标签和 claim boundary，并在写入 editor-applied payload 前做导出 QA：图片块缺 alt、图注、概念标签、claim boundary，或出现真实案例、客户评价、固定价格、固定工期、保修等未经支持 claim，会直接阻断。`publish-executor` 和 `publish-readiness` 会继续校验 editor-applied 链路：选中 editor-applied payload，或选中由 editor-applied 生成的 media-ready payload 时，`rich-content-editor-apply-summary.json` 必须是 `editor_applied_payload_ready_for_owner_review`，并且 payload 必须保留 no-write/no-live 安全标记。`media-assets` 会从 editor-applied payload 里识别新增的 `NEEDS_MEDIA_UPLOAD:*` 图片并补进媒体计划和 URL map 检查。如果选中的 payload 仍包含 `NEEDS_MEDIA_UPLOAD:*`，即使传了 `--media-ready` 也会阻断执行。

`website-publish-adapter` 只读扫描真实网站仓库，生成 `website-publish-adapter.json` 和报告，用于记录 package manager、admin/media helper、SEO 生成脚本、QA/backup/build 命令、`.env.example` key 名称和发布规则文档。它不运行 npm、不调用 CMS、不改源码、不上传媒体、不发布、不部署。

`scheduled-publish-authorization` 校验固定时间发布 profile，生成 `scheduled-publish-authorization.json` 和中文报告。缺少 `scheduled-publish-authorization.yml`、授权 ID、双语 URL、过期日期、QA/media/storage/backup/changelog/rollback 或 live confirmation 时会阻断；它不安装定时任务、不运行 daily automation、不登录 CMS、不上传媒体、不写页面、不发布、不部署。

`scheduled-publish-runner` 生成一次固定时间发布 run request：读取授权 profile，检查当前本地星期/时间窗口、allowed target URL、双语配对和当天重复 ready request，再写 `scheduled-publish-run-request.json`、`scheduled-publish-run-log.csv` 和中文报告。它只生成请求，不运行 daily automation、不登录 CMS、不上传媒体、不写页面、不发布、不部署。

`scheduled-publish-orchestrator` 是未来 cron/launchd 可调用的安全入口：先跑 runner，只有 run request ready 才执行 `daily-automation --pipeline publish-prep` 生成本地图文、媒体、发布队列和 dry-run handoff 产物。它不调用 CMS/admin helper、不上传媒体、不写 live/source 页面、不发布、不部署。

`scheduled-publish-postrun` 是固定时间运行后的复盘器：读取 run request、orchestration、daily automation、readiness、implementation package、operator command 和 execution receipt JSON，分类阻断原因，输出下一步清单。它不重新运行 research/daily/publish，不登录 CMS、不上传媒体、不写页面、不发布、不部署。

`publish-bundle` 是 approved executor 之前的最后一层封包：它把 ready readiness handoff 和 CMS dry-run write request 封装成 `publish-execution-bundle.json`。它不会调用 CMS、不会写源码、不会上传媒体、不会发布；如果 readiness、媒体 URL、media-ready payload、owner approval、QA 或 CMS request 未 ready，会阻断。

`publish-approved-executor` 是真实执行器前的本地模拟门禁：它读取 `publish-execution-bundle.json`，验证业主批准、明确执行、QA、媒体 URL、media-ready payload、安全 flags，以及非 dry-run 模式需要的 backup/changelog/rollback 证据；`live` 还需要 `--confirm-live`。它只写 `publish-approved-execution-record.json` 和 dry-run 报告，不调用 CMS/admin helper、不改源码、不上传媒体、不发布、不部署。

`publish-implementation-package` 会把 ready 的 `publish-approved-execution-record.json` 转成未来真实执行器可读取的实施包：`publish-implementation-package.json`、`publish-admin-helper-call.json` 和中文 runbook。它默认读取 `website-publish-adapter.json`，把真实网站 backup、SEO generation、QA、build 命令、admin helper call、执行顺序、回滚步骤和 helper/source 证据写进包；仍不运行 npm、不调用 CMS/admin helper、不改源码、不上传媒体、不发布、不部署。

`publish-operator-package` 会把 ready 的 implementation package 和 `publish-admin-helper-call.json` 转成未来 operator/执行器可读取的确定性命令清单：备份、CMS helper call、SEO generation、QA、build、rollback、必需人工确认和 dry-run command preview。它要求 website adapter ready 和安全 flags 干净；仍不运行 npm、不调用 CMS/admin helper、不改源码、不上传媒体、不发布、不部署。

`publish-execution-receipt` 会验证未来真实 approved execution 完成后的执行结果：读取 `publish-operator-command.json` 和 `publish-execution-result.json`，检查目标双语 URL、helper function、CMS record ID、备份、CMS 写入、SEO generation、QA、rollback 证据、命令结果，以及 `published` 状态下的 live URL 验证。它只写 `publish-execution-receipt.json` 和中文报告，不运行命令、不调用 CMS、不改源码、不上传媒体、不发布、不部署。

`service-pattern-package` 会为一个 service pattern 或全部 service pattern 生成完整图文内容审核包：双语 brief、富文本图文编辑器、CMS payload 草稿、概念媒体资产、URL map 示例、prompt pack 和报告。它支持 `--target-url`、`--service-slug`、`--all`，仍是 draft-only，不搜索外部网页、不调用图片 API、不上传、不写 CMS、不发布。

专题模块：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py opportunities
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-calendar --days 14
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-system
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py service-pattern-package --service-slug kitchen
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py automation-schedule
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-authorization
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-runner
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-orchestrator
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py scheduled-publish-postrun
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline brief
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py daily-automation --pipeline rich-content --research-search-provider hybrid-rss
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py research-search --target-url https://flashcast.com.my/en/services/kitchen
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
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py content-studio-approval-packet
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py website-publish-adapter --website-root /Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-plan --target-url https://flashcast.com.my/en/services/kitchen --owner-approved --explicit-execution --qa-passed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-executor --owner-approved --explicit-execution --qa-passed --media-ready
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-readiness
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-bundle
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-approved-executor --owner-approved --explicit-execution --qa-passed
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-implementation-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-operator-package
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py publish-execution-receipt
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py entity
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py geo-ai
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py local-seo
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py schema
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py multilingual
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py image-seo
```

发布前 QA：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py qa --target-url https://www.example.com/zh/services/renovation
```

预执行检查：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py apply --plan seo-workspace/drafts/example.md --mode pr
```

Live 模式必须显式确认，且仍需要 backup、QA、changelog 和 rollback plan：

```bash
python .agents/skills/renovation-seo-geo/scripts/seo_geo_cli.py apply --plan seo-workspace/drafts/example.md --mode live --confirm-live
```

## 回滚原则

Live 发布前必须先有：

- backup：页面/CMS/source 改动前备份。
- changelog：记录改动文件、页面、语言版本和提交方式。
- rollback plan：说明如何恢复到发布前版本。
- QA report：发布前 QA 通过，严重问题为 0。

如果发布内容，必须走网站管理后台、既有后台写入路径，或包装这些后台写入路径的受保护发布 API，例如 `saveAdminService` / `saveAdminRecord` / `content-publish`。`content-publish` 可用管理员 Bearer token，或用 `CONTENT_PUBLISH_SECRET` 对应的 `x-cron-secret` 机器密钥。不要直接改 Supabase 表或数据库行，否则客户后台数据、前台内容、缓存、校验和审计记录会不同步。

## 报告在哪里

- 每日草稿：`seo-workspace/drafts/`
- 审计报告：`seo-workspace/reports/`
- 业务数据：`seo-workspace/data/`
- 配置示例：`seo-workspace/config/`
- 操作策略：`.agents/skills/renovation-seo-geo/references/`

常见报告包括：

- workspace validation report
- technical SEO audit
- Google indexation report
- Baidu indexation report
- IndexNow report
- opportunity score report
- content brief
- GEO/AI readiness report
- local SEO report
- schema report
- multilingual SEO report
- image SEO report
- prepublish QA report

## 开发验证

提交或交付前运行：

```bash
python3 -m py_compile $(find .agents/skills/renovation-seo-geo/scripts -name '*.py' -print)
python3 -m pytest -q
python3 validate_workspace.py
```
