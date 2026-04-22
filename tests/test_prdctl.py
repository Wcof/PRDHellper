from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prdctl.py"


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def load_prdctl_module():
    scripts_dir = str((ROOT / "scripts").resolve())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import prdctl  # type: ignore

    return prdctl


def test_help_runs():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "create-prd" in result.stdout
    assert "sync" in result.stdout
    assert "diff-sync" in result.stdout


def test_frontmatter_roundtrip():
    mod = load_prdctl_module()
    body = "# 页面 PRD\n\n## 1. 页面基础信息\n"
    raw = mod.dump_frontmatter(
        {
            "page_id": "page-demo",
            "route": "/demo",
            "code_paths": ["src/pages/demo.tsx"],
            "feature_ids": ["feat-demo-core"],
            "change_ids": ["chg-demo-init"],
            "last_synced_at": "2026-04-20",
        },
        body,
    )
    meta, parsed_body = mod.parse_frontmatter(raw)
    assert meta["page_id"] == "page-demo"
    assert meta["route"] == "/demo"
    assert meta["code_paths"] == ["src/pages/demo.tsx"]
    assert parsed_body.startswith("# 页面 PRD")


def test_sync_from_code_creates_traceability(tmp_path: Path):
    (tmp_path / "src" / "routes").mkdir(parents=True)
    (tmp_path / "src" / "routes" / "index.ts").write_text(
        "export default [{ path: '/demo', name: '演示页', component: () => import('@/pages/demo/index.tsx') }]\n",
        encoding="utf-8",
    )

    init = run_cli("init-project", str(tmp_path), "--mode", "greenfield")
    assert init.returncode == 0, init.stderr
    sync = run_cli("sync", str(tmp_path), "--from-code")
    assert sync.returncode == 0, sync.stderr

    page_prd = tmp_path / "docs/product/pages/demo.md"
    assert page_prd.exists()
    page_text = page_prd.read_text(encoding="utf-8")
    assert page_text.startswith("---\n")
    assert "page_id: page-demo" in page_text
    assert "feature_ids: [\"feat-demo-core\"]" in page_text
    assert "change_ids: [\"chg-demo-init\"]" in page_text

    route_text = (tmp_path / "docs/product/01-页面路由清单.md").read_text(encoding="utf-8")
    assert "page_id" in route_text
    assert "`/demo`" in route_text

    index_path = tmp_path / "docs/product/.index/traceability.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert "page-demo" in index["pages"]
    assert "feat-demo-core" in index["features"]
    assert "chg-demo-init" in index["changes"]


def test_init_project_custom_prd_root_updates_agents(tmp_path: Path):
    result = run_cli("init-project", str(tmp_path), "--mode", "greenfield", "--prd-root", "docs/prd")
    assert result.returncode == 0, result.stderr
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "docs/prd/" in agents
    assert "docs/product/" not in agents
    assert (tmp_path / "docs/prd/01-页面路由清单.md").exists()


def test_sync_from_prd_backfills_feature_and_change(tmp_path: Path):
    run_cli("init-project", str(tmp_path), "--mode", "greenfield")

    page = tmp_path / "docs/product/pages/custom.md"
    page.write_text(
        """---
page_id: page-custom
route: /custom
code_paths: ["src/pages/custom.tsx"]
feature_ids: ["feat-custom-core"]
change_ids: ["chg-custom-init"]
last_synced_at: 2026-04-20
---
# 页面 PRD：自定义页

## 1. 页面基础信息
## 2. 页面目标
## 3. 页面结构
## 4. 字段说明
## 5. 操作说明
## 6. 交互规则
## 7. 状态流转
## 8. 异常场景
## 9. 权限规则
## 10. 数据规则
## 11. 验收标准
""",
        encoding="utf-8",
    )

    result = run_cli("sync", str(tmp_path), "--from-prd")
    assert result.returncode == 0, result.stderr

    feature_text = (tmp_path / "docs/product/02-功能清单.md").read_text(encoding="utf-8")
    assert "feat-custom-core" in feature_text
    assert "page-custom" in feature_text

    change_file = tmp_path / "docs/product/changelog/custom-change.md"
    assert change_file.exists()
    change_text = change_file.read_text(encoding="utf-8")
    assert "chg-custom-init" in change_text

    route_text = (tmp_path / "docs/product/01-页面路由清单.md").read_text(encoding="utf-8")
    assert "page-custom" in route_text
    assert "`/custom`" in route_text


