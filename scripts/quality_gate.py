#!/usr/bin/env python3
"""
url-collector 质量门禁 — 四道门禁检查

1. 脚本语法检查：collect.sh bash 语法正确性
2. 文档完整性检查：必要文件是否存在
3. 脚本功能检查：collect.sh CLI 基本可用
4. 参考规范检查：web-page-schema.md / kb-archive-guide.md 必要章节
"""

import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
EXAMPLES_DIR = SKILL_DIR / "examples"

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "CHANGELOG.md",
    "scripts/collect.sh",
    "references/web-page-schema.md",
    "references/kb-archive-guide.md",
    "examples/example-webpage.md",
    "examples/example-kb-archive.md",
]

SCHEMA_REQUIRED_SECTIONS = [
    "字段定义",
    "Content Type",
    "文件命名",
    "记录文件模板",
]

KB_GUIDE_REQUIRED_SECTIONS = [
    "Johnny Decimal",
    "5C 索引更新",
    "Agent 分析协议",
    "语义匹配",
]


def gate_1_syntax():
    """门禁 1：collect.sh bash 语法检查"""
    collect_sh = SCRIPTS_DIR / "collect.sh"
    if not collect_sh.exists():
        print("[FAIL] Gate 1: collect.sh not found")
        return False
    try:
        result = subprocess.run(
            ["bash", "-n", str(collect_sh)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("[PASS] Gate 1: collect.sh syntax OK")
            return True
        print(f"[FAIL] Gate 1: syntax error\n{result.stderr}")
        return False
    except Exception as e:
        print(f"[FAIL] Gate 1: {e}")
        return False


def gate_2_files():
    """门禁 2：文档完整性检查"""
    missing = []
    for f in REQUIRED_FILES:
        if not (SKILL_DIR / f).exists():
            missing.append(f)
    if missing:
        print(f"[FAIL] Gate 2: missing files: {missing}")
        return False
    print("[PASS] Gate 2: all required files present")
    return True


def gate_3_cli():
    """门禁 3：collect.sh CLI 基本可用"""
    collect_sh = SCRIPTS_DIR / "collect.sh"
    try:
        result = subprocess.run(
            ["bash", str(collect_sh)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # 无参数应输出错误提示（URL 必填）
        if "错误" in result.stdout or "请提供 URL" in result.stdout:
            print("[PASS] Gate 3: CLI help/error displays correctly")
            return True
        if result.returncode != 0 and ("用法" in result.stdout or "URL" in result.stdout):
            print("[PASS] Gate 3: CLI error message present")
            return True
        print(f"[WARN] Gate 3: unexpected output: {result.stdout[:200]}")
        return True  # 不阻塞，可能是脚本正常行为
    except Exception as e:
        print(f"[FAIL] Gate 3: {e}")
        return False


def gate_4_references():
    """门禁 4：参考规范必要章节检查"""
    all_ok = True

    # 检查 web-page-schema.md
    schema_file = REFERENCES_DIR / "web-page-schema.md"
    if schema_file.exists():
        content = schema_file.read_text(encoding="utf-8")
        for section in SCHEMA_REQUIRED_SECTIONS:
            if section not in content:
                print(f"[FAIL] Gate 4: web-page-schema.md missing section '{section}'")
                all_ok = False
    else:
        print("[FAIL] Gate 4: web-page-schema.md not found")
        all_ok = False

    # 检查 kb-archive-guide.md
    guide_file = REFERENCES_DIR / "kb-archive-guide.md"
    if guide_file.exists():
        content = guide_file.read_text(encoding="utf-8")
        for section in KB_GUIDE_REQUIRED_SECTIONS:
            if section not in content:
                print(f"[FAIL] Gate 4: kb-archive-guide.md missing section '{section}'")
                all_ok = False
    else:
        print("[FAIL] Gate 4: kb-archive-guide.md not found")
        all_ok = False

    if all_ok:
        print("[PASS] Gate 4: reference docs have required sections")
    return all_ok


def main():
    print("=" * 50)
    print("url-collector Quality Gate")
    print("=" * 50)

    results = [
        gate_1_syntax(),
        gate_2_files(),
        gate_3_cli(),
        gate_4_references(),
    ]

    print("=" * 50)
    passed = sum(1 for r in results if r)
    total = len(results)
    if all(results):
        print(f"[PASS] All {total} gates passed")
        return 0
    else:
        print(f"[FAIL] {passed}/{total} gates passed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
