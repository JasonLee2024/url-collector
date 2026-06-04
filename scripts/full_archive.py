#!/usr/bin/env python3
# =============================================================================
# url-collector full_archive.py — 完整网页归档脚本 v1.2.0
# =============================================================================
# 功能：接收 URL → 下载页面 → 下载所有图片 → 改写路径 →
#       生成自包含 HTML 归档 + Markdown 资源记录（含全文）
#
# 用法：
#   python3 full_archive.py <URL> --output <dir> [options]
#
# 输出（目标目录下）：
#   {slug}_网页归档.html          # 自包含 HTML（图片路径已改写为本地相对路径）
#   {slug}_网页资源记录.md        # Markdown 资源记录（元数据 + 全文 + 图片引用）
#   images/                        # 下载的图片
#
# 依赖：requests, beautifulsoup4
# 可选依赖：playwright（JS 渲染页面自动 fallback，未安装则跳过）
#
# 变更（v1.2.0）：
#   - 新增 strip_junk_containers() 后处理：删除 data-nosnippet / sidebar / sharing /
#     trending / lightbox / login 等 UI 垃圾容器，自动清理空壳元素
#   - CONTENT_SELECTORS 新增 [itemprop='articleBody'] / #article-body / .article-body，
#     主流新闻站精确定位正文区域（XDA、The Verge、CNN 等）
#   - 三处过滤标签列表加入 <aside>（_has_substantial_content / extract_main_content /
#     body fallback）
#   - 删除全页图片补充下载逻辑（避免下载侧边栏/推荐阅读缩略图）
#
# 变更（v1.1.0）：
#   - 新增 Playwright JS 渲染 fallback：requests 获取静态 HTML 后自动检测正文量，
#     若 <200 chars 则自动启动 headless Chromium 渲染再提取
#   - 新增 --js-render 参数（auto/force/off），控制 JS 渲染策略
# =============================================================================

import argparse
import html as html_mod
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

VERSION = "1.1.0"

# ── Playwright availability ──────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# ── User-Agent for requests ──────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ═══════════════════════════════════════════════════════════════════════
# 1. Page download & metadata extraction
# ═══════════════════════════════════════════════════════════════════════

def fetch_page(url, timeout=30):
    """Download page HTML. Returns (raw_html, final_url)."""
    resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    # Detect encoding
    resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
    return resp.text, resp.url


def _has_substantial_content(html_text, min_body_chars=200):
    """Check if the page has enough body text (not just a JS shell)."""
    soup = BeautifulSoup(html_text, "html.parser")
    # Remove script/style/noscript
    for tag in soup.find_all(["script", "style", "noscript", "meta", "link", "aside"]):
        tag.decompose()
    body = soup.find("body")
    text = body.get_text() if body else soup.get_text()
    # Count meaningful chars (non-whitespace)
    meaningful = len(re.sub(r'\s+', '', text))
    return meaningful >= min_body_chars