def test_audit_strict_reports_unlinked_feature(tmp_path: Path):
    run_cli("init-project", str(tmp_path), "--mode", "greenfield")
    (tmp_path / "docs/product/pages/demo.md").write_text(
        """---
page_id: page-demo
route: /demo
code_paths: ["src/pages/demo.tsx"]
feature_ids: ["feat-missing"]
change_ids: ["chg-demo-init"]
last_synced_at: 2026-04-20
---
# 页面 PRD：演示

## 1. 页面基础信息
## 2. 页面目标
## 3. 页面结构
## 4. 字段说明
## 5. 操作说明
## 6. 交互规则
## 7. 状态流转
## 8. 异常场景
## 9. 权限规则
## 10. 数据规则
## 11. 验收标准
""",
        encoding="utf-8",
    )
    # 确保存在 change_id，避免被其他告警掩盖
    (tmp_path / "docs/product/changelog/demo-change.md").write_text(
        """# 页面变更记录

| change_id | affected_page_ids | affected_feature_ids | source_commit | 版本 | 日期 | 修改类型 | 修改内容 | 影响范围 | 是否同步 PRD | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|
| chg-demo-init | page-demo | feat-missing | test | v0.1 | 2026-04-20 | 初始化 | 初始化 | 页面 PRD | 是 | 测试 |
""",
        encoding="utf-8",
    )
    result = run_cli("audit", str(tmp_path), "--level", "strict")
    assert result.returncode == 0, result.stderr

    audit_file = tmp_path / f"docs/product/audit/{dt.date.today().isoformat()}-consistency-audit.md"
    assert audit_file.exists()
    text = audit_file.read_text(encoding="utf-8")
    assert "feature_id 未在功能清单中" in text or "功能归属页面不存在" in text


def test_run_git_diff_non_repo_is_silent(tmp_path: Path):
    mod = load_prdctl_module()
    changed = mod.run_git_diff(tmp_path, staged=True)
    assert changed == []


def test_parse_markdown_table_prefers_required_headers():
    mod = load_prdctl_module()
    text = """# 功能清单

| feature_id | owner_page_id | status |
|---|---|---|
| feat-a | page-a | todo |

## 说明

| 名称 | 值 |
|---|---|
| x | y |
"""
    headers, rows = mod.parse_markdown_table(text, required_headers=["feature_id", "owner_page_id"])
    assert headers == ["feature_id", "owner_page_id", "status"]
    assert len(rows) == 1
    assert rows[0]["feature_id"] == "feat-a"


def test_collectors_ignore_placeholder_rows(tmp_path: Path):
    run_cli("init-project", str(tmp_path), "--mode", "greenfield")
    feature = tmp_path / "docs/product/02-功能清单.md"
    feature.write_text(
        """# 功能清单

| feature_id | owner_page_id | status | 一级菜单 | 二级页面 | 三级功能 |
|---|---|---|---|---|---|
| [TODO: feat-xxx] | [TODO: page-xxx] | todo | [TODO] | [TODO] | [TODO] |
| feat-real | page-real | done | A | B | C |
""",
        encoding="utf-8",
    )
    route = tmp_path / "docs/product/01-页面路由清单.md"
    route.write_text(
        """# 页面路由清单

| page_id | 所属模块 | 页面名称 | route | code_path | prd_path | 当前状态 |
|---|---|---|---|---|---|---|
| [TODO: page-xxx] | [TODO] | [TODO] | [TODO] | [TODO] | [TODO] | 待确认 |
| page-real | m | n | `/real` | `src/real.ts` | `docs/product/pages/real.md` | done |
""",
        encoding="utf-8",
    )

    mod = load_prdctl_module()
    feature_rows = mod.load_feature_rows(feature)
    assert len(feature_rows) == 1
    assert feature_rows[0]["feature_id"] == "feat-real"
    routes = mod.collect_routes(tmp_path, "docs/product")
    assert "page-real" in routes
    assert all("TODO" not in k for k in routes.keys())


