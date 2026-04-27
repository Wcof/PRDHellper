from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install_skill.py"


def run_install(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INSTALL), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def load_install_module():
    scripts_dir = str((ROOT / "scripts").resolve())
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import install_skill  # type: ignore

    return install_skill


def test_reinstall_skip_when_existing(tmp_path: Path):
    first = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert first.returncode == 0, first.stderr
    second = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "skip",
    )
    assert second.returncode == 0, second.stderr
    assert "跳过" in second.stdout
    wakeup = tmp_path / "AI-PRD-WAKEUP-PROMPT.md"
    assert wakeup.exists()
    assert "create-prd 唤醒词" in wakeup.read_text(encoding="utf-8")


def test_reinstall_reset_creates_backup_and_migration_report(tmp_path: Path):
    first = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert first.returncode == 0, first.stderr

    page = tmp_path / "docs/prd/pages/legacy.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(
        "---\npage_id: page-legacy\nroute: /legacy\ncode_paths: [\"src/pages/legacy.tsx\"]\nfeature_ids: [\"feat-legacy-core\"]\nchange_ids: [\"chg-legacy-init\"]\nlast_synced_at: 2026-04-20\n---\n# 页面 PRD：Legacy\n",
        encoding="utf-8",
    )

    reset = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "reinstall-reset",
    )
    assert reset.returncode == 0, reset.stderr

    backups = list((tmp_path / "docs").glob("prd.backup-*"))
    assert backups, "expected backup directory after reinstall-reset"
    migration_root = tmp_path / "docs/prd/migrations"
    reports = list(migration_root.glob("**/migration-report.md"))
    assert reports, "expected migration report after reinstall-reset"
    # legacy 页面应保留在新目录或冲突目录之一
    migrated_page = tmp_path / "docs/prd/pages/legacy.md"
    conflict_page = next(iter(migration_root.glob("**/legacy.md")), None)
    assert migrated_page.exists() or conflict_page is not None


def test_existing_code_mode_emits_backfill_wakeup_prompt(tmp_path: Path):
    routes = tmp_path / "src" / "routes"
    routes.mkdir(parents=True)
    (routes / "index.ts").write_text(
        "export default [{ path: '/demo', name: '演示页', component: () => import('@/pages/demo/index.tsx') }]\n",
        encoding="utf-8",
    )
    result = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--init-mode",
        "existing-code",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert result.returncode == 0, result.stderr
    wakeup = tmp_path / "AI-PRD-WAKEUP-PROMPT.md"
    assert wakeup.exists()
    text = wakeup.read_text(encoding="utf-8")
    assert "已有页面补全 PRD" in text
    assert "scan-code" in text
    assert "check_consistency.sh" in text
    assert "文案规范建议" in text
    assert "CLAUDE.md" in text
    assert "不要写到 `PRDHellper/docs/`" in text
    assert ".agents/skills/create-prd/" in text
    assert "先创建目标项目根目录下的目录结构" in text
    assert f"目标项目根目录：{tmp_path}" in result.stdout
    assert f"PRD 文档目录：{tmp_path / 'docs/prd'}" in result.stdout
    assert f"页面级 PRD 目录：{tmp_path / 'docs/prd/pages'}" in result.stdout
    assert f"系统级 PRD 目录：{tmp_path / 'docs/prd/system'}" in result.stdout
    assert (tmp_path / "docs/prd/pages/demo.md").exists()
    assert (tmp_path / "docs/prd/changelog/demo-change.md").exists()
    assert (tmp_path / "docs/prd/01-页面路由清单.md").exists()


def test_greenfield_mode_creates_docs_prd_skeleton_without_pages(tmp_path: Path):
    result = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--init-mode",
        "greenfield",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "docs/prd/system").exists()
    assert (tmp_path / "docs/prd/pages").exists()
    assert (tmp_path / "docs/prd/imports").exists()
    assert not any((tmp_path / "docs/prd/pages").glob("*.md"))


def test_axure_mode_creates_docs_prd_skeleton_without_generating_pages(tmp_path: Path):
    result = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--init-mode",
        "axure",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "docs/prd/system").exists()
    assert (tmp_path / "docs/prd/pages").exists()
    assert (tmp_path / "docs/prd/imports").exists()
    assert not any((tmp_path / "docs/prd/pages").glob("*.md"))


def test_install_copies_harness_entry(tmp_path: Path):
    result = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert result.returncode == 0, result.stderr
    wrapper = tmp_path / ".agents/skills/create-prd/scripts/check_consistency.sh"
    harness = tmp_path / ".agents/skills/create-prd/scripts/harness/check_consistency.sh"
    readme = tmp_path / ".agents/skills/create-prd/scripts/harness/README.md"
    assert wrapper.exists()
    assert harness.exists()
    assert readme.exists()


