#!/usr/bin/env bash
# =============================================================================
# url-collector collect.sh — 一键网页收藏脚本 v1.4.0
# =============================================================================
# 功能：接收 URL → 提取页面元数据 → 生成标准化 resource-metadata 记录文件
# 支持三种模式：快速收藏 / 深度存档 / 知识库归档
#
# 用法：
#   快速收藏    collect.sh <URL> [--output <dir>] [--category <name>] [--dry-run]
#   深度存档    collect.sh <URL> --deep [--output <dir>] [--dry-run]
#   KB 归档     collect.sh <URL> --kb <kb-path> [--area <name>] [--category <name>] [--deep] [--dry-run]
#   完整网页归档 collect.sh <URL> --full-archive [--output <dir>] [--slug-prefix <name>] [--jd-number <XX.XX>] [--js-render auto|force|off] [--dry-run]
#
# 变更（v1.4.0）：
#   - 新增 --js-render 参数：控制 JS 渲染策略（auto/force/off），传递给 full_archive.py
#
# 变更（v1.3.0）：
#   - 新增 --full-archive 模式：委托 full_archive.py 下载页面+图片+改写路径+生成 HTML/MD 双输出
#
# 变更（v1.2.0）：
#   - 修复 MODE 切换逻辑 bug（--deep 在 kb 模式下失效）
#   - 新增 DO_DEEP 标志，MODE 与存档解耦
#   - 模板代码去重：提取 write_record() 函数
#   - 新增 OG type 内容类型检测
#   - 新增 --dry-run 模式
#   - 新增 meta keywords 标签自动提取
# =============================================================================

set -euo pipefail

# --- 参数解析 ---
URL=""
MODE="quick"      # quick | deep | kb | full_archive
DO_DEEP=false     # 是否执行离线存档（独立于 MODE）
DRY_RUN=false
OUTPUT_DIR="."
CATEGORY=""
KB_PATH=""
AREA_NAME=""
FULL_ARCHIVE=false
SLUG_PREFIX=""
JD_NUM=""
JS_RENDER="auto"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --deep)
            DO_DEEP=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --category)
            CATEGORY="$2"
            shift 2
            ;;
        --kb)
            MODE="kb"
            KB_PATH="$2"
            shift 2
            ;;
        --area)
            AREA_NAME="$2"
            shift 2
            ;;
        --full-archive)
            FULL_ARCHIVE=true
            shift
            ;;
        --slug-prefix)
            SLUG_PREFIX="$2"
            shift 2
            ;;
        --jd-number)
            JD_NUM="$2"
            shift 2
            ;;
        --js-render)
            JS_RENDER="$2"
            shift 2
            ;;
        -*)
            echo "未知选项: $1"
            echo "用法:"
            echo "  快速收藏    collect.sh <URL> [--output <dir>] [--category <name>] [--dry-run]"
            echo "  深度存档    collect.sh <URL> --deep [--output <dir>] [--dry-run]"
            echo "  KB 归档     collect.sh <URL> --kb <kb-path> [--area <name>] [--category <name>] [--deep] [--dry-run]"
            echo "  完整网页归档 collect.sh <URL> --full-archive [--output <dir>] [--slug-prefix <name>] [--jd-number <XX.XX>] [--js-render auto|force|off] [--dry-run]"
            exit 1
            ;;
        *)
            URL="$1"
            shift
            ;;
    esac
done

# 快速收藏 + --deep → 深度存档模式
if [[ "$MODE" == "quick" ]] && $DO_DEEP; then
    MODE="deep"
fi

# --full-archive → 委托 full_archive.py
if $FULL_ARCHIVE; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    FA_SCRIPT="$SCRIPT_DIR/full_archive.py"
    if [[ ! -f "$FA_SCRIPT" ]]; then
        echo "错误：找不到 full_archive.py（期望路径: $FA_SCRIPT）"
        exit 1
    fi

    FA_ARGS=("$URL" --output "$OUTPUT_DIR" --js-render "$JS_RENDER")
    [[ -n "$SLUG_PREFIX" ]] && FA_ARGS+=(--slug-prefix "$SLUG_PREFIX")
    [[ -n "$JD_NUM" ]] && FA_ARGS+=(--jd-number "$JD_NUM")
    $DRY_RUN && FA_ARGS+=(--dry-run)

    echo ">>> 完整网页归档模式 (full-archive)"
    python3 "$FA_SCRIPT" "${FA_ARGS[@]}"
    exit $?
