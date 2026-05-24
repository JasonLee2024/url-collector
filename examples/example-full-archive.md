# Synology NAS 外部访问快速入门指南 — 完整网页归档示范

> 采集方式：url-collector v1.3.0 full-archive 模式
> 采集日期：2026-05-25 · 演示 URL：https://kb.synology.cn/zh-cn/DSM/tutorial/Quick_Start_External_Access

## 命令

```bash
# 方式一：通过 collect.sh 壳调用
collect.sh \
  "https://kb.synology.cn/zh-cn/DSM/tutorial/Quick_Start_External_Access" \
  --full-archive \
  --output /tmp/demo-full-archive \
  --slug-prefix "Synology_NAS_外部访问快速入门指南" \
  --img-prefix quickconnect

# 方式二：直接调用 Python 脚本
python3 scripts/full_archive.py \
  "https://kb.synology.cn/zh-cn/DSM/tutorial/Quick_Start_External_Access" \
  --output /tmp/demo-full-archive \
  --slug-prefix "Synology_NAS_外部访问快速入门指南" \
  --img-prefix quickconnect

# 方式三：归档到 KB 目录（带 JD 编号前缀）
python3 scripts/full_archive.py \
  "https://kb.synology.cn/zh-cn/DSM/tutorial/Quick_Start_External_Access" \
  --output ~/kb-repo/NAS/10-硬件选型/19-NAS原厂信息/Synology/Product/DS925+/03.使用入门/ \
  --slug-prefix "Synology_NAS_外部访问快速入门指南" \
  --jd-number "03.05"
```

## 执行过程（6 步自动化）

```
=== url-collector full-archive v1.0.0 ===

>>> Step 1: 下载页面...
  页面大小: 74630 bytes
  提取方式: vue_preload ← 自动识别 Synology KB 的数据注入模式

>>> Step 2: 提取元数据...
  标题: Synology NAS 外部访问快速入门指南 - Synology 知识中心
  语言: zh-cn
  标签: DDNS / QuickConnect / 外部访问/端口转发 / Quick Start

>>> Step 3: 提取正文内容...
  正文长度: 19982 chars

>>> Step 4: 处理图片...
  发现 7 张图片
  ✓ quickconnect_1.png (41441 bytes)
  ✓ quickconnect_2.png (34011 bytes)
  ✓ quickconnect_3.png (26963 bytes)
  ✓ quickconnect_4.png (19621 bytes)
  ✓ quickconnect_5.png (20410 bytes)
  ✓ quickconnect_6.png (39780 bytes)
  ✓ quickconnect_7.png (18443 bytes)

>>> Step 5: 改写图片路径 + 转换为 Markdown...
  原路径: "../../../_images/autogen/Quick_Start_External_Access/X.png"
  新路径: "images/quickconnect_X.png"

>>> HTML 归档 & 资源记录已生成
=== 归档完成 ===
```

## 输出产物

```
demo-full-archive/
├── Synology_NAS_外部访问快速入门指南_网页归档.html   ← 21KB 双击浏览器查看
├── Synology_NAS_外部访问快速入门指南_网页资源记录.md  ← 8KB  元数据表 + 全文
└── images/
    ├── quickconnect_1.png  ← 7 张操作截图全部本地化，路径已改写
    ├── quickconnect_2.png
    ├── quickconnect_3.png
    ├── quickconnect_4.png
    ├── quickconnect_5.png
    ├── quickconnect_6.png
    └── quickconnect_7.png
```

## 资源记录结构

```markdown
# Synology NAS 外部访问快速入门指南 - Synology 知识中心 网页资源记录

| 属性 | 值 |
|------|-----|
| 类型 | 网页资源记录 |
| 来源 | https://kb.synology.cn/zh-cn/DSM/tutorial/Quick_Start_External_Access |
| 采集日期 | 2026-05-25 |
| 语言 | zh-cn（简体中文） |
| 标签 | DDNS / 外部访问/端口转发 / QuickConnect / Quick Start |
| 采集方式 | url-collector v1.0.0 full-archive 模式 |
| HTML 归档 | [Synology_NAS_外部访问快速入门指南_网页归档.html](...html) |

## 内容摘要
（自动生成 2-3 句摘要）

---

## 什么是外部访问？
...（完整正文，含本地化图片引用 ![](images/quickconnect_1.png)）

## 设置 QuickConnect
...（7 步操作 SOP）

## 使用 DDNS 创建主机名
...（配置步骤 + 访问方式）

---

> 最后更新：2026-05-25
```

## 与旧模式对比

| 维度 | 快速收藏 (v1.0) | 深度存档 (v1.0) | **完整网页归档 (v1.3)** |
|------|:---:|:---:|:---:|
| 下载图片 | ❌ | ❌ (仅 monolith 内嵌) | ✅ 独立下载 |
| 图片路径改写 | ❌ | ❌ | ✅ 自动改写为 images/ |
| Markdown 全文 | ❌ (占位符) | ❌ (占位符) | ✅ 自动生成 |
| HTML 可离屏查看 | ❌ | ⚠️ (monolith, 需额外安装) | ✅ 自包含 |
| 正文提取 | ❌ | ❌ | ✅ 多策略 (Vue preload / CSS / body) |
| 外部依赖 | curl | curl + cargo monolith | requests + bs4 (已预装) |

> 最后更新：2026-05-25
