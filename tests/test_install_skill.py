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
