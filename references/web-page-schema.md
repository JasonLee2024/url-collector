# 通用网页元数据规范（Web Page Metadata Schema）

> 本规范是 resource-metadata v2.2 的资源类型六，对标 Dublin Core + schema.org/WebPage。
> 用于任意 URL 的收藏与归档，覆盖 article / docs / tool / video 等各类网页。

## 字段定义

| 维度 | 字段（中文） | 字段（English） | 对标标准 | 级别 |
|:------|:-----|:-----|:-----|:----:|
| 标识 | 页面标题 | Title | dc:title, schema:headline | 必需 |
| 标识 | 页面地址 | URL | dc:identifier, schema:url | 必需 |
| 描述 | 摘要/OG描述 | Description | dc:description, schema:abstract | 必需 |
| 归属 | 站点名称 | Site Name | dc:publisher, schema:publisher | 推荐 |
| 归属 | 作者 | Author | dc:creator, schema:author | 可选 |
| 时间 | 收藏日期 | Date Collected | dc:created | 必需 |
| 时间 | 发布日期 | Publish Date | dc:issued, schema:datePublished | 推荐 |
| 语言 | 页面语言 | Language | dc:language, schema:inLanguage | 推荐 |
| 主题 | 标签/关键词 | Tags | dc:subject, schema:keywords | 推荐 |
| 分类 | 用户分类 | Category | dc:type | 推荐 |
| 格式 | 内容类型 | Content Type | dc:format, schema:genre | 必需 |
| 关联 | 离线快照路径 | Snapshot Path | dc:relation | 可选 |
| 关联 | 关联知识库 | Related KB | dc:relation | 可选 |

## Content Type 枚举

| 值 | 说明 | 示例 |
|-----|------|------|
| `article` | 技术文章/博客 | 个人博客、技术文档、教程 |
| `docs` | 官方文档 | API 参考、框架文档、规范 |
| `tool` | 在线工具/平台 | 生成器、转换器、SaaS |
| `video` | 视频页面 | YouTube、Bilibili、教程视频 |
| `other` | 其他 | 不适合以上分类的页面 |

## 文件命名

```
{YYYY-MM-DD}_{title-slug}_网页资源记录.md
```

- `title-slug`：英文小写 + 连字符，取页面标题的前 3-5 个关键词
- 示例：`2026-05-18_rust-async-book_网页资源记录.md`

## 记录文件模板

```markdown
# {页面标题} 网页资源记录

> 最后更新：{YYYY-MM-DD} | 资源类型：通用网页 | 规范版本：v2.2

## 元数据（对标 Dublin Core + schema.org）

| 维度 | 字段（中） | 字段（EN） | 值 | 对标标准 |
|:------|:-----|:-----|:-----|:-----|
| 标识 | 页面标题 | Title | {标题} | dc:title, schema:headline |
| 标识 | 页面地址 | URL | {URL} | dc:identifier, schema:url |
| 描述 | 摘要 | Description | {摘要} | dc:description, schema:abstract |
| 归属 | 站点名称 | Site Name | {站点} | dc:publisher, schema:publisher |
| 归属 | 作者 | Author | {作者，如可获取} | dc:creator, schema:author |
| 时间 | 收藏日期 | Date Collected | {YYYY-MM-DD} | dc:created |
| 时间 | 发布日期 | Publish Date | {如有} | dc:issued, schema:datePublished |
| 语言 | 页面语言 | Language | {zh/en/...} | dc:language, schema:inLanguage |
| 主题 | 标签 | Tags | {关键词} | dc:subject, schema:keywords |
| 分类 | 用户分类 | Category | {分类} | dc:type |
| 格式 | 内容类型 | Content Type | {article/docs/tool/video/other} | dc:format, schema:genre |
| 关联 | 离线快照 | Snapshot Path | {如有，快照路径} | dc:relation |
| 关联 | 关联知识库 | Related KB | {如有，KB路径} | dc:relation |

## 获取方式

- 在线访问：{URL}
- 离线快照：{Snapshot Path，如已存档}

## 内容摘要

{页面核心内容的简要总结，2-3 句话}
```
