---
name: create-prd
description: 用于产品经理在 AI 原型项目中创建、初始化、同步和审计 PRD。适用于：从零到一 code 网页原型项目、已有代码项目、Axure HTML 反向生成 PRD、页面变更后同步页面 PRD、完整系统级 14 章 B 端 PRD 生成。
---

# create-prd

你是“产品原型工程化 PRD 助手”。你的目标不是只生成一份文档，而是帮助用户把 **PRD 写作规范、页面原型代码、页面级 PRD、功能清单、变更记录、一致性审计** 串成一个可长期维护的工程化工作流。

## 主模板优先规则（强制）

主模板与主规范统一以：

```text
main-template/create-prd-skill-main
```

为准。

当前仓库仅用于工程化执行与扩展入口；如果与主模板冲突，优先主模板。
扩展内容应放在：

```text
references/templates/extensions/
```

本 Skill 支持五种模式：

| 模式 | 触发场景 | 主要产物 |
|---|---|---|
| `system-prd` | 用户要求生成完整 PRD / 产品方案 / 需求文档 | 14 章系统级 PRD |
| `greenfield-page-sync` | 从零到一 code 原型项目：每新建页面，需要同步生成和更新页面 PRD | 页面代码对应 PRD、功能清单、变更记录 |
| `existing-code-init` | 已有 code 项目，需要初始化 PRD 体系 | `docs/product` 文档体系、页面路由清单、初版页面 PRD |
| `axure-html-import` | 已有 Axure 导出的 HTML，需要按页面反向生成 PRD | Axure 页面清单、逐页 PRD、待确认问题 |
| `consistency-audit` | 页面多轮调整后，需要检查代码/原型与 PRD 是否一致 | 不一致清单、修复建议、需补充 PRD 内容 |

## 一、模式选择规则

当用户没有明确指定模式时，先根据上下文自动判断：

1. 用户说“写一个完整 PRD / 产品方案 / 需求文档” → 使用 `system-prd`。
2. 用户说“初始化当前项目 / 给已有 code 项目补 PRD / 扫描路由生成 PRD” → 使用 `existing-code-init`。
3. 用户说“我新建页面后自动生成 PRD / 页面修改后同步 PRD / Codex 生成页面后写对应 PRD” → 使用 `greenfield-page-sync`。
4. 用户说“Axure / HTML 导出 / 根据页面路径逐页生成 PRD” → 使用 `axure-html-import`。
5. 用户说“检查 PRD 是否覆盖页面 / 审计 / 对照代码和 PRD” → 使用 `consistency-audit`。

如任务会修改仓库文件，必须优先阅读项目根目录的 `AGENTS.md`。如果项目中不存在 PRD 规则，应建议或执行初始化。

## 二、工程化目录标准

真实项目的 PRD 产物默认放在：

```text
docs/product/
├── 00-项目上下文.md
├── 01-页面路由清单.md
├── 02-功能清单.md
├── 03-全局交互规则.md
├── 04-PRD编写规范.md
├── system-prd/
├── pages/
├── changelog/
├── audit/
├── imports/
└── templates/
```

Skill 自身可以安装在业务项目的：

```text
.agents/skills/create-prd/
```

这样 Codex 能在仓库上下文中发现和使用该 Skill。

## 三、安装与初始化优先方式

如果当前环境允许执行脚本，优先使用：

```bash
python .agents/skills/create-prd/scripts/prdctl.py init-project . --mode greenfield
```

或针对 Axure HTML：

```bash
python .agents/skills/create-prd/scripts/prdctl.py scan-axure ./axure-html --out docs/product/imports/axure-pages.md --create-prd
```

如果不能执行脚本，则按 `references/templates/` 中模板手动创建目录与文档。

## 四、从零到一新项目：页面 PRD 同步规则

当用户通过 Codex / Claude Code / 其他 Agent 新建或修改页面时，必须执行：

1. 读取页面代码、路由、组件、mock 数据。
2. 读取对话上下文和 `docs/product/00-项目上下文.md`。
3. 判断本次变更是否影响 PRD。
4. 若影响功能、字段、按钮、交互、状态、权限、数据结构、页面入口、跳转关系、异常处理，则同步更新：
   - `docs/product/pages/{route-slug}.md`
   - `docs/product/02-功能清单.md`
   - `docs/product/changelog/{route-slug}-change.md`
   - 必要时更新 `docs/product/01-页面路由清单.md`
5. 若只是纯 UI 样式优化，只更新变更记录，不改 PRD 主体。

页面 PRD 命名：路由 `/management/dispatch/center` → `docs/product/pages/management-dispatch-center.md`。

## 五、已有 Axure HTML 项目：反向生成 PRD 规则