fi

if [[ -z "$URL" ]]; then
    echo "错误：请提供 URL"
    exit 1
fi

# ============================================================
# KB 模式辅助函数
# ============================================================
scan_kb() {
    local kb="$1"
    echo ">>> KB 结构扫描: $kb"

    # 列出所有区域（兼容 XX-XX_Name/ 和 XX_Name/ 两种格式）
    echo "  区域列表:"
    if compgen -G "$kb/[0-9]*_*/" > /dev/null 2>&1; then
        for area in "$kb"/[0-9]*_*/; do
            [[ -d "$area" ]] || continue
            local area_name
            area_name=$(basename "$area")
            echo "    $area_name"
            # 列出该区域下的类别
            if compgen -G "${area}"[0-9]*_*/ > /dev/null 2>&1; then
                for cat_dir in "${area}"[0-9]*_*/; do
                    [[ -d "$cat_dir" ]] || continue
                    local cat_name
                    cat_name=$(basename "$cat_dir")
                    local file_count
                    file_count=$(ls "${cat_dir}"*.md 2>/dev/null | wc -l)
                    local max_id
                    max_id=$(ls "${cat_dir}"*.md 2>/dev/null | sed 's/.*\/\([0-9]*\.[0-9]*\)_.*/\1/' | sort -n | tail -1 || echo "无")
                    echo "      ${cat_name} (${file_count} 文件, 最高编号: ${max_id})"
                done
            fi
        done
    else
        echo "    （未检测到区域目录，请确认 KB 路径）"
    fi

    # 检查 CLAUDE.md
    if [[ -f "$kb/CLAUDE.md" ]]; then
        echo "  ✓ CLAUDE.md 存在"
    else
        echo "  ⚠ CLAUDE.md 不存在（无法获取区域映射）"
    fi

    # 检查 SITEMAP.md
    if [[ -f "$kb/SITEMAP.md" ]]; then
        echo "  ✓ SITEMAP.md 存在"
    else
        echo "  ⚠ SITEMAP.md 不存在"
    fi
}

next_id_in_category() {
    local cat_dir="$1"
    local max_id
    max_id=$(ls "${cat_dir}"*.md 2>/dev/null | sed 's/.*\/\([0-9]*\.[0-9]*\)_.*/\1/' | sort -n | tail -1 || echo "")
    if [[ -z "$max_id" ]]; then
        echo ""
        return
    fi
    local major=$(echo "$max_id" | cut -d. -f1)
    local minor=$(echo "$max_id" | cut -d. -f2)
    printf "%s.%02d" "$major" "$((10#$minor + 1))"
}

list_all_categories() {
    local kb="$1"
    echo "  所有类别:"
    if compgen -G "$kb/[0-9]*_*/" > /dev/null 2>&1; then
        for area in "$kb"/[0-9]*_*/; do
            [[ -d "$area" ]] || continue
            local area_name
            area_name=$(basename "$area")
            if compgen -G "${area}"[0-9]*_*/ > /dev/null 2>&1; then
                for cat_dir in "${area}"[0-9]*_*/; do
                    [[ -d "$cat_dir" ]] || continue
                    local cat_name
                    cat_name=$(basename "$cat_dir")
                    echo "    ${area_name}/${cat_name}"
                done
            fi
        done
    else
        echo "    （未检测到类别目录）"
    fi
}

