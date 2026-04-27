#!/usr/bin/env python3
"""
create-prd 安装向导（简化入口）。

支持：
1) 当前项目 / 全局安装
2) 重复安装检测（跳过 / 重装 / 重装并重置文档）
3) 重置后自动备份与迁移（防止历史 PRD 丢失）
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

from prdctl import cmd_install, cmd_scan_code, init_project, safe_read

SKILL_REPO_ROOT = Path(__file__).resolve().parents[1]


def _ask(prompt: str, default: str) -> str:
    raw = input(f"{prompt} [{default}]: ").strip()
    return raw or default


def _ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    default = "Y/n" if default_yes else "y/N"
    raw = input(f"{prompt} ({default}): ").strip().lower()
    if not raw:
        return default_yes
    return raw in {"y", "yes"}


def _mode_to_project_init_mode(mode: str) -> str:
    if mode == "greenfield":
        return "greenfield"
    if mode == "existing-code":
        return "existing-code"
    return "axure"


def _default_project_root() -> Path:
    return resolve_effective_project_root(Path.cwd())


def resolve_effective_project_root(project_root: Path) -> Path:
    resolved = project_root.resolve()
    if resolved == SKILL_REPO_ROOT:
        return resolved.parent
    return resolved


def _current_install_dir(project_root: Path) -> Path:
    return project_root / ".agents" / "skills" / "create-prd"


def _global_install_dir() -> Path:
    return Path.home() / ".claude" / "skills" / "create-prd"


_LOGO = """
██████╗ ██████╗ ██████╗     ██╗  ██╗███████╗██╗     ██████╗ ███████╗██████╗
██╔══██╗██╔══██╗██╔══██╗    ██║  ██║██╔════╝██║     ██╔══██╗██╔════╝██╔══██╗
██████╔╝██████╔╝██║  ██║    ███████║█████╗  ██║     ██████╔╝█████╗  ██████╔╝
██╔═══╝ ██╔══██╗██║  ██║    ██╔══██║██╔══╝  ██║     ██╔═══╝ ██╔══╝  ██╔══██╗
██║     ██║  ██║██████╔╝    ██║  ██║███████╗███████╗██║     ███████╗██║  ██║
╚═╝     ╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝
""".strip()


def _get_version() -> str:
    readme = SKILL_REPO_ROOT / "README.md"
    if readme.exists():
        text = safe_read(readme, limit=10_000)
        m = re.search(r"v(\d+\.\d+\.\d+)", text)
        if m:
            return f"v{m.group(1)}"
    return "v0.1.0"


def _check_status(project_root: Path, prd_root: str) -> dict[str, tuple[bool, str]]:
    install_dir = _current_install_dir(project_root)
    prd_dir = project_root / prd_root
    return {
        "Target Project": (True, str(project_root)),
        "Skill": (install_dir.exists(), str(install_dir) if install_dir.exists() else "未安装"),
        "PRD Docs": (prd_dir.exists() and any(prd_dir.iterdir()), str(prd_dir) if prd_dir.exists() else "未创建"),
        "AGENTS.md": ((project_root / "AGENTS.md").exists(), ""),
        "CLAUDE.md": ((project_root / "CLAUDE.md").exists(), ""),
        "Python": (sys.version_info >= (3, 9), f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
    }


def render_homepage(project_root: Path, prd_root: str, status: dict[str, tuple[bool, str]] | None = None) -> None:
    print(_LOGO)
    print()
    print(f"{_get_version()} · Configure create-prd Skill for AI PRD workflow")
    print()
    print("一键配置")
    print("  ◆ Claude Code")
    print("  ◆ Codex")
    print("  ◆ Trae")
    print("  ◆ Other Agents")
    print()
    print("状态")
    if status is None:
        status = _check_status(project_root, prd_root)
    for name, (ok, detail) in status.items():
        marker = "✓" if ok else "✗"
        line = f"  {marker} {name}"
        if detail:
            line += f": {detail}"
        print(line)
    print()


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def read_key() -> str:
    if os.name == "nt":
        import msvcrt

        ch = msvcrt.getwch()
        if ch in {"\x00", "\xe0"}:
            code = msvcrt.getwch()
            return {
                "H": "up",
                "P": "down",
                "K": "left",
                "M": "right",
            }.get(code, code)
        if ch in {"\r", "\n"}:
            return "enter"
        if ch == "\x1b":
            return "esc"
        return ch

    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            return {
                "[A": "up",
                "[B": "down",
                "[D": "left",
                "[C": "right",
            }.get(seq, "esc")
        if ch in {"\r", "\n"}:
            return "enter"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def render_menu(title: str, options: list[str], selected: int) -> str:
    lines = [f"◆ {title}"]
    for idx, option in enumerate(options):
        prefix = "❯" if idx == selected else " "
        lines.append(f"{prefix} {option}")
    return "\n".join(lines)


def handle_menu_key(key: str, selected: int, count: int) -> tuple[int, str]:
    if key == "up":
        return (selected - 1) % count, "move"
    if key == "down":
        return (selected + 1) % count, "move"
    if key in {"enter", "right"}:
        return selected, "select"
    if key in {"left", "esc", "q", "Q"}:
        return selected, "cancel"
    return selected, "noop"


def choose_menu(title: str, options: list[str], selected: int = 0, redraw=None) -> Optional[int]:
    while True:
        clear_screen()
        if redraw:
            redraw()
        print(render_menu(title, options, selected))
        print("\n↑/↓ 移动，Enter/→ 确认，Esc/←/q 退出")
        key = read_key()
        selected, action = handle_menu_key(key, selected, len(options))
        if action == "select":
            return selected
        if action == "cancel":
            return None
    print(f"{_get_version()} · Configure create-prd Skill for AI PRD workflow")
    print()
    print("一键配置")
    print("  ◆ Claude Code")
    print("  ◆ Codex")
    print("  ◆ Trae")
    print("  ◆ Other Agents")
    print()
    print("状态")
    if status is None:
        status = _check_status(project_root, prd_root)
    for name, (ok, detail) in status.items():
        marker = "✓" if ok else "✗"
        line = f"  {marker} {name}"
        if detail:
            line += f": {detail}"
        print(line)
    print()


DISCOVERY_BLOCK_START = "<!-- create-prd:start -->"
DISCOVERY_BLOCK_END = "<!-- create-prd:end -->"


def _discovery_block_content(prd_root: str) -> str:
    return "\n".join(
        [
            DISCOVERY_BLOCK_START,
            "## create-prd",
            "",
            "当任务涉及 PRD 初始化、页面 PRD、完整 PRD、Axure HTML 导入、页面变更同步 PRD、代码与 PRD 一致性审计时：",
            "",
            "1. 优先阅读 `.agents/skills/create-prd/SKILL.md`。",
            f"2. PRD 输出目录固定写到目标项目根目录下的 `{prd_root}`，不要写到 `PRDHellper/docs/` 或 `.agents/skills/create-prd/` 内。",
            f"3. 如果 `{prd_root}` 或其子目录不存在，先执行 `python .agents/skills/create-prd/scripts/prdctl.py init-project . --mode existing-code --prd-root {prd_root}`，先把目标项目根目录下的目录建出来再写 Markdown 内容。",
            "4. 完成后执行：`bash .agents/skills/create-prd/scripts/check_consistency.sh . --mode=strict`（包含结构一致性与文案规范建议审计）。",
            "5. 如果目标项目没有 Python，可跳过脚本命令，直接按 `.agents/skills/create-prd/SKILL.md` 与项目 AGENTS 规则手工维护 PRD 文档。",
            "6. 如果仓库里还有其他 `SKILL.md` 或说明文件，不要把它们当作 create-prd 本体。",
            "",
            DISCOVERY_BLOCK_END,
        ]
    )


def _upsert_discovery_block(path: Path, heading: str, prd_root: str) -> Path:
    block = _discovery_block_content(prd_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = safe_read(path, limit=2_000_000) if path.exists() else ""
    if DISCOVERY_BLOCK_START in text and DISCOVERY_BLOCK_END in text:
        start = text.index(DISCOVERY_BLOCK_START)
        end = text.index(DISCOVERY_BLOCK_END, start) + len(DISCOVERY_BLOCK_END)
        new_text = text[:start].rstrip() + "\n\n" + block + text[end:]
    elif text.strip():
        new_text = text.rstrip() + "\n\n" + block + "\n"
    else:
        new_text = f"# {heading}\n\n{block}\n"
    path.write_text(new_text, encoding="utf-8")
    print(f"已更新 create-prd 引导块：{path}")
    return path


def _ensure_discovery_files(project_root: Path, prd_root: str) -> None:
    _upsert_discovery_block(project_root / "AGENTS.md", "AGENTS", prd_root)
    _upsert_discovery_block(project_root / "CLAUDE.md", "CLAUDE", prd_root)
    _upsert_discovery_block(project_root / ".agents" / "AGENTS.md", "AGENTS", prd_root)
    _upsert_discovery_block(project_root / ".claude" / "CLAUDE.md", "CLAUDE", prd_root)


def _ensure_unique_backup_path(path: Path) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = path.parent / f"{path.name}.backup-{ts}"
    idx = 1
    while candidate.exists():
        candidate = path.parent / f"{path.name}.backup-{ts}-{idx}"
        idx += 1
    return candidate


def _copy_with_conflict(src: Path, dst: Path, conflict_root: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)
        return
    src_text = safe_read(src, limit=2_000_000)
    dst_text = safe_read(dst, limit=2_000_000)
    if src_text == dst_text:
        return
    conflict = conflict_root / src.name
    conflict_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, conflict)


def _reset_and_migrate_prd(project_root: Path, prd_root: str, init_mode: str) -> Optional[Path]:
    prd_path = project_root / prd_root
    backup_path: Optional[Path] = None
    if prd_path.exists():
        backup_path = _ensure_unique_backup_path(prd_path)
        shutil.move(str(prd_path), str(backup_path))
        print(f"已备份旧 PRD 目录到：{backup_path}")

    init_project(project_root, _mode_to_project_init_mode(init_mode), prd_root=prd_root, force=True)

    if not backup_path:
        return None

    new_root = project_root / prd_root
    migration_root = new_root / "migrations" / backup_path.name
    copied = 0
    conflicts = 0

    migrate_pairs = [
        ("pages", "pages"),
        ("changelog", "changelog"),
        ("system-prd", "system"),
        ("system", "system"),
        ("imports", "imports"),
    ]

    for old_sub, new_sub in migrate_pairs:
        old_dir = backup_path / old_sub
        if not old_dir.exists():
            continue
        for src in old_dir.rglob("*.md"):
            rel = src.relative_to(old_dir)
            dst = new_root / new_sub / rel
            before = dst.exists()
            _copy_with_conflict(src, dst, migration_root / "conflicts" / new_sub / rel.parent)
            if not before and dst.exists():
                copied += 1
            elif before and (migration_root / "conflicts" / new_sub / rel.parent / src.name).exists():
                conflicts += 1

    # 顶层规范文档统一放到迁移目录，避免直接覆盖新模板。
    for name in [
        "00-项目上下文.md",
        "01-页面路由清单.md",
        "02-功能清单.md",
        "03-全局交互规则.md",
        "04-PRD编写规范.md",
    ]:
        src = backup_path / name
        if src.exists():
            target = migration_root / "legacy-root-files" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)

    report = migration_root / "migration-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "\n".join(
            [
                "# PRD 重置迁移报告",
                "",
                f"- 迁移时间：{dt.datetime.now().isoformat(timespec='seconds')}",
                f"- 备份目录：`{backup_path}`",
                f"- 新目录：`{new_root}`",
                f"- 自动迁移文件数：{copied}",
                f"- 冲突文件数：{conflicts}",
                "",
                "## 说明",
                "",
                "- 自动迁移：`pages/`、`changelog/`、`system-prd/` / `system/`、`imports/` 下的 Markdown 文档。",
                "- 冲突文档放在 `conflicts/`，需人工比对合并。",
                "- 顶层规范文档旧版本放在 `legacy-root-files/`，按需手动合并。",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"已生成迁移报告：{report}")
    return backup_path


def _choose_existing_action(args: argparse.Namespace, install_exists: bool, prd_exists: bool) -> str:
    if not install_exists and not prd_exists:
        return "install"
    if args.on_existing:
        return args.on_existing
    if args.yes:
        return "skip"

    print("\n检测到已存在历史安装或文档：")
    if install_exists:
        print("- Skill 已安装")
    if prd_exists:
        print("- PRD 文档目录已存在")
    print("请选择处理方式：")
    print("1) 保留现状（跳过）")
    print("2) 仅重装 Skill（不动文档）")
    print("3) 重装 Skill + 重置并迁移 PRD 文档")
    choice = _ask("输入 1/2/3", "1")
    return {"1": "skip", "2": "reinstall", "3": "reinstall-reset"}.get(choice, "skip")


def _emit_agent_wakeup_prompt(project_root: Path, prd_root: str, reason: str, scene: str = "generic") -> Path:
    if scene == "existing-code-backfill":
        title = "# create-prd 补全唤醒词（已有页面补全 PRD）"
        body = [
            "请在当前仓库执行“已有代码项目 PRD 补全”：",
            "1. 先阅读项目根目录 `AGENTS.md` 与 `CLAUDE.md`，再继续阅读 `.agents/skills/create-prd/SKILL.md`。",
            f"2. 所有 PRD 产物都写到目标项目根目录下的 `{prd_root}`，不要写到 `PRDHellper/docs/` 或 `.agents/skills/create-prd/` 内。",
            f"3. 若 `{prd_root}` 不存在，先执行 `python .agents/skills/create-prd/scripts/prdctl.py init-project . --mode existing-code --prd-root {prd_root}`，先创建目标项目根目录下的目录结构。",
            f"4. 扫描现有路由和页面，并补齐页面 PRD / 功能清单 / 变更记录。重点补齐目录：`{prd_root}/pages`、`{prd_root}/02-功能清单.md`、`{prd_root}/changelog`。",
            f"5. 执行并汇报：`python .agents/skills/create-prd/scripts/prdctl.py scan-code . --create-prd --prd-root {prd_root}`、`bash .agents/skills/create-prd/scripts/check_consistency.sh . --mode=strict`。该入口会自动同步，并输出结构审计与文案规范建议。",
            "6. 如果没有 Python，跳过脚本执行，直接按 Skill 规则补全页面 PRD 与清单，并显式标注 `[TODO: ...]`。",
            "7. 输出：补全了哪些页面、哪些仍待确认（TODO）。",
        ]
    else:
        title = "# create-prd 唤醒词（复制到你的 AI 对话中）"
        body = [
            "请在当前仓库按 create-prd 方式继续推进 PRD 同步：",
            "1. 先阅读项目根目录 `AGENTS.md` 与 `CLAUDE.md`，再继续阅读 `.agents/skills/create-prd/SKILL.md`。",
            f"2. 所有 PRD 产物都写到目标项目根目录下的 `{prd_root}`，不要写到 `PRDHellper/docs/` 或 `.agents/skills/create-prd/` 内。",
            f"3. 若 `{prd_root}` 不存在，先执行 `python .agents/skills/create-prd/scripts/prdctl.py init-project . --mode existing-code --prd-root {prd_root}`，先创建目标项目根目录下的目录结构。",
            f"4. 阅读 `{prd_root}` 下已有文档（至少 `00-项目上下文.md`、`01-页面路由清单.md`、`02-功能清单.md`）。",
            "5. 基于当前代码与路由，补齐或更新页面 PRD、功能清单、变更记录。",
            f"6. 执行并汇报：`bash .agents/skills/create-prd/scripts/check_consistency.sh . --mode=strict`。该入口会自动同步，并输出结构审计与文案规范建议。",
            "7. 如果没有 Python，跳过脚本执行，直接按 Skill 规则完成文档更新并输出一致性结论。",
        ]

    prompt = "\n".join(
        [
            title,
            "",
            *body,
            "",
            f"说明：本次安装状态为「{reason}」。",
            "",
        ]
    )
    out = project_root / "AI-PRD-WAKEUP-PROMPT.md"
    out.write_text(prompt, encoding="utf-8")
    print("\n已生成 AI 唤醒词，可直接复制到你使用的大模型：")
    print(f"- 文件：{out}")
    print("----- 复制以下内容 -----")
    print(prompt)
    print("----- 复制结束 -----")
    return out


def _bootstrap_existing_code_prd(project_root: Path, prd_root: str) -> None:
    cmd_scan_code(
        argparse.Namespace(
            project_root=str(project_root),
            out=f"{prd_root}/01-页面路由清单.md",
            prd_root=prd_root,
            create_prd=True,
            force=False,
        )
    )
    print(f"已为已有代码项目生成页面级 PRD 草稿：{project_root / prd_root / 'pages'}")


def run_status(args: argparse.Namespace) -> int:
    project_root = resolve_effective_project_root(Path(args.project_root)) if args.project_root else _default_project_root()
    prd_root = args.prd_root
    status = _check_status(project_root, prd_root)
    render_homepage(project_root, prd_root, status)
    return 0


def run_tool_config(args: argparse.Namespace) -> int:
    choice = choose_menu("工具配置", ["当前项目", "全局 Claude 用户目录", "返回"])
    if choice is None or choice == 2:
        return 0
    new_args = argparse.Namespace(**vars(args))
    if choice == 1:
        new_args.quick_mode = "global"
    else:
        new_args.quick_mode = "existing-code"
    return run_one_click(new_args)


def run_prd_config(args: argparse.Namespace) -> int:
    print("\n== PRD 目录配置 ==")
    prd_root = input(f"PRD 文档目录名 [{args.prd_root}]: ").strip() or args.prd_root
    new_args = argparse.Namespace(**vars(args))
    new_args.prd_root = prd_root
    new_args.quick_mode = "existing-code"
    return run_one_click(new_args)


def run_homepage_menu(args: argparse.Namespace) -> int:
    try:
        while True:
            project_root = resolve_effective_project_root(Path(args.project_root)) if args.project_root else _default_project_root()
            prd_root = args.prd_root
            choice = choose_menu(
                "请选择操作",
                ["一键配置", "工具配置", "PRD 目录配置", "状态检查", "退出"],
                redraw=lambda: render_homepage(project_root, prd_root, _check_status(project_root, prd_root)),
            )

            if choice is None or choice == 4:
                print("已退出。")
                return 0
            if choice == 0:
                return run_one_click(args)
            elif choice == 1:
                return run_tool_config(args)
            elif choice == 2:
                return run_prd_config(args)
            elif choice == 3:
                clear_screen()
                run_status(args)
                input("\n按 Enter 返回主菜单...")
    except KeyboardInterrupt:
        print("\n已退出。")
        return 0


def run_wizard(args: argparse.Namespace) -> int:
    print("== create-prd 安装向导 ==")
    print("你可以安装到当前项目（推荐）或全局目录。")

    scope = args.scope
    if not scope:
        choice = _ask("选择安装范围：1) 当前项目 2) 全局", "1")
        scope = "current" if choice == "1" else "global"

    if scope == "current":
        project_root = resolve_effective_project_root(Path(args.project_root)) if args.project_root else _default_project_root()
        if not args.yes:
            project_root = resolve_effective_project_root(Path(_ask("业务项目路径", str(project_root))))
        prd_root = args.prd_root
        if not args.yes:
            print("PRD 文档目录会自动创建，不需要你手动新建。")
            prd_root = _ask("PRD 文档目录名（用于存放每个页面 PRD）", prd_root)

        init_needed = args.init_project
        if not args.yes and not args.init_project:
            init_needed = _ask_yes_no("是否现在初始化 PRD 目录结构", default_yes=True)
        if args.yes and not args.init_project:
            init_needed = True

        init_mode = args.init_mode
        if init_needed and not args.yes:
            print("初始化模式说明：")
            print("1) 新项目（推荐）：从零开始建立 PRD 体系")
            print("2) 已有代码项目：先扫代码再补 PRD")
            print("3) Axure HTML 项目：从 Axure 导出页面反向生成 PRD")
            init_choice = _ask("请选择模式（1/2/3）", "1")
            init_mode = {"1": "greenfield", "2": "existing-code", "3": "axure"}.get(init_choice, "greenfield")

        install_dir = _current_install_dir(project_root)
        prd_dir = project_root / prd_root
        action = _choose_existing_action(
            args,
            install_exists=install_dir.exists(),
            prd_exists=prd_dir.exists() and any(prd_dir.iterdir()),
        )

        print("\n将执行：")
        print(f"- 安装位置：{install_dir}")
        print(f"- 目标项目根目录：{project_root}")
        print(f"- PRD 文档目录：{prd_dir}（自动创建）")
        print(f"- 页面级 PRD 目录：{prd_dir / 'pages'}")
        print(f"- 系统级 PRD 目录：{prd_dir / 'system'}")
        if init_needed:
            print(f"- 初始化 PRD 目录：{prd_dir} (mode={init_mode})")
        else:
            print("- 跳过初始化，仅安装 Skill")
        print(f"- 重复安装处理策略：{action}")

        if not args.yes and not _ask_yes_no("确认执行", default_yes=True):
            print("已取消。")
            return 1

        if action == "skip":
            print("检测到已安装，已按你的选择跳过。")
            _emit_agent_wakeup_prompt(project_root, prd_root, reason="重复安装-跳过")
            return 0

        force_install = action in {"reinstall", "reinstall-reset"} or args.force
        cmd_install(
            argparse.Namespace(
                target=str(project_root),
                mode="codex-repo",
                force=force_install,
            )
        )

        if init_needed:
            if action == "reinstall-reset":
                _reset_and_migrate_prd(project_root, prd_root, init_mode)
            else:
                init_project(project_root, _mode_to_project_init_mode(init_mode), prd_root=prd_root, force=False)
            if init_mode == "existing-code":
                _bootstrap_existing_code_prd(project_root, prd_root)
            print(f"已完成：PRD 文件将存放在 {prd_dir}")
            print(f"页面级 PRD 输出目录：{prd_dir / 'pages'}")
            print(f"系统级 PRD 输出目录：{prd_dir / 'system'}")
        _ensure_discovery_files(project_root, prd_root)
        if init_needed and init_mode == "existing-code":
            _emit_agent_wakeup_prompt(
                project_root,
                prd_root,
                reason="已有代码项目-补全模式",
                scene="existing-code-backfill",
            )
        else:
            wakeup_reason = "安装完成-未初始化" if not init_needed else f"初始化完成-{init_mode}"
            _emit_agent_wakeup_prompt(project_root, prd_root, reason=wakeup_reason)
        return 0

    install_dir = _global_install_dir()
    exists = install_dir.exists()
    action = args.on_existing or ("skip" if (exists and args.yes) else "install")
    if exists and not args.on_existing and not args.yes:
        print(f"\n检测到全局已安装：{install_dir}")
        print("请选择处理方式：1) 跳过 2) 重装")
        c = _ask("输入 1/2", "1")
        action = "skip" if c == "1" else "reinstall"

    print(f"\n将执行全局安装：{install_dir}")
    print(f"- 重复安装处理策略：{action}")
    if not args.yes and not _ask_yes_no("确认执行", default_yes=True):
        print("已取消。")
        return 1
    if action == "skip":
        print("检测到已安装，已按你的选择跳过。")
        return 0
    cmd_install(
        argparse.Namespace(
            target=".",
            mode="claude-user",
            force=True,
        )
    )
    print("已完成全局安装。")
    return 0


def run_one_click(args: argparse.Namespace) -> int:
    """
    一键安装：仅选择模式，其他参数全部采用安全默认值并直接执行。
    """
    mode = args.quick_mode
    if not mode:
        if args.yes or not sys.stdin.isatty():
            mode = "existing-code"
        else:
            print("== create-prd 一键安装 ==")
            print("请选择安装场景：")
            print("1) 当前项目（已有代码，推荐）")
            print("2) 当前项目（新项目）")
            print("3) 当前项目（Axure HTML）")
            print("4) 全局安装（Claude 用户目录）")
            choice = _ask("输入 1/2/3/4", "1")
            mode = {"1": "existing-code", "2": "greenfield", "3": "axure", "4": "global"}.get(choice, "existing-code")

    if mode == "global":
        auto_args = argparse.Namespace(
            scope="global",
            project_root=None,
            prd_root=args.prd_root,
            init_project=False,
            init_mode="greenfield",
            force=True,
            on_existing=args.on_existing or "reinstall",
            yes=True,
            one_click=False,
            quick_mode=None,
            reset_docs=False,
        )
        return run_wizard(auto_args)

    project_root = resolve_effective_project_root(Path(args.project_root)) if args.project_root else _default_project_root()
    on_existing = args.on_existing or ("reinstall-reset" if args.reset_docs else "reinstall")
    auto_args = argparse.Namespace(
        scope="current",
        project_root=str(project_root),
        prd_root=args.prd_root,
        init_project=True,
        init_mode=mode,
        force=True,
        on_existing=on_existing,
        yes=True,
        one_click=False,
        quick_mode=None,
        reset_docs=args.reset_docs,
    )
    return run_wizard(auto_args)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="create-prd 安装向导")
    p.add_argument("--one-click", action="store_true", help="一键安装：只选模式，其他配置使用默认值并自动执行")
    p.add_argument("--wizard", action="store_true", help="进入传统安装向导（保留旧交互）")
    p.add_argument("--status", action="store_true", help="只读状态检查，打印当前安装状态")
    p.add_argument(
        "--quick-mode",
        choices=["existing-code", "greenfield", "axure", "global"],
        default=None,
        help="一键安装模式（不传则交互选择）",
    )
    p.add_argument("--reset-docs", action="store_true", help="一键安装时重置并迁移 PRD 文档（等价 on-existing=reinstall-reset）")
    p.add_argument("--scope", choices=["current", "global"], help="安装范围（不传则进入向导）")
    p.add_argument("--project-root", default=None, help="目标项目根目录（scope=current 时有效；若当前目录是 PRDHellper，则默认使用其上一级目录）")
    p.add_argument("--prd-root", default="docs/prd", help="当前项目 PRD 根目录")
    p.add_argument("--init-project", action="store_true", help="安装后立即初始化 PRD 目录（默认交互模式下为是）")
    p.add_argument("--init-mode", choices=["greenfield", "existing-code", "axure"], default="greenfield", help="初始化模式")
    p.add_argument("--force", action="store_true", help="强制覆盖安装 Skill（一般由重复安装策略自动控制）")
    p.add_argument("--on-existing", choices=["skip", "reinstall", "reinstall-reset"], help="检测到重复安装时的处理策略")
    p.add_argument("--yes", action="store_true", help="非交互确认，直接执行")
    return p


def _has_wizard_flags(args: argparse.Namespace) -> bool:
    return bool(
        args.scope
        or args.project_root
        or args.init_project
        or args.init_mode != "greenfield"
        or args.on_existing
    )


def _is_bare_invocation(args: argparse.Namespace) -> bool:
    return not (
        args.wizard
        or args.status
        or args.yes
        or args.one_click
        or args.quick_mode
        or args.reset_docs
        or args.force
        or _has_wizard_flags(args)
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.wizard:
        code = run_wizard(args)
    elif args.status:
        code = run_status(args)
    elif args.one_click or args.quick_mode or args.reset_docs:
        code = run_one_click(args)
    elif args.yes and not _has_wizard_flags(args):
        code = run_one_click(args)
    elif not sys.stdin.isatty() and not _has_wizard_flags(args):
        code = run_one_click(args)
    elif _is_bare_invocation(args) and sys.stdin.isatty():
        code = run_homepage_menu(args)
    else:
        code = run_wizard(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
