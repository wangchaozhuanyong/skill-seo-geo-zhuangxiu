# SEO/GEO Publish Report

日期：2026-06-07
网站：https://flashcast.com.my/
执行模式：业主批准后执行
发布版本：安全版

## 发布页面

- `/en/services/shop-renovation`
- `/zh/services/shop-renovation`

## 发布方式

1. 通过 Supabase `services` 表直接更新已发布的 `shop-renovation` 记录。
2. 将旧别名服务记录 `shoplot` 标记为 `archived`，避免服务列表、SEO 生成与公开读取继续重复暴露旧页。
3. 更新源码仓中的旧别名重定向规则：
   - `/en/services/shoplot` -> `/en/services/shop-renovation`
   - `/zh/services/shoplot` -> `/zh/services/shop-renovation`
4. 重新生成源码仓中的 `functions/seo-manifest.json`、`public/seo-manifest.json`、`public/sitemap.xml`、`public/llms.txt`。
5. 将最新 SEO 生成物同步到现有 `dist/`，并手动部署到 Cloudflare Pages 项目 `flashcast-website`。

## 安全版执行范围

已更新：

- 中英服务标题、摘要、正文
- 中英适合对象
- 中英服务范围
- 中英常见项目
- 中英流程步骤
- 中英 FAQ
- 中英 SEO title
- 中英 meta description
- 中英图片 alt
- 页面正文中的审批支持、商业空间服务页与报价页引导
- `shoplot` 旧别名服务状态
- `/services/shoplot` 旧别名 301 重定向
- `functions/seo-manifest.json`
- `public/seo-manifest.json`
- `public/sitemap.xml`
- `public/llms.txt`
- `dist/seo-manifest.json`
- `dist/sitemap.xml`
- `dist/llms.txt`

未变更：

- 未确认价格
- 未确认保修或售后承诺
- 未确认客户评价
- 未确认真实零售案例
- 未确认 mall / landlord / local council 具体审批承诺

## 备份与部署记录

- 内容备份：`/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main/tmp/shop-renovation-backup-2026-06-07T09-14-28-003Z.json`
- Cloudflare Pages 预览部署：`https://30c8b8fa.flashcast-website.pages.dev`
- 手动部署标记：`manual-shop-seo-20260607`

## 公开验证

已验证正式域原始 HTML：

- EN title：`Shop Renovation Malaysia | Retail Fit-Out & Shoplot Planning | FLASH CAST`
- EN meta：`Plan a shop renovation in Kuala Lumpur or Selangor with FLASH CAST. Review retail layout, customer flow, counters, display planning, facade considerations, timeline factors, and quotation steps.`
- ZH title：`店铺装修 马来西亚 | 零售与商铺空间规划施工 | FLASH CAST`
- ZH meta：`了解 FLASH CAST 在 Kuala Lumpur、Selangor 与 Klang Valley 的店铺装修与 retail fit-out 服务，包括布局规划、展示动线、柜台收纳、门头与饰面协调、工期因素与报价流程。`

已验证旧别名收口：

- `https://flashcast.com.my/en/services/shoplot` 返回 `301` 到 `/en/services/shop-renovation`
- `https://flashcast.com.my/zh/services/shoplot` 返回 `301` 到 `/zh/services/shop-renovation`

已验证索引生成物：

- `sitemap.xml` 仅保留 `/shop-renovation`
- `llms.txt` 已不再列出 `/services/shoplot`
- `seo-manifest.json` 已不再包含 `/services/shoplot`

## 验证限制

- 本机没有可用的 Playwright 浏览器二进制，未完成浏览器渲染态截图验证。
- 由于当前环境没有 `npm` 命令，本次未运行 `npm run i18n:check`、`npm run arch:check` 或完整前端 build。
- 本次沿用“数据库内容 + middleware + SEO 生成物 + 现有 `dist/` 手动部署”的安全链路完成发布。

## 5 行日报

- 已完成：已执行店铺装修双语服务页安全版发布，并完成旧 `/shoplot` 别名收口与 Cloudflare Pages 部署。
- 目标关键词/页面：`shop renovation malaysia` / `店铺装修 马来西亚`；`/en/services/shop-renovation` + `/zh/services/shop-renovation`
- 预期收益：提升高商业意图店铺装修页的 SEO/GEO 清晰度、FAQ 覆盖、商业空间咨询承接与旧别名去重效果。
- 需要业主补充：真实零售/店铺案例、最终 WhatsApp 引导策略、审批相关可公开承诺边界。
- 建议下一步：观察 Search Console 与询盘表现；下一次优先补店铺装修相关文章或真实商业案例页的内链支撑。
