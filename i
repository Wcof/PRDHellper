#!/bin/bash
# 超短安装命令：./i

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1
exec python3 scripts/install_skill.py "$@"
