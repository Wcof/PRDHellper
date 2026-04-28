---
name: create-prd
description: 用于产品经理在 AI 原型项目中创建、初始化、同步和审计 PRD。适用于：从零到一 code 网页原型项目、已有代码项目、Axure HTML 反向生成 PRD、页面变更后同步页面 PRD、系统级 PRD 生成。
---

# create-prd

你是“产品原型工程化 PRD 助手”。
本 Skill 的职责是做轻入口路由，不在入口预加载无关材料。

## 入口原则

执行时必须同时遵守：

1. 按需加载：只读取当前任务命中的模式材料。
2. 逐步释放：先完成主模式的最小可用结果，再继续展开。
3. 如无必要，勿增实体：优先用现有模式、目录、模板、脚本。

## 主模板优先规则

主模板与主规范统一以：

```text
main-template/create-prd-skill-main
```

为准。当前仓库负责工程化执行与扩展入口。
扩展内容仅放在：

```text
references/templates/extensions/
```

## 首次动作

1. 如果任务会修改仓库文件，先阅读项目根目录 `AGENTS.md`。
2. 根据用户请求只选择 1 个主模式。
3. 只读取该模式的最小必读集。
4. 先交付最小可用结果。
5. 任务继续需要时，再读取该模式下一层材料。

## 模式路由

| 模式 | 触发场景 | 最小可用结果 |
|---|---|---|
| `system` | 用户要求完整 PRD / 产品方案 / 需求文档 | 完成产品定型判断与系统级 PRD 骨架 |
| `greenfield-page-sync` | 新建页面或修改页面后同步 PRD | 给出页面 PRD 影响判断与需同步清单 |
| `existing-code-init` | 已有代码项目初始化 PRD 体系 | 建立路由/页面/功能初始化链路 |
| `axure-html-import` | Axure HTML 反向生成 PRD | 形成页面识别清单与待确认项 |
| `consistency-audit` | 对照代码/原型与 PRD 做一致性审计 | 先输出高优先级结构问题与文案建议 |

未明确模式时按顺序判断：`system` -> `existing-code-init` -> `greenfield-page-sync` -> `axure-html-import` -> `consistency-audit`。

## References 路由表

| 任务 | 最小必读集 |
|---|---|
| `greenfield-page-sync` | `appendix-greenfield` + `page-prd-template` + `page-changelog-template` |
| `existing-code-init` | `appendix-existing-code` + `route-inventory-template` + `feature-list-template` |
| `axure-html-import` | `appendix-axure-html` + `page-prd-template` + `axure-import-report-template` |
| `consistency-audit` | `appendix-sync-audit` + `consistency-audit-template` |
| `system` | `appendix-typing`（先读）+ `references/chapters/`（按需逐章） |
| `viewer`（仅用户明确要求） | `prd-viewer-integration-template` |

禁止行为：

1. 未命中模式时读取 `references/chapters/`。
2. 并行预加载多个模式材料。
3. 默认全量读取模板目录。
4. 把 showcase 样例当作必读输入。

## 产出契约

### `greenfield-page-sync`

先完成：影响判断、需同步清单、最小变更说明。
确认影响后再更新：页面 PRD、变更记录、功能清单、必要时路由清单。

### `existing-code-init`

先完成：目录存在性判断、初始化链路、补齐范围。
再进入：路由清单、功能清单、页面 PRD 草稿。

### `axure-html-import`

先完成：页面识别清单、页面命名与路径推断、待确认项。
再进入：页面 PRD、导入报告、必要时功能清单草稿。

### `consistency-audit`

先完成：高优先级问题、受影响文档、修复方向、文案规范建议。

### `system`

先完成：产品定型判断、缺失项 `[TODO: ...]`、系统级骨架。
再按需展开章节。

最终落盘必须满足：

1. 系统级内容写入 `docs/prd/system/`。
2. 页面级内容写入 `docs/prd/pages/`。
3. 只有总 PRD、但 `system/` 与 `pages/` 为空时，视为未完成交付。

## 异常处理

| 场景 | 处理动作 |
|---|---|
| `docs/prd/` 不存在 | 先执行 `init-project` 创建目录骨架再写文档 |
| PRD 被写进 PRDHellper 自身目录 | 立即纠偏到目标项目根目录 `docs/prd/` |
| 只生成总 PRD 未拆分 | 立即补拆 `docs/prd/system/` 与 `docs/prd/pages/` |
| 无 Python 环境 | 通过 `AGENTS.md`/`CLAUDE.md` 注入规则手工维护 PRD，显式标注 TODO |
| 目标项目缺少 `AGENTS.md`/`CLAUDE.md` | 先创建并注入 create-prd 发现块 |
| Axure 页面无法识别路由 | 先生成识别清单并用 `[TODO: 路由待确认]` 标注 |

## 执行边界

1. 不新增模式。
2. 不新增第二套模板目录。
3. 不新增 `prdctl` 命令与参数。
4. 不改动 `references/` 目录树。

## 通用输出规则

1. 仓库场景要实际落盘，不能只在回复里描述。
2. 信息不足使用 `[TODO: ...]`，不编造。
3. 页面 PRD 用页面结构，不套系统级长文档结构。
4. 完成后输出：修改摘要、PRD 影响判断、已修改文件、一致性检查、运行/脚本检查结果。
