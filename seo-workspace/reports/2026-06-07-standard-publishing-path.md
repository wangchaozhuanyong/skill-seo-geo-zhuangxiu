# Standard Publishing Path

日期：2026-06-07
网站：https://flashcast.com.my/
执行类型：发布流程规范化

## 业主确认

业主要求后续执行采用更规范的长期方式：

- 日常内容发布优先走管理后台或现有后台服务层。
- 服务内容优先复用 `saveAdminService` / `saveAdminRecord` 这类既有写入路径。
- 直接 Supabase 表更新只用于紧急修复、明确授权的自动化或有记录的批量操作。

## 已固化规则

已更新：

- `AGENTS.md`
- `.agents/skills/renovation-seo-geo/SKILL.md`
- 自动化记忆 `flash-cast-daily-seo-geo/memory.md`

## 后续执行标准

以后发布已批准的服务页、案例页、地区页或其他 CMS 内容时，应按以下顺序选择路径：

1. 优先使用管理后台 UI。
2. 如果自动化执行且不能登录后台，优先复用网站源码里已有的后台服务函数或 mutation 路径，例如 `saveAdminService` / `saveAdminRecord`。
3. 需要更新边缘 SEO 层时，再重新生成 `seo-manifest`、`sitemap`、`llms` 并部署。
4. 只有在紧急修复、批量操作或业主明确授权时，才直接通过 Supabase API 更新表。
5. 直接更新数据库时，必须先备份影响行，并在报告中说明为什么绕过后台服务路径。

## 目的

这个规则让后台内容、前台客户内容、状态字段、版本字段、缓存失效、审计记录和 SEO 生成物尽量保持一致，减少后台打开旧内容后覆盖线上内容的风险。

## 执行状态

等待后续具体发布任务按该规则执行。
