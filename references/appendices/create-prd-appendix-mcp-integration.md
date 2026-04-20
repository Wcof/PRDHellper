# 附录：Skill / MCP / AGENTS.md 分工

## AGENTS.md

用于项目级稳定规则：目录结构、构建命令、PRD 同步要求、验收标准。

## Skill

用于可复用流程：如何初始化 PRD、如何写页面 PRD、如何解析 Axure、如何做一致性审计。

## MCP

当 Agent 需要访问本地仓库之外的工具时使用，例如：Figma、浏览器、内部文档、设计系统、接口平台。MCP 不替代 Skill，而是给 Skill 提供外部工具能力。

## 推荐组合

- 业务项目根目录：`AGENTS.md`
- 业务项目 Skill：`.agents/skills/create-prd/`
- 业务项目 PRD：`docs/product/`
- 外部设计/文档工具：按需配置 MCP
