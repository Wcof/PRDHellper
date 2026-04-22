# 页面内 PRD 查看器接入模板

> 目标：在页面右下角显示 `PRD` 按钮，点击后查看当前路由对应的页面 PRD。

## 1) 目录建议

```text
src/prd_docs/
├── route-map.ts
├── management-dispatch-center.md
└── ...
```

## 2) 路由映射表示例

```ts
// src/prd_docs/route-map.ts
export const PRD_ROUTE_MAP: Record<string, string> = {
  "/management/dispatch/center": "management-dispatch-center.md",
};
```

## 3) 行为规范（必须）

1. 右下角固定按钮文案：`PRD`。
2. 点击打开 PRD 面板；再次点击关闭。
3. 点击遮罩关闭；面板内必须有关闭按钮。
4. 内容区滚动，遮罩不滚动。
5. 路由未命中提示：`未找到该页面对应的 PRD 文件`。

## 4) UI 建议

- 浮动按钮：`position: fixed; right: 24px; bottom: 24px; z-index: 560;`
- 遮罩层：`z-index: 600;`
- 面板容器：`max-width: 980px; max-height: 80vh; overflow: auto;`

## 5) 最低验收

- [ ] 任意页面右下角可看到 `PRD` 按钮。
- [ ] 能打开并关闭 PRD 面板（按钮、遮罩、关闭按钮三种关闭方式至少两种生效）。
- [ ] 当前路由能命中并展示对应 PRD。
- [ ] 路由未命中时展示明确错误提示。
- [ ] 面板不遮挡系统级弹窗优先级（z-index 合理）。
