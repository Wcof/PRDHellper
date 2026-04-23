#!/usr/bin/env python3
"""
构建 create-prd Skill 的独立 prompt 和 .skill 文本包。
"""
from pathlib import Path
import re

SKILL_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = SKILL_DIR / "dist"
REFS_DIR = SKILL_DIR / "references"
POLICY_FILE = SKILL_DIR / "configs" / "template-policy.yaml"

BASE_ORDERED_REL = [
    Path("SKILL.md"),
    Path("references/appendices/create-prd-appendix-typing.md"),
    Path("references/chapters/create-prd-ch01-background.md"),
    Path("references/chapters/create-prd-ch02-basic.md"),
    Path("references/chapters/create-prd-ch03-commercial.md"),
    Path("references/chapters/create-prd-ch04-goals.md"),
    Path("references/chapters/create-prd-ch05-overview.md"),
    Path("references/chapters/create-prd-ch06-scope.md"),
    Path("references/chapters/create-prd-ch07-risks.md"),
    Path("references/chapters/create-prd-ch08-09-terms.md"),
    Path("references/chapters/create-prd-ch10-functions.md"),
    Path("references/chapters/create-prd-ch11-tracking.md"),
    Path("references/chapters/create-prd-ch12-permissions.md"),
    Path("references/chapters/create-prd-ch13-operations.md"),
    Path("references/chapters/create-prd-ch14-tbd.md"),
    Path("references/appendices/create-prd-appendix-selfcheck.md"),
]

LOCAL_ORDERED = [
    REFS_DIR / "appendices" / "create-prd-appendix-engineering.md",
    REFS_DIR / "appendices" / "create-prd-appendix-mode-router.md",
    REFS_DIR / "appendices" / "create-prd-appendix-greenfield.md",
    REFS_DIR / "appendices" / "create-prd-appendix-existing-code.md",
    REFS_DIR / "appendices" / "create-prd-appendix-axure-html.md",
    REFS_DIR / "appendices" / "create-prd-appendix-sync-audit.md",
    REFS_DIR / "appendices" / "create-prd-appendix-mcp-integration.md",
]

TEMPLATE_DIR = REFS_DIR / "templates"
PROMPT_DIR = REFS_DIR / "prompts"


def normalize_skill(content: str) -> str:
    if content.startswith("---"):
        end = content.index("---", 3)
        content = content[end + 3:].strip()
    content = re.sub(r"\[([^\]]+)\]\(references/[^)]+\)", r"\1", content)
    return content


def section_label(fpath: Path, content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    rel = fpath.relative_to(SKILL_DIR).as_posix()
    rel = re.sub(r"(^|/)create-prd-ch\d+(?:-\d+)?-", r"\1", rel)
    rel = rel.replace("create-prd-", "")
    rel = rel.replace(".md", "")
    rel = rel.replace("/", " / ")
    return rel


def policy_main_source() -> Path:
    default_source = SKILL_DIR / "main-template" / "create-prd-skill-main"
    if not POLICY_FILE.exists():
        return default_source
    text = POLICY_FILE.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^\s*main_template_source:\s*(.+?)\s*$", text, flags=re.M)
    if not m:
        return default_source
    raw = m.group(1).strip().strip("'").strip('"')
    p = (SKILL_DIR / raw).resolve()
    return p if p.exists() else default_source


def ordered_files() -> list[Path]:
    main_root = policy_main_source()
    files: list[Path] = []
    for rel in BASE_ORDERED_REL:
        base_file = main_root / rel
        local_fallback = SKILL_DIR / rel
        files.append(base_file if base_file.exists() else local_fallback)
    files.extend(LOCAL_ORDERED)
    return files


def build() -> None:
    DIST_DIR.mkdir(exist_ok=True)
    parts = [
        "# Create-PRD 工程化完整独立 Prompt\n",
        "> 本文件可在任意 LLM 中直接使用，也可作为 Codex/Claude Code Skill 的参考文本。\n",
        "> 包含系统级 PRD、页面级 PRD、项目初始化、Axure HTML 反向生成、代码与 PRD 同步审计规则。\n",
        "---\n",
    ]
    for fpath in ordered_files():
        if not fpath.exists():
            print(f"WARNING 缺失: {fpath.relative_to(SKILL_DIR)}")
            continue
        content = fpath.read_text(encoding="utf-8")
        if fpath.name == "SKILL.md":
            content = normalize_skill(content)
        parts.append(f"\n{'=' * 72}\n")
        parts.append(f"## {section_label(fpath, content)}\n")
        parts.append(content)
        parts.append("\n")

    for folder in [TEMPLATE_DIR, PROMPT_DIR]:
        for fpath in sorted(folder.glob("*.md")):
            content = fpath.read_text(encoding="utf-8")
            parts.append(f"\n{'=' * 72}\n")
            parts.append(f"## {section_label(fpath, content)}\n")
            parts.append(content)
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
