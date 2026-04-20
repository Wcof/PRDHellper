# AGENTS.md

## 项目定位

本项目是一个“AI 原型设计 + PRD 同步维护”的产品原型项目。Agent 不只是前端实现助手，还必须维护页面 PRD、功能清单、变更记录和一致性审计。

## PRD Skill

本项目使用 create-prd Skill：

```text
.agents/skills/create-prd/
```

当任务涉及 PRD 初始化、页面 PRD、Axure HTML 反向生成、页面变更同步 PRD、代码与 PRD 一致性审计时，必须优先参考该 Skill。

## PRD 输出目录

所有真实项目 PRD 产物必须输出到：

```text
docs/product/
```

目录说明：

```text
docs/product/00-项目上下文.md
docs/product/01-页面路由清单.md
docs/product/02-功能清单.md
docs/product/03-全局交互规则.md
docs/product/04-PRD编写规范.md
docs/product/system-prd/
docs/product/pages/
docs/product/changelog/
docs/product/audit/
docs/product/imports/
docs/product/templates/
```

## 页面 PRD 命名规则

路由 `/management/dispatch/center` 对应：

```text
docs/product/pages/management-dispatch-center.md
docs/product/changelog/management-dispatch-center-change.md
```

## 每次修改页面后的强制规则

每次修改页面代码后，必须判断是否影响 PRD。

必须同步 PRD 的情况：新增/删除功能、修改字段、按钮、筛选条件、页面结构、交互流程、状态流转、权限规则、数据展示逻辑、异常处理、入口、跳转、mock 数据结构、业务规则。

纯视觉样式优化可以不更新 PRD 主体，但必须更新页面变更记录。

## 新增页面规则

新增页面时必须同步新增或更新：

1. 页面代码
2. 页面路由
3. 页面 PRD
4. 页面变更记录
5. 页面路由清单
6. 功能清单

## 完成输出格式

每次任务完成后必须输出：

### 1. 页面修改摘要

### 2. PRD 影响判断

| 页面 | 是否影响 PRD | 原因 |
|---|---|---|

### 3. 已修改文件

| 文件类型 | 文件路径 | 修改说明 |
|---|---|---|

### 4. 一致性检查

| 检查项 | 结果 | 说明 |
|---|---|---|
| 页面代码是否已修改 |  |  |
| 页面 PRD 是否已同步 |  |  |
| 功能清单是否已同步 |  |  |
| 变更记录是否已同步 |  |  |
| 路由清单是否已同步 |  |  |

### 5. 运行检查结果

说明是否执行了构建、lint、类型检查或页面预览。如果未执行，需要说明原因。

## 优先级规则

当用户最新描述、现有 PRD、现有代码三者冲突时，优先级为：

1. 用户最新明确描述
2. 页面 PRD
3. 当前代码实现

如果根据用户最新描述修改了代码，必须同步修正 PRD。
