---
name: url-collector
description: >
  通用网址收藏技能。接收任意 URL → 提取页面元数据 → 按 resource-metadata 规范生成标准化资源记录 → 可选离线存档。
  支持四种模式：快速收藏 / 深度存档 / 完整网页归档 / 知识库归档（KB-aware：Johnny Decimal 编号 + SITEMAP.md 索引更新）。
  Use when the user wants to "收藏这个网址", "记录这个链接", "保存这个网页", "离线存档",
  "归档到 XX 知识库", "把这个链接加入 KB", "bookmark this URL", "collect this link", "save this webpage",
  or provides a general URL and asks to record/archive it.
  区别于 platform-specific capture（Medium/小红书/Bilibili 等有专门技能），本技能处理无专用采集器的通用网页。
allowed-tools: Read, Write, Edit, Bash, WebFetch, AskUserQuestion
---

# URL Collector — 通用网址收藏

> v1.4.1 · 对标 resource-metadata v2.2 · Dublin Core · schema.org  
> 互补技能：`medium-article-capture`（Medium 专用）· `opencli-kb-bridge`（B站/知乎/微信/YouTube）

## 已知限制

- **HTML 解析**：`collect.sh` 使用 `curl | grep -oPi` 提取元数据，对 JS 渲染的 SPA 页面失效。**首选 WebFetch** 获取页面信息，脚本作为降级方案。
- **内容摘要**：快速收藏 / 深度存档模式下，脚本生成的是占位符 `（请根据实际阅读内容填写...）`。**Claude 必须用 WebFetch 读取页面正文**，生成 2-3 句真实摘要填入记录文件。
- **SPA 页面**：`full_archive.py` 默认使用 `requests` 获取静态 HTML。v1.1.0 起内置智能检测：正文 < 200 chars 时自动启动 Playwright headless Chromium 渲染 JS 页面（需安装 `playwright`，可选依赖）。也可通过 `--js-render force` 强制 Playwright，或 `--js-render off` 跳过。

## 触发条件

- 「收藏这个网址」「记录这个链接」「保存这个网页」
- 「离线存档」「完整保存这个页面」
- 「归档到 XX 知识库」「把这个链接加入 KB」「收录到 KB」
- 「采集内容到 XX」「保持 html 格式」「图片下载到本地」
- 「bookmark this URL」「collect this link」「save this webpage」
- 用户提供任意 URL 并要求记录/归档（无专用采集器的通用网页）

## 四种模式

| 模式 | 触发 | 行为 |
|------|------|------|
| **快速收藏** | "收藏这个网址" / "记录这个链接" | 提取元数据 → resource-metadata 记录文件 → 当前目录 |
| **深度存档** | "离线存档" / "完整保存" | 快速收藏 + monolith 离线 HTML 快照 + 可选全文 Markdown |
| **完整网页归档** | "采集内容到 KB" / "保持 html 格式" | 下载页面+图片→改写路径→生成自包含HTML归档+Markdown资源记录（含全文） |
| **知识库归档** | "归档到 XX 知识库" / "加入 KB" | KB 结构发现 → JD 编号分配 → KB 兼容格式 → 5C 索引更新 |

## 安装

```bash
npx skills add JasonLee2024/url-collector
```

### 依赖

- `agent-browser`（已安装）— 网页信息提取（标题、OG 标签、全文）
- `monolith`（需安装 `cargo install monolith`）— 仅深度存档模式需要
- `resource-metadata`（已安装）— 元数据规范复用
- `playwright`（推荐安装）— JS 动态渲染页面自动 fallback

```bash
# 安装 monolith（仅深度存档模式需要）
cargo install monolith

# 安装 Playwright（推荐，解决新浪/SPA 等 JS 页面采集问题）
pip install playwright && playwright install chromium
```

> `playwright` 为可选依赖。未安装时 `full_archive.py` 自动跳过 JS 渲染，对静态页面无影响。首次遇到 JS 页面时会提示安装。

---

## 工作流 SOP

### 模式一：快速收藏

```
用户提供 URL
  ↓
① 页面信息提取
  - WebFetch 或 agent-browser 获取标题、OG description、站点名、发布日期、语言
  ↓
② 展示元数据预览、确认分类
  - 展示提取到的元数据供用户确认
  - 用户指定分类标签（或自动从 OG tags 推断）
  - 确认 Content Type（article / docs / tool / video / other）
  ↓
③ 生成资源记录文件
  - 运行 collect.sh <URL> [--output <dir>] [--dry-run]
  - 脚本自动提取元数据、类型、标签 → 生成记录文件骨架
  - ⚠️ 脚本内容摘要为占位符，Claude 必须随后填入真实摘要
  ↓
④ 补充内容摘要（Claude 执行）
  - 用 WebFetch 阅读页面正文
  - 在记录文件中将占位符替换为 2-3 句核心内容总结
  ↓
⑤ 索引更新
  - 目标目录 README.md 追加条目
  - SITEMAP.md 同步（如适用）
```

### 模式二：深度存档

```
① 快速收藏流程（同上）
  ↓
② monolith 离线快照
  - monolith --isolate -o {title-slug}.html <URL>
  - 默认输出: ~/AI/web/archive/{title-slug}.html
  ↓
③（可选）全文 Markdown 提取
  - agent-browser 提取正文文本
  - 输出: ~/AI/web/articles/{title-slug}.md
  ↓
④ 回写快照路径到资源记录文件
```

### 模式三：完整网页归档（new in v1.3.0）

