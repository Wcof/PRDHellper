from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_lint_module():
    scripts_dir = str((ROOT / "scripts").resolve())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import lint_copy_rules  # type: ignore

    return lint_copy_rules


def test_copy_lint_ignores_code_and_paths(tmp_path: Path):
    mod = load_lint_module()
    md = tmp_path / "sample.md"
    md.write_text(
        """# Demo

URL: https://example.com/api/test
Path: /api/v1/users
Inline: `chatgpt` `openai api` `你`

```ts
const s = "chatgpt";
```
""",
        encoding="utf-8",
    )
    issues = mod.scan_paths([md])
    assert issues == []


def test_copy_lint_detects_quotes_address_terms_and_typos(tmp_path: Path):
    mod = load_lint_module()
    md = tmp_path / "bad.md"
    md.write_text(
        """# 文案

你可以查看 "结果"。
这里接入 chatgpt 和 openai api。
请先登陆系统并校验阀值。
""",
        encoding="utf-8",
    )
    issues = mod.scan_paths([md])
    kinds = {i.kind for i in issues}
    assert "quote" in kinds
    assert "address" in kinds
    assert "ai-term" in kinds
    assert "typo" in kinds
