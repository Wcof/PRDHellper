# Changelog

## v0.4.1-root-cleanup

- 根目录安装入口统一为 `install.py`（跨平台自动识别系统）。
- 移除多端分散安装脚本：`i`、`install.sh`、`install.command`、`install.ps1`、`install.bat`。
- `scripts/install_skill.py` 默认项目路径改为当前工作目录，避免跨目录执行时装错位置。
- README 安装章节改为“单入口 + 一键安装”说明，根目录更简洁。

## v0.4.0-traceability-loop

- 主模板内置化：将 `create-prd-skill` 主模板/主规范内置到 `main-template/create-prd-skill-main`，不再依赖外部绝对路径。
- 新增使用教程目录：`docs/usage/`，补充“模板自定义与维护”指南，明确当前项目改法与默认模板改法。
- 新增更便捷安装入口：`./i`（超短命令）与 `install.command`（macOS 双击安装）。
- 新增多端安装入口：`install.sh`（macOS/Linux）、`install.bat`（Windows CMD/双击）、`install.ps1`（Windows PowerShell）。
- 新增中途安装唤醒词：当选择“跳过”或“不初始化”时，自动生成 `AI-PRD-WAKEUP-PROMPT.md` 并打印可复制 Prompt。
- 新增已有代码补全唤醒词：当安装模式选择“已有代码项目”时，自动生成可复制 Prompt 指导 AI 扫描并补全存量页面 PRD。
- 新增“页面内 PRD 查看入口”规范：支持右下角 `PRD` 按钮、遮罩面板、路由映射读取当前页面 PRD。
- 新增模板：`references/templates/prd-viewer-integration-template.md`，用于前端原型快速接入 PRD 查看器。
- 新增 `scripts/install_skill.py` 交互式安装向导：引导选择当前项目/全局安装，并确认 PRD 存储目录名。
- 新增重复安装治理：检测已安装并支持 `skip/reinstall/reinstall-reset` 三种策略。
- 新增“重置并迁移”能力：重置前自动备份旧 PRD 目录，重置后自动迁移核心文档并输出迁移报告。
- 修复自定义 PRD 目录场景：`AGENTS.md` 模板支持动态 `{PRD_ROOT}` 并输出正确命令。
- 修复一致性脚本目录透传：`scripts/check_consistency.sh` 支持 `PRD_ROOT` 环境变量并使用绝对脚本路径。
- 修复非 git 目录执行 `diff-sync --staged` 的噪音问题，改为静默降级为空变更。
- 优化安装拷贝过滤规则，避免把 `.pytest_cache/.mypy_cache/.ruff_cache` 等开发缓存带入目标项目。
- 新增 traceability 轻量元数据模型：页面 PRD frontmatter 包含 `page_id/route/code_paths/feature_ids/change_ids/last_synced_at`。
- 升级路由清单、功能清单、页面变更记录模板，增加可机器解析字段。
- `scripts/prdctl.py` 新增 `sync`、`diff-sync`，审计升级为 `audit --level basic|strict`，并支持 `--fail-on-high`。
- 新增 traceability 索引输出：`docs/product/.index/traceability.json`。
- 新增一致性检查脚本：`scripts/check_consistency.sh`。
- 新增 pre-commit 本地检查配置（warn 模式）和 GitHub Actions 一致性流程。
- 测试从单一 `--help` 扩展到 frontmatter、sync、strict audit 等核心能力。

## v0.3.0-engineered

- 将 create-prd 从单一系统级 PRD 生成器升级为工程化 PRD Skill。
- 新增五种模式：system、greenfield-page-sync、existing-code-init、axure-html-import、consistency-audit。
- 新增 `scripts/prdctl.py` 统一 CLI。
- 新增 Codex 仓库级安装路径 `.agents/skills/create-prd/`。
- 新增 `docs/product` 业务项目 PRD 目录初始化能力。
- 新增代码路由扫描、Axure HTML 页面扫描、页面 PRD 草稿生成、轻量审计能力。
- 新增页面 PRD、变更记录、功能清单、路由清单、AGENTS.md 模板。

## v0.2.0

- 原始 create-prd 系统级 PRD 生成能力。
