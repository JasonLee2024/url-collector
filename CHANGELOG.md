# CHANGELOG

## v1.4.0 (2026-05-26)

### 新功能：Playwright JS 渲染 fallback

- `full_archive.py` 升级至 v1.1.0，新增 Playwright headless Chromium 渲染层
  - `fetch_page_playwright()`：启动 headless Chromium 渲染 JS 页面
  - `_has_substantial_content()`：自动检测正文是否充足（阈值 200 chars）
  - 智能 fallback 策略：`requests` 获取 → 正文 < 200 chars → 自动 Playwright
  - 新增 `--js-render` 参数：`auto`（默认）/ `force`（强制 Playwright）/ `off`（仅 requests）
  - Playwright 为可选依赖，未安装时自动跳过并继续用静态 HTML
- 解决了新浪财经、Vue/React SPA 等 JS 动态渲染页面的正文提取问题
- HTML 归档页脚新增渲染方式标注：`Playwright (JS)` / `requests (static)`

### 文档更新

- SKILL.md 「已知限制」更新，移除 SPA 硬性限制描述
- SKILL.md 版本号 v1.3.0 → v1.4.0

## v1.3.0 (2026-05-24)

### 新功能：完整网页归档（full-archive）

- 新增 `scripts/full_archive.py`：完整网页归档 Python 脚本
  - 下载页面 HTML + 自动发现所有 `<img>` 标签 → 下载图片 → 本地 `images/` 目录
  - 图片路径自动改写为本地相对路径（`images/xxx.png`）
  - 双输出：自包含 HTML 归档（`_网页归档.html`）+ Markdown 资源记录（`_网页资源记录.md`，含全文）
  - 支持 `--slug-prefix` / `--jd-number` / `--img-prefix` / `--dry-run` 参数
  - 内置 HTML→Markdown 转换器（无外部依赖）
  - 内置 Vue preload JSON 提取器（兼容 Synology KB 等站点）
  - 多策略正文提取（CSS selector 优先 + body 降级）
- `collect.sh` 新增 `--full-archive` 模式，自动委托 `full_archive.py`
  - 新增 `--slug-prefix` / `--jd-number` 参数支持
- 依赖：`requests` + `beautifulsoup4`（Python 标准库外仅此两项，均已预装）

### 文档更新

- SKILL.md 版本升级至 v1.3.0，模式表由 3 种扩展为 4 种
- 新增「模式三：完整网页归档」SOP（5 步）
- 新增 SPA/Vue preload 页面支持说明
- README.md 版本号及最新更新条目更新
- `scripts/collect.sh` 注释头更新至 v1.3.0

### 技能目录变更

```
scripts/full_archive.py  ← 新增（~450 行）
scripts/collect.sh       ← 修改（+~15 行，新增 --full-archive 委托逻辑）
SKILL.md                 ← 修改（版本 + 第四种模式 SOP + 已知限制更新）
README.md                ← 修改（版本 + 模式数量更新）
CHANGELOG.md             ← 修改（本文件）
```

## v1.2.0 (2026-05-18)

### 缺陷修复
- 修复 `collect.sh` MODE 切换逻辑 bug（`MODE="${MODE%/kb}"` 永为空操作），改为 `DO_DEEP` 布尔标志
- `--deep` 标志现在可在 KB 模式下正常工作（KB + 离线存档）

### 代码质量
- 模板代码去重：提取 `write_record()` 统一函数，消除 ~70 行重复 heredoc
- 新增 `quality_gate.py`（四道门禁：语法/文档/CLI/参考规范）
- `quality_gate.py` 已加入 `REQUIRED_FILES` 列表

### 功能增强
- 新增 `--dry-run` 模式：输出内容到 stdout 而非写入文件
- 内容类型检测加入 OG type 标签（`og:type=article` → `article`），优先级高于 URL 模式推断
- 标签自动提取：优先 `meta keywords`，降级为标题关键词提取（英文过滤停用词+中文词组）
- `MODE` 与存档解耦：`DO_DEEP` 独立控制离线存档

### 协议升级（kb-archive-guide.md）
- 匹配权重修正因子：饱和度惩罚（≥8篇）、活跃度奖励（30天内更新）、新鲜度惩罚（90天无更新）
- 新增 LOW-GATE "不应归档"判定协议：全 LOW 匹配时强制警告
- Top-3 候选输出增加饱和度/最近更新标注

### 文档改进（SKILL.md）
- 新增「已知限制」节：HTML 解析局限性 + WebFetch 首选建议
- SOP 步骤④ 显式化「补充内容摘要」：Claude 须用 WebFetch 阅读正文并填入真实摘要
- 版本号更新至 v1.2.0

- 新增「Agent KB 结构分析协议」（`references/kb-archive-guide.md` 第五节）
  - 5 步协议：元信息→内容图谱→URL分析→语义匹配→推荐确认
  - 结构化输出：Top-3 候选 + 匹配度 + JD 编号
  - Agent 检查清单
- 升级 SITEMAP.md 解析策略：树形/表格两种格式的提取方法
- `SKILL.md` 步骤① ② 合并为「Agent 分析 KB 结构→推荐归属」一步

## v1.1.0 (2026-05-18)

- 新增知识库归档模式：KB 结构自动发现（CLAUDE.md / SITEMAP.md / TODO.md）
- Johnny Decimal 编号分配算法（语义匹配 + 最高 ID + 0.01）
- KB 兼容 frontmatter 格式（Markdown 表格，适配目标 KB）
- 5C 索引更新协议（类别/区域 README + SITEMAP.md + TODO.md + 交叉引用）
- 新增 `references/kb-archive-guide.md`：JD 编号规则 + 5C 协议 + 关键词匹配策略
- 新增 `examples/example-kb-archive.md`：完整 KB 归档示范
- `scripts/collect.sh` 升级：新增 `--kb` / `--area` / `--category` 参数 + KB 扫描函数
- `SKILL.md` 重构：三种模式 × 各自 SOP × KB 兼容模板

## v1.0.0 (2026-05-18)

- 初版发布
- 快速收藏模式：URL → 元数据提取 → 标准化 resource-metadata 记录文件
- 深度存档模式：快速收藏 + monolith 离线 HTML 快照 + 可选全文 Markdown
- 通用网页元数据规范（resource-metadata v2.2 资源类型六）
- `scripts/collect.sh` 一键采集脚本
- 参考 public skills：`maragudk/skills@save-web-page` + `yangsonhung/awesome-agent-skills@topic-bookmarks-reorganizer-cn`
