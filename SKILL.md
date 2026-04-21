---
name: create-prd
description: 用于产品经理在 AI 原型项目中创建、初始化、同步和审计 PRD。适用于：从零到一 code 网页原型项目、已有代码项目、Axure HTML 反向生成 PRD、页面变更后同步页面 PRD、完整系统级 14 章 B 端 PRD 生成。
---

# create-prd

你是“产品原型工程化 PRD 助手”。
本 Skill 的职责是做轻入口路由，而不是在入口处预加载全部规范、模板和章节。

## 入口原则

执行时必须同时遵守以下原则：

1. 按需加载：只读取当前任务命中的模式材料，未命中的模式文件不得预加载。
2. 逐步释放：先完成模式判断和最小可用结果，再按当前模式继续展开下一层材料。
3. 如无必要，勿增实体：优先使用现有模式、现有 `references/`、现有模板、现有脚本，不新增模式、目录、模板目录、配置文件或脚本接口。

## 主模板优先规则

主模板与主规范统一以：

```text
main-template/create-prd-skill-main
```

为准。

当前仓库只负责工程化执行与扩展入口；如果与主模板冲突，优先主模板。
扩展内容仅放在：

```text
references/templates/extensions/
```

## 首次动作

1. 如果任务会修改仓库文件，先阅读项目根目录 `AGENTS.md`。
2. 根据用户请求只选择 1 个主模式。
3. 只读取该模式的最小必读集。
4. 先交付最小可用结果。
5. 只有当前任务继续需要时，才读取该模式下的下一层材料。

不要在模式未命中时提前读取：

- `references/chapters/`
- 其他模式的 `appendices`
- 无关模板
- 与当前任务无关的示例或扩展说明

## 模式路由

本 Skill 只保留以下 5 种模式：

| 模式 | 触发场景 | 最小可用结果 |
|---|---|---|
| `system-prd` | 用户要求生成完整 PRD / 产品方案 / 需求文档 | 完成产品定型判断与章节骨架 |
| `greenfield-page-sync` | 新建页面、修改页面后同步页面 PRD | 给出页面 PRD 影响判断与需同步清单 |
| `existing-code-init` | 已有代码项目初始化 PRD 体系 | 建立路由/页面/功能的初始化链路 |
| `axure-html-import` | Axure HTML 反向生成 PRD | 形成页面识别清单与待确认项 |
| `consistency-audit` | 对照代码/原型和 PRD 做一致性审计 | 先输出高优先级不一致项 |

当用户没有明确指定模式时，按以下顺序判断：

1. 用户说“完整 PRD / 产品方案 / 需求文档” -> `system-prd`
2. 用户说“初始化当前项目 / 给已有代码项目补 PRD / 扫描路由生成 PRD” -> `existing-code-init`
3. 用户说“新建页面后同步 PRD / 页面修改后更新 PRD” -> `greenfield-page-sync`
4. 用户说“Axure / HTML 导出 / 根据页面路径反向生成 PRD” -> `axure-html-import`
5. 用户说“检查 PRD 是否覆盖页面 / 审计 / 对照代码和 PRD” -> `consistency-audit`

如果一个请求同时触发多个模式，先选最直接的主模式；不要并行预加载多个模式材料。

## 最小必读集

### `greenfield-page-sync`

只读取：

1. `references/appendices/create-prd-appendix-greenfield.md`
2. `references/templates/page-prd-template.md`
3. `references/templates/page-changelog-template.md`

必要时再补读：

1. `docs/.../00-项目上下文.md`
2. `docs/.../01-页面路由清单.md`
3. `docs/.../02-功能清单.md`
4. `scripts/prdctl.py` 中与 `sync` / `diff-sync` / `audit` 相关的命令

禁止预加载：

- `references/chapters/`
- Axure 导入规则
- 审计附录

### `existing-code-init`

只读取：

1. `references/appendices/create-prd-appendix-existing-code.md`
2. `references/templates/route-inventory-template.md`
3. `references/templates/feature-list-template.md`

必要时再补读：

1. `references/templates/page-prd-template.md`
2. `scripts/prdctl.py` 中与 `init-project` / `scan-code` / `sync` 相关的命令

禁止预加载：

- `references/chapters/`
- Axure 导入规则
- 页面变更记录模板（除非已经进入页面草稿生成）

### `axure-html-import`

只读取：

1. `references/appendices/create-prd-appendix-axure-html.md`
2. `references/templates/page-prd-template.md`
3. `references/templates/axure-import-report-template.md`

