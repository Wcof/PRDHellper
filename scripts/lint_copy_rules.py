#!/usr/bin/env python3
"""轻量中文文案规则检查。

默认用于 Markdown 可见正文（跳过 fenced code、行内代码、URL、API 路径）。
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
URL_RE = re.compile(r"https?://\S+")
API_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+(?![A-Za-z0-9_])"
)
INLINE_LINK_RE = re.compile(r"(!?\[[^\]]*]\()([^)]+)(\))")

FORBIDDEN_QUOTES = {
    '"': "ASCII 双引号",
    "“": "中文弯引号",
    "”": "中文弯引号",
}

NON_WORD_CHARS = r"\u4e00-\u9fffA-Za-z0-9_"
PREFIX_CONTEXT_CHARS = "与跟对向给帮替为请让"
SUFFIX_HINTS = "可会要能应需请把将来去做看读写用"

FORBIDDEN_ADDRESS_PATTERNS = [
    (
        re.compile(
            rf"(?<![{NON_WORD_CHARS}])你(?=$|[^\u4e00-\u9fff]|[{SUFFIX_HINTS}])"
        ),
        "你",
    ),
    (re.compile(rf"(?<=[{PREFIX_CONTEXT_CHARS}])你"), "你"),
    (re.compile(r"您"), "您"),
    (re.compile(r"同学(?:们|們)?"), "同学"),
]

CASE_RULES = [
    (re.compile(r"(?<![A-Za-z0-9_])id(?![A-Za-z0-9_])"), "ID"),
    (re.compile(r"(?<![A-Za-z0-9_])Id(?![A-Za-z0-9_])"), "ID"),
    (re.compile(r"(?<![A-Za-z0-9_])http(?![A-Za-z0-9_])"), "HTTP"),
    (re.compile(r"(?<![A-Za-z0-9_])Http(?![A-Za-z0-9_])"), "HTTP"),
    (re.compile(r"(?<![A-Za-z0-9_])url(?![A-Za-z0-9_])"), "URL"),
    (re.compile(r"(?<![A-Za-z0-9_])Url(?![A-Za-z0-9_])"), "URL"),
    (re.compile(r"(?<![A-Za-z0-9_])json(?![A-Za-z0-9_])"), "JSON"),
    (re.compile(r"(?<![A-Za-z0-9_])Json(?![A-Za-z0-9_])"), "JSON"),
    (re.compile(r"(?<![A-Za-z0-9_])api(?![A-Za-z0-9_])"), "API"),
    (re.compile(r"(?<![A-Za-z0-9_])Api(?![A-Za-z0-9_])"), "API"),
    (re.compile(r"(?<![A-Za-z0-9_])ai(?![A-Za-z0-9_])"), "AI"),
    (re.compile(r"(?<![A-Za-z0-9_])Ai(?![A-Za-z0-9_])"), "AI"),
]

AI_TERM_RULES = [
    (re.compile(r"(?<![A-Za-z0-9_])llm(?![A-Za-z0-9_])"), "LLM"),
    (re.compile(r"(?<![A-Za-z0-9_])Llm(?![A-Za-z0-9_])"), "LLM"),
    (re.compile(r"(?<![A-Za-z0-9_])aigc(?![A-Za-z0-9_])"), "AIGC"),
    (re.compile(r"(?<![A-Za-z0-9_])Aigc(?![A-Za-z0-9_])"), "AIGC"),
    (re.compile(r"(?<![A-Za-z0-9_])rag(?![A-Za-z0-9_])"), "RAG"),
    (re.compile(r"(?<![A-Za-z0-9_])Rag(?![A-Za-z0-9_])"), "RAG"),
    (re.compile(r"(?<![A-Za-z0-9_])chatgpt(?![A-Za-z0-9_])"), "ChatGPT"),
    (re.compile(r"(?<![A-Za-z0-9_])Chatgpt(?![A-Za-z0-9_])"), "ChatGPT"),
    (re.compile(r"(?<![A-Za-z0-9_])openai\\s+api(?![A-Za-z0-9_])"), "OpenAI API"),
    (re.compile(r"(?<![A-Za-z0-9_])OpenAI\\s+api(?![A-Za-z0-9_])"), "OpenAI API"),
    (re.compile(r"(?<![A-Za-z0-9_])embeding(?![A-Za-z0-9_])"), "embedding"),
    (re.compile(r"(?<![A-Za-z0-9_])finetune(?![A-Za-z0-9_])"), "fine-tuning"),
    (re.compile(r"(?<![A-Za-z0-9_])fine\\s+tune(?![A-Za-z0-9_])"), "fine-tuning"),
]

TYPO_RULES = [
    (re.compile(r"阀值"), "阈值"),
    (re.compile(r"登陆"), "登录"),
    (re.compile(r"布署"), "部署"),
    (re.compile(r"配制"), "配置"),
    (re.compile(r"起用"), "启用"),
    (re.compile(r"反回"), "返回"),
    (re.compile(r"回朔"), "回溯"),
    (re.compile(r"标示"), "标识"),
    (re.compile(r"帐户"), "账户"),
    (re.compile(r"帐号"), "账号"),
    (re.compile(r"截止"), "截至"),
    (re.compile(r"搜寻"), "搜索"),
    (re.compile(r"做为"), "作为"),
]


@dataclass
class Violation:
    file: Path
    line: int
    col: int
    kind: str
    message: str
    snippet: str


def _mask_match(text: str, regex: re.Pattern[str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        return " " * (match.end() - match.start())

    return regex.sub(replacer, text)


def prepare_visible_line(line: str) -> str:
    visible = line
    visible = _mask_match(visible, INLINE_CODE_RE)
    visible = INLINE_LINK_RE.sub(
        lambda m: f"{m.group(1)}{' ' * len(m.group(2))}{m.group(3)}", visible
    )
    visible = _mask_match(visible, URL_RE)
    visible = _mask_match(visible, API_PATH_RE)
    return visible


def _iter_forbidden_address_matches(line: str):
    seen = set()
    for pattern, label in FORBIDDEN_ADDRESS_PATTERNS:
        for match in pattern.finditer(line):
            key = (match.start(), match.end(), label)
            if key in seen:
                continue
            seen.add(key)
            yield match, label


def scan_markdown(path: Path) -> List[Violation]:
    violations: List[Violation] = []
    if not path.exists() or path.suffix.lower() != ".md":
        return violations
    in_fence = False
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    in_front_matter = bool(lines and lines[0].strip() == "---")

    for line_no, raw in enumerate(lines, start=1):
        if in_front_matter:
            if line_no != 1 and raw.strip() in {"---", "..."}:
                in_front_matter = False
            continue

        if FENCE_RE.match(raw):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        visible = prepare_visible_line(raw)

        for quote, label in FORBIDDEN_QUOTES.items():
            for match in re.finditer(re.escape(quote), visible):
                violations.append(
                    Violation(
                        file=path,
                        line=line_no,
                        col=match.start() + 1,
                        kind="quote",
                        message=f"可见正文包含 {label}，建议改为直角引号「」",
                        snippet=raw.strip(),
                    )
                )

        for match, term in _iter_forbidden_address_matches(visible):
            violations.append(
                Violation(
                    file=path,
                    line=line_no,
                    col=match.start() + 1,
                    kind="address",
                    message=f"可见正文包含禁用称呼「{term}」",
                    snippet=raw.strip(),
                )
            )

        for pattern, suggested in CASE_RULES:
            for match in pattern.finditer(visible):
                wrong = match.group(0)
                violations.append(
                    Violation(
                        file=path,
                        line=line_no,
                        col=match.start() + 1,
                        kind="casing",
                        message=f"术语「{wrong}」建议改为「{suggested}」",
                        snippet=raw.strip(),
                    )
                )

        for pattern, suggested in AI_TERM_RULES:
            for match in pattern.finditer(visible):
                wrong = match.group(0)
                violations.append(
                    Violation(
                        file=path,
                        line=line_no,
                        col=match.start() + 1,
                        kind="ai-term",
                        message=f"AI 术语「{wrong}」建议改为「{suggested}」",
                        snippet=raw.strip(),
                    )
                )

        for pattern, suggested in TYPO_RULES:
            for match in pattern.finditer(visible):
                wrong = match.group(0)
                violations.append(
                    Violation(
                        file=path,
                        line=line_no,
                        col=match.start() + 1,
                        kind="typo",
                        message=f"词语「{wrong}」建议改为「{suggested}」",
                        snippet=raw.strip(),
                    )
                )

    return violations


def expand_targets(targets: Iterable[Path]) -> List[Path]:
    files: List[Path] = []
    for target in targets:
        if target.is_file() and target.suffix.lower() == ".md":
            files.append(target)
            continue
        if target.is_dir():
            files.extend(sorted(target.rglob("*.md")))
    return files


def scan_paths(targets: Iterable[Path]) -> List[Violation]:
    issues: List[Violation] = []
    for path in expand_targets(targets):
        issues.extend(scan_markdown(path))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="轻量中文文案规则检查")
    parser.add_argument("targets", nargs="*", default=["."], help="文件或目录，默认当前目录")
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
        help="命中规则时返回非零退出码",
    )
    args = parser.parse_args()

    targets = [Path(x).resolve() for x in args.targets]
    issues = scan_paths(targets)
    for item in issues:
        rel = item.file
        print(f"{rel}:{item.line}:{item.col} [{item.kind}] {item.message}")
        if item.snippet:
            print(f"  -> {item.snippet}")
    print(f"copy-lint issues: {len(issues)}")
    if args.fail_on_violation and issues:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
