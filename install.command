#!/bin/bash
# PRDHellper 双击安装入口（macOS）

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "== PRDHellper 一键安装（双击入口）=="
echo
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/install.py"
  STATUS=$?
else
  echo "[WARN] 未检测到 Python 3，切换到无 Python 安装模式。"
  bash "$SCRIPT_DIR/scripts/install_no_python.sh"
  STATUS=$?
fi
echo
if [ "$STATUS" -eq 0 ]; then
  echo "安装流程已结束。"
else
  echo "安装流程异常退出（exit=$STATUS）。"
fi
echo
read -r -p "按回车键关闭窗口..."
exit "$STATUS"