```
用户提供 URL + 目标目录
  ↓
① 一键运行 full_archive.py
  - python3 full_archive.py <URL> --output <dir> [--slug-prefix <name>] [--jd-number <XX.XX>]
  - 或通过 collect.sh: collect.sh <URL> --full-archive [--output <dir>] [--slug-prefix <name>]
  - 自动完成: 页面下载 → 元数据提取 → 正文提取 → 图片发现→下载→路径改写
  ↓
② 输出产物（目标目录下）
  - {slug}_网页归档.html       # 自包含 HTML（图片路径已改写为本地 images/ 相对路径）
  - {slug}_网页资源记录.md     # Markdown 资源记录（元数据表 + 内容摘要 + 全文 + 图片引用）
  - images/                     # 下载的图片（按 {prefix}_{N}.{ext} 命名）
  ↓
③ Claude 审核 + 补充
  - 检查自动生成的内容摘要是否准确，必要时修改
  - 补充 Markdown 记录中的标签、分类信息
  ↓
④ 索引更新（如归档到 KB 目录）
  - 类别 README.md 追加条目
  - SITEMAP.md 更新
```

**支持的页面模式**：
- 静态 HTML 页面（通用）
- Vue.js 预加载数据页面（如 Synology KB — 自动从 `preload` JSON 提取正文）
- 后续可通过 `CONTENT_SELECTORS` 扩展其他模式

**依赖**：`requests`, `beautifulsoup4`（Python 标准库外仅此两项，均已预装）

### 模式四：知识库归档

```
用户提供 URL + 目标知识库
  ↓
① Agent 分析 KB 结构 → 推荐归属
  - 执行「Agent KB 结构分析协议」（5 步，详见 references/kb-archive-guide.md 第五节）
    1. 读取 KB 元信息（CLAUDE.md → 区域速查表 → 构建 AreaMap）
    2. 构建 KB 内容图谱（SITEMAP.md → 类别+文件列表 → 构建 CategoryMap）
    3. 分析 URL 内容（标题/OG/正文 → 内容摘要 + 5-10 个主题关键词）
    4. 语义匹配 → 候选排序（URL 关键词 vs CategoryMap → Top-3 候选 + 匹配度）
    5. 推荐 → 用户确认（呈现 Top-3 + 匹配理由 + JD 编号）
  - 脚本辅助：collect.sh --kb <KB> 列出区域/类别/编号
  ↓
② 页面信息提取（同快速收藏）
  ↓
③ 生成 KB 兼容记录文件
  - 编号: {XX.XX}_{title-slug}_网页资源记录.md
  - Frontmatter: Markdown 表格（适配目标 KB 格式，非 YAML）
  - 放置到 <KB>/<区域>/<类别>/
  ↓
④ 深度存档（可选）
  - monolith 快照路径回写到 KB 记录文件
  ↓
⑤ 索引更新（5C 标准）
  - 类别 README.md 追加条目
  - 区域 README.md（如新增类别）
  - SITEMAP.md 更新目录树 + 最近更新表
  - TODO.md（如涉及预留文章）
  - 交叉引用（如涉及相关文章）
```

---

## 文件命名

### 快速收藏 / 深度存档

```
{YYYY-MM-DD}_{title-slug}_网页资源记录.md
```

### 知识库归档

```
{XX.XX}_{title-slug}_网页资源记录.md
```

> `XX.XX` 为 Johnny Decimal 编号，由 Claude 根据 KB 结构分配

---

## KB 兼容 frontmatter 格式

### 快速收藏 / 深度存档（独立目录）

```markdown
# {页面标题} 网页资源记录

> 最后更新：{日期} | 资源类型：通用网页 | 规范版本：v2.2

## 元数据（对标 Dublin Core + schema.org）
...
```

### 知识库归档（KB 内）

```markdown
# {页面标题} 网页资源记录

| 属性 | 值 |
|------|-----|
| 编号 | 41.03 |
| 类型 | 网页资源记录 |
| 来源 | {URL} |
| 收藏日期 | YYYY-MM-DD |
| 语言 | zh / en |
| 难度 | ⭐⭐ |
| 状态 | 🌱 初稿 |
| 采集方式 | url-collector v1.1.0 KB 归档模式 |

## 元数据（对标 Dublin Core + schema.org）
...

## 归档决策记录

- **目标 KB**：{KB路径}
- **分配编号**：{XX.XX}
- **归属区域**：{Area}
- **归属类别**：{Category}
```

---

## 文件结构

```
url-collector/
├── SKILL.md                        # 本文件
├── README.md                       # 概况 + 兼容性 + npx 安装命令
├── CHANGELOG.md                    # 版本变更
├── references/
│   ├── web-page-schema.md          # 通用网页元数据规范
│   └── kb-archive-guide.md         # 知识库归档参考（JD编号+5C索引+KB兼容格式）
├── examples/
│   ├── example-webpage.md          # 快速收藏示范
│   └── example-kb-archive.md       # KB 归档示范
└── scripts/
    ├── collect.sh                  # 一键采集脚本（支持 --kb / --deep / --full-archive 模式）
    └── full_archive.py             # 完整网页归档（页面+图片下载+路径改写+HTML/MD双输出）new in v1.3.0
```

## 与其他技能的关系

| 技能 | 关系 | 说明 |
|------|------|------|
| `resource-metadata` | 下游 | 采集的 URL 按 resource-metadata 规范生成标准化记录 |
| `annotated-commonplace` | 互补 | url-collector 收藏网页，annotated-commonplace 收藏文字片段——不同内容类型的入库通道 |
| `markdown-quality-gate` | 下游 | 生成的 Markdown 自动触发格式门禁 |
| `skill-audit` | 质量验收 | 评分 ≥ 70% 达标 |