# ============================================================
# 元数据提取
# ============================================================
extract_metadata() {
    # 返回变量：TITLE, DESCRIPTION, SITE_NAME, PUBLISH_DATE, LANGUAGE, OG_TYPE, TAGS
    local url="$1"

    echo ">>> 提取页面元数据: $url"

    HTML=$(curl -sL --max-time 15 -A "Mozilla/5.0" "$url" 2>/dev/null || true)

    if [[ -z "$HTML" ]]; then
        echo "警告：无法获取页面内容，仅记录 URL"
        TITLE="$url"
        DESCRIPTION="（未能获取页面内容）"
        SITE_NAME=""
        PUBLISH_DATE=""
        LANGUAGE="unknown"
        OG_TYPE=""
        TAGS=""
        return
    fi

    # 标准元数据提取
    TITLE=$(echo "$HTML" | grep -oPi '<title[^>]*>\K[^<]+' | head -1 | sed 's/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&#39;/'"'"'/g' || echo "$url")
    DESCRIPTION=$(echo "$HTML" | grep -oPi '<meta[^>]*property="og:description"[^>]*content="\K[^"]+' | head -1 | sed 's/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&#39;/'"'"'/g' || echo "（无描述）")
    SITE_NAME=$(echo "$HTML" | grep -oPi '<meta[^>]*property="og:site_name"[^>]*content="\K[^"]+' | head -1 | sed 's/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&#39;/'"'"'/g' || echo "")
    PUBLISH_DATE=$(echo "$HTML" | grep -oPi '<meta[^>]*property="article:published_time"[^>]*content="\K[^"]+' | head -1 || echo "")
    LANGUAGE=$(echo "$HTML" | grep -oPi '<html[^>]*lang="\K[^"]+' | head -1 || echo "unknown")

    # OG type 检测（用于内容类型判定）
    OG_TYPE=$(echo "$HTML" | grep -oPi '<meta[^>]*property="og:type"[^>]*content="\K[^"]+' | head -1 || echo "")

    # Meta keywords 提取
    TAGS=$(echo "$HTML" | grep -oPi '<meta[^>]*name="keywords"[^>]*content="\K[^"]+' | head -1 | sed 's/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g; s/&quot;/"/g; s/&#39;/'"'"'/g' || echo "")

    echo "  标题: $TITLE"
    echo "  摘要: ${DESCRIPTION:0:80}..."
    echo "  站点: ${SITE_NAME:-（未获取）}"
    echo "  语言: $LANGUAGE"
    [[ -n "$OG_TYPE" ]] && echo "  OG type: $OG_TYPE"
    [[ -n "$TAGS" ]] && echo "  Tags: $TAGS"
}

# ============================================================
# 内容类型推断（URL 模式 + OG type）
# ============================================================
infer_content_type() {
    local url="$1"
    local og_type="$2"

    # 优先使用 OG type
    if [[ -n "$og_type" ]]; then
        case "$(echo "$og_type" | tr '[:upper:]' '[:lower:]')" in
            article|blogposting|newsarticle) echo "article"; return ;;
            video*)                           echo "video"; return ;;
            product)                          echo "tool"; return ;;
            website)                          ;;  # 继续 URL 推断
        esac
    fi

    # URL 模式推断
    if echo "$url" | grep -qiE '(docs|documentation|reference|guide|book|tutorial)'; then
        echo "docs"
    elif echo "$url" | grep -qiE '(blog|article|post|medium|dev\.to)'; then
        echo "article"
    elif echo "$url" | grep -qiE '(youtube|bilibili|vimeo|video)'; then
        echo "video"
    elif echo "$url" | grep -qiE '(tool|app|playground|generator|converter)'; then
        echo "tool"
    else
        echo "other"
    fi
}

# ============================================================
# 标签自动提取（meta keywords 不足时从标题补充）
# ============================================================
generate_tags() {
    local title="$1"
    local meta_keywords="$2"

    if [[ -n "$meta_keywords" ]]; then
        echo "$meta_keywords"
        return
    fi

    # 从标题提取候选关键词（取 3-5 个英文单词 + 中文词组）
    # 英文：过滤常见停用词，取 ≥4 字符的单词
    local en_words
    en_words=$(echo "$title" | grep -oP '[A-Za-z]{4,}' | grep -viE '^(this|that|with|from|about|over|into|through|when|where|which|what|there|their|have|been|were|they|will|would|could|should|also|just|more|some|other|each|every)$' | tr '\n' ', ' | sed 's/, $//')

    # 中文：取 2-4 字的连续中文字符
    local zh_words
    zh_words=$(echo "$title" | grep -oP '[\x{4e00}-\x{9fff}]{2,4}' | tr '\n' ', ' | sed 's/, $//')

    if [[ -n "$en_words" ]] && [[ -n "$zh_words" ]]; then
        echo "$zh_words, $en_words"
    elif [[ -n "$en_words" ]]; then
        echo "$en_words"
    elif [[ -n "$zh_words" ]]; then
        echo "$zh_words"
    else
        echo ""
    fi
}