def test_install_injects_discovery_block_into_agents_and_claude(tmp_path: Path):
    result = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert result.returncode == 0, result.stderr
    agents = tmp_path / "AGENTS.md"
    claude = tmp_path / "CLAUDE.md"
    agents_hidden = tmp_path / ".agents" / "AGENTS.md"
    claude_hidden = tmp_path / ".claude" / "CLAUDE.md"
    assert agents.exists()
    assert claude.exists()
    assert agents_hidden.exists()
    assert claude_hidden.exists()
    agents_text = agents.read_text(encoding="utf-8")
    claude_text = claude.read_text(encoding="utf-8")
    agents_hidden_text = agents_hidden.read_text(encoding="utf-8")
    claude_hidden_text = claude_hidden.read_text(encoding="utf-8")
    assert "<!-- create-prd:start -->" in agents_text
    assert ".agents/skills/create-prd/SKILL.md" in agents_text
    assert "文案规范建议审计" in agents_text
    assert "不要写到 `PRDHellper/docs/`" in agents_text
    assert ".agents/skills/create-prd/" in agents_text
    assert "<!-- create-prd:start -->" in claude_text
    assert ".agents/skills/create-prd/SKILL.md" in claude_text
    assert "文案规范建议审计" in claude_text
    assert "先把目标项目根目录下的目录建出来再写 Markdown 内容" in claude_text
    assert "<!-- create-prd:start -->" in agents_hidden_text
    assert ".agents/skills/create-prd/SKILL.md" in agents_hidden_text
    assert "<!-- create-prd:start -->" in claude_hidden_text
    assert ".agents/skills/create-prd/SKILL.md" in claude_hidden_text


def test_install_preserves_existing_agents_and_updates_discovery_block(tmp_path: Path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# existing\n\nkeep me\n", encoding="utf-8")
    claude = tmp_path / "CLAUDE.md"
    claude.write_text("# CLAUDE\n\nold\n", encoding="utf-8")

    result = run_install(
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert result.returncode == 0, result.stderr
    agents_text = agents.read_text(encoding="utf-8")
    claude_text = claude.read_text(encoding="utf-8")
    assert "keep me" in agents_text
    assert agents_text.count("<!-- create-prd:start -->") == 1
    assert ".agents/skills/create-prd/SKILL.md" in agents_text
    assert claude_text.count("<!-- create-prd:start -->") == 1


def test_status_flag_prints_status(tmp_path: Path):
    result = run_install("--status", "--project-root", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "Target Project:" in result.stdout
    assert "Skill:" in result.stdout
    assert "PRD Docs:" in result.stdout
    assert "AGENTS.md" in result.stdout
    assert "CLAUDE.md" in result.stdout
    assert "Python:" in result.stdout
    assert "Configure create-prd Skill" in result.stdout


def test_render_menu_marks_selected_option():
    mod = load_install_module()
    text = mod.render_menu("请选择操作", ["一键配置", "工具配置", "退出"], 1)
    assert "◆ 请选择操作" in text
    assert "  一键配置" in text
    assert "❯ 工具配置" in text


def test_handle_menu_key_moves_selects_and_cancels():
    mod = load_install_module()
    assert mod.handle_menu_key("down", 0, 3) == (1, "move")
    assert mod.handle_menu_key("up", 0, 3) == (2, "move")
    assert mod.handle_menu_key("enter", 1, 3) == (1, "select")
    assert mod.handle_menu_key("right", 1, 3) == (1, "select")
    assert mod.handle_menu_key("esc", 1, 3) == (1, "cancel")
    assert mod.handle_menu_key("left", 1, 3) == (1, "cancel")
    assert mod.handle_menu_key("q", 1, 3) == (1, "cancel")


def test_yes_bypasses_homepage_and_installs(tmp_path: Path):
    helper = tmp_path / "PRDHellper"
    helper.mkdir()
    result = subprocess.run(
        [sys.executable, str(INSTALL), "--yes"],
        cwd=str(helper),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (helper / ".agents/skills/create-prd/SKILL.md").exists()
    assert (helper / "docs/prd").exists()
    assert "请选择操作" not in result.stdout


def test_wizard_flag_preserves_old_wizard(tmp_path: Path):
    result = run_install(
        "--wizard",
        "--scope",
        "current",
        "--project-root",
        str(tmp_path),
        "--prd-root",
        "docs/prd",
        "--init-project",
        "--yes",
        "--on-existing",
        "reinstall",
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / ".agents/skills/create-prd/SKILL.md").exists()


def test_resolve_effective_project_root_uses_parent_for_helper_repo_root():
    mod = load_install_module()
    assert mod.resolve_effective_project_root(ROOT) == ROOT.parent


def test_run_install_writes_to_parent_when_project_root_points_to_helper(tmp_path: Path):
    helper_root = tmp_path / "PRDHellper"
    target_root = helper_root.parent
    helper_root.mkdir(parents=True)
    install_dir = target_root / ".agents/skills/create-prd"
    install_dir.mkdir(parents=True)
    docs_dir = target_root / "docs/prd/pages"
    docs_dir.mkdir(parents=True)
    (docs_dir / "legacy.md").write_text("# legacy\n", encoding="utf-8")

    mod = load_install_module()
    old_root = mod.SKILL_REPO_ROOT
    try:
        mod.SKILL_REPO_ROOT = helper_root.resolve()
        code = mod.run_wizard(
            mod.argparse.Namespace(
                scope="current",
                project_root=str(helper_root),
                prd_root="docs/prd",
                init_project=True,
                init_mode="greenfield",
                force=True,
                on_existing="reinstall-reset",
                yes=True,
                one_click=False,
                quick_mode=None,
                reset_docs=False,
            )
        )
        assert code == 0
    finally:
        mod.SKILL_REPO_ROOT = old_root

    assert (target_root / "AGENTS.md").exists()
    assert (target_root / "CLAUDE.md").exists()
    assert (target_root / "AI-PRD-WAKEUP-PROMPT.md").exists()
    assert (target_root / "docs/prd/system").exists()
    assert not (helper_root / "AGENTS.md").exists()
    assert not (helper_root / "docs").exists()
