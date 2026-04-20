#!/bin/bash
# macOS 可双击安装入口（Finder 中双击 .command 会在终端运行）

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "== create-prd 一键安装 =="
echo "正在启动安装向导..."
echo
python3 scripts/install_skill.py
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