# ============================================================
# 生成 slug
# ============================================================
make_slug() {
    local title="$1"
    echo "$title" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//' | cut -c1-60
}

# ============================================================
# 统一记录文件生成函数（KB 模式 / 快速收藏 / 深度存档 共用）
# ============================================================
write_record() {
    local output_file="$1"
    local mode="$2"           # "kb" | "quick" | "deep"
    local jd_number="$3"      # KB 模式时有值
    local tags="$4"
    local snapshot="${5:-}"   # 离线快照路径

    local snapshot_line=""
    [[ -n "$snapshot" ]] && snapshot_line="- 离线快照：${snapshot}"

    # 通用元数据表（所有模式共用）
    local metadata_table
    metadata_table=$(cat <<META
| 维度 | 字段（中） | 字段（EN） | 值 | 对标标准 |
|:------|:-----|:-----|:-----|:-----|
| 标识 | 页面标题 | Title | ${TITLE} | dc:title, schema:headline |
| 标识 | 页面地址 | URL | ${URL} | dc:identifier, schema:url |
| 描述 | 摘要 | Description | ${DESCRIPTION} | dc:description, schema:abstract |
| 归属 | 站点名称 | Site Name | ${SITE_NAME:-—} | dc:publisher, schema:publisher |
| 归属 | 作者 | Author | — | dc:creator, schema:author |
| 时间 | 收藏日期 | Date Collected | ${DATE} | dc:created |
| 时间 | 发布日期 | Publish Date | ${PUBLISH_DATE:--} | dc:issued, schema:datePublished |
| 语言 | 页面语言 | Language | ${LANGUAGE} | dc:language, schema:inLanguage |
| 主题 | 标签 | Tags | ${tags:--} | dc:subject, schema:keywords |
| 分类 | 用户分类 | Category | ${CATEGORY:--} | dc:type |
| 格式 | 内容类型 | Content Type | ${CONTENT_TYPE} | dc:format, schema:genre |
| 关联 | 离线快照 | Snapshot Path | ${snapshot:--} | dc:relation |
| 关联 | 关联知识库 | Related KB | $([[ "$mode" == "kb" ]] && echo "${KB_PATH}" || echo "—") | dc:relation |
META
)

    if [[ "$mode" == "kb" ]] && [[ -n "$jd_number" ]]; then
        # KB 归档模式：Markdown 表格 frontmatter + 元数据表 + 归档决策
        cat <<RECORD
# ${TITLE} 网页资源记录

| 属性 | 值 |
|------|-----|
| 编号 | ${jd_number} |
| 类型 | 网页资源记录 |
| 来源 | ${URL} |
| 收藏日期 | ${DATE} |
| 语言 | ${LANGUAGE} |
| 难度 | ⭐⭐ |
| 状态 | 🌱 初稿 |
| 采集方式 | url-collector v1.2.0 KB 归档模式 |

## 元数据（对标 Dublin Core + schema.org）

${metadata_table}

## 获取方式

- 在线访问：${URL}
${snapshot_line}

## 归档决策记录

- **目标 KB**：${KB_PATH}
- **分配编号**：${jd_number}
- **归属区域**：${AREA_NAME:--}
- **归属类别**：${CATEGORY:--}

## 内容摘要

（请根据实际阅读内容填写 2-3 句话的页面核心内容总结）
RECORD
    else
        # 快速收藏 / 深度存档模式
        cat <<RECORD
# ${TITLE} 网页资源记录

> 最后更新：${DATE} | 资源类型：通用网页 | 规范版本：v2.2

## 元数据（对标 Dublin Core + schema.org）

${metadata_table}

## 获取方式

- 在线访问：${URL}
${snapshot_line}

## 内容摘要

（请根据实际阅读内容填写 2-3 句话的页面核心内容总结）
RECORD
    fi
}

