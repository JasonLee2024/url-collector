# URL Collector — 通用网址收藏

> 任意网页的「收藏 → 元数据记录 → 知识库归档」标准化技能。
> 三种模式：快速收藏 / 深度存档 / KB 归档。
> 基于 resource-metadata v2.2 通用网页资源类型，对标 Dublin Core + schema.org。

## 最新更新

- **v1.2.0** (2026-05-18)：修复 MODE 逻辑 bug + 模板去重 + quality_gate.py + --dry-run + OG type 检测 + 标签自动提取 + 匹配权重修正 + "不应归档"协议。
- **v1.1.1** (2026-05-18)：新增 Agent KB 结构分析协议（5 步），SKILL.md 步骤合并优化
- **v1.1.0** (2026-05-18)：新增知识库归档模式。Johnny Decimal 编号分配 + 5C 索引更新 + KB 兼容 frontmatter。
- **v1.0.0** (2026-05-18)：初版。快速收藏 + 深度存档两种模式，通用网页元数据规范，一键采集脚本。

## 安装

```bash
npx skills add JasonLee2024/url-collector
```

### 依赖安装（仅深度存档模式需要）

```bash
cargo install monolith
```

## 兼容性

- 依赖 `agent-browser`（网页信息提取）
- 深度存档依赖 `monolith`（离线 HTML 快照）
- 元数据规范基于 `resource-metadata` v2.2
- KB 归档兼容任何 Johnny Decimal 组织的知识库

## 与现有采集技能的关系

| 技能 | 覆盖范围 | 何时用 |
|------|----------|--------|
| `url-collector` | **通用网页 + KB 归档** | 无专用采集器的任意 URL，或归档到知识库 |
| `medium-article-capture` | Medium.com | Medium 文章（含付费墙） |
| `medium-to-kb-pipeline` | Medium → KB | Medium 文章全流程入库 |
| `opencli-kb-bridge` | B站/知乎/微信/YouTube | 特定平台内容 |
| `xiaohongshu-capture` | 小红书 | 小红书笔记 |