def fetch_page_playwright(url, timeout=30):
    """Render page with headless Chromium for JS-heavy pages.
    Returns (raw_html, final_url). Falls back gracefully if Playwright unavailable.
    """
    if not HAS_PLAYWRIGHT:
        print("  ⚠ Playwright 未安装，跳过 JS 渲染（pip install playwright && playwright install chromium）")
        return None, url

    print("  ⏳ 启动 headless Chromium 渲染 JS 页面...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            # Wait a bit more for any lazy-loaded content
            time.sleep(2)
            html = page.content()
            final_url = page.url
            browser.close()
            print(f"  ✓ Playwright 渲染完成: {len(html)} bytes")
            return html, final_url
    except Exception as e:
        print(f"  ✗ Playwright 渲染失败: {e}")
        return None, url


def extract_metadata(soup, url):
    """Extract metadata from BeautifulSoup-parsed page."""
    meta = {
        "title": "",
        "description": "",
        "site_name": "",
        "publish_date": "",
        "language": "",
        "tags": [],
        "og_type": "",
        "author": "",
    }

    # Title: og:title > <title>
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        meta["title"] = og_title["content"].strip()
    if not meta["title"]:
        title_tag = soup.find("title")
        meta["title"] = title_tag.get_text(strip=True) if title_tag else url

    # Description: og:description > meta description
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        meta["description"] = og_desc["content"].strip()
    if not meta["description"]:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            meta["description"] = meta_desc["content"].strip()

    # Site name
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        meta["site_name"] = og_site["content"].strip()

    # Publish date
    for prop in ["article:published_time", "article:modified_time"]:
        tag = soup.find("meta", property=prop)
        if tag and tag.get("content"):
            meta["publish_date"] = tag["content"].strip()
            break

    # Language
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        meta["language"] = html_tag["lang"].strip()

    # OG type
    og_type = soup.find("meta", property="og:type")
    if og_type and og_type.get("content"):
        meta["og_type"] = og_type["content"].strip()

    # Author: article:author > meta name="author" > .article-author link text
    art_author = soup.find("meta", property="article:author")
    if art_author and art_author.get("content"):
        meta["author"] = art_author["content"].strip()
    if not meta["author"]:
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            meta["author"] = meta_author["content"].strip()
    if not meta["author"]:
        author_link = soup.select_one("a.article-author, .w-author-name a, [rel='author']")
        if author_link:
            meta["author"] = author_link.get_text(strip=True)

    # Tags: meta keywords
    kw_tag = soup.find("meta", attrs={"name": "keywords"})
    if kw_tag and kw_tag.get("content"):
        meta["tags"] = [t.strip() for t in kw_tag["content"].split(",") if t.strip()]

    return meta


# ═══════════════════════════════════════════════════════════════════════
# 2. Content extraction
# ═══════════════════════════════════════════════════════════════════════

# Priority selectors for finding the main article content
CONTENT_SELECTORS = [
    # Synology KB: Vue preload data
    ("vue_preload", None),
    # Semantic article body selectors (HTML5 microdata, mainstream news sites)
    ("[itemprop='articleBody']", None),
    ("#article-body", None),
    (".article-body", None),
    # Common article containers
    ("article", None),
    ("[role='main']", None),
    ("main", None),
    (".article-content", None),
    (".post-content", None),
    (".entry-content", None),
    (".content", None),
    (".markdown-body", None),
    (".kb_accordion_container", None),
    ("#content", None),
    (".document", None),
    ("body", None),  # fallback
]


def extract_vue_preload(soup):
    """Extract article content from Vue.js preload JSON (Synology KB pattern)."""
    for script in soup.find_all("script"):
        if not script.string:
            continue
        m = re.search(r'"preload":(\{.*?"doc_date":"\d+"\})', script.string)
        if m:
            try:
                preload = json.loads(m.group(1))
                content = preload.get("content", "")
                if content:
                    content = html_mod.unescape(content)
                    return content, preload
            except (json.JSONDecodeError, KeyError):
                continue
    return None, None


def extract_main_content(soup, html_text):
    """Extract the main article body as HTML string."""
    # Strategy 1: Vue preload (Synology KB)
    content, preload = extract_vue_preload(soup)
    if content:
        return content, "vue_preload", preload

    # Strategy 2: CSS selector scan
    for selector, _ in CONTENT_SELECTORS:
        if selector == "vue_preload":
            continue
        el = soup.select_one(selector)
        if el:
            # Remove script/style tags
            for tag in el.find_all(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = str(el)
            if len(text.strip()) > 100:
                text = strip_junk_containers(text)
                return text, selector, None

    # Fallback: use body, strip nav/footer/header/script/aside
    body = soup.find("body")
    if body:
        for tag in body.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return strip_junk_containers(str(body)), "body", None

    return html_text, "raw", None


# ── Content cleanup ──────────────────────────────────────────────────

def strip_junk_containers(content_html):
    """Post-extraction cleanup: remove UI chrome, sidebars, trending sections, etc."""
    soup = BeautifulSoup(content_html, "html.parser")

    # 1. Remove elements whose class/id match known junk patterns (main cleanup)
    _junk_re = re.compile(
        r'\b(sidebar|sharing|share[-_]|social[-_]|lightbox|gallery[-_]lightbox|'
        r'trending[-_]now|trending|login[-_]|sign[-_]?in|sign[-_]?up|newsletter|'
        r'author[-_]bio|author[-_]box|'
        r'comment[s]?[-_]|ad[-_]|advertisement|sponsor|promoted|'
        r'follow[-_]|like[-_]btn|action[-_]bar|quick[-_]action|'
        r'cookie[-_]|consent[-_]|popup|modal[-_])\b',
        re.I
    )
    for el in soup.find_all(class_=_junk_re):
        el.decompose()
    for el in soup.find_all(id=_junk_re):
        el.decompose()

    # 2. Remove data-nosnippet elements that ALSO match junk patterns
    #    (XDA uses data-nosnippet on both UI chrome AND editor-added summary blocks,
    #     so we only remove those with junk class/id — not all data-nosnippet)
    for el in soup.find_all(attrs={"data-nosnippet": True}):
        classes = " ".join(el.get("class", []))
        el_id = el.get("id", "") or ""
        if _junk_re.search(classes) or _junk_re.search(el_id):
            el.decompose()

    # 3. Remove empty wrapper elements (divs/sections/spans with no text and no media)
    for el in soup.find_all(["div", "section", "span"]):
        if not el.get_text(strip=True) and not el.find(["img", "a", "video", "iframe", "picture"]):
            el.decompose()

    # 4. Fix responsive-img padding-bottom placeholders (used by XDA for aspect ratio).
    #    In archived HTML these become large empty gaps since the img is no longer
    #    absolutely positioned. Remove the padding-bottom to collapse the gap.
    for el in soup.find_all(class_="responsive-img"):
        if el.get("style"):
            el["style"] = re.sub(r'padding-bottom\s*:\s*[\d.]+%?\s*;?', '', el["style"])
            if not el["style"].strip():
                del el["style"]

    # 5. Remove stray data-srcset/srcset attributes that are noise in offline archives
    #    (images used local src= paths, leftover srcset/data-srcset from <picture>/<source>)
    for el in soup.find_all(["source", "img"]):
        for attr in ["data-srcset", "data-img-url", "srcset"]:
            if el.has_attr(attr):
                del el[attr]

    # 6. Strip stale metadata inside display-cards (comment counts, author bylines
    #    duplicated from the main article header, etc.)
    for el in soup.find_all(class_=re.compile(r'\bw-display-card-extra\b|\bw-display-card-details\b')):
        el.decompose()

    # 7. Mark Related-article display-card blocks with a clean wrapper class
    #    so CSS can give them visual separation from the main article body.
    for el in soup.find_all(class_=re.compile(r'\bdisplay-card\b')):
        el["class"] = ["related-card"]

    return str(soup)


# ═══════════════════════════════════════════════════════════════════════
# 3. Image download & path rewriting
# ═══════════════════════════════════════════════════════════════════════

def resolve_image_urls(soup_or_html, base_url):
    """Find all image URLs in the HTML content. Returns list of (original_url, resolved_url)."""
    if isinstance(soup_or_html, str):
        s = BeautifulSoup(soup_or_html, "html.parser")
    else:
        s = soup_or_html

    images = []
    seen = set()
    for img in s.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        # Resolve relative URL
        resolved = urljoin(base_url, src)
        if resolved not in seen:
            seen.add(resolved)
            images.append((src, resolved))
    return images


def download_images(image_list, output_dir, prefix="img", timeout=30):
    """Download images to output_dir/images/. Returns dict mapping original_src -> local_filename."""
    if not image_list:
        return {}

    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    mapping = {}
    for idx, (orig_src, resolved_url) in enumerate(image_list, 1):
        try:
            resp = requests.get(resolved_url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()

            # Determine extension from Content-Type or URL
            ct = resp.headers.get("Content-Type", "")
            ext = ".png"  # default
            if "jpeg" in ct or "jpg" in ct:
                ext = ".jpg"
            elif "gif" in ct:
                ext = ".gif"
            elif "svg" in ct:
                ext = ".svg"
            elif "webp" in ct:
                ext = ".webp"
            else:
                # Fallback to URL extension
                parsed = urlparse(resolved_url)
                path_ext = os.path.splitext(parsed.path)[1].lower()
                if path_ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"):
                    ext = path_ext
                    if ext == ".jpeg":
                        ext = ".jpg"

            fname = f"{prefix}_{idx}{ext}"
            fpath = os.path.join(img_dir, fname)
            with open(fpath, "wb") as f:
                f.write(resp.content)

            mapping[orig_src] = fname
            print(f"  ✓ 图片 {idx}: {fname} ({len(resp.content)} bytes)")

        except requests.RequestException as e:
            print(f"  ✗ 图片 {idx} 下载失败: {resolved_url} — {e}")
            mapping[orig_src] = None

    return mapping


def rewrite_image_paths(html_content, mapping, img_subdir="images"):
    """Rewrite image src paths in HTML from original URLs to local paths."""
    result = html_content
    for orig_src, local_name in mapping.items():
        if local_name is None:
            continue
        new_path = f"{img_subdir}/{local_name}"

        # Try multiple quoting patterns
        # Double quotes
        result = result.replace(f'src="{orig_src}"', f'src="{new_path}"')
        result = result.replace(f"src='{orig_src}'", f"src='{new_path}'")
        # HTML entity variants
        escaped = orig_src.replace("&", "&amp;")
        if escaped != orig_src:
            result = result.replace(f'src="{escaped}"', f'src="{new_path}"')

    return result


# ═══════════════════════════════════════════════════════════════════════
# 4. HTML-to-Markdown converter (minimal, no external dependency)
# ═══════════════════════════════════════════════════════════════════════

def _md_escape(text):
    """Escape special Markdown characters in plain text."""
    return text.replace("\\", "\\\\")


def _inline_convert(el):
    """Convert inline elements to Markdown."""
    if el.name is None:
        # Plain text / NavigableString
        return el.string or ""

    text = ""
    for child in el.children:
        if child.name is None:
            text += str(child) if child else ""
        elif child.name in ("strong", "b"):
            text += f"**{_inline_convert(child)}**"
        elif child.name in ("em", "i"):
            text += f"*{_inline_convert(child)}*"
        elif child.name == "code":
            text += f"`{child.get_text()}`"
        elif child.name == "a":
            href = child.get("href", "")
            inner = _inline_convert(child)
            if href:
                text += f"[{inner}]({href})"
            else:
                text += inner
        elif child.name == "img":
            alt = child.get("alt", "")
            src = child.get("src", "")
            text += f"![{alt}]({src})"
        elif child.name == "br":
            text += "\n"
        elif child.name == "span":
            text += _inline_convert(child)
        elif child.name in ("ul", "ol", "div", "section", "dl", "details"):
            # Nested block inside inline — recurse to catch images/links within
            text += " " + _inline_convert(child) + " "
        else:
            # Unknown element — extract text preserving inline children
            if child.find(["img", "a", "strong", "em", "code"]):
                text += " " + _inline_convert(child) + " "
            else:
                text += child.get_text() if child else ""
    return text


def html_to_markdown(html_content):
    """Convert HTML body content to Markdown."""
    soup = BeautifulSoup(html_content, "html.parser")
    lines = []
    _block_convert(soup, lines, depth=0)
    return "\n".join(lines)


def _block_convert(el, lines, depth=0):
    """Convert block-level elements, appending lines."""
    if el.name is None:
        text = str(el).strip()
        if text:
            lines.append(text)
        return

    for child in el.children:
        if child.name is None:
            text = str(child).strip()
            if text:
                lines.append(text)
            continue

        tag = child.name.lower() if child.name else ""

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            heading_text = _inline_convert(child).strip()
            if heading_text:
                # Remove anchor IDs if present
                heading_text = re.sub(r'\s*<a[^>]*></a>\s*', '', heading_text)
                lines.append(f"\n{'#' * level} {heading_text}")

        elif tag == "p":
            text = _inline_convert(child).strip()
            if text:
                lines.append(f"\n{text}")

        elif tag in ("ul", "ol"):
            lines.append("")
            _list_convert(child, lines, tag == "ol", depth + 1)
            lines.append("")

        elif tag == "blockquote":
            text = _inline_convert(child).strip()
            if text:
                lines.append(f"\n> {text}")

        elif tag == "pre":
            code_text = child.get_text() if child else ""
            lines.append(f"\n```\n{code_text}\n```")

        elif tag in ("div", "section", "article", "main"):
            # Recurse into block containers
            _block_convert(child, lines, depth)

        elif tag == "hr":
            lines.append("\n---")

        elif tag == "table":
            lines.append("")
            _table_convert(child, lines)
            lines.append("")

        elif tag == "br":
            lines.append("")

        elif tag in ("span", "em", "i", "strong", "b", "a", "code"):
            text = _inline_convert(child).strip()
            if text:
                lines.append(text)

        elif tag in ("dl", "figure", "figcaption", "details", "summary"):
            _block_convert(child, lines, depth)

        else:
            # Unknown tag: recurse or extract text
            text = child.get_text().strip()
            if text:
                # Only add if the direct text is substantial
                _block_convert(child, lines, depth)


def _list_convert(el, lines, ordered, depth):
    """Convert a list element (ul/ol)."""
    idx = 1
    for li in el.find_all("li", recursive=False):
        prefix = f"{idx}." if ordered else "-"
        text = _inline_convert(li).strip()
        if text:
            indent = "  " * (depth - 1)
            lines.append(f"{indent}{prefix} {text}")
            idx += 1


def _table_convert(table, lines):
    """Convert HTML table to Markdown table."""
    rows = table.find_all("tr")
    if not rows:
        return

    for row_idx, row in enumerate(rows):
        cells = row.find_all(["th", "td"])
        cell_texts = [_inline_convert(c).strip().replace("|", "\\|") for c in cells]
        if not cell_texts:
            continue
        lines.append("| " + " | ".join(cell_texts) + " |")
        # Header separator after first row
        if row_idx == 0:
            lines.append("|" + "|".join(["------" for _ in cell_texts]) + "|")


# ═══════════════════════════════════════════════════════════════════════
# 5. Output generators
# ═══════════════════════════════════════════════════════════════════════

def make_slug(title, max_len=60):
    """Generate a URL-safe slug from a title. Preserves Chinese characters as-is."""
    # Remove problematic characters, keep Chinese, letters, digits, spaces, hyphens
    slug = re.sub(r'[^\w\s-]', '', title, flags=re.UNICODE)
    slug = re.sub(r'\s+', '_', slug.strip())
    slug = slug[:max_len].rstrip('_')
    if not slug:
        slug = "webpage"
    return slug


def make_html_archive(content_html, meta, mapping, output_dir, slug):
    """Write self-contained HTML archive file. Image paths already rewritten by caller."""
    # Build a clean HTML wrapper
    tags_str = " / ".join(meta.get("tags", [])) or "—"
    services_str = "—"  # will be filled by caller if available

    # Build article header from extracted metadata
    title = meta.get('title', '')
    author_meta = meta.get('author', '')
    pub_date = meta.get('publish_date', '')
    if pub_date:
        # Reformat ISO date to readable form
        try:
            from datetime import datetime as dt
            d = dt.fromisoformat(pub_date.replace('Z', '+00:00'))
            pub_date = d.strftime('%B %d, %Y')
        except (ValueError, TypeError):
            pass

    header_html = ""
    if title:
        header_html += f'<h1>{title}</h1>\n'
    if author_meta or pub_date:
        header_html += '<div class="article-meta">\n'
        if author_meta:
            header_html += f'  <span class="author">By {author_meta}</span>\n'
        if pub_date:
            header_html += f'  <span class="date">Published {pub_date}</span>\n'
        header_html += '</div>\n'

    html_out = f"""<!DOCTYPE html>
<html lang="{meta.get('language', 'zh-cn') or 'zh-cn'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title or 'Web Page Archive'}</title>
<style>
body {{ font-family: "Microsoft YaHei", "PingFang SC", system-ui, sans-serif;
       max-width: 860px; margin: 0 auto; padding: 20px 24px;
       color: #333; line-height: 1.85; }}
h1 {{ font-size: 1.6em; border-bottom: 2px solid #0052cc;
     padding-bottom: 12px; color: #1a1a1a; }}
h2 {{ font-size: 1.25em; margin-top: 28px; color: #0052cc; }}
h3 {{ font-size: 1.1em; margin-top: 20px; }}
.article-meta {{ color: #666; font-size: 0.92em; margin-bottom: 24px; }}
.article-meta .author {{ margin-right: 16px; }}
.article-meta .date {{ color: #888; }}
img {{ border: 1px solid #e0e0e0; border-radius: 4px; margin: 12px 0;
      max-width: 100%; height: auto; }}
ol, ul {{ padding-left: 24px; }}
li {{ margin: 6px 0; }}
code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px;
       font-size: 0.92em; }}
em {{ background: #fff3cd; padding: 1px 4px; border-radius: 2px;
      font-style: normal; }}
a {{ color: #0052cc; }}
.source-note {{ color: #999; font-size: 0.85em; margin-top: 40px;
               border-top: 1px solid #eee; padding-top: 16px; }}
.related-card {{ display: block; margin: 32px 0; padding: 20px 24px;
                border: 1px solid #d0d7de; border-radius: 8px;
                background: #f6f8fa; }}
.related-card img {{ border: none; margin: 0 0 12px 0; }}
.related-card .article-card-label {{ text-transform: uppercase;
                font-size: 0.78em; color: #666; font-weight: 600;
                margin-bottom: 8px; display: block; }}
.related-card h5 {{ font-size: 1.05em; margin: 4px 0 8px 0; }}
.related-card h5 a {{ color: #0052cc; text-decoration: none; }}
.related-card p {{ font-size: 0.92em; color: #555; margin: 4px 0; }}
.further_reading {{ border-top: 1px solid #eee; padding-top: 20px;
                   margin-top: 30px; }}
</style>
</head>
<body>
{header_html}
{content_html}
<div class="source-note">
<p>来源：<a href="{meta.get('url', '')}">{meta.get('title', '')}</a></p>
<p>采集日期：{datetime.now().strftime('%Y-%m-%d')} | 标签：{tags_str} | 渲染：{'Playwright (JS)' if meta.get('js_rendered') else 'requests (static)'}</p>
<p>采集方式：url-collector v{VERSION} full-archive 模式</p>
</div>
</body>
</html>"""

    fpath = os.path.join(output_dir, f"{slug}_网页归档.html")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f">>> HTML 归档: {fpath} ({len(html_out)} bytes)")
    return fpath


def make_markdown_record(meta, content_md, mapping, output_dir, slug, url, extra=None):
    """Write Markdown resource record file with full content."""
    extra = extra or {}
    tags_str = " / ".join(meta.get("tags", [])) or "—"
    lang = meta.get("language", "unknown")
    lang_label = f"{lang}（简体中文）" if lang.startswith("zh") else lang
    date_str = datetime.now().strftime("%Y-%m-%d")
    publish_date = meta.get("publish_date", "—")
    html_archive_name = f"{slug}_网页归档.html"

    # Build image references section for images we downloaded
    img_lines = ""
    for orig_src, local_name in mapping.items():
        if local_name:
            img_lines += f"\n![{local_name}](images/{local_name})"

    record = f"""# {meta.get('title', url)} 网页资源记录

| 属性 | 值 |
|------|-----|
| 类型 | 网页资源记录 |
| 来源 | {url} |
| 采集日期 | {date_str} |
| 语言 | {lang_label} |
| 标签 | {tags_str} |
| 更新时间 | {publish_date} |
| 采集方式 | url-collector v{VERSION} full-archive 模式 |
| HTML 归档 | [{html_archive_name}]({html_archive_name}) |

## 内容摘要

{extra.get('summary', '（请补充页面核心内容的 2-3 句话总结）')}

---

{content_md}

---

> 最后更新：{date_str}
"""

    fpath = os.path.join(output_dir, f"{slug}_网页资源记录.md")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(record)
    print(f">>> 资源记录: {fpath} ({len(record)} bytes)")
    return fpath


# ═══════════════════════════════════════════════════════════════════════
# 6. Main pipeline
# ═══════════════════════════════════════════════════════════════════════

def generate_summary(content_html, max_sentences=3):
    """Generate a brief content summary from the HTML body."""
    soup = BeautifulSoup(content_html, "html.parser")
    # Get first few paragraphs of text
    paragraphs = []
    for p in soup.find_all(["p", "li"]):
        text = p.get_text().strip()
        if len(text) > 10 and text not in paragraphs:
            paragraphs.append(text)
        if len(paragraphs) >= max_sentences:
            break
    if paragraphs:
        return "。".join(paragraphs) + "。"
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="url-collector full-archive — 完整网页归档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 full_archive.py https://example.com/article --output ./my-archive
  python3 full_archive.py https://example.com --output ./kb-dir --jd-number 03.04
  python3 full_archive.py https://example.com --output . --slug-prefix "my-custom-name"
        """,
    )
    parser.add_argument("url", help="要归档的网页 URL")
    parser.add_argument("--output", "-o", default=".", help="输出目录（默认当前目录）")
    parser.add_argument("--jd-number", help="Johnny Decimal 编号前缀（如 03.04）")
    parser.add_argument("--slug-prefix", help="自定义文件名前缀（覆盖自动生成的 slug）")
    parser.add_argument("--img-prefix", default="img", help="图片文件名前缀（默认 img）")
    parser.add_argument("--dry-run", action="store_true", help="仅分析不写入")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP 请求超时秒数（默认 30）")
    parser.add_argument("--js-render", choices=["auto", "force", "off"], default="auto",
                        help="JS 渲染策略: auto=自动检测薄页面后 Playwright fallback / force=强制 Playwright / off=仅 requests（默认 auto）")
    parser.add_argument("--version", action="version", version=f"full_archive.py v{VERSION}")

    args = parser.parse_args()

    print(f"=== url-collector full-archive v{VERSION} ===")
    print(f"URL: {args.url}")
    print(f"输出目录: {os.path.abspath(args.output)}")

    # ── Step 1: Download page ──
    print("\n>>> Step 1: 下载页面...")
    js_rendered = False
    try:
        raw_html, final_url = fetch_page(args.url, timeout=args.timeout)
        print(f"  页面大小: {len(raw_html)} bytes (requests)")
        print(f"  最终 URL: {final_url}")
    except requests.RequestException as e:
        print(f"  requests 下载失败: {e}")
        if args.js_render != "off":
            print("  → 尝试 Playwright 渲染...")
            raw_html, final_url = fetch_page_playwright(args.url, timeout=args.timeout)
            if raw_html is None:
                print(f"错误：无法获取页面")
                sys.exit(1)
            js_rendered = True
        else:
            print(f"错误：无法下载页面（--js-render=off，不尝试 Playwright）")
            sys.exit(1)

    # Auto-detect JS-rendered pages: if content is thin, fallback to Playwright
    if not js_rendered and args.js_render != "off":
        if args.js_render == "force":
            print("  --js-render=force: 强制 Playwright 渲染")
            pw_html, pw_url = fetch_page_playwright(args.url, timeout=args.timeout)
            if pw_html:
                raw_html, final_url = pw_html, pw_url
                js_rendered = True
        elif not _has_substantial_content(raw_html):
            print("  ⚠ 页面正文 < 200 chars，疑似 JS 动态渲染，自动切换到 Playwright...")
            pw_html, pw_url = fetch_page_playwright(args.url, timeout=args.timeout)
            if pw_html:
                raw_html, final_url = pw_html, pw_url
                js_rendered = True
            else:
                print("  ⚠ Playwright 不可用，使用 requests 获取的静态 HTML 继续")

    if js_rendered:
        print(f"  渲染后大小: {len(raw_html)} bytes")

    soup = BeautifulSoup(raw_html, "html.parser")

    # ── Step 2: Extract metadata ──
    print("\n>>> Step 2: 提取元数据...")
    meta = extract_metadata(soup, args.url)
    meta["url"] = args.url
    meta["js_rendered"] = js_rendered
    print(f"  标题: {meta['title'][:80]}")
    print(f"  摘要: {meta['description'][:80] if meta['description'] else '（无）'}")
    print(f"  站点: {meta['site_name'] or '（未知）'}")
    print(f"  语言: {meta['language'] or '（未知）'}")

    # ── Step 3: Extract main content ──
    print("\n>>> Step 3: 提取正文内容...")
    content_html, source, preload_data = extract_main_content(soup, raw_html)
    print(f"  提取方式: {source}")
    print(f"  正文长度: {len(content_html)} chars")

    # Extract additional tags from preload (Synology pattern)
    if preload_data:
        tags = preload_data.get("tags", [])
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, dict):
                    meta.setdefault("tags", [])
                    if t.get("text") and t["text"] not in meta["tags"]:
                        meta["tags"].append(t["text"])
                elif isinstance(t, str) and t not in meta.get("tags", []):
                    meta.setdefault("tags", []).append(t)
        services = preload_data.get("services", [])
        if isinstance(services, list):
            meta["services"] = [s["text"] if isinstance(s, dict) else s for s in services]

    # ── Step 4: Find & download images ──
    print("\n>>> Step 4: 处理图片...")
    # Parse the content HTML to find images
    content_soup = BeautifulSoup(content_html, "html.parser")
    image_list = resolve_image_urls(content_soup, final_url)
    print(f"  发现 {len(image_list)} 张图片")

    mapping = {}
    if args.dry_run:
        print("\n  [DRY RUN] 将下载以下图片:")
        for orig, resolved in image_list:
            print(f"    {orig} → {resolved}")
    else:
        # Download images found in the main content (after junk stripping)
        mapping = download_images(image_list, args.output, prefix=args.img_prefix, timeout=args.timeout)

    # ── Step 5: Generate slug ──
    print("\n>>> Step 5: 生成输出...")
    if args.slug_prefix:
        slug = args.slug_prefix
    else:
        slug = make_slug(meta["title"])
    if args.jd_number:
        slug = f"{args.jd_number}_{slug}"
    print(f"  Slug: {slug}")

    # ── Step 6: Generate content summary ──
    summary = generate_summary(content_html)

    # ── Step 7: Rewrite image paths in content, then convert to Markdown ──
    print("  改写图片路径 + 转换为 Markdown...")
    content_html = rewrite_image_paths(content_html, mapping)
    content_md = html_to_markdown(content_html)

    # ── Step 8: Write output files ──
    if args.dry_run:
        print("\n=== DRY RUN 完成 ===")
        print(f"  会生成:")
        print(f"    {slug}_网页归档.html")
        print(f"    {slug}_网页资源记录.md")
        print(f"    images/  ({len(image_list)} 张图片)")
    else:
        os.makedirs(args.output, exist_ok=True)

        make_html_archive(content_html, meta, mapping, args.output, slug)
        extra = {"summary": summary}
        make_markdown_record(meta, content_md, mapping, args.output, slug, args.url, extra)

        print(f"\n=== 归档完成 ===")
        print(f"  目录: {os.path.abspath(args.output)}")
        downloaded = sum(1 for v in mapping.values() if v is not None)
        print(f"  图片: {downloaded}/{len(mapping)} 张下载成功")


if __name__ == "__main__":
    main()