def test_scan_axure_skips_auxiliary_export_pages(tmp_path: Path):
    html_root = tmp_path / "axure"
    (html_root / "resources" / "chrome").mkdir(parents=True)
    (html_root / "index.html").write_text("<html><head><title>Untitled Document</title></head></html>", encoding="utf-8")
    (html_root / "start.html").write_text("<html><head><title>start</title></head></html>", encoding="utf-8")
    (html_root / "resources" / "reload.html").write_text("<html><head><title>reload</title></head></html>", encoding="utf-8")
    (html_root / "resources" / "chrome" / "chrome.html").write_text(
        "<html><head><title>Install extension</title></head></html>",
        encoding="utf-8",
    )
    (html_root / "业务页面.html").write_text(
        "<html><head><title>业务页面</title></head><body><button>保存</button></body></html>",
        encoding="utf-8",
    )

    run_cli("scan-axure", str(html_root), "--project-root", str(tmp_path), "--create-prd")

    report = (tmp_path / "docs/product/imports/axure-pages.md").read_text(encoding="utf-8")
    assert "业务页面" in report
    assert "index.html" not in report
    assert "start.html" not in report
    assert "reload.html" not in report
    assert "chrome.html" not in report

    pages_dir = tmp_path / "docs/product/pages"
    generated = sorted(p.name for p in pages_dir.glob("*.md"))
    assert generated == ["业务页面.md"]


def test_sync_from_prd_repairs_missing_frontmatter_fields(tmp_path: Path):
    run_cli("init-project", str(tmp_path), "--mode", "greenfield")
    page = tmp_path / "docs/product/pages/minimal.md"
    page.write_text(
        """---
route: /minimal
---
# 页面 PRD：最小页

## 1. 页面基础信息
## 2. 页面目标
## 3. 页面结构
## 4. 字段说明
## 5. 操作说明
## 6. 交互规则
## 7. 状态流转
## 8. 异常场景
## 9. 权限规则
## 10. 数据规则
## 11. 验收标准
""",
        encoding="utf-8",
    )
    result = run_cli("sync", str(tmp_path), "--from-prd")
    assert result.returncode == 0, result.stderr
    text = page.read_text(encoding="utf-8")
    assert "page_id: page-minimal" in text
    assert "feature_ids: [\"feat-minimal-core\"]" in text
    assert "change_ids: [\"chg-minimal-init\"]" in text


def test_check_consistency_harness_detects_docs_produc(tmp_path: Path):
    docs = tmp_path / "docs" / "produc"
    (docs / "pages").mkdir(parents=True)
    (docs / "changelog").mkdir(parents=True)
    (docs / "audit").mkdir(parents=True)
    (docs / ".index").mkdir(parents=True)
    (docs / "01-页面路由清单.md").write_text("# 页面路由清单\n\n", encoding="utf-8")
    (docs / "02-功能清单.md").write_text("# 功能清单\n\n", encoding="utf-8")

    script = ROOT / "scripts" / "check_consistency.sh"
    result = subprocess.run(
        ["bash", str(script), str(tmp_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "prd_root=docs/produc" in result.stdout


def test_check_consistency_harness_accepts_split_mode_flag(tmp_path: Path):
    docs = tmp_path / "docs" / "product"
    (docs / "pages").mkdir(parents=True)
    (docs / "changelog").mkdir(parents=True)
    (docs / "audit").mkdir(parents=True)
    (docs / ".index").mkdir(parents=True)
    (docs / "01-页面路由清单.md").write_text("# 页面路由清单\n\n", encoding="utf-8")
    (docs / "02-功能清单.md").write_text("# 功能清单\n\n", encoding="utf-8")

    script = ROOT / "scripts" / "check_consistency.sh"
    result = subprocess.run(
        ["bash", str(script), str(tmp_path), "--mode", "strict"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "mode=strict" in result.stdout


def test_diff_sync_treats_component_changes_as_code_changes(tmp_path: Path):
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(tmp_path), check=True)

    init = run_cli("init-project", str(tmp_path), "--mode", "greenfield")
    assert init.returncode == 0, init.stderr
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), check=True, capture_output=True, text=True)

    component = tmp_path / "components" / "FilterPanel.tsx"
    component.parent.mkdir(parents=True, exist_ok=True)
    component.write_text("export const FilterPanel = () => null;\n", encoding="utf-8")
    subprocess.run(["git", "add", str(component.relative_to(tmp_path))], cwd=str(tmp_path), check=True)

    result = run_cli("diff-sync", str(tmp_path), "--staged")
    assert result.returncode == 0, result.stderr

    report = tmp_path / f"docs/product/audit/{dt.date.today().isoformat()}-diff-sync.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "需执行 `prdctl sync --from-code`" in text
