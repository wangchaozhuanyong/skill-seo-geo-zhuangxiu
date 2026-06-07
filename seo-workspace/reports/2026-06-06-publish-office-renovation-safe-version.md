# SEO/GEO Publish Report

日期：2026-06-06
网站：https://flashcast.com.my/
执行模式：业主批准后执行
发布版本：安全版

## 发布页面

- `/en/services/office-renovation`
- `/zh/services/office-renovation`

## 发布方式

1. 通过 Supabase `services` 表直接更新已发布的 `office-renovation` 记录。
2. 重新生成源码仓库中的 `functions/seo-manifest.json`、`public/seo-manifest.json`、`public/sitemap.xml`、`public/llms.txt`。
3. 将最新 SEO 生成物同步到现有 `dist/`，并手动部署到 Cloudflare Pages 项目 `flashcast-website`。

## 安全版执行范围

已更新：

- 中文服务标题、摘要、正文
- 英文服务标题、摘要、正文
- 中英适合对象
- 中英服务范围
- 中英常见项目
- 中英流程步骤
- 中英 FAQ
- 中英 SEO title
- 中英 meta description
- 中英图片 alt
- 页面正文中的相关案例、服务页与报价页引导
- `functions/seo-manifest.json`
- `public/seo-manifest.json`
- `public/sitemap.xml`
- `public/llms.txt`
- `dist/seo-manifest.json`
- `dist/sitemap.xml`
- `dist/llms.txt`

未变更：

- 旧别名页面 `/en/services/office` 与 `/zh/services/office`
- 未确认价格
- 未确认保修或售后承诺
- 未确认客户评价
- 未确认资质、奖项或认证
- 未确认额外办公室案例

## 备份与部署记录

- 内容备份：`/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main/tmp/office-renovation-backup-2026-06-06T09-21-08-183Z.json`
- Cloudflare Pages 预览部署：`https://d070d698.flashcast-website.pages.dev`
- 手动部署标记：`manual-office-seo-20260606`

## 公开验证

已验证正式域原始 HTML：

- EN title：`Office Renovation Malaysia | Commercial Fit-Out & Space Planning | FLASH CAST`
- EN meta：`Plan an office renovation in Kuala Lumpur or Selangor with FLASH CAST. Review layout planning, partitions, reception areas, M&E coordination, timeline factors, and quotation steps.`
- ZH title：`办公室装修 马来西亚 | 商业空间规划与施工 | FLASH CAST`
- ZH meta：`了解 FLASH CAST 在吉隆坡、雪兰莪与 Klang Valley 的办公室装修与商业空间施工服务，包括布局规划、隔间、前台、会议室、机电协调、工期因素与报价流程。`

已验证浏览器渲染结果：

- 英文页显示新 H1、新正文、新 FAQ。
- 中文页显示新 H1、新正文、新 FAQ。
- 英文页已显示 `Kota Damansara Clinic Reception Fit-Out` 参考内容。
- 中文页已显示 `Kota 白沙罗诊所装修案例` 参考内容与“全部服务项目 / 获取免费报价”引导。

## 注意事项

- 本机 `npm` 不可用，且当前 Vite / rolldown 原生绑定损坏，无法重新完整 build。
- 因本次未修改前端源码，只修改 CMS 内容与 SEO 生成物，所以使用既有 `dist/` 产物同步最新 `seo-manifest`、`sitemap` 与 `llms` 后完成手动部署。
- 正式域本次验证返回 `x-flashcast-html-cache: miss`，说明已拿到新 HTML；后续再次请求应逐步进入缓存命中。

## 5 行日报

- 已完成：已执行办公室装修双语服务页安全版发布，并完成 Cloudflare Pages 手动部署。
- 目标关键词/页面：`office renovation malaysia` / `办公室装修 马来西亚`；`/en/services/office-renovation` + `/zh/services/office-renovation`
- 预期收益：提升高商业意图办公室装修页的 SEO/GEO 清晰度、FAQ 覆盖、商业案例支撑和报价引导。
- 需要业主补充：更多办公室/商业空间真实案例、最终 WhatsApp 引导策略、如需补强 `/services/office` 旧别名页请单独确认。
- 建议下一步：观察 Search Console 与询盘表现；下一次优先处理 `office` 旧别名页是否重定向或同步优化。