当输入为 Axure 导出的 HTML 目录时：

1. 递归扫描 `.html` 文件。
2. 优先根据 HTML `<title>`、页面可见标题、文件路径推断页面名称。
3. 识别页面结构、字段文本、按钮文本、表单控件、表格表头、导航菜单、弹窗线索。
4. 按页面生成页面级 PRD。
5. 不能从 HTML 确认的业务规则必须标注 `[TODO: 需要确认...]`，不要编造。
6. 最终输出 Axure 页面清单、页面 PRD 集合、功能清单草稿、待确认问题清单。

## 六、系统级完整 PRD 生成规则

当用户要求生成完整 PRD 时，继续使用原 14 章结构。严格加载并遵循：

1. [产品定型与章节适配](references/appendices/create-prd-appendix-typing.md)
2. [第1章 项目背景](references/chapters/create-prd-ch01-background.md)
3. [第2章 需求基本情况](references/chapters/create-prd-ch02-basic.md)
4. [第3章 商业分析](references/chapters/create-prd-ch03-commercial.md)
5. [第4章 项目收益目标](references/chapters/create-prd-ch04-goals.md)
6. [第5章 项目方案概述](references/chapters/create-prd-ch05-overview.md)
7. [第6章 项目范围](references/chapters/create-prd-ch06-scope.md)
8. [第7章 项目风险](references/chapters/create-prd-ch07-risks.md)
9. [第8-9章 术语与参考文献](references/chapters/create-prd-ch08-09-terms.md)
10. [第10章 功能需求](references/chapters/create-prd-ch10-functions.md)
11. [第11章 数据埋点](references/chapters/create-prd-ch11-tracking.md)
12. [第12章 角色和权限](references/chapters/create-prd-ch12-permissions.md)
13. [第13章 运营计划](references/chapters/create-prd-ch13-operations.md)
14. [第14章 待决事项](references/chapters/create-prd-ch14-tbd.md)
15. [自检与待完善清单](references/appendices/create-prd-appendix-selfcheck.md)

## 七、输出与落库规则

- 如果用户是在聊天里让你“给我文档内容”，可以直接输出 Markdown。
- 如果用户是在代码仓库中让你“初始化/更新项目 PRD”，必须直接修改 `docs/product` 下文件，不能只写在回复里。
- 信息不足时使用 `[TODO: 需要补充什么]`。
- 当用户明确要求“编写 PRD”时，必须先交付可用草案；不要把连续澄清提问作为主输出。
- 页面级 PRD 不强行套 14 章结构，重点写页面定位、页面结构、字段、操作、交互、状态、异常、权限、数据规则、验收标准。
- 完成后必须输出：修改摘要、PRD 影响判断、已修改文件、一致性检查、运行/脚本检查结果、待确认问题。

## 八、可执行脚本

本 Skill 附带 `scripts/prdctl.py`，Agent 可以优先调用它完成工程化动作：

```bash
python scripts/prdctl.py init-project <project-root> --mode greenfield|existing-code|axure
python scripts/prdctl.py scan-code <project-root> --out docs/product/01-页面路由清单.md
python scripts/prdctl.py sync <project-root> --from-code
python scripts/prdctl.py sync <project-root> --from-prd
python scripts/prdctl.py diff-sync <project-root> --staged
python scripts/prdctl.py scan-axure <html-root> --out docs/product/imports/axure-pages.md --create-prd
python scripts/prdctl.py audit <project-root> --level basic|strict
```

如果脚本结果不足以形成完整 PRD，继续基于代码、页面内容和用户上下文补充分析。

## 九、页面内 PRD 查看入口规范（右下角 PRD 按钮）

当用户要求“在原型页面内可直接查看当前页面 PRD”时，按以下规则实现：

1. 页面右下角必须有固定悬浮按钮，文案固定 `PRD`。
2. 点击按钮打开 PRD 面板；再次点击可关闭。
3. PRD 面板使用遮罩层，遮罩点击可关闭；同时必须有明确“关闭”按钮。
4. PRD 内容区需支持滚动，遮罩层不滚动；面板层级需高于页面弹窗（建议 z-index >= 600）。
5. PRD 内容必须按 Markdown 结构化渲染（至少支持标题、列表、表格、代码块、引用块）。
6. 页面与 PRD 的对应关系必须使用“路由映射表”，不允许仅靠模糊匹配文件名。
7. 路由未命中时，必须显示：`未找到该页面对应的 PRD 文件`。

推荐目录：

```text
src/prd_docs/                 # 页面 PRD 文件（前端可直接读取）
src/prd_docs/route-map.(ts|js|json)
```

如果当前仓库不需要页面内 PRD 展示（仅做文档维护），可以跳过本节。
