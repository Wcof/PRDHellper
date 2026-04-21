# create-prd — 工程化 PRD Skill

> 面向产品经理的 PRD 工程化助手：支持完整系统级 PRD、code 网页原型页面 PRD 同步、已有代码项目 PRD 初始化、Axure HTML 反向生成 PRD、代码与 PRD 一致性审计。

这个项目不再只是“把业务描述生成一份 PRD”的 Prompt，而是一个可以放进 Codex / Claude Code / 其他 Agent 工作流中的 **PRD Skill 工程包**。

## 1. 设计目标

你的核心场景有两个：

1. **从零到一的新项目**：加载本 Skill 后，每新建一个页面，Agent 根据页面内容、页面代码、路由、mock 数据和对话上下文，生成并持续更新对应页面 PRD。
2. **已有项目 / Axure 项目**：根据已有代码路由或 Axure 导出的 HTML 页面路径，逐页阅读和理解页面，按规范反向生成页面级 PRD。

工程化后的 create-prd 采用四层结构：

```text
Skill 层：SKILL.md 定义触发条件、模式选择、工作流程
Template 层：references/templates 提供页面 PRD、功能清单、AGENTS.md 等模板
Script 层：scripts/prdctl.py 提供初始化、扫描、审计命令
Project Docs 层：业务项目 docs/product 存放真实 PRD 产物
```

## 主模板策略（重要）

当前主模板与主规范固定以：

```text
main-template/create-prd-skill-main
```

为准。

本仓库（PRDHellper）定位为：
1. 安装与工程化脚手架
2. 一致性检查与同步工具
3. 扩展入口（不替代主模板）

扩展入口目录：

```text
references/templates/extensions/
```

策略配置见：

```text
configs/template-policy.yaml
```

补充：`scripts/build.py` 会按 `template-policy.yaml` 的 `main_template_source` 优先读取主规范，再叠加本仓工程化附录与模板。

## 2. 支持模式

| 模式 | 适用场景 | 产物 |
|---|---|---|
| `system-prd` | 生成完整 14 章 B 端 PRD | `docs/product/system-prd/*.md` |
| `greenfield-page-sync` | 从零到一新项目，页面生成后同步 PRD | 页面 PRD、功能清单、变更记录 |
| `existing-code-init` | 已有 code 项目初始化 PRD 体系 | 路由清单、功能清单、页面 PRD 草稿 |
| `axure-html-import` | Axure HTML 逐页反向生成 PRD | Axure 页面清单、逐页 PRD |
| `consistency-audit` | 检查代码/HTML 与 PRD 是否一致 | 审计报告、修复建议 |

## 3. 推荐项目结构

把 Skill 放进业务项目：

```text
你的业务项目/
├── src/
├── docs/
│   └── product/
│       ├── 00-项目上下文.md
│       ├── 01-页面路由清单.md
│       ├── 02-功能清单.md
│       ├── 03-全局交互规则.md
│       ├── 04-PRD编写规范.md
│       ├── system-prd/
│       ├── pages/
│       ├── changelog/
│       ├── audit/
│       ├── imports/
│       └── templates/
├── .agents/
│   └── skills/
│       └── create-prd/
└── AGENTS.md
```

其中：

- `.agents/skills/create-prd/`：存放本 Skill。
- `docs/product/`：存放当前业务项目真实 PRD 产物。
- `AGENTS.md`：存放当前项目给 Codex / Agent 的长期规则。

## 4. 安装方式

### 推荐：统一一键安装（跨平台）

根目录只保留一个安装入口：

```bash
python3 install.py
```

Windows 也使用同一个入口：

```powershell
py -3 install.py
```

安装器会自动识别当前系统（macOS / Linux / Windows），并进入一键模式：只需选择安装场景（已有代码/新项目/Axure/全局），其余参数自动完成（自动安装、自动初始化、重复安装默认重装 Skill）。

如需完整向导（逐项配置）：

```bash
python3 install.py --wizard
```

完整向导会引导你：

1. 选择安装到“当前项目”还是“全局”；
2. 若选当前项目：默认目标是 **skill 目录的上一级**（适合“把本文件夹拖进项目里”）；
3. 确认 PRD 文档目录名（默认 `docs/product`，可改成 `docs/prd` 等）；
4. 该目录会 **自动创建**，无需手动创建；
5. 初始化默认开启，并用中文提示模式含义（新项目 / 已有代码 / Axure）。

### 重复安装处理

若检测到已经安装过，向导会让你选择：

1. 保留现状（跳过）
2. 仅重装 Skill（不动已有文档）
3. 重装 Skill + 重置文档并自动迁移历史文件（会先备份，再生成迁移报告）

当你选择“跳过”或“安装后不初始化（中途安装）”时，会自动生成一个可复制给 AI 的唤醒词文件：

```text
AI-PRD-WAKEUP-PROMPT.md
```

如果你在安装时选择了“已有代码项目”模式，也会自动生成该唤醒词，用于让 AI 直接执行“已有页面补全 PRD”。

安装到当前项目后会出现：

```text
.agents/skills/create-prd/
```

### 非交互安装（CI/脚本）

安装到当前项目并初始化：

```bash
python3 scripts/install_skill.py --scope current --project-root /path/to/your-project --prd-root docs/product --init-project --yes --force
```

检测到重复安装时，指定策略：

```bash
python3 scripts/install_skill.py --scope current --project-root /path/to/your-project --prd-root docs/product --init-project --yes --on-existing skip
python3 scripts/install_skill.py --scope current --project-root /path/to/your-project --prd-root docs/product --init-project --yes --on-existing reinstall
python3 scripts/install_skill.py --scope current --project-root /path/to/your-project --prd-root docs/product --init-project --yes --on-existing reinstall-reset
```

