# 附录：工程化使用总则

create-prd 不应只是一个“生成 PRD 的提示词”，而应作为一个可复用工程能力：

- Skill 层：定义 Agent 什么时候触发、按什么模式工作。
- Template 层：提供页面 PRD、功能清单、变更记录、AGENTS.md 等标准模板。
- Script 层：提供初始化、代码扫描、Axure HTML 扫描、一致性审计等可执行动作。
- Project Docs 层：在业务项目中沉淀真实 PRD 产物。

推荐把 Skill 安装到业务项目 `.agents/skills/create-prd/`，把真实 PRD 输出到 `docs/prd/`。二者不要混在一起。
