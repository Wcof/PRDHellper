#!/usr/bin/env python3
"""
prdctl: create-prd 工程化辅助命令。

提供业务项目 PRD 目录初始化、代码路由扫描、Axure HTML 扫描、轻量一致性审计。
无第三方依赖，适合 Codex / Claude Code / 其他 Agent 调用。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "references" / "templates"
TODAY = _dt.date.today().isoformat()


def route_to_slug(route: str) -> str:
    route = route.strip() or "unknown"
    route = route.split("?")[0].split("#")[0]
    route = route.strip("/")
    if not route:
        return "index"
    slug = re.sub(r"[^A-Za-z0-9_\u4e00-\u9fa5/-]+", "-", route)
    slug = slug.replace("/", "-").strip("-")
    return slug or "unknown"


def safe_read(path: Path, limit: int = 500_000) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
        return data[:limit]
    except Exception:
        return ""


def write_if_missing(path: Path, content: str, force: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def load_template(name: str) -> str:
    p = TEMPLATES / name
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def render_template(text: str, **kwargs: str) -> str:
    for k, v in kwargs.items():
        text = text.replace("{" + k + "}", v)
    text = text.replace("{日期}", TODAY)
    return text


def init_project(project_root: Path, mode: str, prd_root: str = "docs/product", force: bool = False) -> None:
    root = project_root.resolve()
    docs = root / prd_root
    dirs = [
        docs,
        docs / "system-prd",
        docs / "pages",
        docs / "changelog",
        docs / "audit",
        docs / "imports",
        docs / "templates",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # copy templates
    for tpl in TEMPLATES.glob("*.md"):
        shutil.copy2(tpl, docs / "templates" / tpl.name)

    write_if_missing(root / "AGENTS.md", load_template("project-agents-template.md"), force=force)
    write_if_missing(docs / "00-项目上下文.md", f"# 项目上下文\n\n> 初始化模式：{mode}\n\n[TODO: 补充项目背景、系统定位、目标用户、核心业务流程、重要约束。]\n", force=force)
    write_if_missing(docs / "01-页面路由清单.md", load_template("route-inventory-template.md"), force=force)
    write_if_missing(docs / "02-功能清单.md", load_template("feature-list-template.md"), force=force)
    write_if_missing(docs / "03-全局交互规则.md", "# 全局交互规则\n\n[TODO: 补充新增、编辑、删除、搜索、筛选、分页、弹窗、抽屉、权限、空状态、错误状态等通用规则。]\n", force=force)
    write_if_missing(docs / "04-PRD编写规范.md", load_template("prd-writing-standard-template.md"), force=force)

    print(f"PRD 项目初始化完成: {docs}")
    print(f"模式: {mode}")
    print("已创建/更新模板、AGENTS.md 与 docs/product 基础文档。")


@dataclass
class RouteItem:
    route: str
    file: str
    name: str
    module: str = "[TODO: 所属模块]"


def scan_code_routes(project_root: Path) -> List[RouteItem]:
    root = project_root.resolve()
    explicit_files: List[Path] = []
    inferred_files: List[Path] = []

    for rel in ["src/router", "src/routes", "router", "routes"]:
        p = root / rel
        if p.exists():
            explicit_files.extend([x for x in p.rglob("*") if x.suffix.lower() in {".js", ".ts", ".tsx", ".jsx"}])

    for rel in ["src/pages", "src/views", "app", "pages"]:
        p = root / rel
        if p.exists():
            inferred_files.extend([x for x in p.rglob("*") if x.suffix.lower() in {".js", ".ts", ".tsx", ".jsx", ".vue", ".svelte"}])

    items: List[RouteItem] = []
    seen = set()
    route_patterns = [
        re.compile(r"path\s*:\s*['\"]([^'\"]+)['\"]"),
        re.compile(r"route\s*[:=]\s*['\"]([^'\"]+)['\"]"),
    ]
    name_patterns = [
        re.compile(r"name\s*:\s*['\"]([^'\"]+)['\"]"),
        re.compile(r"title\s*:\s*['\"]([^'\"]+)['\"]"),
        re.compile(r"meta\s*:\s*\{[^}]*title\s*:\s*['\"]([^'\"]+)['\"]", re.S),
    ]
    component_patterns = [
        re.compile(r"component\s*:\s*\(\)\s*=>\s*import\(['\"]([^'\"]+)['\"]\)"),
        re.compile(r"component\s*:\s*import\(['\"]([^'\"]+)['\"]\)"),
    ]

    # 1) 优先读取显式 router/routes。只要存在显式路由，就不再把 pages/views 文件强行推断为额外路由，避免重复。
    for f in explicit_files:
        text = safe_read(f)
        rel = str(f.relative_to(root))
        routes = []
        for pat in route_patterns:
            routes.extend(pat.findall(text))
        if not routes:
            continue
        names = []
        for pat in name_patterns:
            names.extend(pat.findall(text))
        comps = []
        for pat in component_patterns:
            comps.extend(pat.findall(text))
        for idx, r in enumerate(routes):
            key = r
            if key in seen:
                continue
            seen.add(key)
            name = names[idx] if idx < len(names) else (names[0] if names else route_to_slug(r))
            comp = comps[idx] if idx < len(comps) else (comps[0] if comps else rel)
            items.append(RouteItem(route=r, file=comp, name=name))

    if items:
        return items

    # 2) 没有显式路由时，兼容 Next/Nuxt/文件路由或普通 pages/views 目录。
    for f in inferred_files:
        rel = str(f.relative_to(root))
        stem = f.with_suffix("").relative_to(root)
        parts = list(stem.parts)
        for key in ["pages", "views", "app"]:
            if key in parts:
                idx = parts.index(key)
                route = "/" + "/".join(parts[idx + 1:])
                route = route.replace("/index", "") or "/"
                if route in seen:
                    continue
                seen.add(route)
                items.append(RouteItem(route=route, file=rel, name=f.stem))
                break
    return items

def write_route_inventory(project_root: Path, out_path: Path, items: List[RouteItem]) -> None:
    lines = ["# 页面路由清单", "", "| 所属模块 | 页面名称 | 页面路由 | 页面文件 | PRD 文件 | 当前状态 |", "|---|---|---|---|---|---|"]
    for it in items:
        slug = route_to_slug(it.route)
        prd = f"docs/product/pages/{slug}.md"
        lines.append(f"| {it.module} | {it.name} | `{it.route}` | `{it.file}` | `{prd}` | 待确认 |")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_page_prd(project_root: Path, route: str, page_name: str, page_file: str, prd_root: str = "docs/product", force: bool = False) -> Path:
    slug = route_to_slug(route)
    p = project_root / prd_root / "pages" / f"{slug}.md"
    tpl = load_template("page-prd-template.md")
    content = render_template(tpl, 页面名称=page_name, 页面路由=route, 页面文件=page_file)
    write_if_missing(p, content, force=force)
    c = project_root / prd_root / "changelog" / f"{slug}-change.md"
    ctpl = load_template("page-changelog-template.md")
    write_if_missing(c, render_template(ctpl, 页面名称=page_name), force=force)
    return p


def cmd_scan_code(args: argparse.Namespace) -> None:
    root = Path(args.project_root)
    items = scan_code_routes(root)
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path
    write_route_inventory(root, out_path, items)
    if args.create_prd:
        for it in items:
            create_page_prd(root, it.route, it.name, it.file, force=args.force)
    print(f"已识别页面/路由: {len(items)}")
    print(f"已输出: {out_path}")


def strip_html(raw: str) -> str:
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def extract_title(raw: str, fallback: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I|re.S)
    if m:
        t = strip_html(m.group(1)).strip()
        if t:
            return t[:80]
    for tag in ["h1", "h2"]:
        m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", raw, flags=re.I|re.S)
        if m:
            t = strip_html(m.group(1)).strip()
            if t:
                return t[:80]
    return fallback


def extract_ui_terms(raw: str) -> Tuple[List[str], List[str], List[str]]:
    text = strip_html(raw)
    # 按中文/英文片段粗略切分
    chunks = [c.strip() for c in re.split(r"[|｜。；;\n\r\t]+", text) if 1 <= len(c.strip()) <= 50]
    # buttons/links
    buttons = []
    for pat in [r"<button[^>]*>(.*?)</button>", r"<a[^>]*>(.*?)</a>"]:
        for m in re.findall(pat, raw, flags=re.I|re.S):
            v = strip_html(m)
            if v and len(v) <= 30:
                buttons.append(v)
    inputs = []
    for m in re.findall(r"<(?:input|textarea|select)[^>]*(?:placeholder|aria-label|title)=['\"]([^'\"]+)['\"]", raw, flags=re.I):
        if m.strip():
            inputs.append(html.unescape(m.strip()))
    return sorted(set(chunks))[:80], sorted(set(buttons))[:40], sorted(set(inputs))[:40]


def cmd_scan_axure(args: argparse.Namespace) -> None:
    html_root = Path(args.html_root).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd().resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = project_root / out_path
    pages = []
    for f in html_root.rglob("*.html"):
        if f.name.lower() in {"start.html"}:
            pass
        raw = safe_read(f, limit=1_000_000)
        title = extract_title(raw, f.stem)
        rel = str(f.relative_to(html_root))
        route = "/" + str(f.with_suffix("").relative_to(html_root)).replace(os.sep, "/")
        texts, buttons, inputs = extract_ui_terms(raw)
        pages.append((title, rel, route, texts, buttons, inputs))

    lines = ["# Axure HTML 页面导入清单", "", f"> 来源目录：`{html_root}`", "", "| 页面名称 | HTML 路径 | 推断路由 | 页面 PRD | 识别置信度 | 待确认项 |", "|---|---|---|---|---|---|"]
    for title, rel, route, texts, buttons, inputs in pages:
        slug = route_to_slug(route)
        prd = f"docs/product/pages/{slug}.md"
        confidence = "中" if texts or buttons or inputs else "低"
        lines.append(f"| {title} | `{rel}` | `{route}` | `{prd}` | {confidence} | 业务规则、权限、状态流转需确认 |")
        if args.create_prd:
            content = render_template(load_template("page-prd-template.md"), 页面名称=title, 页面路由=route, 页面文件=rel)
            extracted = ["", "## Axure 页面显性元素识别", "", "### 可见文本", ""]
            extracted += [f"- {x}" for x in texts[:30]] or ["- [TODO: 未识别到可见文本]"]
            extracted += ["", "### 按钮 / 链接", ""]
            extracted += [f"- {x}" for x in buttons[:30]] or ["- [TODO: 未识别到按钮/链接文本]"]
            extracted += ["", "### 表单线索", ""]
            extracted += [f"- {x}" for x in inputs[:30]] or ["- [TODO: 未识别到表单线索]"]
            extracted += ["", "> 注意：以上内容来自 HTML 静态结构识别，隐藏交互、动态面板、业务规则、权限和状态流转需人工确认。", ""]
            prd_path = project_root / "docs/product/pages" / f"{slug}.md"
            write_if_missing(prd_path, content + "\n" + "\n".join(extracted), force=args.force)
            changelog_path = project_root / "docs/product/changelog" / f"{slug}-change.md"
            write_if_missing(changelog_path, render_template(load_template("page-changelog-template.md"), 页面名称=title), force=args.force)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"已扫描 HTML 页面: {len(pages)}")
    print(f"已输出: {out_path}")


def cmd_audit(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    docs = root / args.prd_root
    pages = list((docs / "pages").glob("*.md")) if (docs / "pages").exists() else []
    route_inventory = docs / "01-页面路由清单.md"
    feature_list = docs / "02-功能清单.md"
    issues = []
    if not route_inventory.exists():
        issues.append(("路由清单缺失", "docs/product/01-页面路由清单.md", "未找到", "需要先执行 init-project / scan-code"))
    if not feature_list.exists():
        issues.append(("功能清单缺失", "docs/product/02-功能清单.md", "未找到", "需要创建功能清单"))
    for p in pages:
        txt = safe_read(p)
        for sec in ["页面基础信息", "页面目标", "页面结构", "字段说明", "操作说明", "交互规则", "状态流转", "异常场景", "权限规则", "数据规则", "验收标准"]:
            if sec not in txt:
                issues.append(("页面 PRD 章节缺失", str(p.relative_to(root)), sec, "补充该章节"))
    out_dir = docs / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{TODAY}-consistency-audit.md"
    lines = ["# 代码与 PRD 一致性审计", "", f"> 审计日期：{TODAY}", "", "## 审计结论", ""]
    lines.append(f"共发现 {len(issues)} 个显性问题。此脚本为轻量审计，复杂一致性仍需 Agent 结合代码语义复核。")
    lines += ["", "## 不一致问题清单", "", "| 问题类型 | 文件/页面 | 表现 | 建议修复 |", "|---|---|---|---|"]
    if issues:
        for t, f, show, fix in issues:
            lines.append(f"| {t} | `{f}` | {show} | {fix} |")
    else:
        lines.append("| 无显性问题 | - | - | - |")
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"审计完成: {out_file}")


def cmd_install(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    if args.mode == "codex-repo":
        dest = target / ".agents" / "skills" / "create-prd"
    elif args.mode == "claude-user":
        home = Path(os.environ.get("USERPROFILE", str(Path.home()))) if os.name == "nt" else Path.home()
        dest = home / ".claude" / "skills" / "create-prd"
    else:
        dest = target
    if dest.exists() and args.force:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for item in SKILL_ROOT.iterdir():
        if item.name in {".git", "__pycache__"}:
            continue
        target_item = dest / item.name
        if item.is_dir():
            if target_item.exists():
                shutil.rmtree(target_item)
            shutil.copytree(item, target_item, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
        else:
            shutil.copy2(item, target_item)
    print(f"已安装 create-prd Skill 到: {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description="create-prd 工程化辅助命令")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init-project", help="初始化业务项目 PRD 体系")
    p.add_argument("project_root")
    p.add_argument("--mode", choices=["greenfield", "existing-code", "axure"], default="greenfield")
    p.add_argument("--prd-root", default="docs/product")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=lambda a: init_project(Path(a.project_root), a.mode, a.prd_root, a.force))

    p = sub.add_parser("scan-code", help="扫描代码项目路由/页面")
    p.add_argument("project_root")
    p.add_argument("--out", default="docs/product/01-页面路由清单.md")
    p.add_argument("--create-prd", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_scan_code)

    p = sub.add_parser("scan-axure", help="扫描 Axure 导出 HTML")
    p.add_argument("html_root")
    p.add_argument("--project-root", default=None)
    p.add_argument("--out", default="docs/product/imports/axure-pages.md")
    p.add_argument("--create-prd", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_scan_axure)

    p = sub.add_parser("audit", help="轻量检查 PRD 目录完整性")
    p.add_argument("project_root")
    p.add_argument("--prd-root", default="docs/product")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("install", help="安装 Skill 到 Codex 项目或 Claude Code 用户目录")
    p.add_argument("target", nargs="?", default=".")
    p.add_argument("--mode", choices=["codex-repo", "claude-user", "raw-dir"], default="codex-repo")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_install)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