# ============================================================
# 主流程
# ============================================================

# Step 1：提取元数据
extract_metadata "$URL"

# Step 2：推断内容类型
CONTENT_TYPE=$(infer_content_type "$URL" "$OG_TYPE")

# Step 3：生成标签
TAGS=$(generate_tags "$TITLE" "$TAGS")

# Step 4：生成 slug + 日期
SLUG=$(make_slug "$TITLE")
DATE=$(date +%Y-%m-%d)

# Step 5：KB 模式扫描
JD_NUMBER=""
if [[ "$MODE" == "kb" ]]; then
    if [[ ! -d "$KB_PATH" ]]; then
        echo "错误：知识库路径不存在: $KB_PATH"
        exit 1
    fi

    scan_kb "$KB_PATH"

    echo ""
    echo "--- KB 归档辅助信息 ---"

    list_all_categories "$KB_PATH"

    if [[ -n "$AREA_NAME" ]] && [[ -n "$CATEGORY" ]]; then
        AREA_DIR=$(ls -d "$KB_PATH"/*"$AREA_NAME"*/ 2>/dev/null | head -1 || echo "")
        if [[ -z "$AREA_DIR" ]]; then
            echo "警告：未找到匹配区域 '$AREA_NAME'"
        else
            CAT_DIR=$(ls -d "${AREA_DIR}"*"$CATEGORY"*/ 2>/dev/null | head -1 || echo "")
            if [[ -z "$CAT_DIR" ]]; then
                echo "警告：未找到匹配类别 '$CATEGORY'，可能需要新建"
            else
                JD_NUMBER=$(next_id_in_category "$CAT_DIR")
                echo "  目标类别: $(basename "$CAT_DIR")"
                echo "  分配编号: $JD_NUMBER"
                OUTPUT_DIR="$CAT_DIR"
            fi
        fi
    else
        echo "  未指定 --area / --category，请 Claude 做主题匹配决策"
    fi

    echo "  KB 路径: $KB_PATH"
    echo "  模式: KB 归档"
fi

# Step 6：深度存档（独立于 MODE）
SNAPSHOT_PATH=""
if $DO_DEEP; then
    ARCHIVE_DIR="$HOME/AI/web/archive"
    mkdir -p "$ARCHIVE_DIR"

    if command -v monolith &>/dev/null; then
        echo ">>> monolith 离线存档..."
        monolith --isolate -o "$ARCHIVE_DIR/${SLUG}.html" "$URL"
        SNAPSHOT_PATH="$ARCHIVE_DIR/${SLUG}.html"
        echo "  快照: $SNAPSHOT_PATH"
    else
        echo "警告：monolith 未安装，跳过离线存档"
        echo "  安装：cargo install monolith"
    fi
fi

# Step 7：生成记录文件
if [[ "$MODE" == "kb" ]] && [[ -n "$JD_NUMBER" ]]; then
    OUTPUT_FILE="$OUTPUT_DIR/${JD_NUMBER}_${SLUG}_网页资源记录.md"
else
    OUTPUT_FILE="$OUTPUT_DIR/${DATE}_${SLUG}_网页资源记录.md"
fi

if $DRY_RUN; then
    echo ""
    echo "=== DRY RUN — 以下为将写入的内容 ==="
    write_record "$OUTPUT_FILE" "$MODE" "$JD_NUMBER" "$TAGS" "$SNAPSHOT_PATH"
    echo "=== DRY RUN 结束 ==="
    echo "  目标文件: $OUTPUT_FILE"
else
    write_record "$OUTPUT_FILE" "$MODE" "$JD_NUMBER" "$TAGS" "$SNAPSHOT_PATH" > "$OUTPUT_FILE"
    echo ">>> 资源记录已生成: $OUTPUT_FILE"
    if [[ "$MODE" == "kb" ]]; then
        echo ">>> 编号: $JD_NUMBER"
        echo ">>> 下一步：Claude 做 SITEMAP.md + README.md 索引更新"
    else
        echo ">>> 请检查并补充：标签(Tags)、作者(Author)、分类(Category)、内容摘要"
    fi
fi
