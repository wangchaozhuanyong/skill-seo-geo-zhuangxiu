# Office Homepage Dedup Execution

日期：2026-06-07
网站：https://flashcast.com.my/
执行类型：办公室服务入口去重

## 本次执行

为消除首页和公开服务摘要中的办公室重复入口，本次执行了两类修复：

1. 直接更新生产内容数据  
   - 将 `services` 表中的旧记录 `office` 从 `published` 改为 `archived`
   - 保留 `office-renovation` 为唯一公开办公室主服务页

2. 更新源码兜底入口  
   - 将 [`/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main/src/components/sections/ServicesSection.tsx`](/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main/src/components/sections/ServicesSection.tsx) 中办公室服务卡兜底链接改为 `/services/office-renovation`
   - 为 `office-renovation` 补上 `Briefcase` 图标映射

## 备份

- 旧 `office` 服务记录备份：
  [`/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main/tmp/office-legacy-service-backup-2026-06-07T09-12-09-760Z.json`](/Users/wangchao/Desktop/装修网站/zhuangxiuwangzhan-main/tmp/office-legacy-service-backup-2026-06-07T09-12-09-760Z.json)

## 公开验证

已验证当前生产库状态：

- `office`：`archived`
- `office-renovation`：`published`

已验证正式域首页：

- 英文首页办公室入口只剩 `/en/services/office-renovation`
- 中文首页办公室入口只剩 `/zh/services/office-renovation`
- 旧 `/services/office` 首页卡片已不再公开展示

## 当前状态

- 办公室装修主题已统一到一个公开主服务页
- 旧别名页仍保留 301 重定向能力
- 首页、服务摘要、SEO 主页路径三层都已收口

## 注意事项

- 本次不需要重新 Cloudflare Pages 部署即可生效，因为首页重复项的根因是生产 CMS 内容里同时公开了两条办公室服务记录。
- 源码兜底入口已同步修正，但由于本机完整 build 环境仍有 `Vite/rolldown` 原生绑定问题，源码改动尚未单独重新构建发布。
