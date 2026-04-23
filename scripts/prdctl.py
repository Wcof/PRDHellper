#!/usr/bin/env python3
"""
prdctl: create-prd 工程化辅助命令。

提供业务项目 PRD 目录初始化、代码路由扫描、Axure HTML 扫描、
traceability 同步、diff 驱动同步建议、分级一致性审计。
无第三方依赖，适合 Codex / Claude Code / 其他 Agent 调用。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import html
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "references" / "templates"
TODAY = _dt.date.today().isoformat()
REQUIRED_PAGE_SECTIONS = [
    "页面基础信息",
    "页面目标",
    "页面结构",
    "字段说明",
    "操作说明",
    "交互规则",
    "状态流转",
    "异常场景",
    "权限规则",
    "数据规则",
    "验收标准",
]
CODE_PATH_PREFIXES = (
    "src/",
    "app/",
    "pages/",
    "views/",
    "router/",
    "routes/",
    "components/",
    "layouts/",
    "features/",
    "modules/",
    "store/",
    "stores/",
    "service/",
    "services/",
    "api/",
    "mock/",
    "mocks/",
    "lib/",
    "utils/",
    "hooks/",
    "composables/",
    "constants/",
    "types/",
    "schemas/",
    "models/",
)
CODE_FILE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".css", ".scss", ".sass", ".less", ".styl", ".json"}


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


def is_code_related_path(path: str, prd_root: Optional[str] = None) -> bool:
    normalized = path.strip().replace("\\", "/")
    if not normalized:
        return False
    if prd_root:
        root_prefix = prd_root.strip("/").replace("\\", "/") + "/"
        if normalized.startswith(root_prefix):
            return False
    if normalized.startswith("docs/") or normalized.endswith(".md"):
        return False
    if normalized.startswith(CODE_PATH_PREFIXES):
        return True
    return Path(normalized).suffix.lower() in CODE_FILE_EXTENSIONS


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


def parse_value(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        values = []
        for part in inner.split(","):
            v = part.strip().strip("'").strip('"')
            if v:
                values.append(v)
        return values
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    return raw.strip("'").strip('"')


def format_value(value: Any) -> str:
    if isinstance(value, list):
        quoted = [json.dumps(str(x), ensure_ascii=False) for x in value]
        return "[" + ", ".join(quoted) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    meta_block = text[4:end]
    body = text[end + 5 :]
    meta: Dict[str, Any] = {}
    for line in meta_block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = parse_value(v)
    return meta, body


def dump_frontmatter(meta: Dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key in ["page_id", "route", "code_paths", "feature_ids", "change_ids", "last_synced_at"]:
        if key in meta:
            lines.append(f"{key}: {format_value(meta[key])}")
    for key, value in meta.items():
        if key not in {"page_id", "route", "code_paths", "feature_ids", "change_ids", "last_synced_at"}:
            lines.append(f"{key}: {format_value(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body.lstrip("\n")


def _split_table_blocks(text: str) -> List[List[str]]:
    blocks: List[List[str]] = []
    current: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("|"):
            current.append(line)
            continue
        if current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _parse_table_block(lines: List[str]) -> Tuple[List[str], List[Dict[str, str]]]:
    if len(lines) < 2:
        return [], []
    headers = [c.strip() for c in lines[0].strip("|").split("|")]
    sep = [c.strip() for c in lines[1].strip("|").split("|")]
    if not headers or not all(re.fullmatch(r"-+", c) for c in sep):
        return [], []
    rows: List[Dict[str, str]] = []
    for line in lines[2:]:
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < len(headers):
            cols.extend([""] * (len(headers) - len(cols)))
        rows.append({headers[i]: cols[i] for i in range(len(headers))})
    return headers, rows


def parse_markdown_table(text: str, required_headers: Optional[List[str]] = None) -> Tuple[List[str], List[Dict[str, str]]]:
    blocks = _split_table_blocks(text)
    if not blocks:
        return [], []

    parsed: List[Tuple[List[str], List[Dict[str, str]]]] = []
    for block in blocks:
        headers, rows = _parse_table_block(block)
        if headers:
            parsed.append((headers, rows))
    if not parsed:
        return [], []

    if not required_headers:
        return parsed[0]

    req = set(required_headers)
    best_score = -1
    best: Tuple[List[str], List[Dict[str, str]]] = ([], [])
    for headers, rows in parsed:
        score = len(req.intersection(set(headers)))
        if score > best_score:
            best_score = score
            best = (headers, rows)
    return best


def markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    sep = ["---"] * len(headers)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(sep) + " |"]
    for row in rows:
        fixed = row + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(fixed[: len(headers)]) + " |")
    return "\n".join(lines)


def normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if not value:
        return []
    return [str(value).strip()]


def normalize_id_list(value: Any) -> List[str]:
    if isinstance(value, list):
        parts = [str(x).strip() for x in value if str(x).strip()]
    elif value:
        parts = [str(value).strip()]
    else:
        parts = []
    out: List[str] = []
    for part in parts:
        for token in re.split(r"[,，;\n]+", part):
            v = token.strip().strip("`")
            if v:
                out.append(v)
    return sorted(set(out))


def is_placeholder(value: str) -> bool:
    raw = parse_backticked(value).strip()
    if not raw:
        return True
    upper = raw.upper()
    return raw.startswith("[TODO") or "TODO" in upper


def parse_backticked(value: str) -> str:
    return value.replace("`", "").strip()


def ensure_prd_dirs(project_root: Path, prd_root: str = "docs/prd") -> Path:
    docs = project_root / prd_root
    for d in [
        docs,
        docs / "system",
        docs / "pages",
        docs / "changelog",
        docs / "audit",
        docs / "imports",
        docs / "templates",
        docs / ".index",
    ]:
        d.mkdir(parents=True, exist_ok=True)
    return docs


def init_project(project_root: Path, mode: str, prd_root: str = "docs/prd", force: bool = False) -> None:
    root = project_root.resolve()
    docs = ensure_prd_dirs(root, prd_root=prd_root)

    for tpl in TEMPLATES.glob("*.md"):
        shutil.copy2(tpl, docs / "templates" / tpl.name)

    write_if_missing(
        root / "AGENTS.md",
        render_template(load_template("project-agents-template.md"), PRD_ROOT=prd_root),
        force=force,
    )
    write_if_missing(
        docs / "00-项目上下文.md",
        f"# 项目上下文\n\n> 初始化模式：{mode}\n\n[TODO: 补充项目背景、系统定位、目标用户、核心业务流程、重要约束。]\n",
        force=force,
    )
    write_if_missing(docs / "01-页面路由清单.md", load_template("route-inventory-template.md"), force=force)
    write_if_missing(docs / "02-功能清单.md", load_template("feature-list-template.md"), force=force)
    write_if_missing(
        docs / "03-全局交互规则.md",
        "# 全局交互规则\n\n[TODO: 补充新增、编辑、删除、搜索、筛选、分页、弹窗、抽屉、权限、空状态、错误状态等通用规则。]\n",
        force=force,
    )
    write_if_missing(docs / "04-PRD编写规范.md", load_template("prd-writing-standard-template.md"), force=force)
    write_traceability_index(root, prd_root=prd_root)
    print(f"PRD 项目初始化完成: {docs}")
    print(f"模式: {mode}")
    print(f"已创建/更新模板、AGENTS.md 与 {prd_root} 基础文档。")


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
            if r in seen:
                continue
            seen.add(r)
            name = names[idx] if idx < len(names) else (names[0] if names else route_to_slug(r))
            comp = comps[idx] if idx < len(comps) else (comps[0] if comps else rel)
            items.append(RouteItem(route=r, file=comp, name=name))

    if items:
        return items

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


def make_page_id(route: str) -> str:
    return f"page-{route_to_slug(route)}"


def make_feature_id(route: str) -> str:
    return f"feat-{route_to_slug(route)}-core"


def make_change_id(route: str) -> str:
    return f"chg-{route_to_slug(route)}-init"


def upsert_frontmatter(path: Path, updates: Dict[str, Any]) -> Dict[str, Any]:
    text = safe_read(path)
    meta, body = parse_frontmatter(text)
    meta.update(updates)
    if "last_synced_at" not in meta:
        meta["last_synced_at"] = TODAY
    path.write_text(dump_frontmatter(meta, body), encoding="utf-8")
    return meta


def create_page_prd(
    project_root: Path,
    route: str,
    page_name: str,
    page_file: str,
    prd_root: str = "docs/prd",
    force: bool = False,
) -> Path:
    slug = route_to_slug(route)
    page_id = make_page_id(route)
    feature_id = make_feature_id(route)
    change_id = make_change_id(route)
    p = project_root / prd_root / "pages" / f"{slug}.md"
    tpl = load_template("page-prd-template.md")
    content = render_template(
        tpl,
        页面名称=page_name,
        页面路由=route,
        页面文件=page_file,
        页面ID=page_id,
        功能ID=feature_id,
        变更ID=change_id,
    )
    write_if_missing(p, content, force=force)
    c = project_root / prd_root / "changelog" / f"{slug}-change.md"
    ctpl = load_template("page-changelog-template.md")
    write_if_missing(
        c,
        render_template(ctpl, 页面名称=page_name, 页面ID=page_id, 功能ID=feature_id, 变更ID=change_id),
        force=force,
    )
    if p.exists():
        upsert_frontmatter(
            p,
            {
                "page_id": page_id,
                "route": route,
                "code_paths": [page_file],
                "feature_ids": [feature_id],
                "change_ids": [change_id],
                "last_synced_at": TODAY,
            },
        )
    return p


def load_existing_route_map(route_inventory: Path) -> Dict[str, Dict[str, str]]:
    if not route_inventory.exists():
        return {}
    _, rows = parse_markdown_table(safe_read(route_inventory), required_headers=["route", "page_id"])
    route_map: Dict[str, Dict[str, str]] = {}
    for row in rows:
        route = parse_backticked(row.get("页面路由", row.get("route", "")))
        if route and not is_placeholder(route):
            route_map[route] = row
    return route_map


def write_route_inventory(out_path: Path, items: List[RouteItem], route_map: Dict[str, Dict[str, str]], prd_root: str) -> None:
    headers = ["page_id", "所属模块", "页面名称", "route", "code_path", "prd_path", "当前状态"]
    rows: List[List[str]] = []
    for it in items:
        slug = route_to_slug(it.route)
        row = route_map.get(it.route, {})
        page_id = row.get("page_id", make_page_id(it.route))
        prd = row.get("prd_path", f"{prd_root}/pages/{slug}.md")
        status = row.get("当前状态", row.get("status", "待确认"))
        module = row.get("所属模块", it.module)
        name = row.get("页面名称", it.name)
        rows.append(
            [
                page_id,
                module,
                name,
                f"`{it.route}`",
                f"`{it.file}`",
                f"`{prd}`",
                status,
            ]
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("# 页面路由清单\n\n" + markdown_table(headers, rows) + "\n", encoding="utf-8")


def load_feature_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    _, rows = parse_markdown_table(safe_read(path), required_headers=["feature_id", "owner_page_id", "status"])
    normalized = []
    for row in rows:
        feature_id = row.get("feature_id", "").strip()
        if is_placeholder(feature_id):
            continue
        normalized.append(
            {
                "feature_id": feature_id,
                "owner_page_id": row.get("owner_page_id", "").strip(),
                "status": row.get("status", "todo").strip() or "todo",
                "一级菜单": row.get("一级菜单", "[TODO]").strip() or "[TODO]",
                "二级页面": row.get("二级页面", "[TODO]").strip() or "[TODO]",
                "三级功能": row.get("三级功能", "[TODO]").strip() or "[TODO]",
            }
        )
    return normalized


def write_feature_rows(path: Path, rows: List[Dict[str, str]]) -> None:
    headers = ["feature_id", "owner_page_id", "status", "一级菜单", "二级页面", "三级功能"]
    body_rows = [[r[h] for h in headers] for r in rows]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# 功能清单\n\n" + markdown_table(headers, body_rows) + "\n", encoding="utf-8")


def ensure_changelog_row(path: Path, change_id: str, page_id: str, feature_ids: List[str], source_commit: str) -> None:
    if not path.exists():
        base = load_template("page-changelog-template.md")
        if base:
            path.write_text(
                render_template(base, 页面名称=page_id, 页面ID=page_id, 功能ID=(feature_ids[0] if feature_ids else ""), 变更ID=change_id),
                encoding="utf-8",
            )
    text = safe_read(path)
    headers, rows = parse_markdown_table(text, required_headers=["change_id"])
    if not headers:
        headers = ["change_id", "affected_page_ids", "affected_feature_ids", "source_commit", "版本", "日期", "修改类型", "修改内容", "影响范围", "是否同步 PRD", "备注"]
    has = False
    normalized_rows: List[Dict[str, str]] = []
    for row in rows:
        cid = row.get("change_id", "").strip()
        if cid == change_id:
            has = True
        normalized_rows.append(
            {
                "change_id": cid,
                "affected_page_ids": row.get("affected_page_ids", page_id),
                "affected_feature_ids": row.get("affected_feature_ids", ",".join(feature_ids)),
                "source_commit": row.get("source_commit", source_commit),
                "版本": row.get("版本", "v0.1"),
                "日期": row.get("日期", TODAY),
                "修改类型": row.get("修改类型", "初始化"),
                "修改内容": row.get("修改内容", "创建页面变更记录"),
                "影响范围": row.get("影响范围", "页面 PRD"),
                "是否同步 PRD": row.get("是否同步 PRD", "是"),
                "备注": row.get("备注", "自动补齐"),
            }
        )
    if not has:
        normalized_rows.append(
            {
                "change_id": change_id,
                "affected_page_ids": page_id,
                "affected_feature_ids": ",".join(feature_ids),
                "source_commit": source_commit,
                "版本": "v0.1",
                "日期": TODAY,
                "修改类型": "初始化",
                "修改内容": "自动补齐变更链路",
                "影响范围": "页面 PRD",
                "是否同步 PRD": "是",
                "备注": "自动补齐",
            }
        )
    ordered = ["change_id", "affected_page_ids", "affected_feature_ids", "source_commit", "版本", "日期", "修改类型", "修改内容", "影响范围", "是否同步 PRD", "备注"]
    rows_text = [[r.get(k, "") for k in ordered] for r in normalized_rows]
    path.write_text("# 页面变更记录\n\n" + markdown_table(ordered, rows_text) + "\n", encoding="utf-8")


def get_git_head(project_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(project_root),
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except Exception:
        return "unknown"


def collect_page_docs(project_root: Path, prd_root: str) -> Dict[str, Dict[str, Any]]:
    docs = project_root / prd_root
    pages_dir = docs / "pages"
    pages: Dict[str, Dict[str, Any]] = {}
    for p in sorted(pages_dir.glob("*.md")):
        text = safe_read(p)
        meta, body = parse_frontmatter(text)
        slug = p.stem
        route = str(meta.get("route", f"/{slug}"))
        page_id = str(meta.get("page_id", make_page_id(route)))
        code_paths = normalize_list(meta.get("code_paths"))
        feature_ids = normalize_id_list(meta.get("feature_ids"))
        change_ids = normalize_id_list(meta.get("change_ids"))
        pages[page_id] = {
            "page_id": page_id,
            "route": route,
            "code_paths": code_paths,
            "feature_ids": feature_ids,
            "change_ids": change_ids,
            "last_synced_at": str(meta.get("last_synced_at", TODAY)),
            "prd_path": str(p.relative_to(project_root)),
            "missing_sections": [sec for sec in REQUIRED_PAGE_SECTIONS if sec not in body],
        }
    return pages


def collect_routes(project_root: Path, prd_root: str) -> Dict[str, Dict[str, str]]:
    route_file = project_root / prd_root / "01-页面路由清单.md"
    _, rows = parse_markdown_table(safe_read(route_file), required_headers=["page_id", "route"])
    result = {}
    for r in rows:
        route = parse_backticked(r.get("route", r.get("页面路由", "")))
        if not route or is_placeholder(route):
            continue
        page_id = r.get("page_id", "").strip()
        if not page_id or is_placeholder(page_id):
            page_id = make_page_id(route)
        result[page_id] = {
            "page_id": page_id,
            "route": route,
            "code_path": parse_backticked(r.get("code_path", r.get("页面文件", ""))),
            "prd_path": parse_backticked(r.get("prd_path", r.get("PRD 文件", ""))),
        }
    return result


def collect_features(project_root: Path, prd_root: str) -> Dict[str, Dict[str, str]]:
    feature_file = project_root / prd_root / "02-功能清单.md"
    rows = load_feature_rows(feature_file)
    return {r["feature_id"]: r for r in rows if r["feature_id"]}


def collect_changes(project_root: Path, prd_root: str) -> Dict[str, Dict[str, str]]:
    changes: Dict[str, Dict[str, str]] = {}
    changelog_dir = project_root / prd_root / "changelog"
    for file in sorted(changelog_dir.glob("*.md")):
        _, rows = parse_markdown_table(safe_read(file), required_headers=["change_id"])
        for row in rows:
            cid = row.get("change_id", "").strip()
            if not cid or is_placeholder(cid):
                continue
            changes[cid] = {
                "change_id": cid,
                "affected_page_ids": row.get("affected_page_ids", ""),
                "affected_feature_ids": row.get("affected_feature_ids", ""),
                "source_commit": row.get("source_commit", ""),
                "file": str(file.relative_to(project_root)),
            }
    return changes


def build_traceability_index(project_root: Path, prd_root: str = "docs/prd") -> Dict[str, Any]:
    pages = collect_page_docs(project_root, prd_root)
    routes = collect_routes(project_root, prd_root)
    features = collect_features(project_root, prd_root)
    changes = collect_changes(project_root, prd_root)
    return {
        "generated_at": TODAY,
        "pages": pages,
        "routes": routes,
        "features": features,
        "changes": changes,
    }


def write_traceability_index(project_root: Path, prd_root: str = "docs/prd") -> Path:
    index = build_traceability_index(project_root, prd_root=prd_root)
    out = project_root / prd_root / ".index" / "traceability.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def cmd_scan_code(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    ensure_prd_dirs(root, prd_root=args.prd_root)
    items = scan_code_routes(root)
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / out_path
    route_map = load_existing_route_map(out_path)
    write_route_inventory(out_path, items, route_map, args.prd_root)
    if args.create_prd:
        for it in items:
            create_page_prd(root, it.route, it.name, it.file, prd_root=args.prd_root, force=args.force)
    index = write_traceability_index(root, prd_root=args.prd_root)
    print(f"已识别页面/路由: {len(items)}")
    print(f"已输出: {out_path}")
    print(f"Traceability 索引: {index}")


def cmd_sync(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    docs = ensure_prd_dirs(root, prd_root=args.prd_root)
    route_file = docs / "01-页面路由清单.md"
    feature_file = docs / "02-功能清单.md"
    source_commit = get_git_head(root)

    if args.from_code:
        items = scan_code_routes(root)
        route_map = load_existing_route_map(route_file)
        write_route_inventory(route_file, items, route_map, args.prd_root)
        for it in items:
            page_path = create_page_prd(root, it.route, it.name, it.file, prd_root=args.prd_root, force=False)
            slug = route_to_slug(it.route)
            page_id = make_page_id(it.route)
            feature_id = make_feature_id(it.route)
            change_id = make_change_id(it.route)
            meta = upsert_frontmatter(
                page_path,
                {
                    "page_id": page_id,
                    "route": it.route,
                    "code_paths": sorted(set(normalize_list(parse_frontmatter(safe_read(page_path))[0].get("code_paths")) + [it.file])),
                    "feature_ids": sorted(set(normalize_list(parse_frontmatter(safe_read(page_path))[0].get("feature_ids")) + [feature_id])),
                    "change_ids": sorted(set(normalize_list(parse_frontmatter(safe_read(page_path))[0].get("change_ids")) + [change_id])),
                    "last_synced_at": TODAY,
                },
            )
            features = load_feature_rows(feature_file)
            if feature_id not in {f["feature_id"] for f in features}:
                features.append(
                    {
                        "feature_id": feature_id,
                        "owner_page_id": page_id,
                        "status": "todo",
                        "一级菜单": "[TODO]",
                        "二级页面": it.name,
                        "三级功能": "[TODO]",
                    }
                )
                write_feature_rows(feature_file, features)
            change_file = docs / "changelog" / f"{slug}-change.md"
            ensure_changelog_row(change_file, change_id, page_id, normalize_list(meta.get("feature_ids")), source_commit)
        print(f"sync --from-code 完成，处理页面: {len(items)}")

    if args.from_prd:
        pages_dir = docs / "pages"
        for page_file in sorted(pages_dir.glob("*.md")):
            text = safe_read(page_file)
            meta, _ = parse_frontmatter(text)
            slug = page_file.stem
            route = str(meta.get("route", f"/{slug}")).strip() or f"/{slug}"
            page_id = str(meta.get("page_id", "")).strip() or make_page_id(route)
            code_paths = normalize_list(meta.get("code_paths"))
            if not code_paths:
                code_paths = [f"[TODO: 补充页面代码路径/{slug}]"]
            feature_ids = normalize_id_list(meta.get("feature_ids"))
            if not feature_ids:
                feature_ids = [make_feature_id(route)]
            change_ids = normalize_id_list(meta.get("change_ids"))
            if not change_ids:
                change_ids = [make_change_id(route)]
            upsert_frontmatter(
                page_file,
                {
                    "page_id": page_id,
                    "route": route,
                    "code_paths": code_paths,
                    "feature_ids": feature_ids,
                    "change_ids": change_ids,
                    "last_synced_at": TODAY,
                },
            )
        pages = collect_page_docs(root, prd_root=args.prd_root)
        feature_rows = load_feature_rows(feature_file)
        feature_ids = {r["feature_id"] for r in feature_rows}
        route_rows = load_existing_route_map(route_file)
        for page in pages.values():
            route = page["route"]
            slug = route_to_slug(route)
            page_id = page["page_id"]
            for fid in page["feature_ids"]:
                if fid not in feature_ids:
                    feature_rows.append(
                        {
                            "feature_id": fid,
                            "owner_page_id": page_id,
                            "status": "todo",
                            "一级菜单": "[TODO]",
                            "二级页面": slug,
                            "三级功能": "[TODO]",
                        }
                    )
                    feature_ids.add(fid)
            change_file = docs / "changelog" / f"{slug}-change.md"
            for cid in page["change_ids"]:
                ensure_changelog_row(change_file, cid, page_id, page["feature_ids"], source_commit)
            if route not in route_rows:
                route_rows[route] = {
                    "page_id": page_id,
                    "所属模块": "[TODO: 所属模块]",
                    "页面名称": slug,
                    "route": route,
                    "code_path": ",".join(page["code_paths"]),
                    "prd_path": page["prd_path"],
                    "当前状态": "待确认",
                }
        write_feature_rows(feature_file, feature_rows)
        synced_items: List[RouteItem] = []
        for route, row in route_rows.items():
            synced_items.append(RouteItem(route=route, file=parse_backticked(row.get("code_path", "")) or "unknown", name=row.get("页面名称", route_to_slug(route)), module=row.get("所属模块", "[TODO: 所属模块]")))
        write_route_inventory(route_file, synced_items, route_rows, args.prd_root)
        print(f"sync --from-prd 完成，处理页面: {len(pages)}")

    if not args.from_code and not args.from_prd:
        raise SystemExit("sync 需要 --from-code 或 --from-prd")

    index = write_traceability_index(root, prd_root=args.prd_root)
    print(f"Traceability 索引: {index}")


def strip_html(raw: str) -> str:
    raw = re.sub(r"<script[\s\S]*?</script>", " ", raw, flags=re.I)
    raw = re.sub(r"<style[\s\S]*?</style>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def extract_title(raw: str, fallback: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
    if m:
        t = strip_html(m.group(1)).strip()
        if t:
            return t[:80]
    for tag in ["h1", "h2"]:
        m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", raw, flags=re.I | re.S)
        if m:
            t = strip_html(m.group(1)).strip()
            if t:
                return t[:80]
    return fallback


def extract_ui_terms(raw: str) -> Tuple[List[str], List[str], List[str]]:
    text = strip_html(raw)
    chunks = [c.strip() for c in re.split(r"[|｜。；;\n\r\t]+", text) if 1 <= len(c.strip()) <= 50]
    buttons = []
    for pat in [r"<button[^>]*>(.*?)</button>", r"<a[^>]*>(.*?)</a>"]:
        for m in re.findall(pat, raw, flags=re.I | re.S):
            v = strip_html(m)
            if v and len(v) <= 30:
                buttons.append(v)
    inputs = []
    for m in re.findall(r"<(?:input|textarea|select)[^>]*(?:placeholder|aria-label|title)=['\"]([^'\"]+)['\"]", raw, flags=re.I):
        if m.strip():
            inputs.append(html.unescape(m.strip()))
    return sorted(set(chunks))[:80], sorted(set(buttons))[:40], sorted(set(inputs))[:40]


def is_auxiliary_axure_html(path: Path, html_root: Path) -> bool:
    try:
        rel = path.relative_to(html_root)
    except ValueError:
        rel = path
    rel_posix = rel.as_posix()
    lower = rel_posix.lower()
    name = path.name.lower()

    if lower.startswith(("resources/", "plugins/", "data/", "images/")):
        return True

    if name in {"index.html", "start.html", "start_c_1.html", "start_with_pages.html"}:
        return True

    return False


def cmd_scan_axure(args: argparse.Namespace) -> None:
    html_root = Path(args.html_root).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else Path.cwd().resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = project_root / out_path
    pages = []
    for f in html_root.rglob("*.html"):
        if is_auxiliary_axure_html(f, html_root):
            continue
        raw = safe_read(f, limit=1_000_000)
        title = extract_title(raw, f.stem)
        rel = str(f.relative_to(html_root))
        route = "/" + str(f.with_suffix("").relative_to(html_root)).replace(os.sep, "/")
        texts, buttons, inputs = extract_ui_terms(raw)
        pages.append((title, rel, route, texts, buttons, inputs))

    lines = [
        "# Axure HTML 页面导入清单",
        "",
        f"> 来源目录：`{html_root}`",
        "",
        "| 页面名称 | HTML 路径 | 推断路由 | 页面 PRD | 识别置信度 | 待确认项 |",
        "|---|---|---|---|---|---|",
    ]
    for title, rel, route, texts, buttons, inputs in pages:
        slug = route_to_slug(route)
        prd = f"{args.prd_root}/pages/{slug}.md"
        confidence = "中" if texts or buttons or inputs else "低"
        lines.append(f"| {title} | `{rel}` | `{route}` | `{prd}` | {confidence} | 业务规则、权限、状态流转需确认 |")
        if args.create_prd:
            content = render_template(
                load_template("page-prd-template.md"),
                页面名称=title,
                页面路由=route,
                页面文件=rel,
                页面ID=make_page_id(route),
                功能ID=make_feature_id(route),
                变更ID=make_change_id(route),
            )
            extracted = ["", "## Axure 页面显性元素识别", "", "### 可见文本", ""]
            extracted += [f"- {x}" for x in texts[:30]] or ["- [TODO: 未识别到可见文本]"]
            extracted += ["", "### 按钮 / 链接", ""]
            extracted += [f"- {x}" for x in buttons[:30]] or ["- [TODO: 未识别到按钮/链接文本]"]
            extracted += ["", "### 表单线索", ""]
            extracted += [f"- {x}" for x in inputs[:30]] or ["- [TODO: 未识别到表单线索]"]
            extracted += ["", "> 注意：以上内容来自 HTML 静态结构识别，隐藏交互、动态面板、业务规则、权限和状态流转需人工确认。", ""]
            prd_path = project_root / args.prd_root / "pages" / f"{slug}.md"
            write_if_missing(prd_path, content + "\n" + "\n".join(extracted), force=args.force)
            changelog_path = project_root / args.prd_root / "changelog" / f"{slug}-change.md"
            write_if_missing(
                changelog_path,
                render_template(
                    load_template("page-changelog-template.md"),
                    页面名称=title,
                    页面ID=make_page_id(route),
                    功能ID=make_feature_id(route),
                    变更ID=make_change_id(route),
                ),
                force=args.force,
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_traceability_index(project_root, prd_root=args.prd_root)
    print(f"已扫描 HTML 页面: {len(pages)}")
    print(f"已输出: {out_path}")


def run_git_diff(project_root: Path, base: str = "HEAD", staged: bool = False) -> List[str]:
    probe = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return []
    args = ["git", "diff", "--name-only"]
    if staged:
        args.append("--cached")
    else:
        args.append(base)
    try:
        result = subprocess.run(
            args,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def cmd_diff_sync(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    changed = run_git_diff(root, base=args.base, staged=args.staged)
    code_changed = [p for p in changed if is_code_related_path(p, prd_root=args.prd_root)]
    prd_changed = [p for p in changed if p.startswith(f"{args.prd_root}/")]
    must_sync = []
    if code_changed:
        must_sync.append("页面代码变更，需执行 `prdctl sync --from-code`。")
    if any("/pages/" in p for p in prd_changed):
        must_sync.append("页面 PRD 变更，需执行 `prdctl sync --from-prd`。")
    if not must_sync:
        must_sync.append("未发现明确的一致性风险。")

    out_dir = root / args.prd_root / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{TODAY}-diff-sync.md"
    lines = ["# Diff 驱动一致性建议", "", f"> 日期：{TODAY}", ""]
    lines += ["## 变更文件", ""]
    if changed:
        lines += [f"- `{x}`" for x in changed]
    else:
        lines += ["- [TODO: 当前未检测到 git diff 文件，确认是否在 git 仓库中执行。]"]
    lines += ["", "## 必须同步项", ""]
    lines += [f"- {x}" for x in must_sync]
    lines += [
        "",
        "## 建议命令",
        "",
        f"- `python scripts/prdctl.py sync . --from-code --prd-root {args.prd_root}`",
        f"- `python scripts/prdctl.py sync . --from-prd --prd-root {args.prd_root}`",
        f"- `python scripts/prdctl.py audit . --level strict --prd-root {args.prd_root}`",
    ]
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"diff-sync 报告: {out_file}")
    print(f"变更文件数量: {len(changed)}")


def audit_basic(project_root: Path, prd_root: str) -> List[Tuple[str, str, str, str, int]]:
    root = project_root
    docs = root / prd_root
    pages = list((docs / "pages").glob("*.md")) if (docs / "pages").exists() else []
    route_inventory = docs / "01-页面路由清单.md"
    feature_list = docs / "02-功能清单.md"
    issues: List[Tuple[str, str, str, str, int]] = []
    if not route_inventory.exists():
        issues.append(("路由清单缺失", f"{prd_root}/01-页面路由清单.md", "未找到", "需要先执行 init-project / scan-code", 2))
    if not feature_list.exists():
        issues.append(("功能清单缺失", f"{prd_root}/02-功能清单.md", "未找到", "需要创建功能清单", 2))
    for p in pages:
        txt = safe_read(p)
        for sec in REQUIRED_PAGE_SECTIONS:
            if sec not in txt:
                issues.append(("页面 PRD 章节缺失", str(p.relative_to(root)), sec, "补充该章节", 1))
    return issues


def audit_strict(project_root: Path, prd_root: str) -> List[Tuple[str, str, str, str, int]]:
    issues = audit_basic(project_root, prd_root)
    index = build_traceability_index(project_root, prd_root=prd_root)
    pages = index["pages"]
    routes = index["routes"]
    features = index["features"]
    changes = index["changes"]

    seen_page_ids = set()
    for page_id, p in pages.items():
        if page_id in seen_page_ids:
            issues.append(("page_id 冲突", p["prd_path"], page_id, "确保 page_id 全局唯一", 3))
        seen_page_ids.add(page_id)
        for key in ["page_id", "route", "code_paths", "feature_ids", "change_ids", "last_synced_at"]:
            if not p.get(key):
                issues.append(("页面 frontmatter 缺失", p["prd_path"], key, "补充 frontmatter 字段", 2))
        for fid in p["feature_ids"]:
            if fid not in features:
                issues.append(("feature_id 未在功能清单中", p["prd_path"], fid, "执行 sync --from-prd 补齐功能清单", 2))
        for cid in p["change_ids"]:
            if cid not in changes:
                issues.append(("change_id 未在变更记录中", p["prd_path"], cid, "执行 sync --from-prd 补齐变更记录", 2))
        if not p["change_ids"]:
            issues.append(("页面缺少变更链路", p["prd_path"], "change_ids 为空", "至少维护一个 change_id", 1))

    for page_id, route_row in routes.items():
        if page_id not in pages:
            issues.append(("路由清单引用孤儿页面", f"{prd_root}/01-页面路由清单.md", page_id, "修正 page_id 或补齐页面 PRD", 2))
        if route_row.get("prd_path") and not (project_root / route_row["prd_path"]).exists():
            issues.append(("路由清单 PRD 路径无效", f"{prd_root}/01-页面路由清单.md", route_row["prd_path"], "修正 prd_path", 2))

    for fid, feature in features.items():
        owner = feature.get("owner_page_id", "")
        if not owner:
            issues.append(("功能清单缺少 owner_page_id", f"{prd_root}/02-功能清单.md", fid, "补充 owner_page_id", 1))
        elif owner not in pages:
            issues.append(("功能归属页面不存在", f"{prd_root}/02-功能清单.md", f"{fid}->{owner}", "修正 owner_page_id 或新增页面 PRD", 2))

    for cid, change in changes.items():
        pages_ref = [x.strip() for x in change.get("affected_page_ids", "").split(",") if x.strip()]
        feature_ref = [x.strip() for x in change.get("affected_feature_ids", "").split(",") if x.strip()]
        for p in pages_ref:
            if p not in pages:
                issues.append(("变更记录引用不存在页面", change["file"], f"{cid}->{p}", "修正 affected_page_ids", 2))
        for f in feature_ref:
            if f not in features:
                issues.append(("变更记录引用不存在功能", change["file"], f"{cid}->{f}", "修正 affected_feature_ids", 1))
    return issues


def cmd_audit(args: argparse.Namespace) -> None:
    root = Path(args.project_root).resolve()
    docs = root / args.prd_root
    docs.mkdir(parents=True, exist_ok=True)
    if args.level == "strict":
        issues = audit_strict(root, args.prd_root)
    else:
        issues = audit_basic(root, args.prd_root)
    out_dir = docs / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{TODAY}-consistency-audit.md"
    write_traceability_index(root, prd_root=args.prd_root)
    high = len([x for x in issues if x[4] >= 2])
    lines = ["# 代码与 PRD 一致性审计", "", f"> 审计日期：{TODAY}", f"> 审计级别：{args.level}", "", "## 审计结论", ""]
    lines.append(f"共发现 {len(issues)} 个问题，其中高优先级（P2+）{high} 个。")
    lines += ["", "## 不一致问题清单", "", "| 优先级 | 问题类型 | 文件/页面 | 表现 | 建议修复 |", "|---|---|---|---|---|"]
    if issues:
        for t, f, show, fix, prio in issues:
            lines.append(f"| P{prio} | {t} | `{f}` | {show} | {fix} |")
    else:
        lines.append("| P0 | 无显性问题 | - | - | - |")
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"审计完成: {out_file}")
    print(f"问题总数: {len(issues)}，高优先级: {high}")
    if args.fail_on_high and high > 0:
        raise SystemExit(2)


def cmd_install(args: argparse.Namespace) -> None:
    target = Path(args.target).resolve()
    if args.mode == "codex-repo":
        dest = target / ".agents" / "skills" / "create-prd"
    elif args.mode == "claude-user":
        home = Path(os.environ.get("USERPROFILE", str(Path.home()))) if os.name == "nt" else Path.home()
        dest = home / ".claude" / "skills" / "create-prd"
    else:
        dest = target
    if dest.exists() and not args.force:
        print(f"已检测到安装目录已存在: {dest}")
        print("未执行覆盖安装。若需重装请追加 --force。")
        return
    if dest.exists() and args.force:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    skip_names = {".git", ".agents", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".DS_Store"}
    for item in SKILL_ROOT.iterdir():
        if item.name in skip_names:
            continue
        # 防止目标目录位于源目录之下时发生递归自拷贝。
        if item.is_dir():
            try:
                dest.relative_to(item)
                continue
            except ValueError:
                pass
        target_item = dest / item.name
        if item.is_dir():
            if target_item.exists():
                shutil.rmtree(target_item)
            shutil.copytree(
                item,
                target_item,
                ignore=shutil.ignore_patterns(
                    "__pycache__", ".DS_Store", ".agents", ".pytest_cache", ".mypy_cache", ".ruff_cache"
                ),
            )
        else:
            shutil.copy2(item, target_item)
    print(f"已安装 create-prd Skill 到: {dest}")


def main() -> None:
    parser = argparse.ArgumentParser(description="create-prd 工程化辅助命令")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init-project", help="初始化业务项目 PRD 体系")
    p.add_argument("project_root")
    p.add_argument("--mode", choices=["greenfield", "existing-code", "axure"], default="greenfield")
    p.add_argument("--prd-root", default="docs/prd")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=lambda a: init_project(Path(a.project_root), a.mode, a.prd_root, a.force))

    p = sub.add_parser("scan-code", help="扫描代码项目路由/页面")
    p.add_argument("project_root")
    p.add_argument("--out", default="docs/prd/01-页面路由清单.md")
    p.add_argument("--prd-root", default="docs/prd")
    p.add_argument("--create-prd", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_scan_code)

    p = sub.add_parser("sync", help="同步 traceability 链路")
    p.add_argument("project_root")
    p.add_argument("--prd-root", default="docs/prd")
    p.add_argument("--from-code", action="store_true")
    p.add_argument("--from-prd", action="store_true")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("diff-sync", help="根据 git diff 输出一致性同步建议")
    p.add_argument("project_root")
    p.add_argument("--prd-root", default="docs/prd")
    p.add_argument("--base", default="HEAD")
    p.add_argument("--staged", action="store_true")
    p.set_defaults(func=cmd_diff_sync)

    p = sub.add_parser("scan-axure", help="扫描 Axure 导出 HTML")
    p.add_argument("html_root")
    p.add_argument("--project-root", default=None)
    p.add_argument("--prd-root", default="docs/prd")
    p.add_argument("--out", default="docs/prd/imports/axure-pages.md")
    p.add_argument("--create-prd", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_scan_axure)

    p = sub.add_parser("audit", help="一致性审计")
    p.add_argument("project_root")
    p.add_argument("--prd-root", default="docs/prd")
    p.add_argument("--level", choices=["basic", "strict"], default="basic")
    p.add_argument("--fail-on-high", action="store_true")
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
