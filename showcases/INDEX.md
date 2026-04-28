# PRDHellper Showcase Index

本目录用于展示 create-prd 安装后的典型产出，不包含真实业务数据。

## 核心场景

| 场景 | 目标 | 关键产物 |
|---|---|---|
| 已有代码初始化 | 安装后自动补齐页面 PRD 草稿 | `docs/prd/pages/*.md`、`01-页面路由清单.md`、`02-功能清单.md` |
| Axure HTML 导入 | 从 Axure 页面识别并反向生成 PRD | `docs/prd/imports/`、`docs/prd/pages/*.md` |
| 系统级 PRD 拆分 | 防止只生成总 PRD | `docs/prd/system/*.md` + `docs/prd/pages/*.md` |
| 页面变更同步 | 页面改动后保持 PRD 同步 | `docs/prd/changelog/*.md`、`traceability.json` |
| 一致性审计 | 输出结构问题与文案建议 | `docs/prd/audit/*-consistency-audit.md` |
| 无 Python 发现链路 | 仅依赖发现文件唤醒 Skill | `AGENTS.md`、`CLAUDE.md`、`.agents/AGENTS.md`、`.claude/CLAUDE.md` |

## 样例产物

样例见：`showcases/sample-output/`

- `tree.txt`：安装后目标项目 `docs/prd/` 目录骨架
- `system-sample.md`：系统级 PRD 样例片段
- `page-sample.md`：页面级 PRD 样例片段
- `audit-sample.md`：一致性审计样例片段
