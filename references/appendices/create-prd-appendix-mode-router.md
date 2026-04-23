# 附录：模式选择器

## system

用户要求完整 PRD、产品方案、需求文档时使用。先输出系统级 PRD 骨架，再按需展开章节内容。

## greenfield-page-sync

从零到一 code 原型项目使用。每新增或修改页面，都根据页面代码、路由、mock 数据和对话上下文更新页面 PRD。

## existing-code-init

已有代码项目使用。先扫描路由和页面，建立 `docs/prd` 目录、页面路由清单、功能清单和初版页面 PRD。

## axure-html-import

已有 Axure HTML 项目使用。递归读取 HTML 页面，提取页面文本、按钮、表单、表格、导航，按页面生成 PRD。

## consistency-audit

用于检查代码/HTML 和 PRD 是否一致，输出问题清单和修复建议。
