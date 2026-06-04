# 页面采集内容过滤优化指南

> v1.0 · 基于 XDA Developers 实测优化 · 适用于 `full_archive.py` 代码迭代

## 核心原则

**优先精确定位，多层兜底清洗** — 不能只靠一层过滤，也不能一刀切删除。

| 层 | 位置 | 作用 | 风险 |
|---|------|------|------|
| 选择器优先级 | `CONTENT_SELECTORS` | 精确定位正文区域 | 可能丢失 header 元数据（标题/作者/日期） |
| 标签级过滤 | `find_all([...])` 中的 `<aside>` | 删除侧边栏容器 | 安全，`<aside>` 按 HTML 规范就是旁路内容 |
| 后处理清洗 | `strip_junk_containers()` | class/id 模式匹配 + 空壳清理 | 容易过杀，需要验证回归 |
| 元数据补偿 | `make_html_archive()` 的 header_html | 补充选择器跳过但需要的元信息 | 依赖提取准确度 |

## 选择器优先级设计

```
[vue_preload]          # Synology KB 等 Vue 预渲染页面
[itemprop='articleBody']  # ← W3C 标准，XDA/The Verge/CNN 通用
#article-body          # ID 选择器兜底
.article-body          # class 选择器兜底
article                # 通用容器，最后手段
[role='main']          # 语义角色
main                   # HTML5 语义标签
...                    # 更多兜底选择器
body                   # 终极兜底
```

**关键教训**：用 `article` 选择器会匹配到 XDA 的顶层 `<article>` 容器，内含侧边栏/分享按钮/Trending Now 等全部 UI 垃圾。必须用更精确的选择器类（`[itemprop='articleBody']`）优先匹配。

## 后处理清洗函数设计

`strip_junk_containers()` 是内容过滤的核心，对已提取的 content HTML 做二次清理。**顺序很重要**：

### 步骤 1：class/id 垃圾模式匹配（先执行，底层过滤）

```python
_junk_re = re.compile(r'\b(sidebar|sharing|share[-_]|social[-_]|lightbox|'
    r'gallery[-_]lightbox|trending[-_]now|trending|login[-_]|sign[-_]?in|'
    r'sign[-_]?up|newsletter|author[-_]bio|author[-_]box|comment[s]?[-_]|'
    r'ad[-_]|advertisement|sponsor|promoted|follow[-_]|like[-_]btn|'
    r'action[-_]bar|quick[-_]action|cookie[-_]|consent[-_]|popup|modal[-_])\b',
    re.I)
```

删除命中 class 或 id 的元素。

### 步骤 2：data-nosnippet 条件删除（XDA 特殊处理）

**错误做法**：删除所有 `data-nosnippet` 元素 → XDA 用它标记编辑器 Summary块和 Related 卡片 → 误删有价值内容

**正确做法**：仅当 `data-nosnippet` 元素**同时**匹配垃圾 class/id 模式才删除

```python
for el in soup.find_all(attrs={"data-nosnippet": True}):
    classes = " ".join(el.get("class", []))
    el_id = el.get("id", "") or ""
    if _junk_re.search(classes) or _junk_re.search(el_id):
        el.decompose()
```

### 步骤 3：空壳元素清理

删除无文本且无图片/链接/视频的 `<div>` / `<section>` / `<span>`。

### 步骤 4：responsive-img padding-bottom 修复

XDA 等站点用 `padding-bottom: 56.25%` 做图片宽高比占位（配合 absolute 定位的 `<img>`）。离线归档后 `<img>` 不再 absolute，padding 变成大面积空白。

```python
for el in soup.find_all(class_="responsive-img"):
    if el.get("style"):
        el["style"] = re.sub(r'padding-bottom\s*:\s*[\d.]+%?\s*;?', '', el["style"])
```

### 步骤 5：图片冗余属性清理

`srcset`、`data-srcset`、`data-img-url` 在离线归档中无意义（图片已用本地 `src=`），清除以减少 HTML 噪音。

### 步骤 6：Related 卡片冗余元数据清理

Related 卡片内含评论数（`w-display-card-extra` → `<label>Posts</label>`）和重复作者署名（`w-display-card-details`），这些在归档中无意义。

```python
for el in soup.find_all(class_=re.compile(r'\bw-display-card-extra\b|\bw-display-card-details\b')):
    el.decompose()
```

### 步骤 7：Related 卡片 class 替换

原始 `display-card article article-card small no-badge active-content` 等杂乱 class → 替换为干净的单 class `related-card`，配合 CSS 卡片样式渲染。

## 元数据补偿

精确定位选择器（如 `[itemprop='articleBody']`）跳过 article header 区域后，标题/作者/日期需要在 HTML 归档头部补回。

### 作者提取三级兜底

```python
# 1. <meta property="article:author" content="...">
# 2. <meta name="author" content="...">
# 3. DOM: a.article-author, .w-author-name a, [rel='author']  ← XDA 落入此路径
```

### 日期提取

```python
# <meta property="article:published_time" content="2026-06-02T16:47:56Z">
# → reformat 为 "June 02, 2026"
```

### HTML 注入

在 `make_html_archive()` 中，`<body>` 开头注入 `<h1>` + `<div class="article-meta">`（含 author + date），正文内容跟在后面。

## 验证方法

每次修改后对同一篇 XDA 文章运行：

```bash
python3 scripts/full_archive.py \
  "https://www.xda-developers.com/microsoft-new-surface-rtx-spark-dev-box-packs-serious-arm-based-ai-power/" \
  --output /tmp/archive-test --timeout 30
```

### 验证清单

| 检查项 | 应出现 | 不应出现 |
|--------|--------|---------|
| 标题 `<h1>` | 是 | — |
| 作者 + 日期 | By Patrick O'Rourke, June 02, 2026 | — |
| Summary 摘要块 | 3 条 key points | — |
| 正文段落 | RTX Spark Dev Box specs | — |
| 产品实拍图 | `surface-rtx-dev-box-grill.jpg` | — |
| Related 卡片 | Surface Laptop Ultra 推荐 | — |
| 侧边栏 Sign in | — | 否 |
| Follow/Like/Thread 按钮 | — | 否 |
| 社交分享（Facebook/X/...） | — | 否 |
| Trending Now | — | 否 |
| 作者个人简介 | — | 否 |
| Posts 评论数标签 | — | 否 |
| 图片下方大片空白 | — | 否 |

## 已知限制

- **站点特异性的 class 模式**：`emaki-custom-key-points`（XDA Summary）、`display-card`（XDA Related）等是 XDA 特有的。对其他站点的适配需要观察其 DOM 结构并扩展 `_junk_re` 或 `CONTENT_SELECTORS`。
- **原文 top header 图**：XDA 文章的标题背景图（`surface-rtx-spark-dev-box-header.jpg`）在 `<article>` 头部但在 `[itemprop='articleBody']` 之外，当前方案不采集此图。正文内的产品实物图已覆盖。
- **monolith 模式**不受此文件影响——monolith 是全页快照工具，需要配合 `--isolate` 做独立页面但做不了内容筛选。
