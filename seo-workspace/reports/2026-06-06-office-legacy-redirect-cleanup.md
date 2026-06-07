# Office Legacy Redirect Cleanup

日期：2026-06-06
网站：https://flashcast.com.my/
执行类型：已发布页面的去重与 canonical 收口

## 本次动作

为避免办公室服务页出现重复索引与关键词内耗，本次将旧别名页：

- `/en/services/office`
- `/zh/services/office`

统一 301 重定向到：

- `/en/services/office-renovation`
- `/zh/services/office-renovation`

## 已执行内容

- 在 `functions/_middleware.ts` 添加旧办公室 URL 的 `301` 精确重定向规则。
- 在 SEO 生成脚本中把旧办公室别名加入 legacy redirect 排除集合。
- 重新生成：
  - `functions/seo-manifest.json`
  - `public/seo-manifest.json`
  - `public/sitemap.xml`
  - `public/llms.txt`
- 同步最新 SEO 生成物到 `dist/`
- 手动部署到 Cloudflare Pages

## 预览部署

- `https://8ecaa8ff.flashcast-website.pages.dev`

## 验证结果

已验证正式域：

- `https://flashcast.com.my/en/services/office` 返回 `301` 到 `/en/services/office-renovation`
- `https://flashcast.com.my/zh/services/office` 返回 `301` 到 `/zh/services/office-renovation`

已验证本地生成物：

- `functions/seo-manifest.json` 不再包含旧办公室别名
- `public/sitemap.xml` 不再列出旧办公室别名
- `public/llms.txt` 不再列出旧办公室别名

## 当前状态

- `/office-renovation` 已成为办公室装修主题的唯一主服务页
- 旧别名页已收口，不再继续作为独立可索引页面参与竞争

## 后续建议

- 如后续能恢复完整前端 build 环境，可再把首页服务卡和其他可能残留的前端静态跳转入口直接改到 `/services/office-renovation`，减少一次 301 跳转。
- 后续办公室相关文章、落地页和案例页继续只向 `/services/office-renovation` 聚合内链。