全局安装（Claude 用户级）：

```bash
python3 scripts/install_skill.py --scope global --yes --force
```

### 兼容旧命令（可选）

```bash
python3 scripts/prdctl.py install /path/to/your-project --mode codex-repo --force
python3 scripts/prdctl.py install --mode claude-user --force
```

### 任意大模型复制 Prompt

```bash
python scripts/build.py
```

然后复制：

```text
dist/create-prd-universal-prompt.md
```

## 5. 初始化业务项目 PRD 体系

进入业务项目后执行：

```bash
python .agents/skills/create-prd/scripts/prdctl.py init-project . --mode greenfield
```

已有代码项目可用：

```bash
python .agents/skills/create-prd/scripts/prdctl.py init-project . --mode existing-code
python .agents/skills/create-prd/scripts/prdctl.py scan-code . --create-prd
```

Axure HTML 项目可用：

```bash
python .agents/skills/create-prd/scripts/prdctl.py init-project . --mode axure
python .agents/skills/create-prd/scripts/prdctl.py scan-axure ./axure-html --project-root . --create-prd
```

一致性审计（基础 / 严格）：

```bash
python .agents/skills/create-prd/scripts/prdctl.py audit . --level basic
python .agents/skills/create-prd/scripts/prdctl.py audit . --level strict
```

增量同步（代码驱动 / PRD 驱动）：

```bash
python .agents/skills/create-prd/scripts/prdctl.py sync . --from-code
python .agents/skills/create-prd/scripts/prdctl.py sync . --from-prd
```

说明：
1. `--from-prd` 现在会自动补齐页面 PRD 的 traceability frontmatter（`page_id/route/code_paths/feature_ids/change_ids/last_synced_at`）。
2. 严格审计会自动忽略模板中的 `[TODO: ...]` 占位行，减少初始化阶段误报。
3. 对包含多张表格的文档（例如功能清单附加说明）会优先解析目标表头，避免串表导致 `owner_page_id` 误判。

页面内 PRD 查看器（右下角 PRD 按钮，按路由查看当前页面 PRD）：

```text
参考模板：
references/templates/prd-viewer-integration-template.md
```

Diff 驱动同步建议：

```bash
python .agents/skills/create-prd/scripts/prdctl.py diff-sync . --staged
```

如果你在安装向导里把 PRD 目录改成了非默认值（例如 `docs/prd`），请在命令后追加：

```bash
--prd-root docs/prd
```

## 6. 给 Codex 的推荐任务写法

### 新建页面并同步 PRD

```markdown
请使用 create-prd Skill 新建页面：

- 页面名称：总调度台
- 页面路由：/management/dispatch/center
- 所属模块：管理端 / 总调度

要求：
1. 实现页面 code 原型；
2. 生成或更新 docs/product/pages/management-dispatch-center.md；
3. 更新 docs/product/02-功能清单.md；
4. 更新 docs/product/01-页面路由清单.md；
5. 生成或更新 docs/product/changelog/management-dispatch-center-change.md；
6. 完成后输出代码与 PRD 一致性检查。
```

### 页面调整后同步 PRD

```markdown
页面：/management/dispatch/center

本次修改：增加自动执行 / 手动执行两种调度模式。

请修改页面代码，并同步更新页面 PRD、功能清单和变更记录。若本次修改影响字段、按钮、交互、状态流转或业务规则，必须更新 PRD 主体。
```

### Axure HTML 反向生成 PRD

```markdown
请使用 create-prd Skill 读取 ./axure-html 目录，逐页生成页面级 PRD。输出到 docs/product/pages，并生成 docs/product/imports/axure-pages.md。
```

## 7. Skill / AGENTS.md / MCP 的分工

- **AGENTS.md**：项目级长期规则，告诉 Codex 每次在这个仓库里怎么工作。
- **Skill**：可复用能力，定义 PRD 初始化、页面 PRD、Axure 解析、审计等流程。
- **MCP**：外部工具连接方式。当需要读取 Figma、浏览器、接口平台、内部知识库时再引入。

因此本项目优先把 PRD 工作流做成 Skill；MCP 作为增强项，不作为第一步必需项。

## 8. 仓库结构

```text
SKILL.md
agents/openai.yaml
configs/
references/
  chapters/          # 原 14 章系统级 PRD 指引
  appendices/        # 工程化、模式选择、Axure、同步审计等规则
  templates/         # 页面 PRD、变更记录、AGENTS.md 等模板
  prompts/           # 各模式可复制任务模板
scripts/
  prdctl.py          # 统一 CLI
  build.py           # 构建 dist prompt
  install_skill.py   # 安装入口
examples/            # Codex 任务示例
dist/                # 构建产物
```

## 9. 使用教程（维护与自定义）

如果你后期要维护和自定义 PRD 模板，先看：

```text
docs/usage/模板自定义与维护教程.md
```

核心结论（简版）：
1. 只改当前项目：优先改 `.agents/skills/create-prd/references/templates/`。
2. 作为默认模板：改本仓库 `references/templates/`，然后 `python3 scripts/build.py`。
3. 改完要验证：运行 `sync + audit --level strict`。

## 10. 版本说明

当前版本在原 create-prd 基础上增加工程化能力：

- 模式选择
- Codex 仓库级 Skill 安装
- `docs/product` 初始化
- 代码项目路由扫描
- Axure HTML 扫描
- 页面 PRD 模板
- 页面变更记录
- 一致性审计
- traceability 索引（`docs/product/.index/traceability.json`）
