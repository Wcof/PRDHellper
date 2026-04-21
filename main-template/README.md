# 主模板内置说明

本目录用于内置主模板与主规范，避免依赖外部绝对路径。

当前主模板来源目录：

```text
main-template/create-prd-skill-main
```

使用规则：

1. 对外分发时，默认以本目录为主模板来源，不依赖本机环境路径。
2. 若要升级主模板，可替换 `create-prd-skill-main` 目录内容，并同步更新 `configs/template-policy.yaml` 说明。
3. 扩展内容请放在 `references/templates/extensions/`，不要直接破坏主模板原始结构。
