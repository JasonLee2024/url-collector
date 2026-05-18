# 将 agentskill.work 归档到 Claude_Code_HaHa 知识库 网页资源记录

> 演示 url-collector v1.2.0 KB 归档模式的完整产物。
> 以下展示的是归档到 `Claude_Code_HaHa` 知识库 → `02_Claude_Code_Skills` → 新类别 `14_Skills发现平台` 的结果。

| 属性 | 值 |
|------|-----|
| 编号 | 14.01 |
| 类型 | 网页资源记录 |
| 来源 | https://agentskill.work/zh |
| 收藏日期 | 2026-05-18 |
| 语言 | zh |
| 难度 | ⭐ |
| 状态 | 🌱 初稿 |
| 采集方式 | url-collector v1.2.0 KB 归档模式 |

## 元数据（对标 Dublin Core + schema.org）

| 维度 | 字段（中） | 字段（EN） | 值 | 对标标准 |
|:------|:-----|:-----|:-----|:-----|
| 标识 | 页面标题 | Title | agentskill.work — Claude Skill 项目聚合平台 | dc:title, schema:headline |
| 标识 | 页面地址 | URL | https://agentskill.work/zh | dc:identifier, schema:url |
| 描述 | 摘要 | Description | 自动汇总 GitHub 上热门 Claude Skill 项目，集中展示与搜索 | dc:description, schema:abstract |
| 归属 | 站点名称 | Site Name | agentskill.work | dc:publisher, schema:publisher |
| 归属 | 作者 | Author | — | dc:creator, schema:author |
| 时间 | 收藏日期 | Date Collected | 2026-05-18 | dc:created |
| 时间 | 发布日期 | Publish Date | 2026（持续更新） | dc:issued, schema:datePublished |
| 语言 | 页面语言 | Language | zh-CN | dc:language, schema:inLanguage |
| 主题 | 标签 | Tags | Claude Skill, GitHub, 技能发现, 项目聚合 | dc:subject, schema:keywords |
| 分类 | 用户分类 | Category | Skills 发现平台 | dc:type |
| 格式 | 内容类型 | Content Type | tool | dc:format, schema:genre |
| 关联 | 离线快照 | Snapshot Path | ~/AI/web/archive/agentskill-work.html | dc:relation |
| 关联 | 关联知识库 | Related KB | /home/skywalker/cc-haha/Docs/ | dc:relation |

## 获取方式

- 在线访问：https://agentskill.work/zh
- 离线快照：~/AI/web/archive/agentskill-work.html

## 归档决策记录

- **目标 KB**：Claude_Code_HaHa（`/home/skywalker/cc-haha/Docs/`）
- **归属区域**：02_Claude_Code_Skills（技能体系）
- **归属类别**：14_Skills发现平台（新建。原 02 区域最大类别编号为 13_Public_Skills，取 14）
- **分配编号**：14.01（该类别第一个文件）
- **SITEMAP.md 已更新**：目录树 + 最近更新表
- **区域 README 已更新**：追加 14_Skills发现平台 类别条目

## 内容摘要

agentskill.work 是一个 Claude Skill 项目聚合平台，从 GitHub 自动索引高星 Claude Skill 仓库（当前 1030+ 项目），支持按名称/描述/话题搜索、按编程语言过滤、热门项目和最新开源分类浏览。平台还提供 OpenAPI (Swagger)、llms.txt 和 RSS feed 供开发者集成。默认每小时同步一次 GitHub 数据，可作为 find-skills 技能的补充发现渠道。
