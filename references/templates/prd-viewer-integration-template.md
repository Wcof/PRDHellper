# 页面内 PRD 查看器接入模板

> 目标：在页面顶部工具区提供 `PRD` 入口，点击后用全屏遮罩查看当前路由对应的页面级 PRD。

## 1) PRD 来源

真实 PRD 文件统一来自目标项目根目录：

```text
docs/prd/pages/<route-slug>.md
```

不要读取 `.agents/skills/create-prd/` 内的任何内容作为页面 PRD。

## 2) 路由映射规范

需要维护一个“当前路由 -> PRD slug”的映射表。最小结构如下：

```ts
type PrdRouteMap = Record<string, string>;

export const PRD_ROUTE_MAP: PrdRouteMap = {
  "/management/dispatch/center": "management-dispatch-center",
};
```

命中后读取：

```text
docs/prd/pages/<slug>.md
```

未命中时提示：

```text
未找到该页面对应的 PRD 文件
```

## 3) 交互规范（必须）

1. 页面顶部工具区固定显示 `PRD` 入口按钮。
2. 点击按钮打开全屏遮罩面板，再次点击或点关闭按钮可关闭。
3. 点击遮罩空白区可关闭。
4. 遮罩内内容区域单独滚动，页面底层不滚动。
5. 遮罩面板内必须按 Markdown 渲染 PRD 内容，不允许纯文本堆叠。

## 4) UI 约定

1. `PRD` 按钮放在页面顶部工具区，和页面标题、主操作区同层。
2. 遮罩层覆盖整个视口。
3. 面板主体居中显示，建议宽度 `min(1200px, 92vw)`。
4. 面板内容区建议高度 `min(80vh, 900px)`，超出后内部滚动。
5. 遮罩层 z-index 必须高于页面业务内容和常规弹层。

## 5) 最低验收

- [ ] 任意接入页面的顶部工具区可看到 `PRD` 按钮。
- [ ] 点击后可打开全屏遮罩。
- [ ] 能根据当前路由正确映射到 `docs/prd/pages/<slug>.md`。
- [ ] 路由未命中时展示 `未找到该页面对应的 PRD 文件`。
- [ ] PRD 内容按 Markdown 结构化渲染。
- [ ] 关闭方式至少支持：关闭按钮、遮罩点击。
