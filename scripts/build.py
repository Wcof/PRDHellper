#!/usr/bin/env python3
"""
构建 create-prd Skill 的独立 prompt 和 .skill 文本包。
"""
from pathlib import Path
import re

SKILL_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = SKILL_DIR / "dist"
REFS_DIR = SKILL_DIR / "references"

ORDERED_FILES = [
    SKILL_DIR / "SKILL.md",
    REFS_DIR / "appendices" / "create-prd-appendix-engineering.md",
    REFS_DIR / "appendices" / "create-prd-appendix-mode-router.md",
    REFS_DIR / "appendices" / "create-prd-appendix-greenfield.md",
    REFS_DIR / "appendices" / "create-prd-appendix-existing-code.md",
    REFS_DIR / "appendices" / "create-prd-appendix-axure-html.md",
    REFS_DIR / "appendices" / "create-prd-appendix-sync-audit.md",
    REFS_DIR / "appendices" / "create-prd-appendix-mcp-integration.md",
    REFS_DIR / "appendices" / "create-prd-appendix-typing.md",
    REFS_DIR / "chapters" / "create-prd-ch01-background.md",
    REFS_DIR / "chapters" / "create-prd-ch02-basic.md",
    REFS_DIR / "chapters" / "create-prd-ch03-commercial.md",
    REFS_DIR / "chapters" / "create-prd-ch04-goals.md",
    REFS_DIR / "chapters" / "create-prd-ch05-overview.md",
    REFS_DIR / "chapters" / "create-prd-ch06-scope.md",
    REFS_DIR / "chapters" / "create-prd-ch07-risks.md",
    REFS_DIR / "chapters" / "create-prd-ch08-09-terms.md",
    REFS_DIR / "chapters" / "create-prd-ch10-functions.md",
    REFS_DIR / "chapters" / "create-prd-ch11-tracking.md",
    REFS_DIR / "chapters" / "create-prd-ch12-permissions.md",
    REFS_DIR / "chapters" / "create-prd-ch13-operations.md",
    REFS_DIR / "chapters" / "create-prd-ch14-tbd.md",
    REFS_DIR / "appendices" / "create-prd-appendix-selfcheck.md",
]

TEMPLATE_DIR = REFS_DIR / "templates"
PROMPT_DIR = REFS_DIR / "prompts"


def normalize_skill(content: str) -> str:
    if content.startswith("---"):
        end = content.index("---", 3)
        content = content[end + 3:].strip()
    content = re.sub(r"\[([^\]]+)\]\(references/[^)]+\)", r"\1", content)
    return content


def build() -> None:
    DIST_DIR.mkdir(exist_ok=True)
    parts = [
        "# Create-PRD 工程化完整独立 Prompt\n",
        "> 本文件可在任意 LLM 中直接使用，也可作为 Codex/Claude Code Skill 的参考文本。\n",
        "> 包含完整 14 章系统 PRD、页面级 PRD、项目初始化、Axure HTML 反向生成、代码与 PRD 同步审计规则。\n",
        "---\n",
    ]
    for fpath in ORDERED_FILES:
        if not fpath.exists():
            print(f"WARNING 缺失: {fpath.relative_to(SKILL_DIR)}")
            continue
        content = fpath.read_text(encoding="utf-8")
        if fpath.name == "SKILL.md":
            content = normalize_skill(content)
        parts.append(f"\n{'=' * 72}\n")
        parts.append(f"## {fpath.relative_to(SKILL_DIR)}\n")
        parts.append(content)
        parts.append("\n")

    for folder in [TEMPLATE_DIR, PROMPT_DIR]:
        for fpath in sorted(folder.glob("*.md")):
            parts.append(f"\n{'=' * 72}\n")
            parts.append(f"## {fpath.relative_to(SKILL_DIR)}\n")
            parts.append(fpath.read_text(encoding="utf-8"))
            parts.append("\n")

    universal = "\n".join(parts)
    out_prompt = DIST_DIR / "create-prd-universal-prompt.md"
    out_skill = DIST_DIR / "create-prd.skill"
    out_prompt.write_text(universal, encoding="utf-8")
    out_skill.write_text(universal, encoding="utf-8")
    print(f"universal prompt: {out_prompt}")
    print(f"skill text: {out_skill}")
    print(f"size: {len(universal):,} chars")


if __name__ == "__main__":
    build()
