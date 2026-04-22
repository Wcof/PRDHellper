# Harness 扩展说明

当前 `scripts/harness/` 目录用于承载项目级约束入口。

现阶段只保留一个入口：

```text
scripts/harness/check_consistency.sh
```

设计原则：

1. 对外入口尽量稳定，避免每次扩展都改 Agent 调用方式。
2. 当前仍保留 `scripts/check_consistency.sh` 作为兼容包装器。
3. 后续如果需要新增更多约束，可继续在该目录下扩展，而不影响已有入口。

当前行为：

1. 自动识别 `PRD_ROOT`，优先顺序为 `docs/produc` -> `docs/product` -> `docs/prd`
2. 先按变更类型推断同步模式，再执行一致性检查
3. 默认 `HARNESS_SYNC_MODE=auto`

同步模式说明：

- `auto`：优先根据 git 变更判断
- `code`：强制执行 `sync --from-code`
- `prd`：强制执行 `sync --from-prd`
- `off`：跳过 sync，只做 diff-sync + audit

交接建议：

1. 对外始终让 Agent 调用 `scripts/check_consistency.sh`
2. 真实逻辑放在 `scripts/harness/` 内维护
3. 新增检查器时，优先保持旧入口不变，再扩展编排逻辑

建议扩展方向：

- `check_prd_sync.sh`：页面改动后的 PRD 同步门禁
- `check_axure_import.sh`：Axure 导入产物质量检查
- `check_traceability.sh`：page/feature/change 链路完整性检查
- `entry.sh`：按不同 profile 编排多个检查器
