#!/bin/bash
# PRDHellper 双击安装入口（macOS）

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "== PRDHellper 一键安装（双击入口）=="
echo
python3 "$SCRIPT_DIR/install.py"
STATUS=$?
echo
if [ "$STATUS" -eq 0 ]; then
  echo "安装流程已结束。"
else
  echo "安装流程异常退出（exit=$STATUS）。"
fi
echo
read -r -p "按回车键关闭窗口..."
exit "$STATUS"