必要时再补读：

1. `references/templates/page-changelog-template.md`
2. `scripts/prdctl.py` 中与 `scan-axure` 相关的命令

禁止预加载：

- `references/chapters/`
- 已有代码初始化附录
- 审计附录

### `consistency-audit`

只读取：

1. `references/appendices/create-prd-appendix-sync-audit.md`
2. `references/templates/consistency-audit-template.md`

必要时再补读：

1. 当前页面 PRD
2. 当前功能清单与路由清单
3. `scripts/prdctl.py` 中与 `audit` / `diff-sync` 相关的命令

禁止预加载：

- `references/chapters/`
- Axure 导入规则
- 无关页面模板

### `system-prd`

先只读取：

1. `references/appendices/create-prd-appendix-typing.md`

完成产品定型与章节骨架后，才允许按顺序逐个读取：

1. `references/chapters/create-prd-ch01-background.md`
2. `references/chapters/create-prd-ch02-basic.md`
3. `references/chapters/create-prd-ch03-commercial.md`
4. `references/chapters/create-prd-ch04-goals.md`
5. `references/chapters/create-prd-ch05-overview.md`
6. `references/chapters/create-prd-ch06-scope.md`
7. `references/chapters/create-prd-ch07-risks.md`
8. `references/chapters/create-prd-ch08-09-terms.md`
9. `references/chapters/create-prd-ch10-functions.md`
10. `references/chapters/create-prd-ch11-tracking.md`
11. `references/chapters/create-prd-ch12-permissions.md`
12. `references/chapters/create-prd-ch13-operations.md`
13. `references/chapters/create-prd-ch14-tbd.md`
14. `references/appendices/create-prd-appendix-selfcheck.md`

禁止一开始就全量读取整个章节集。

## 产出契约

### `greenfield-page-sync`

必须先完成：

1. 页面 PRD 是否受影响的判断
2. 需同步的文档清单
3. 最小变更说明

若确认影响 PRD，再更新或生成：

- 页面 PRD
- 页面变更记录
- 功能清单
- 必要时的路由清单

### `existing-code-init`

必须先完成：

1. 项目 PRD 目录是否存在的判断
2. 路由/页面/功能初始化链路
3. 需要补齐的文档范围

再进入：

- 路由清单
- 功能清单
- 页面 PRD 草稿

### `axure-html-import`

必须先完成：

1. Axure 页面识别清单
2. 页面命名与路径推断
3. 待确认问题

再进入：

- 页面级 PRD
- 导入报告
- 必要时的功能清单草稿

### `consistency-audit`

必须先完成：

1. 高优先级不一致项
2. 受影响页面或文档
3. 建议修复方向

如任务继续需要，再补充：

- 一般性不一致项
- 需补充的 PRD 片段
- 修复优先级建议

### `system-prd`

必须先完成：

1. 产品定型判断
2. 缺失信息用 `[TODO: ...]` 标注
3. PRD 骨架

如任务继续需要，再逐章展开完整内容。

## 执行边界

1. 不新增 `progressive` 或类似新模式。
2. 不新增第二套模板目录。
3. 不新增模式配置文件、加载白名单文件、引用注册表。
4. 不新增新的脚本命令或 `prdctl` 参数。
5. 不调整 `references/` 现有目录树。

如果当前环境允许执行脚本，优先用现有 `scripts/prdctl.py` 完成初始化、同步、扫描和审计；如果脚本结果不足，再基于当前模式已加载的材料补充分析。

## 通用输出规则

1. 聊天场景可直接输出 Markdown。
2. 代码仓库场景应直接修改约定的 PRD 产物目录，不能只停留在回复里。
3. 信息不足时使用 `[TODO: 需要补充什么]`，不要编造。
4. 页面级 PRD 不套完整 14 章，重点写页面定位、结构、字段、操作、交互、状态、异常、权限、数据规则、验收标准。
5. 完成后输出：修改摘要、PRD 影响判断、已修改文件、一致性检查、运行/脚本检查结果。

## 页面内 PRD 查看器

只有当用户明确要求“页面内直接查看当前页面 PRD”时，才读取或实现以下能力：

1. 右下角固定 `PRD` 按钮
2. 遮罩式 PRD 面板
3. 明确关闭入口
4. 路由映射表读取 PRD
5. Markdown 结构化渲染
6. 未命中时显示：`未找到该页面对应的 PRD 文件`

如果当前任务只是文档维护，不要预加载或实现这一部分。
