#!/usr/bin/env python3
"""
发布前只读验收脚本。

目标：检查产品化口径是否完整、路径是否统一、关键实体是否存在。
本脚本不修改任何文件。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class CheckResult:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def ok(self, message: str) -> None:
        print(f"[OK] {message}")

    def fail(self, message: str) -> None:
        self.failures.append(message)
        print(f"[FAIL] {message}")

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"[WARN] {message}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def ensure_file_exists(path: Path, result: CheckResult) -> None:
    if path.exists():
        result.ok(f"文件存在: {path.relative_to(ROOT)}")
    else:
        result.fail(f"缺失文件: {path.relative_to(ROOT)}")


def check_readme(result: CheckResult) -> None:
    path = ROOT / "README.md"
    ensure_file_exists(path, result)
    text = read_text(path)
    required = [
        "docs/prd/",
        "docs/prd/pages/",
        "docs/prd/system/",
        "showcases/INDEX.md",
        "scripts/verify_release.py",
    ]
    for needle in required:
        if needle in text:
            result.ok(f"README 包含关键口径: {needle}")
        else:
            result.fail(f"README 缺少关键口径: {needle}")


def check_skill(result: CheckResult) -> None:
    path = ROOT / "SKILL.md"
    ensure_file_exists(path, result)
    text = read_text(path)
    required = [
        "按需加载",
        "逐步释放",
        "References 路由表",
        "异常处理",
        "docs/prd/system/",
        "docs/prd/pages/",
    ]
    for needle in required:
        if needle in text:
            result.ok(f"SKILL 包含: {needle}")
        else:
            result.fail(f"SKILL 缺少: {needle}")


def check_install_paths(result: CheckResult) -> None:
    path = ROOT / "scripts" / "install_skill.py"
    ensure_file_exists(path, result)
    text = read_text(path)
    required = [
        "AGENTS.md",
        "CLAUDE.md",
        ".agents/skills/create-prd",
        "docs/prd",
        "_print_next_steps",
    ]
    for needle in required:
        if needle in text:
            result.ok(f"安装器口径存在: {needle}")
        else:
            result.fail(f"安装器口径缺失: {needle}")
    target_cfg = ROOT / "configs" / "install-targets.yaml"
    ensure_file_exists(target_cfg, result)
    cfg = read_text(target_cfg)
    if "path: docs/prd" in cfg:
        result.ok("安装目标口径为 docs/prd")
    else:
        result.fail("安装目标口径不是 docs/prd")


def check_showcases(result: CheckResult) -> None:
    required_files = [
        ROOT / "showcases" / "INDEX.md",
        ROOT / "showcases" / "sample-output" / "tree.txt",
        ROOT / "showcases" / "sample-output" / "system-sample.md",
        ROOT / "showcases" / "sample-output" / "page-sample.md",
        ROOT / "showcases" / "sample-output" / "audit-sample.md",
    ]
    for path in required_files:
        ensure_file_exists(path, result)


def check_test_prompts(result: CheckResult) -> None:
    path = ROOT / "test-prompts.json"
    ensure_file_exists(path, result)
    text = read_text(path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        result.fail(f"test-prompts.json 不是合法 JSON: {exc}")
        return
    if not isinstance(data, list) or len(data) < 6:
        result.fail("test-prompts.json 场景数量不足（至少 6 个）")
        return
    result.ok(f"test-prompts.json 场景数: {len(data)}")

    joined = json.dumps(data, ensure_ascii=False)
    required_keywords = [
        "existing-code",
        "Axure",
        "changelog",
        "文案",
        "system",
        "pages",
    ]
    for keyword in required_keywords:
        if keyword in joined:
            result.ok(f"test-prompts 覆盖关键字: {keyword}")
        else:
            result.fail(f"test-prompts 缺少关键字: {keyword}")


def check_banned_phrases(result: CheckResult) -> None:
    targets = [
        ROOT / "README.md",
        ROOT / "SKILL.md",
        ROOT / "configs" / "install-targets.yaml",
    ]
    banned = [
        "docs/product",
        "14 章",
    ]
    for path in targets:
        text = read_text(path)
        for phrase in banned:
            if phrase in text:
                result.fail(f"发现旧口径 `{phrase}` in {path.relative_to(ROOT)}")

    # 对于主模板或章节文件中遗留的文件名不做失败判定，只提醒。
    chapter_hint = re.compile(r"create-prd-ch14", re.IGNORECASE)
    for path in [ROOT / "scripts" / "build.py", ROOT / "main-template" / "create-prd-skill-main" / "scripts" / "build.py"]:
        text = read_text(path)
        if chapter_hint.search(text):
            result.warn(f"检测到章节文件名引用（允许，仅提醒）: {path.relative_to(ROOT)}")


def check_dist(result: CheckResult) -> None:
    for path in [ROOT / "dist" / "create-prd.skill", ROOT / "dist" / "create-prd-universal-prompt.md"]:
        ensure_file_exists(path, result)


def check_gitignore(result: CheckResult) -> None:
    path = ROOT / ".gitignore"
    ensure_file_exists(path, result)
    text = read_text(path)
    required = [".DS_Store", ".pytest_cache/", "__pycache__/"]
    for needle in required:
        if needle in text:
            result.ok(f".gitignore 包含: {needle}")
        else:
            result.fail(f".gitignore 缺少: {needle}")


def main() -> int:
    result = CheckResult()
    print("== verify_release: start ==")

    check_readme(result)
    check_skill(result)
    check_install_paths(result)
    check_showcases(result)
    check_test_prompts(result)
    check_banned_phrases(result)
    check_dist(result)
    check_gitignore(result)

    print("\n== verify_release: summary ==")
    print(f"failures: {len(result.failures)}")
    print(f"warnings: {len(result.warnings)}")

    if result.failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
